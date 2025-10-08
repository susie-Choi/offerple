"""GitHub repository metadata collector."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .base import BaseDataSource, DataSourceError, SourceResult


class GitHubDataSource(BaseDataSource):
    """Collect repository metadata, issues, and activity statistics."""

    source_name = "github"
    API_URL = "https://api.github.com"

    def __init__(
        self,
        *,
        token: Optional[str] = None,
        timeout: float = 15.0,
        rate_limit_sleep: float = 1.0,
        session=None,
    ) -> None:
        super().__init__(timeout=timeout, rate_limit_sleep=rate_limit_sleep, session=session)
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def collect(self, package: str, *, cutoff: datetime) -> SourceResult:
        owner, repo = self._parse_repo(package)
        repo_payload = self._get(f"/repos/{owner}/{repo}")
        default_branch = repo_payload.get("default_branch", "main")
        branches_payload = self._get(
            f"/repos/{owner}/{repo}/commits",
            params={"sha": default_branch, "per_page": 100},
        )
        cutoff_iso = cutoff.astimezone(timezone.utc).isoformat()
        issues_payload = self._get(
            f"/repos/{owner}/{repo}/issues",
            params={
                "state": "all",
                "since": cutoff_iso,
                "per_page": 100,
            },
        )
        pulls_payload = self._get(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": "all", "per_page": 100},
        )
        data = {
            "repository": repo_payload,
            "commits": self._filter_by_cutoff(branches_payload, cutoff),
            "issues": self._filter_by_cutoff(issues_payload, cutoff, field="created_at"),
            "pull_requests": self._filter_by_cutoff(pulls_payload, cutoff, field="created_at"),
        }
        return SourceResult(
            source=self.source_name,
            package=f"{owner}/{repo}",
            collected_at=datetime.utcnow(),
            payload=data,
        )

    def _get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        response = self._request("GET", f"{self.API_URL}{path}", headers=self._headers(), params=params)
        if response.headers.get("X-RateLimit-Remaining") == "0":
            reset = response.headers.get("X-RateLimit-Reset")
            raise DataSourceError(
                "GitHub rate limit exceeded; wait until reset timestamp "
                f"{reset} before re-running"
            )
        return response.json()

    @staticmethod
    def _parse_repo(repo_url: str) -> tuple[str, str]:
        if repo_url.startswith("https://"):
            parts = repo_url.rstrip("/").split("/")
            owner, repo = parts[-2], parts[-1]
        elif "/" in repo_url:
            owner, repo = repo_url.split("/", 1)
        else:
            raise ValueError("GitHub repository must be in 'owner/repo' format")
        return owner, repo

    @staticmethod
    def _filter_by_cutoff(items: Any, cutoff: datetime, *, field: str = "commit") -> Any:
        if not isinstance(items, list):
            return items
        filtered = []
        for item in items:
            timestamp = GitHubDataSource._extract_timestamp(item, field)
            if timestamp and timestamp <= cutoff:
                filtered.append(item)
        return filtered

    @staticmethod
    def _extract_timestamp(item: Dict[str, Any], field: str) -> Optional[datetime]:
        value = item
        for part in field.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        if isinstance(value, dict) and "author" in value:
            author = value.get("author") or {}
            date_str = author.get("date")
            if isinstance(date_str, str):
                try:
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    return None
        return None


__all__ = ["GitHubDataSource"]
