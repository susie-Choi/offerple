"""Feature extraction from signals."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List

from ..models import CommitSignal, PRSignal, IssueSignal, ReleaseSignal
from ..exceptions import InsufficientDataError


class FeatureExtractor:
    """Extract structural features from signals."""
    
    def extract_commit_features(
        self,
        commits: List[CommitSignal],
    ) -> Dict[str, float]:
        """Extract features from commit history.
        
        Features:
        - commit_frequency: commits per day
        - lines_added_avg: average lines added
        - lines_deleted_avg: average lines deleted
        - lines_added_total: total lines added
        - lines_deleted_total: total lines deleted
        - files_per_commit_avg: average files changed per commit
        - author_diversity: number of unique authors
        - author_concentration: Gini coefficient of commit distribution
        - commit_hour_morning: ratio of commits in morning (6-12)
        - commit_hour_afternoon: ratio of commits in afternoon (12-18)
        - commit_hour_evening: ratio of commits in evening (18-24)
        - commit_hour_night: ratio of commits at night (0-6)
        - file_type_py: ratio of Python files
        - file_type_js: ratio of JavaScript files
        - file_type_java: ratio of Java files
        - file_type_config: ratio of config files
        - file_type_test: ratio of test files
        - file_type_doc: ratio of documentation files
        
        Args:
            commits: List of CommitSignal objects
            
        Returns:
            Dictionary of feature names to values
            
        Raises:
            InsufficientDataError: If no commits provided
        """
        if not commits:
            raise InsufficientDataError("No commits provided for feature extraction")
        
        features = {}
        
        # Time-based features
        timestamps = [c.timestamp for c in commits]
        time_span = (max(timestamps) - min(timestamps)).total_seconds() / 86400  # days
        features["commit_frequency"] = len(commits) / max(time_span, 1.0)
        
        # Lines changed features
        total_added = sum(c.lines_added for c in commits)
        total_deleted = sum(c.lines_deleted for c in commits)
        features["lines_added_avg"] = total_added / len(commits)
        features["lines_deleted_avg"] = total_deleted / len(commits)
        features["lines_added_total"] = float(total_added)
        features["lines_deleted_total"] = float(total_deleted)
        
        # Files changed features
        total_files = sum(len(c.files_changed) for c in commits)
        features["files_per_commit_avg"] = total_files / len(commits)
        
        # Author diversity features
        authors = [c.author for c in commits]
        unique_authors = set(authors)
        features["author_diversity"] = float(len(unique_authors))
        
        # Author concentration (Gini coefficient)
        author_counts = Counter(authors)
        features["author_concentration"] = self._calculate_gini(list(author_counts.values()))
        
        # Commit time pattern features
        hours = [c.timestamp.hour for c in commits]
        total_commits = len(commits)
        features["commit_hour_morning"] = sum(1 for h in hours if 6 <= h < 12) / total_commits
        features["commit_hour_afternoon"] = sum(1 for h in hours if 12 <= h < 18) / total_commits
        features["commit_hour_evening"] = sum(1 for h in hours if 18 <= h < 24) / total_commits
        features["commit_hour_night"] = sum(1 for h in hours if 0 <= h < 6) / total_commits
        
        # File type distribution features
        all_files = [f for c in commits for f in c.files_changed]
        total_file_changes = len(all_files)
        
        if total_file_changes > 0:
            features["file_type_py"] = sum(1 for f in all_files if f.endswith(('.py', '.pyx'))) / total_file_changes
            features["file_type_js"] = sum(1 for f in all_files if f.endswith(('.js', '.jsx', '.ts', '.tsx'))) / total_file_changes
            features["file_type_java"] = sum(1 for f in all_files if f.endswith('.java')) / total_file_changes
            features["file_type_config"] = sum(1 for f in all_files if any(
                f.endswith(ext) for ext in ('.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.xml')
            )) / total_file_changes
            features["file_type_test"] = sum(1 for f in all_files if 'test' in f.lower()) / total_file_changes
            features["file_type_doc"] = sum(1 for f in all_files if any(
                f.endswith(ext) for ext in ('.md', '.rst', '.txt', '.doc')
            )) / total_file_changes
        else:
            features["file_type_py"] = 0.0
            features["file_type_js"] = 0.0
            features["file_type_java"] = 0.0
            features["file_type_config"] = 0.0
            features["file_type_test"] = 0.0
            features["file_type_doc"] = 0.0
        
        return features
    
    def _calculate_gini(self, values: List[int]) -> float:
        """Calculate Gini coefficient for concentration measurement.
        
        Args:
            values: List of counts
            
        Returns:
            Gini coefficient (0 = perfect equality, 1 = perfect inequality)
        """
        if not values or sum(values) == 0:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = 0
        
        for i, val in enumerate(sorted_values):
            cumsum += (i + 1) * val
        
        return (2 * cumsum) / (n * sum(sorted_values)) - (n + 1) / n
    
    def extract_pr_features(
        self,
        prs: List[PRSignal],
    ) -> Dict[str, float]:
        """Extract features from PR history.
        
        Features:
        - pr_frequency: PRs per week
        - pr_merge_time_avg: average time to merge (hours)
        - pr_review_count_avg: average number of reviews
        - pr_merged_ratio: ratio of merged PRs
        - security_label_ratio: ratio of security-labeled PRs
        
        Args:
            prs: List of PRSignal objects
            
        Returns:
            Dictionary of feature names to values
        """
        if not prs:
            return {
                "pr_frequency": 0.0,
                "pr_merge_time_avg": 0.0,
                "pr_review_count_avg": 0.0,
                "pr_merged_ratio": 0.0,
                "security_label_ratio": 0.0,
            }
        
        features = {}
        
        # Time-based features
        timestamps = [pr.created_at for pr in prs]
        time_span = (max(timestamps) - min(timestamps)).total_seconds() / (86400 * 7)  # weeks
        features["pr_frequency"] = len(prs) / max(time_span, 1.0)
        
        # Merge time features
        merge_times = []
        merged_count = 0
        for pr in prs:
            if pr.merged_at:
                merged_count += 1
                merge_time = (pr.merged_at - pr.created_at).total_seconds() / 3600  # hours
                merge_times.append(merge_time)
        
        features["pr_merge_time_avg"] = sum(merge_times) / len(merge_times) if merge_times else 0.0
        features["pr_merged_ratio"] = merged_count / len(prs)
        
        # Review count features
        review_counts = [pr.review_count for pr in prs]
        features["pr_review_count_avg"] = sum(review_counts) / len(prs)
        
        # Security label features
        security_keywords = ["security", "vulnerability", "cve", "exploit"]
        security_count = sum(
            1 for pr in prs
            if any(keyword in label.lower() for label in pr.labels for keyword in security_keywords)
        )
        features["security_label_ratio"] = security_count / len(prs)
        
        return features
    
    def extract_issue_features(
        self,
        issues: List[IssueSignal],
    ) -> Dict[str, float]:
        """Extract features from issue history.
        
        Features:
        - issue_frequency: issues per week
        - security_keyword_ratio: ratio with security keywords
        - response_time_avg: average time to first comment (hours)
        - resolution_time_avg: average time to close (hours)
        - participant_count_avg: average comments per issue
        - closed_ratio: ratio of closed issues
        
        Args:
            issues: List of IssueSignal objects
            
        Returns:
            Dictionary of feature names to values
        """
        if not issues:
            return {
                "issue_frequency": 0.0,
                "security_keyword_ratio": 0.0,
                "response_time_avg": 0.0,
                "resolution_time_avg": 0.0,
                "participant_count_avg": 0.0,
                "closed_ratio": 0.0,
            }
        
        features = {}
        
        # Time-based features
        timestamps = [issue.created_at for issue in issues]
        time_span = (max(timestamps) - min(timestamps)).total_seconds() / (86400 * 7)  # weeks
        features["issue_frequency"] = len(issues) / max(time_span, 1.0)
        
        # Security keyword features
        security_count = sum(
            1 for issue in issues
            if issue.metadata.get("has_security_keyword", False)
        )
        features["security_keyword_ratio"] = security_count / len(issues)
        
        # Response time features (time to first comment)
        # Note: We don't have comment timestamps, so we'll use comment count as proxy
        comment_counts = [len(issue.comments) for issue in issues]
        features["participant_count_avg"] = sum(comment_counts) / len(issues)
        
        # Resolution time features
        resolution_times = []
        closed_count = 0
        for issue in issues:
            if issue.closed_at:
                closed_count += 1
                resolution_time = (issue.closed_at - issue.created_at).total_seconds() / 3600  # hours
                resolution_times.append(resolution_time)
        
        features["resolution_time_avg"] = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
        features["closed_ratio"] = closed_count / len(issues)
        
        # Response time (placeholder - would need comment timestamps)
        features["response_time_avg"] = 0.0
        
        return features
    
    def extract_dependency_features(
        self,
        releases: List[ReleaseSignal],
    ) -> Dict[str, float]:
        """Extract features from dependency changes.
        
        Features:
        - release_frequency: releases per month
        - version_bump_major: ratio of major version bumps
        - version_bump_minor: ratio of minor version bumps
        - version_bump_patch: ratio of patch version bumps
        - prerelease_ratio: ratio of prereleases
        
        Args:
            releases: List of ReleaseSignal objects
            
        Returns:
            Dictionary of feature names to values
        """
        if not releases:
            return {
                "release_frequency": 0.0,
                "version_bump_major": 0.0,
                "version_bump_minor": 0.0,
                "version_bump_patch": 0.0,
                "prerelease_ratio": 0.0,
            }
        
        features = {}
        
        # Time-based features
        timestamps = [r.published_at for r in releases]
        time_span = (max(timestamps) - min(timestamps)).total_seconds() / (86400 * 30)  # months
        features["release_frequency"] = len(releases) / max(time_span, 1.0)
        
        # Version bump pattern analysis
        major_count = 0
        minor_count = 0
        patch_count = 0
        
        for i in range(1, len(releases)):
            prev_version = self._parse_version(releases[i-1].version)
            curr_version = self._parse_version(releases[i].version)
            
            if prev_version and curr_version:
                if curr_version[0] > prev_version[0]:
                    major_count += 1
                elif curr_version[1] > prev_version[1]:
                    minor_count += 1
                elif curr_version[2] > prev_version[2]:
                    patch_count += 1
        
        total_bumps = major_count + minor_count + patch_count
        if total_bumps > 0:
            features["version_bump_major"] = major_count / total_bumps
            features["version_bump_minor"] = minor_count / total_bumps
            features["version_bump_patch"] = patch_count / total_bumps
        else:
            features["version_bump_major"] = 0.0
            features["version_bump_minor"] = 0.0
            features["version_bump_patch"] = 0.0
        
        # Prerelease ratio
        prerelease_count = sum(
            1 for r in releases
            if r.metadata.get("prerelease", False)
        )
        features["prerelease_ratio"] = prerelease_count / len(releases)
        
        return features
    
    def _parse_version(self, version_str: str) -> tuple:
        """Parse version string into (major, minor, patch) tuple.
        
        Args:
            version_str: Version string (e.g., "v1.2.3" or "1.2.3")
            
        Returns:
            Tuple of (major, minor, patch) or None if parsing fails
        """
        try:
            # Remove 'v' prefix if present
            version_str = version_str.lstrip('v')
            # Split by '.' and take first 3 parts
            parts = version_str.split('.')[:3]
            # Convert to integers
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return (major, minor, patch)
        except (ValueError, IndexError):
            return None
    
    def extract_temporal_features(
        self,
        signals: List,
        window_days: int = 30,
    ) -> Dict[str, float]:
        """Extract time-series features.
        
        Features:
        - trend: linear regression slope of signal frequency
        - volatility: standard deviation of signal frequency
        - recent_activity_ratio: ratio of signals in last window_days
        
        Args:
            signals: List of signal objects (any type with timestamp/created_at)
            window_days: Time window for recent activity (default 30 days)
            
        Returns:
            Dictionary of feature names to values
        """
        if not signals:
            return {
                "trend": 0.0,
                "volatility": 0.0,
                "recent_activity_ratio": 0.0,
            }
        
        features = {}
        
        # Extract timestamps
        timestamps = []
        for signal in signals:
            if hasattr(signal, 'timestamp'):
                timestamps.append(signal.timestamp)
            elif hasattr(signal, 'created_at'):
                timestamps.append(signal.created_at)
            elif hasattr(signal, 'published_at'):
                timestamps.append(signal.published_at)
        
        if not timestamps:
            return {
                "trend": 0.0,
                "volatility": 0.0,
                "recent_activity_ratio": 0.0,
            }
        
        # Sort timestamps
        timestamps.sort()
        
        # Calculate trend (simple linear regression slope)
        min_time = timestamps[0]
        time_diffs = [(t - min_time).total_seconds() / 86400 for t in timestamps]  # days
        
        if len(time_diffs) > 1:
            # Simple linear regression
            n = len(time_diffs)
            x_mean = sum(time_diffs) / n
            y_mean = n / 2  # Index mean
            
            numerator = sum((time_diffs[i] - x_mean) * (i - y_mean) for i in range(n))
            denominator = sum((time_diffs[i] - x_mean) ** 2 for i in range(n))
            
            features["trend"] = numerator / denominator if denominator != 0 else 0.0
        else:
            features["trend"] = 0.0
        
        # Calculate volatility (std dev of inter-signal times)
        if len(timestamps) > 1:
            inter_times = [
                (timestamps[i+1] - timestamps[i]).total_seconds() / 86400
                for i in range(len(timestamps) - 1)
            ]
            mean_inter_time = sum(inter_times) / len(inter_times)
            variance = sum((t - mean_inter_time) ** 2 for t in inter_times) / len(inter_times)
            features["volatility"] = variance ** 0.5
        else:
            features["volatility"] = 0.0
        
        # Calculate recent activity ratio
        max_time = timestamps[-1]
        cutoff_time = max_time - timedelta(days=window_days)
        recent_count = sum(1 for t in timestamps if t >= cutoff_time)
        features["recent_activity_ratio"] = recent_count / len(timestamps)
        
        return features
