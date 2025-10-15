"""GitHub signal collector for time-series data."""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, List, Optional

from ...data_sources.base import BaseDataSource, DataSourceError
from ..models import CommitSignal, PRSignal, IssueSignal, ReleaseSignal
from ..exceptions import GitHubRateLimitError, RepositoryNotFoundError, TimeRangeError


class GitHubSignalCollector(BaseDataSource):
    """Collect time-series signals from GitHub repositories."""
    
    source_name = "github_signals"
    BASE_URL = "https://api.github.com"
    
    def __init__(
        self,
        *,
        timeout: float = 30.0,
        rate_limit_sleep: float = 1.0,
        github_token: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize GitHub signal collector.
        
        Args:
            timeout: Request timeout in seconds
            rate_limit_sleep: Sleep time between requests
            github_token: GitHub personal access token
            **kwargs: Additional arguments for BaseDataSource
        """
        super().__init__(timeout=timeout, rate_limit_sleep=rate_limit_sleep, **kwargs)
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        
        if self.github_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            })
    
    def _handle_rate_limit(self, response) -> None:
        """Handle GitHub API rate limiting.
        
        Args:
            response: Response object from GitHub API
            
        Raises:
            GitHubRateLimitError: If rate limit is exceeded
        """
        if response.status_code == 403:
            rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", "0")
            if rate_limit_remaining == "0":
                reset_time = int(response.headers.get("X-RateLimit-Reset", "0"))
                wait_time = max(reset_time - time.time(), 0)
                raise GitHubRateLimitError(
                    f"GitHub API rate limit exceeded. Reset in {wait_time:.0f} seconds"
                )
        
        if response.status_code == 404:
            raise RepositoryNotFoundError("Repository not found or not accessible")
    
    def collect_commit_history(
        self,
        repo: str,
        since: datetime,
        until: datetime,
    ) -> List[CommitSignal]:
        """Collect commit history within time range.
        
        Args:
            repo: Repository in format "owner/repo"
            since: Start of time range
            until: End of time range
            
        Returns:
            List of CommitSignal objects
            
        Raises:
            TimeRangeError: If time range is invalid
            RepositoryNotFoundError: If repository not found
            GitHubRateLimitError: If rate limit exceeded
        """
        if since >= until:
            raise TimeRangeError("'since' must be before 'until'")
        
        commits = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.BASE_URL}/repos/{repo}/commits"
            params = {
                "since": since.isoformat(),
                "until": until.isoformat(),
                "per_page": per_page,
                "page": page,
            }
            
            try:
                response = self._request("GET", url, params=params)
                self._handle_rate_limit(response)
            except DataSourceError as e:
                if "404" in str(e):
                    raise RepositoryNotFoundError(f"Repository {repo} not found")
                raise
            
            data = response.json()
            
            if not data:
                break
            
            for commit_data in data:
                commit = commit_data.get("commit", {})
                author_info = commit.get("author", {})
                
                # Get detailed commit info for files changed
                commit_sha = commit_data.get("sha")
                commit_detail = self._get_commit_detail(repo, commit_sha)
                
                commits.append(CommitSignal(
                    sha=commit_sha,
                    message=commit.get("message", ""),
                    author=author_info.get("name", "Unknown"),
                    timestamp=datetime.fromisoformat(
                        author_info.get("date", "").replace("Z", "+00:00")
                    ),
                    files_changed=commit_detail.get("files_changed", []),
                    lines_added=commit_detail.get("lines_added", 0),
                    lines_deleted=commit_detail.get("lines_deleted", 0),
                    metadata={
                        "url": commit_data.get("html_url"),
                        "author_email": author_info.get("email"),
                    },
                ))
            
            # Rate limiting
            time.sleep(self.rate_limit_sleep)
            
            # Check if there are more pages
            if len(data) < per_page:
                break
            
            page += 1
        
        return commits
    
    def _get_commit_detail(self, repo: str, sha: str) -> dict:
        """Get detailed commit information including file changes.
        
        Args:
            repo: Repository in format "owner/repo"
            sha: Commit SHA
            
        Returns:
            Dictionary with files_changed, lines_added, lines_deleted
        """
        url = f"{self.BASE_URL}/repos/{repo}/commits/{sha}"
        
        try:
            response = self._request("GET", url)
            data = response.json()
            
            files = data.get("files", [])
            files_changed = [f.get("filename") for f in files]
            
            stats = data.get("stats", {})
            lines_added = stats.get("additions", 0)
            lines_deleted = stats.get("deletions", 0)
            
            time.sleep(self.rate_limit_sleep)
            
            return {
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
            }
        except Exception:
            # If we can't get details, return empty data
            return {
                "files_changed": [],
                "lines_added": 0,
                "lines_deleted": 0,
            }
    
    def collect_pr_history(
        self,
        repo: str,
        since: datetime,
        until: datetime,
    ) -> List[PRSignal]:
        """Collect pull request history.
        
        Args:
            repo: Repository in format "owner/repo"
            since: Start of time range
            until: End of time range
            
        Returns:
            List of PRSignal objects
            
        Raises:
            TimeRangeError: If time range is invalid
            RepositoryNotFoundError: If repository not found
            GitHubRateLimitError: If rate limit exceeded
        """
        if since >= until:
            raise TimeRangeError("'since' must be before 'until'")
        
        prs = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.BASE_URL}/repos/{repo}/pulls"
            params = {
                "state": "all",  # Get both open and closed PRs
                "sort": "created",
                "direction": "desc",
                "per_page": per_page,
                "page": page,
            }
            
            try:
                response = self._request("GET", url, params=params)
                self._handle_rate_limit(response)
            except DataSourceError as e:
                if "404" in str(e):
                    raise RepositoryNotFoundError(f"Repository {repo} not found")
                raise
            
            data = response.json()
            
            if not data:
                break
            
            for pr_data in data:
                created_at = datetime.fromisoformat(
                    pr_data.get("created_at", "").replace("Z", "+00:00")
                )
                
                # Filter by time range
                if created_at < since:
                    # PRs are sorted by creation date desc, so we can stop
                    return prs
                
                if created_at > until:
                    continue
                
                merged_at_str = pr_data.get("merged_at")
                merged_at = None
                if merged_at_str:
                    merged_at = datetime.fromisoformat(merged_at_str.replace("Z", "+00:00"))
                
                # Get review count
                review_count = self._get_pr_review_count(repo, pr_data.get("number"))
                
                labels = [label.get("name", "") for label in pr_data.get("labels", [])]
                
                prs.append(PRSignal(
                    number=pr_data.get("number"),
                    title=pr_data.get("title", ""),
                    description=pr_data.get("body", ""),
                    author=pr_data.get("user", {}).get("login", "Unknown"),
                    created_at=created_at,
                    merged_at=merged_at,
                    labels=labels,
                    review_count=review_count,
                    metadata={
                        "url": pr_data.get("html_url"),
                        "state": pr_data.get("state"),
                        "comments": pr_data.get("comments", 0),
                    },
                ))
            
            time.sleep(self.rate_limit_sleep)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return prs
    
    def _get_pr_review_count(self, repo: str, pr_number: int) -> int:
        """Get number of reviews for a PR.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: PR number
            
        Returns:
            Number of reviews
        """
        url = f"{self.BASE_URL}/repos/{repo}/pulls/{pr_number}/reviews"
        
        try:
            response = self._request("GET", url)
            reviews = response.json()
            time.sleep(self.rate_limit_sleep)
            return len(reviews)
        except Exception:
            return 0
    
    def collect_issue_history(
        self,
        repo: str,
        since: datetime,
        until: datetime,
    ) -> List[IssueSignal]:
        """Collect issue discussion history.
        
        Args:
            repo: Repository in format "owner/repo"
            since: Start of time range
            until: End of time range
            
        Returns:
            List of IssueSignal objects
            
        Raises:
            TimeRangeError: If time range is invalid
            RepositoryNotFoundError: If repository not found
            GitHubRateLimitError: If rate limit exceeded
        """
        if since >= until:
            raise TimeRangeError("'since' must be before 'until'")
        
        # Security-related keywords to identify
        security_keywords = [
            "vulnerability", "security", "exploit", "cve", "patch",
            "malicious", "attack", "injection", "xss", "csrf",
            "authentication", "authorization", "privilege", "escalation"
        ]
        
        issues = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.BASE_URL}/repos/{repo}/issues"
            params = {
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": per_page,
                "page": page,
            }
            
            try:
                response = self._request("GET", url, params=params)
                self._handle_rate_limit(response)
            except DataSourceError as e:
                if "404" in str(e):
                    raise RepositoryNotFoundError(f"Repository {repo} not found")
                raise
            
            data = response.json()
            
            if not data:
                break
            
            for issue_data in data:
                # Skip pull requests (they appear in issues API too)
                if "pull_request" in issue_data:
                    continue
                
                created_at = datetime.fromisoformat(
                    issue_data.get("created_at", "").replace("Z", "+00:00")
                )
                
                # Filter by time range
                if created_at < since:
                    return issues
                
                if created_at > until:
                    continue
                
                closed_at_str = issue_data.get("closed_at")
                closed_at = None
                if closed_at_str:
                    closed_at = datetime.fromisoformat(closed_at_str.replace("Z", "+00:00"))
                
                # Get comments
                comments = self._get_issue_comments(repo, issue_data.get("number"))
                
                labels = [label.get("name", "") for label in issue_data.get("labels", [])]
                
                # Check for security keywords
                body = issue_data.get("body", "").lower()
                title = issue_data.get("title", "").lower()
                has_security_keyword = any(
                    keyword in body or keyword in title
                    for keyword in security_keywords
                )
                
                issues.append(IssueSignal(
                    number=issue_data.get("number"),
                    title=issue_data.get("title", ""),
                    body=issue_data.get("body", ""),
                    author=issue_data.get("user", {}).get("login", "Unknown"),
                    created_at=created_at,
                    closed_at=closed_at,
                    labels=labels,
                    comments=comments,
                    metadata={
                        "url": issue_data.get("html_url"),
                        "state": issue_data.get("state"),
                        "has_security_keyword": has_security_keyword,
                        "comment_count": len(comments),
                    },
                ))
            
            time.sleep(self.rate_limit_sleep)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return issues
    
    def _get_issue_comments(self, repo: str, issue_number: int) -> List[str]:
        """Get comments for an issue.
        
        Args:
            repo: Repository in format "owner/repo"
            issue_number: Issue number
            
        Returns:
            List of comment bodies
        """
        url = f"{self.BASE_URL}/repos/{repo}/issues/{issue_number}/comments"
        
        try:
            response = self._request("GET", url)
            comments_data = response.json()
            time.sleep(self.rate_limit_sleep)
            return [c.get("body", "") for c in comments_data]
        except Exception:
            return []
    
    def collect_release_history(
        self,
        repo: str,
        since: datetime,
        until: datetime,
    ) -> List[ReleaseSignal]:
        """Collect release history with dependency changes.
        
        Args:
            repo: Repository in format "owner/repo"
            since: Start of time range
            until: End of time range
            
        Returns:
            List of ReleaseSignal objects
            
        Raises:
            TimeRangeError: If time range is invalid
            RepositoryNotFoundError: If repository not found
            GitHubRateLimitError: If rate limit exceeded
        """
        if since >= until:
            raise TimeRangeError("'since' must be before 'until'")
        
        releases = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.BASE_URL}/repos/{repo}/releases"
            params = {
                "per_page": per_page,
                "page": page,
            }
            
            try:
                response = self._request("GET", url, params=params)
                self._handle_rate_limit(response)
            except DataSourceError as e:
                if "404" in str(e):
                    raise RepositoryNotFoundError(f"Repository {repo} not found")
                raise
            
            data = response.json()
            
            if not data:
                break
            
            for release_data in data:
                published_at_str = release_data.get("published_at")
                if not published_at_str:
                    continue
                
                published_at = datetime.fromisoformat(
                    published_at_str.replace("Z", "+00:00")
                )
                
                # Filter by time range
                if published_at < since:
                    return releases
                
                if published_at > until:
                    continue
                
                # Note: Getting actual dependency information requires
                # parsing package manifest files (requirements.txt, package.json, etc.)
                # For now, we'll store basic release info
                releases.append(ReleaseSignal(
                    version=release_data.get("tag_name", ""),
                    published_at=published_at,
                    dependencies={},  # Would need to parse manifest files
                    dependency_diff=None,
                    metadata={
                        "url": release_data.get("html_url"),
                        "name": release_data.get("name", ""),
                        "body": release_data.get("body", ""),
                        "prerelease": release_data.get("prerelease", False),
                    },
                ))
            
            time.sleep(self.rate_limit_sleep)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return releases
