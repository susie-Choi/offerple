"""EPSS (Exploit Prediction Scoring System) data collector."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .base import BaseDataSource, SourceResult


class EPSSDataSource(BaseDataSource):
    """Collect EPSS scores from FIRST.org.
    
    EPSS API: https://www.first.org/epss/api
    """

    source_name = "epss"
    BASE_URL = "https://api.first.org/data/v1/epss"

    def __init__(self, **kwargs):
        # Disable SSL verification for corporate proxies
        kwargs.setdefault('verify_ssl', False)
        super().__init__(**kwargs)

    def collect_by_cve(self, cve_id: str, *, cutoff: datetime) -> SourceResult:
        """Collect EPSS score for a specific CVE ID."""
        params = {"cve": cve_id}
        
        response = self._request("GET", self.BASE_URL, params=params)
        data = response.json()
        
        epss_data = data.get("data", [])
        
        return SourceResult(
            source=self.source_name,
            package=cve_id,
            collected_at=datetime.utcnow(),
            payload={
                "cve_id": cve_id,
                "epss_data": epss_data,
                "total_results": len(epss_data),
            },
        )

    def collect_multiple_cves(self, cve_ids: List[str], *, cutoff: datetime) -> SourceResult:
        """Collect EPSS scores for multiple CVE IDs (up to 100 at once)."""
        # EPSS API supports comma-separated CVE IDs
        cve_list = ",".join(cve_ids[:100])  # Max 100 CVEs per request
        params = {"cve": cve_list}
        
        response = self._request("GET", self.BASE_URL, params=params)
        data = response.json()
        
        epss_data = data.get("data", [])
        
        return SourceResult(
            source=self.source_name,
            package=f"batch:{len(cve_ids)}",
            collected_at=datetime.utcnow(),
            payload={
                "cve_ids": cve_ids,
                "epss_data": epss_data,
                "total_results": len(epss_data),
            },
        )

    def collect(self, package: str, *, cutoff: datetime) -> SourceResult:
        """Collect EPSS data. Package should be CVE-ID."""
        if package.startswith("CVE-"):
            return self.collect_by_cve(package, cutoff=cutoff)
        else:
            # Try as CVE ID anyway
            return self.collect_by_cve(package, cutoff=cutoff)


__all__ = ["EPSSDataSource"]
