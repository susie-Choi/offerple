"""GitHub Security Advisory data collector."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import BaseDataSource, SourceResult


class GitHubAdvisoryDataSource(BaseDataSource):
    """Collect security advisories from GitHub Advisory Database.
    
    GitHub Advisory Database API: https://docs.github.com/en/rest/security-advisories
    """

    source_name = "github_advisory"
    BASE_URL = "https://api.github.com/advisories"

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        rate_limit_sleep: float = 1.0,
        github_token: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(timeout=timeout, rate_limit_sleep=rate_limit_sleep, **kwargs)
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if self.github_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            })

    def collect_by_cve(self, cve_id: str, *, cutoff: datetime) -> SourceResult:
        """Collect advisories for a specific CVE ID."""
        params = {
            "cve_id": cve_id,
            "per_page": 100,
        }
        
        response = self._request("GET", self.BASE_URL, params=params)
        advisories = response.json()
        
        # Make cutoff timezone-aware if it isn't
        if cutoff.tzinfo is None:
            from datetime import timezone
            cutoff = cutoff.replace(tzinfo=timezone.utc)
        
        # Filter by cutoff date
        filtered_advisories = []
        for advisory in advisories:
            published = advisory.get("published_at")
            if published:
                pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                if pub_date <= cutoff:
                    filtered_advisories.append(advisory)
        
        return SourceResult(
            source=self.source_name,
            package=cve_id,
            collected_at=datetime.now(timezone.utc),
            payload={
                "cve_id": cve_id,
                "advisories": filtered_advisories,
                "total_results": len(filtered_advisories),
            },
        )

    def collect_by_ecosystem(
        self,
        ecosystem: str,
        *,
        cutoff: datetime,
        severity: Optional[str] = None,
    ) -> SourceResult:
        """Collect advisories for a specific ecosystem (npm, pip, maven, etc.)."""
        params = {
            "ecosystem": ecosystem,
            "per_page": 100,
        }
        
        if severity:
            params["severity"] = severity
        
        response = self._request("GET", self.BASE_URL, params=params)
        advisories = response.json()
        
        # Make cutoff timezone-aware if it isn't
        if cutoff.tzinfo is None:
            from datetime import timezone
            cutoff = cutoff.replace(tzinfo=timezone.utc)
        
        # Filter by cutoff date
        filtered_advisories = []
        for advisory in advisories:
            published = advisory.get("published_at")
            if published:
                pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                if pub_date <= cutoff:
                    filtered_advisories.append(advisory)
        
        return SourceResult(
            source=self.source_name,
            package=f"ecosystem:{ecosystem}",
            collected_at=datetime.now(timezone.utc),
            payload={
                "ecosystem": ecosystem,
                "advisories": filtered_advisories,
                "total_results": len(filtered_advisories),
            },
        )

    def collect(self, package: str, *, cutoff: datetime) -> SourceResult:
        """Collect advisory data. Package can be CVE-ID or ecosystem:name."""
        if package.startswith("CVE-"):
            return self.collect_by_cve(package, cutoff=cutoff)
        elif package.startswith("ecosystem:"):
            ecosystem = package.replace("ecosystem:", "")
            return self.collect_by_ecosystem(ecosystem, cutoff=cutoff)
        else:
            # Default to CVE search
            return self.collect_by_cve(package, cutoff=cutoff)


__all__ = ["GitHubAdvisoryDataSource"]
