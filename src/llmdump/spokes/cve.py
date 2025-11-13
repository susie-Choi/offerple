"""CVE (Common Vulnerabilities and Exposures) collector from NVD."""

import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

from .base import BaseCollector, CollectionError

logger = logging.getLogger(__name__)


class CVECollector(BaseCollector):
    """
    Collect CVE data from the National Vulnerability Database (NVD) API 2.0.
    
    API Documentation: https://nvd.nist.gov/developers/vulnerabilities
    """
    
    source_name = "cve"
    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    def __init__(
        self,
        output_dir: str = "data/raw",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize CVE collector.
        
        Args:
            output_dir: Directory to save collected data
            api_key: NVD API key (optional, increases rate limit)
            **kwargs: Additional arguments for BaseCollector
        """
        # NVD requires 6 seconds between requests without API key
        rate_limit = 0.6 if api_key else 6.0
        super().__init__(
            output_dir=output_dir,
            rate_limit_sleep=rate_limit,
            **kwargs
        )
        
        self.api_key = api_key
        if api_key:
            self.session.headers.update({"apiKey": api_key})
    
    def collect(
        self,
        cve_ids: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keyword: Optional[str] = None,
        max_results: int = 100,
    ) -> Dict[str, Any]:
        """
        Collect CVE data from NVD.
        
        Args:
            cve_ids: List of specific CVE IDs to collect
            start_date: Start date for date range (ISO format)
            end_date: End date for date range (ISO format)
            keyword: Keyword to search for
            max_results: Maximum number of results to collect
            
        Returns:
            Collection statistics
        """
        all_cves = []
        
        if cve_ids:
            # Collect specific CVEs
            for cve_id in cve_ids:
                try:
                    cve_data = self._collect_by_id(cve_id)
                    if cve_data:
                        all_cves.append(cve_data)
                except CollectionError as e:
                    logger.error(f"Failed to collect {cve_id}: {e}")
        
        elif start_date and end_date:
            # Collect by date range
            all_cves = self._collect_by_date_range(start_date, end_date, max_results)
        
        elif keyword:
            # Collect by keyword
            all_cves = self._collect_by_keyword(keyword, max_results)
        
        else:
            raise ValueError("Must provide cve_ids, date range, or keyword")
        
        # Save to JSONL
        if all_cves:
            filename = f"cves_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
            self.save_jsonl(all_cves, filename)
        
        return self.get_stats(all_cves)
    
    def _collect_by_id(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """Collect a specific CVE by ID."""
        logger.info(f"Collecting {cve_id}")
        
        params = {"cveId": cve_id}
        response = self._request("GET", self.BASE_URL, params=params)
        time.sleep(self.rate_limit_sleep)
        
        data = response.json()
        vulnerabilities = data.get("vulnerabilities", [])
        
        if not vulnerabilities:
            logger.warning(f"CVE {cve_id} not found")
            return None
        
        # Extract first vulnerability
        vuln = vulnerabilities[0]
        return self._parse_cve(vuln)
    
    def _collect_by_date_range(
        self,
        start_date: str,
        end_date: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Collect CVEs within a date range."""
        logger.info(f"Collecting CVEs from {start_date} to {end_date}")
        
        params = {
            "pubStartDate": start_date,
            "pubEndDate": end_date,
            "resultsPerPage": min(max_results, 2000),
        }
        
        response = self._request("GET", self.BASE_URL, params=params)
        time.sleep(self.rate_limit_sleep)
        
        data = response.json()
        vulnerabilities = data.get("vulnerabilities", [])
        
        logger.info(f"Found {len(vulnerabilities)} CVEs")
        
        return [self._parse_cve(vuln) for vuln in vulnerabilities]
    
    def _collect_by_keyword(
        self,
        keyword: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Collect CVEs matching a keyword."""
        logger.info(f"Collecting CVEs matching '{keyword}'")
        
        params = {
            "keywordSearch": keyword,
            "resultsPerPage": min(max_results, 2000),
        }
        
        response = self._request("GET", self.BASE_URL, params=params)
        time.sleep(self.rate_limit_sleep)
        
        data = response.json()
        vulnerabilities = data.get("vulnerabilities", [])
        
        logger.info(f"Found {len(vulnerabilities)} CVEs")
        
        return [self._parse_cve(vuln) for vuln in vulnerabilities]
    
    def _parse_cve(self, vuln: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CVE data from NVD format."""
        cve_data = vuln.get("cve", {})
        
        # Extract basic info
        cve_id = cve_data.get("id", "")
        published = cve_data.get("published", "")
        last_modified = cve_data.get("lastModified", "")
        
        # Extract description
        descriptions = cve_data.get("descriptions", [])
        description = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break
        
        # Extract CVSS scores
        metrics = cve_data.get("metrics", {})
        cvss_v3 = metrics.get("cvssMetricV31", [{}])[0] if "cvssMetricV31" in metrics else {}
        cvss_v2 = metrics.get("cvssMetricV2", [{}])[0] if "cvssMetricV2" in metrics else {}
        
        cvss_score = None
        cvss_severity = None
        if cvss_v3:
            cvss_data = cvss_v3.get("cvssData", {})
            cvss_score = cvss_data.get("baseScore")
            cvss_severity = cvss_data.get("baseSeverity")
        elif cvss_v2:
            cvss_data = cvss_v2.get("cvssData", {})
            cvss_score = cvss_data.get("baseScore")
            cvss_severity = cvss_v2.get("baseSeverity")
        
        # Extract CWE
        weaknesses = cve_data.get("weaknesses", [])
        cwe_ids = []
        for weakness in weaknesses:
            for desc in weakness.get("description", []):
                if desc.get("lang") == "en":
                    cwe_ids.append(desc.get("value", ""))
        
        # Extract CPE (affected products)
        configurations = cve_data.get("configurations", [])
        cpe_list = []
        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    if cpe_match.get("vulnerable"):
                        cpe_list.append(cpe_match.get("criteria", ""))
        
        # Extract references
        references = cve_data.get("references", [])
        ref_urls = [ref.get("url", "") for ref in references]
        
        return {
            "cve_id": cve_id,
            "published": published,
            "last_modified": last_modified,
            "description": description,
            "cvss_score": cvss_score,
            "cvss_severity": cvss_severity,
            "cwe_ids": cwe_ids,
            "cpe_list": cpe_list,
            "references": ref_urls,
        }
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate CVE data."""
        required_fields = ["cve_id", "published", "description"]
        
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate CVE ID format
        cve_id = data["cve_id"]
        if not cve_id.startswith("CVE-"):
            logger.warning(f"Invalid CVE ID format: {cve_id}")
            return False
        
        return True


__all__ = ['CVECollector']
