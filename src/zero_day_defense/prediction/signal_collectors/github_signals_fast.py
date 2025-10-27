"""Fast GitHub signal collector for real-time code push analysis.

This version is optimized for speed:
1. No N+1 queries (no detailed commit info)
2. Minimal API calls
3. Focus on recent activity only
4. Caching support
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from typing import Any, List, Optional, Dict
import json
from pathlib import Path

from ...data_sources.base import BaseDataSource, DataSourceError
from ..models import CommitSignal
from ..exceptions import GitHubRateLimitError, RepositoryNotFoundError, TimeRangeError


class FastGitHubSignalCollector(BaseDataSource):
    """Fast GitHub signal collector for real-time predictions."""
    
    source_name = "github_signals_fast"
    BASE_URL = "https://api.github.com"
    
    def __init__(
        self,
        *,
        timeout: float = 10.0,
        rate_limit_sleep: float = 0.1,  # Much faster
        github_token: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = 3600,  # 1 hour cache
        **kwargs: Any,
    ) -> None:
        """Initialize fast GitHub signal collector.
        
        Args:
            timeout: Request timeout in seconds
            rate_limit_sleep: Sleep time between requests (reduced)
            github_token: GitHub personal access token
            cache_dir: Directory for caching results
            cache_ttl: Cache time-to-live in seconds
            **kwargs: Additional arguments for BaseDataSource
        """
        super().__init__(timeout=timeout, rate_limit_sleep=rate_limit_sleep, **kwargs)
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.cache_dir = cache_dir or Path("cache/github_signals")
        self.cache_ttl = cache_ttl
        
        if self.github_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            })
        
        # Create cache directory
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, repo: str, since: datetime, until: datetime) -> str:
        """Generate cache key for a query.
        
        Args:
            repo: Repository name
            since: Start time
            until: End time
            
        Returns:
            Cache key string
        """
        return f"{repo.replace('/', '_')}_{since.date()}_{until.date()}"
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Load data from cache if available and fresh.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None
        """
        if not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        # Check if cache is still fresh
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age > self.cache_ttl:
            return None
        
        try:
            with cache_file.open("r") as f:
                return json.load(f)
        except Exception:
            return None
    
    def _save_to_cache(self, cache_key: str, data: List[Dict]) -> None:
        """Save data to cache.
        
        Args:
            cache_key: Cache key
            data: Data to cache
        """
        if not self.cache_dir:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with cache_file.open("w") as f:
                json.dump(data, f)
        except Exception:
            pass  # Ignore cache errors
    
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
    
    def collect_recent_commits(
        self,
        repo: str,
        days: int = 30,
        max_commits: int = 100,
    ) -> List[CommitSignal]:
        """Collect recent commits (optimized for speed).
        
        This method:
        - Only fetches basic commit info (no detailed file changes)
        - Uses caching to avoid repeated API calls
        - Limits the number of commits
        
        Args:
            repo: Repository in format "owner/repo"
            days: Number of days to look back
            max_commits: Maximum number of commits to fetch
            
        Returns:
            List of CommitSignal objects
            
        Raises:
            RepositoryNotFoundError: If repository not found
            GitHubRateLimitError: If rate limit exceeded
        """
        until = datetime.now()
        since = until - timedelta(days=days)
        
        # Check cache first
        cache_key = self._get_cache_key(repo, since, until)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data:
            return [self._parse_commit(c) for c in cached_data]
        
        # Fetch from API
        commits = []
        url = f"{self.BASE_URL}/repos/{repo}/commits"
        params = {
            "since": since.isoformat(),
            "until": until.isoformat(),
            "per_page": min(max_commits, 100),
            "page": 1,
        }
        
        try:
            response = self._request("GET", url, params=params)
            self._handle_rate_limit(response)
        except DataSourceError as e:
            if "404" in str(e):
                raise RepositoryNotFoundError(f"Repository {repo} not found")
            raise
        
        data = response.json()
        
        # Save to cache
        self._save_to_cache(cache_key, data[:max_commits])
        
        # Parse commits (without detailed info)
        for commit_data in data[:max_commits]:
            commits.append(self._parse_commit(commit_data))
        
        return commits
    
    def _parse_commit(self, commit_data: Dict) -> CommitSignal:
        """Parse commit data without making additional API calls.
        
        Args:
            commit_data: Raw commit data from GitHub API
            
        Returns:
            CommitSignal object
        """
        commit = commit_data.get("commit", {})
        author_info = commit.get("author", {})
        
        # Extract basic file info from commit message (heuristic)
        message = commit.get("message", "")
        files_changed = self._extract_files_from_message(message)
        
        return CommitSignal(
            sha=commit_data.get("sha"),
            message=message,
            author=author_info.get("name", "Unknown"),
            timestamp=datetime.fromisoformat(
                author_info.get("date", "").replace("Z", "+00:00")
            ),
            files_changed=files_changed,
            lines_added=0,  # Not available without detailed call
            lines_deleted=0,  # Not available without detailed call
            metadata={
                "url": commit_data.get("html_url"),
                "author_email": author_info.get("email"),
            },
        )
    
    def _extract_files_from_message(self, message: str) -> List[str]:
        """Extract file names from commit message (heuristic).
        
        Args:
            message: Commit message
            
        Returns:
            List of file names found in message
        """
        # Simple heuristic: look for common file extensions
        import re
        
        extensions = [
            r'\.py', r'\.js', r'\.ts', r'\.java', r'\.go', r'\.rs',
            r'\.c', r'\.cpp', r'\.h', r'\.rb', r'\.php', r'\.sql',
            r'\.json', r'\.yaml', r'\.yml', r'\.xml', r'\.html',
        ]
        
        pattern = r'\b[\w/\-\.]+(?:' + '|'.join(extensions) + r')\b'
        files = re.findall(pattern, message, re.IGNORECASE)
        
        return files[:10]  # Limit to 10 files
    
    def analyze_push(
        self,
        repo: str,
        commit_sha: str,
        context_days: int = 30,
    ) -> Dict[str, Any]:
        """Analyze a specific push/commit in context of recent activity.
        
        This is the main method for real-time prediction on code push.
        
        Args:
            repo: Repository in format "owner/repo"
            commit_sha: SHA of the commit being pushed
            context_days: Days of context to analyze
            
        Returns:
            Analysis result with risk score and signals
        """
        # Get recent commits for context
        recent_commits = self.collect_recent_commits(repo, days=context_days)
        
        # Get the specific commit being analyzed
        target_commit = self._get_single_commit(repo, commit_sha)
        
        # Analyze in context
        analysis = {
            "target_commit": target_commit,
            "recent_commits": recent_commits,
            "context_days": context_days,
            "total_recent_commits": len(recent_commits),
            "analysis_timestamp": datetime.now().isoformat(),
        }
        
        return analysis
    
    def _get_single_commit(self, repo: str, sha: str) -> CommitSignal:
        """Get a single commit (for the push being analyzed).
        
        Args:
            repo: Repository name
            sha: Commit SHA
            
        Returns:
            CommitSignal object
        """
        url = f"{self.BASE_URL}/repos/{repo}/commits/{sha}"
        
        try:
            response = self._request("GET", url)
            commit_data = response.json()
            return self._parse_commit(commit_data)
        except Exception as e:
            raise DataSourceError(f"Failed to fetch commit {sha}: {e}")
    
    def get_repo_stats(self, repo: str) -> Dict[str, Any]:
        """Get basic repository statistics (cached).
        
        Args:
            repo: Repository name
            
        Returns:
            Repository statistics
        """
        cache_key = f"repo_stats_{repo.replace('/', '_')}"
        cached = self._load_from_cache(cache_key)
        
        if cached:
            return cached[0] if cached else {}
        
        url = f"{self.BASE_URL}/repos/{repo}"
        
        try:
            response = self._request("GET", url)
            data = response.json()
            
            stats = {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "watchers": data.get("watchers_count", 0),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "language": data.get("language"),
            }
            
            self._save_to_cache(cache_key, [stats])
            return stats
            
        except Exception:
            return {}


# Convenience function for quick analysis
def analyze_code_push(
    repo: str,
    commit_sha: str,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Quick analysis of a code push.
    
    Args:
        repo: Repository in format "owner/repo"
        commit_sha: SHA of the commit
        github_token: GitHub token (optional)
        
    Returns:
        Analysis result
    """
    collector = FastGitHubSignalCollector(github_token=github_token)
    return collector.analyze_push(repo, commit_sha)
