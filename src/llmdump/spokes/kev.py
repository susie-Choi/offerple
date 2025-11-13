"""CISA KEV (Known Exploited Vulnerabilities) collector."""

from datetime import datetime
from typing import Dict, Any, List
import logging

from .base import BaseCollector

logger = logging.getLogger(__name__)


class KEVCollector(BaseCollector):
    """
    Collect CISA Known Exploited Vulnerabilities catalog.
    
    KEV provides government-verified list of actively exploited CVEs.
    Source: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
    """
    
    source_name = "kev"
    KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect KEV catalog from CISA.
        
        Returns:
            Collection statistics
        """
        logger.info("Collecting CISA KEV catalog")
        
        response = self._request("GET", self.KEV_URL)
        data = response.json()
        
        vulnerabilities = data.get("vulnerabilities", [])
        logger.info(f"Found {len(vulnerabilities)} KEV entries")
        
        # Parse KEV entries
        kev_entries = [self._parse_kev(vuln) for vuln in vulnerabilities]
        
        # Validate entries
        valid_entries = [entry for entry in kev_entries if self.validate(entry)]
        logger.info(f"Validated {len(valid_entries)} KEV entries")
        
        # Save to JSONL
        if valid_entries:
            filename = f"kev_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
            self.save_jsonl(valid_entries, filename)
        
        return self.get_stats(valid_entries)
    
    def _parse_kev(self, vuln: Dict[str, Any]) -> Dict[str, Any]:
        """Parse KEV entry."""
        return {
            "cve_id": vuln.get("cveID", ""),
            "vulnerability_name": vuln.get("vulnerabilityName", ""),
            "vendor_project": vuln.get("vendorProject", ""),
            "product": vuln.get("product", ""),
            "date_added": vuln.get("dateAdded", ""),
            "short_description": vuln.get("shortDescription", ""),
            "required_action": vuln.get("requiredAction", ""),
            "due_date": vuln.get("dueDate", ""),
            "known_ransomware_use": vuln.get("knownRansomwareCampaignUse", "") == "Known",
            "notes": vuln.get("notes", ""),
        }
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate KEV data."""
        required_fields = ["cve_id", "vulnerability_name", "date_added"]
        
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


__all__ = ['KEVCollector']
