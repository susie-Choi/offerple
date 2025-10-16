"""CVE (Common Vulnerabilities and Exposures) data collector from NVD."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import BaseDataSource, DataSourceError, SourceResult


class CVEDataSource(BaseDataSource):
    """Collect CVE data from the National Vulnerability Database (NVD) API.
    
    NVD API 2.0 documentation: https://nvd.nist.gov/developers/vulnerabilities
    """

    source_name = "nvd_cve"
    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        rate_limit_sleep: float = 6.0,  # NVD requires 6 seconds between requests without API key
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(timeout=timeout, rate_limit_sleep=rate_limit_sleep, **kwargs)
        self.api_key = api_key
        if api_key:
            self.session.headers.update({"apiKey": api_key})
            self.rate_limit_sleep = 0.6  # With API key, 50 requests per 30 seconds
    
    def _parse_published_date(self, published_str: str) -> datetime:
        """Parse published date string and ensure timezone-aware."""
        # Replace 'Z' with '+00:00' for ISO format
        pub_date_str = published_str.replace("Z", "+00:00")
        pub_date = datetime.fromisoformat(pub_date_str)
        # Ensure timezone-aware
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
        return pub_date
    
    def _ensure_cutoff_aware(self, cutoff: datetime) -> datetime:
        """Ensure cutoff datetime is timezone-aware."""
        if cutoff.tzinfo is None:
            return cutoff.replace(tzinfo=timezone.utc)
        return cutoff

    def collect_by_cve_id(self, cve_id: str, *, cutoff: datetime) -> SourceResult:
        """Collect data for a specific CVE ID (e.g., CVE-2021-44228)."""
        cutoff = self._ensure_cutoff_aware(cutoff)
        
        params = {"cveId": cve_id}
        response = self._request("GET", self.BASE_URL, params=params)
        time.sleep(self.rate_limit_sleep)
        
        data = response.json()
        vulnerabilities = data.get("vulnerabilities", [])
        
        if not vulnerabilities:
            raise DataSourceError(f"CVE {cve_id} not found in NVD")
        
        # Filter by cutoff date
        filtered_vulns = []
        for vuln in vulnerabilities:
            cve_data = vuln.get("cve", {})
            published = cve_data.get("published")
            if published:
                pub_date = self._parse_published_date(published)
                if pub_date <= cutoff:
                    filtered_vulns.append(vuln)
        
        return SourceResult(
            source=self.source_name,
            package=cve_id,
            collected_at=datetime.now(timezone.utc),
            payload={
                "vulnerabilities": filtered_vulns,
                "total_results": len(filtered_vulns),
            },
        )

    def collect_by_keyword(
        self,
        keyword: str,
        *,
        cutoff: datetime,
        max_results: int = 100,
    ) -> SourceResult:
        """Collect CVEs matching a keyword search (e.g., 'log4j', 'apache')."""
        cutoff = self._ensure_cutoff_aware(cutoff)
        
        params = {
            "keywordSearch": keyword,
            "resultsPerPage": min(max_results, 2000),  # NVD max is 2000
        }
        
        response = self._request("GET", self.BASE_URL, params=params)
        time.sleep(self.rate_limit_sleep)
        
        data = response.json()
        vulnerabilities = data.get("vulnerabilities", [])
        
        # Filter by cutoff date
        filtered_vulns = []
        for vuln in vulnerabilities:
            cve_data = vuln.get("cve", {})
            published = cve_data.get("published")
            if published:
                pub_date = self._parse_published_date(published)
                if pub_date <= cutoff:
                    filtered_vulns.append(vuln)
        
        return SourceResult(
            source=self.source_name,
            package=f"keyword:{keyword}",
            collected_at=datetime.now(timezone.utc),
            payload={
                "keyword": keyword,
                "vulnerabilities": filtered_vulns,
                "total_results": len(filtered_vulns),
            },
        )

    def collect_by_cpe(
        self,
        cpe_name: str,
        *,
        cutoff: datetime,
        max_results: int = 100,
    ) -> SourceResult:
        """Collect CVEs for a specific CPE (Common Platform Enumeration).
        
        Example CPE: cpe:2.3:a:apache:log4j:2.14.1:*:*:*:*:*:*:*
        """
        cutoff = self._ensure_cutoff_aware(cutoff)
        
        params = {
            "cpeName": cpe_name,
            "resultsPerPage": min(max_results, 2000),
        }
        
        response = self._request("GET", self.BASE_URL, params=params)
        time.sleep(self.rate_limit_sleep)
        
        data = response.json()
        vulnerabilities = data.get("vulnerabilities", [])
        
        # Filter by cutoff date
        filtered_vulns = []
        for vuln in vulnerabilities:
            cve_data = vuln.get("cve", {})
            published = cve_data.get("published")
            if published:
                pub_date = self._parse_published_date(published)
                if pub_date <= cutoff:
                    filtered_vulns.append(vuln)
        
        return SourceResult(
            source=self.source_name,
            package=f"cpe:{cpe_name}",
            collected_at=datetime.now(timezone.utc),
            payload={
                "cpe": cpe_name,
                "vulnerabilities": filtered_vulns,
                "total_results": len(filtered_vulns),
            },
        )

    def collect(self, package: str, *, cutoff: datetime) -> SourceResult:
        """Collect CVE data. Package can be CVE-ID, keyword:term, or cpe:name."""
        if package.startswith("CVE-"):
            return self.collect_by_cve_id(package, cutoff=cutoff)
        elif package.startswith("keyword:"):
            keyword = package.replace("keyword:", "")
            return self.collect_by_keyword(keyword, cutoff=cutoff)
        elif package.startswith("cpe:"):
            cpe_name = package.replace("cpe:", "")
            return self.collect_by_cpe(cpe_name, cutoff=cutoff)
        else:
            # Default to keyword search
            return self.collect_by_keyword(package, cutoff=cutoff)


__all__ = ["CVEDataSource"]
