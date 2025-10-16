"""Dataset validator for quality checks."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from ...prediction.signal_collectors.github_signals import GitHubSignalCollector


logger = logging.getLogger(__name__)


class DatasetValidator:
    """Validate CVE dataset quality.
    
    Checks:
    1. GitHub repository exists and is accessible
    2. Sufficient commit history (>= min_commits)
    3. Sufficient time range for signal collection (>= min_days)
    4. Repository is active (recent commits)
    """
    
    def __init__(
        self,
        *,
        min_commits: int = 50,
        min_days: int = 180,
        max_days_since_activity: int = 365,
        github_token: Optional[str] = None,
    ):
        """Initialize validator.
        
        Args:
            min_commits: Minimum number of commits required
            min_days: Minimum days of history required
            max_days_since_activity: Maximum days since last activity
            github_token: GitHub token for API access
        """
        self.min_commits = min_commits
        self.min_days = min_days
        self.max_days_since_activity = max_days_since_activity
        
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_collector = GitHubSignalCollector(
            github_token=self.github_token,
        )
    
    def validate_cve(self, cve_record: Dict) -> Dict:
        """Validate a single CVE record.
        
        Args:
            cve_record: CVE record with github_repo field
        
        Returns:
            Validation result dict with:
                - valid: bool
                - score: float (0-1)
                - issues: List[str]
                - metadata: Dict
        """
        cve_id = cve_record.get("cve_id", "UNKNOWN")
        github_repo = cve_record.get("github_repo")
        
        if not github_repo:
            return {
                "valid": False,
                "score": 0.0,
                "issues": ["No GitHub repository"],
                "metadata": {},
            }
        
        issues = []
        score = 1.0
        metadata = {}
        
        # Check 1: Repository exists
        repo_exists = self._check_repo_exists(github_repo)
        if not repo_exists:
            issues.append(f"Repository {github_repo} not found or not accessible")
            score = 0.0
            return {
                "valid": False,
                "score": score,
                "issues": issues,
                "metadata": metadata,
            }
        
        # Check 2: Get repository info
        repo_info = self._get_repo_info(github_repo)
        if not repo_info:
            issues.append("Could not fetch repository information")
            score *= 0.5
        else:
            metadata.update(repo_info)
            
            # Check commit count
            if repo_info.get("commit_count", 0) < self.min_commits:
                issues.append(
                    f"Insufficient commits: {repo_info['commit_count']} < {self.min_commits}"
                )
                score *= 0.7
            
            # Check repository age
            created_at = repo_info.get("created_at")
            if created_at:
                age_days = (datetime.now() - created_at).days
                if age_days < self.min_days:
                    issues.append(
                        f"Repository too young: {age_days} days < {self.min_days} days"
                    )
                    score *= 0.7
                metadata["age_days"] = age_days
            
            # Check recent activity
            last_commit = repo_info.get("last_commit_date")
            if last_commit:
                days_since_activity = (datetime.now() - last_commit).days
                if days_since_activity > self.max_days_since_activity:
                    issues.append(
                        f"Repository inactive: {days_since_activity} days since last commit"
                    )
                    score *= 0.8
                metadata["days_since_activity"] = days_since_activity
        
        # Check 3: Verify CVE disclosure date is after repo creation
        published_date = cve_record.get("published_date")
        if published_date and repo_info.get("created_at"):
            try:
                pub_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
                if pub_date < repo_info["created_at"]:
                    issues.append("CVE published before repository creation")
                    score *= 0.5
            except:
                pass
        
        valid = score >= 0.5 and len(issues) == 0
        
        return {
            "valid": valid,
            "score": score,
            "issues": issues,
            "metadata": metadata,
        }
    
    def validate_dataset(self, cve_records: List[Dict]) -> Dict:
        """Validate entire dataset.
        
        Args:
            cve_records: List of CVE records
        
        Returns:
            Validation summary dict
        """
        logger.info(f"Validating {len(cve_records)} CVE records...")
        
        results = []
        valid_count = 0
        
        for cve_record in cve_records:
            result = self.validate_cve(cve_record)
            results.append({
                "cve_id": cve_record.get("cve_id"),
                "github_repo": cve_record.get("github_repo"),
                **result,
            })
            
            if result["valid"]:
                valid_count += 1
        
        # Calculate statistics
        scores = [r["score"] for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Group issues
        all_issues = []
        for r in results:
            all_issues.extend(r["issues"])
        
        from collections import Counter
        issue_counts = Counter(all_issues)
        
        summary = {
            "total_cves": len(cve_records),
            "valid_cves": valid_count,
            "invalid_cves": len(cve_records) - valid_count,
            "validation_rate": valid_count / len(cve_records) if cve_records else 0.0,
            "avg_score": avg_score,
            "common_issues": dict(issue_counts.most_common(10)),
            "results": results,
        }
        
        logger.info(f"Validation complete:")
        logger.info(f"  Valid: {valid_count}/{len(cve_records)} ({summary['validation_rate']:.1%})")
        logger.info(f"  Avg Score: {avg_score:.2f}")
        
        if issue_counts:
            logger.info(f"  Common Issues:")
            for issue, count in issue_counts.most_common(5):
                logger.info(f"    - {issue}: {count}")
        
        return summary
    
    def _check_repo_exists(self, github_repo: str) -> bool:
        """Check if GitHub repository exists.
        
        Args:
            github_repo: Repository in format "owner/repo"
        
        Returns:
            True if repository exists and is accessible
        """
        url = f"https://api.github.com/repos/{github_repo}"
        headers = {}
        
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _get_repo_info(self, github_repo: str) -> Optional[Dict]:
        """Get repository information.
        
        Args:
            github_repo: Repository in format "owner/repo"
        
        Returns:
            Repository info dict or None
        """
        url = f"https://api.github.com/repos/{github_repo}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Get commit count (approximate from default branch)
            commits_url = f"https://api.github.com/repos/{github_repo}/commits"
            commits_response = requests.get(
                commits_url,
                headers=headers,
                params={"per_page": 1},
                timeout=10,
            )
            
            # Estimate commit count from pagination
            commit_count = 0
            if commits_response.status_code == 200:
                link_header = commits_response.headers.get("Link", "")
                if "last" in link_header:
                    # Extract page number from last link
                    import re
                    match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if match:
                        commit_count = int(match.group(1))
                else:
                    # No pagination, small repo
                    commit_count = len(commits_response.json())
            
            # Get last commit date
            last_commit_date = None
            if commits_response.status_code == 200:
                commits = commits_response.json()
                if commits:
                    commit_date_str = commits[0].get("commit", {}).get("author", {}).get("date")
                    if commit_date_str:
                        last_commit_date = datetime.fromisoformat(
                            commit_date_str.replace("Z", "+00:00")
                        )
            
            # Parse created date
            created_at = None
            created_at_str = data.get("created_at")
            if created_at_str:
                created_at = datetime.fromisoformat(
                    created_at_str.replace("Z", "+00:00")
                )
            
            return {
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "created_at": created_at,
                "last_commit_date": last_commit_date,
                "commit_count": commit_count,
                "language": data.get("language"),
                "archived": data.get("archived", False),
            }
        
        except Exception as e:
            logger.error(f"Error fetching repo info for {github_repo}: {e}")
            return None
