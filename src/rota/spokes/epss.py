"""EPSS (Exploit Prediction Scoring System) collector."""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from .base import BaseCollector

logger = logging.getLogger(__name__)


class EPSSCollector(BaseCollector):
    """
    Collect EPSS scores from FIRST.org.
    
    EPSS provides daily probability scores for CVE exploitation.
    API Documentation: https://www.first.org/epss/api
    """
    
    source_name = "epss"
    BASE_URL = "https://api.first.org/data/v1/epss"
    
    def collect(
        self,
        cve_ids: Optional[List[str]] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Collect EPSS scores.
        
        Args:
            cve_ids: List of CVE IDs to collect scores for
            date: Specific date to get scores for (YYYY-MM-DD)
            
        Returns:
            Collection statistics
        """
        all_scores = []
        
        if cve_ids:
            # Collect in batches of 100 (API limit)
            for i in range(0, len(cve_ids), 100):
                batch = cve_ids[i:i+100]
                scores = self._collect_batch(batch, date)
                all_scores.extend(scores)
        else:
            # Collect all scores for a date
            all_scores = self._collect_all(date)
        
        # Save to JSONL
        if all_scores:
            filename = f"epss_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
            self.save_jsonl(all_scores, filename)
        
        return self.get_stats(all_scores)
    
    def _collect_batch(
        self,
        cve_ids: List[str],
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Collect EPSS scores for a batch of CVEs."""
        logger.info(f"Collecting EPSS scores for {len(cve_ids)} CVEs")
        
        params = {"cve": ",".join(cve_ids)}
        if date:
            params["date"] = date
        
        response = self._request("GET", self.BASE_URL, params=params)
        data = response.json()
        
        epss_data = data.get("data", [])
        logger.info(f"Retrieved {len(epss_data)} EPSS scores")
        
        return [self._parse_epss(item) for item in epss_data]
    
    def _collect_all(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Collect all EPSS scores for a date."""
        logger.info(f"Collecting all EPSS scores for {date or 'latest'}")
        
        params = {}
        if date:
            params["date"] = date
        
        response = self._request("GET", self.BASE_URL, params=params)
        data = response.json()
        
        epss_data = data.get("data", [])
        logger.info(f"Retrieved {len(epss_data)} EPSS scores")
        
        return [self._parse_epss(item) for item in epss_data]
    
    def _parse_epss(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse EPSS data."""
        return {
            "cve_id": item.get("cve", ""),
            "epss_score": float(item.get("epss", 0)),
            "percentile": float(item.get("percentile", 0)),
            "date": item.get("date", ""),
        }
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate EPSS data."""
        required_fields = ["cve_id", "epss_score"]
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate score range
        score = data.get("epss_score", 0)
        if not (0 <= score <= 1):
            logger.warning(f"Invalid EPSS score: {score}")
            return False
        
        return True


__all__ = ['EPSSCollector']
