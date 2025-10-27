"""
GitHub Signals Collector - Collect behavioral signals from GitHub repositories.
"""
import os
import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from .base import BaseCollector


class GitHubSignalsCollector(BaseCollector):
    """
    Collect behavioral signals from GitHub repositories.
    
    Signals include:
    - Commit patterns and frequency
    - Security-related commits
    - Issue activity
    - Pull request patterns
    - Developer behavior
    """
    
    def __init__(self, output_dir: str = "data/raw/github", token: Optional[str] = None):
        """
        Initialize GitHub signals collector.
        
        Args:
            output_dir: Directory to save collected data
            token: GitHub personal access token (or use GITHUB_TOKEN env var)
        """
        super().__init__(output_dir)
        self.logger = logging.getLogger(__name__)
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable.")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
    
    def collect(
        self,
        repository: str,
        days_back: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Collect GitHub signals for a repository.
        
        Args:
            repository: Repository in format "owner/repo"
            days_back: Number of days to look back
        
        Returns:
            Statistics dictionary
        """
        since = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        self.logger.info(f"Collecting GitHub signals for {repository} (last {days_back} days)")
        
        # Collect all signals
        commits = self._collect_commits(repository, since)
        issues = self._collect_issues(repository, since)
        prs = self._collect_pull_requests(repository, since)
        repo_info = self._get_repository_info(repository)
        
        # Analyze signals
        signals = self._analyze_signals(commits, issues, prs, repo_info, days_back)
        
        # Save to file
        filename = f"{repository.replace('/', '_')}_signals.jsonl"
        output_file = self.save_jsonl([signals], filename)
        
        return {
            'repository': repository,
            'days_back': days_back,
            'total_commits': len(commits),
            'total_issues': len(issues),
            'total_prs': len(prs),
            'output_file': str(output_file),
        }
    
    def _collect_commits(self, repository: str, since: datetime) -> List[Dict]:
        """Collect commits since a date."""
        url = f"{self.base_url}/repos/{repository}/commits"
        params = {
            'since': since.isoformat(),
            'per_page': 100
        }
        
        commits = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            commits.extend(data)
            page += 1
            
            if len(data) < 100:  # Last page
                break
        
        return commits
    
    def _collect_issues(self, repository: str, since: datetime) -> List[Dict]:
        """Collect issues since a date."""
        url = f"{self.base_url}/repos/{repository}/issues"
        params = {
            'since': since.isoformat(),
            'state': 'all',
            'per_page': 100
        }
        
        issues = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            # Filter out pull requests (they appear in issues API)
            issues.extend([item for item in data if 'pull_request' not in item])
            page += 1
            
            if len(data) < 100:
                break
        
        return issues
    
    def _collect_pull_requests(self, repository: str, since: datetime) -> List[Dict]:
        """Collect pull requests since a date."""
        url = f"{self.base_url}/repos/{repository}/pulls"
        params = {
            'state': 'all',
            'sort': 'updated',
            'direction': 'desc',
            'per_page': 100
        }
        
        prs = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
            
            # Filter by date
            for pr in data:
                updated = datetime.fromisoformat(pr['updated_at'].replace('Z', '+00:00'))
                if updated >= since:
                    prs.append(pr)
                else:
                    return prs  # Stop when we hit old PRs
            
            page += 1
            
            if len(data) < 100:
                break
        
        return prs
    
    def _get_repository_info(self, repository: str) -> Dict:
        """Get repository metadata."""
        url = f"{self.base_url}/repos/{repository}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate collected GitHub signals data."""
        required_fields = ['repository', 'collected_at', 'days']
        return all(field in data for field in required_fields)
    
    def _analyze_signals(
        self,
        commits: List[Dict],
        issues: List[Dict],
        prs: List[Dict],
        repo_info: Dict,
        days_back: int
    ) -> Dict[str, Any]:
        """Analyze collected data to extract behavioral signals."""
        
        # Security keywords
        security_keywords = [
            'security', 'vulnerability', 'cve', 'exploit', 'xss', 'sql injection',
            'csrf', 'auth', 'authentication', 'authorization', 'password', 'token',
            'encryption', 'sanitize', 'escape', 'injection', 'rce', 'dos'
        ]
        
        # Analyze commits
        security_commits = 0
        late_night_commits = 0
        weekend_commits = 0
        unique_authors = set()
        auth_changes = False
        db_changes = False
        
        for commit in commits:
            message = commit.get('commit', {}).get('message', '').lower()
            
            # Security-related
            if any(keyword in message for keyword in security_keywords):
                security_commits += 1
            
            # Auth/DB changes
            if 'auth' in message or 'login' in message:
                auth_changes = True
            if 'database' in message or 'query' in message or 'sql' in message:
                db_changes = True
            
            # Author
            author = commit.get('commit', {}).get('author', {}).get('name')
            if author:
                unique_authors.add(author)
            
            # Time patterns
            date_str = commit.get('commit', {}).get('author', {}).get('date')
            if date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                if dt.hour < 6 or dt.hour > 22:  # Late night
                    late_night_commits += 1
                if dt.weekday() >= 5:  # Weekend
                    weekend_commits += 1
        
        # Analyze issues
        security_issues = 0
        critical_issues = 0
        open_issues = 0
        
        for issue in issues:
            title = issue.get('title', '').lower()
            body = issue.get('body', '').lower() if issue.get('body') else ''
            labels = [label.get('name', '').lower() for label in issue.get('labels', [])]
            
            if any(keyword in title or keyword in body for keyword in security_keywords):
                security_issues += 1
            
            if any(label in ['critical', 'high', 'security'] for label in labels):
                critical_issues += 1
            
            if issue.get('state') == 'open':
                open_issues += 1
        
        # Analyze PRs
        security_prs = 0
        emergency_fixes = 0
        
        for pr in prs:
            title = pr.get('title', '').lower()
            body = pr.get('body', '').lower() if pr.get('body') else ''
            
            if any(keyword in title or keyword in body for keyword in security_keywords):
                security_prs += 1
            
            if 'hotfix' in title or 'emergency' in title or 'urgent' in title:
                emergency_fixes += 1
        
        # Calculate patterns
        commit_frequency = len(commits) / days_back if days_back > 0 else 0
        avg_commits_per_day = 1.0  # Baseline
        commit_spike = commit_frequency > avg_commits_per_day * 2
        
        return {
            'repository': repo_info.get('full_name'),
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'days': days_back,
            
            # Commit signals
            'commit_count': len(commits),
            'security_commits': security_commits,
            'commit_spike': commit_spike,
            'late_night_commits': late_night_commits,
            'weekend_activity': 'High' if weekend_commits > len(commits) * 0.3 else 'Normal',
            'unusual_patterns': 'Detected' if (late_night_commits > 5 or commit_spike) else 'None detected',
            
            # Issue signals
            'open_issues': open_issues,
            'security_issues': security_issues,
            'critical_issues': critical_issues,
            'discussion_intensity': 'High' if len(issues) > 20 else 'Normal',
            
            # PR signals
            'pr_count': len(prs),
            'security_prs': security_prs,
            'emergency_fixes': emergency_fixes,
            
            # Developer signals
            'contributors': len(unique_authors),
            'new_contributors': 0,  # TODO: Compare with historical data
            
            # Code change signals
            'files_modified': 0,  # TODO: Analyze commit diffs
            'security_files': 0,  # TODO: Detect security-sensitive files
            'auth_changes': auth_changes,
            'db_changes': db_changes,
            
            # Repository info
            'stars': repo_info.get('stargazers_count', 0),
            'forks': repo_info.get('forks_count', 0),
            'watchers': repo_info.get('watchers_count', 0),
        }
