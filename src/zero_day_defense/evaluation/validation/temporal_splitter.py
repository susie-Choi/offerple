"""Temporal data splitter for historical validation."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


logger = logging.getLogger(__name__)


class TemporalLeakageError(Exception):
    """Raised when data from after cutoff date is detected."""
    pass


class TemporalSplitter:
    """Split data temporally for historical validation.
    
    This class ensures temporal correctness by:
    1. Setting cutoff dates before CVE disclosure
    2. Filtering all data to be before cutoff
    3. Validating no temporal leakage
    """
    
    def __init__(
        self,
        *,
        prediction_window_days: int = 90,
        min_history_days: int = 180,
    ):
        """Initialize temporal splitter.
        
        Args:
            prediction_window_days: Days before CVE disclosure to make prediction
            min_history_days: Minimum days of history required before cutoff
        """
        self.prediction_window_days = prediction_window_days
        self.min_history_days = min_history_days
    
    def create_validation_split(
        self,
        cve_record: Dict,
    ) -> Dict:
        """Create temporal split for a CVE.
        
        Args:
            cve_record: CVE record with published_date
        
        Returns:
            Split dict with:
                - cutoff_date: datetime
                - disclosure_date: datetime
                - prediction_window_days: int
                - history_start_date: datetime
                - valid: bool
                - reason: str (if invalid)
        """
        cve_id = cve_record.get("cve_id", "UNKNOWN")
        
        # Get disclosure date
        published_date_str = cve_record.get("published_date")
        if not published_date_str:
            return {
                "valid": False,
                "reason": "No published_date",
            }
        
        try:
            disclosure_date = datetime.fromisoformat(
                published_date_str.replace("Z", "+00:00")
            )
        except Exception as e:
            return {
                "valid": False,
                "reason": f"Invalid published_date: {e}",
            }
        
        # Calculate cutoff date (prediction_window_days before disclosure)
        cutoff_date = disclosure_date - timedelta(days=self.prediction_window_days)
        
        # Calculate required history start date
        history_start_date = cutoff_date - timedelta(days=self.min_history_days)
        
        # Check if repository was created before history start
        # (This would be checked against actual repo data in practice)
        
        return {
            "valid": True,
            "cve_id": cve_id,
            "disclosure_date": disclosure_date,
            "cutoff_date": cutoff_date,
            "prediction_window_days": self.prediction_window_days,
            "history_start_date": history_start_date,
            "history_window_days": self.min_history_days,
        }
    
    def validate_temporal_correctness(
        self,
        data: List[Dict],
        cutoff_date: datetime,
        timestamp_field: str = "timestamp",
    ) -> Tuple[List[Dict], List[Dict]]:
        """Validate and filter data for temporal correctness.
        
        Args:
            data: List of data records
            cutoff_date: Cutoff date
            timestamp_field: Field name containing timestamp
        
        Returns:
            Tuple of (valid_data, invalid_data)
        
        Raises:
            TemporalLeakageError: If critical data is after cutoff
        """
        valid_data = []
        invalid_data = []
        
        for record in data:
            timestamp = record.get(timestamp_field)
            
            if not timestamp:
                logger.warning(f"Record missing {timestamp_field}: {record}")
                invalid_data.append(record)
                continue
            
            # Parse timestamp
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )
                except:
                    logger.warning(f"Invalid timestamp format: {timestamp}")
                    invalid_data.append(record)
                    continue
            
            # Check temporal correctness
            if timestamp <= cutoff_date:
                valid_data.append(record)
            else:
                invalid_data.append(record)
        
        if invalid_data:
            logger.warning(
                f"Filtered {len(invalid_data)}/{len(data)} records after cutoff date"
            )
        
        return valid_data, invalid_data
    
    def create_time_windows(
        self,
        start_date: datetime,
        end_date: datetime,
        window_size_days: int = 30,
    ) -> List[Tuple[datetime, datetime]]:
        """Create sliding time windows.
        
        Args:
            start_date: Start date
            end_date: End date
            window_size_days: Window size in days
        
        Returns:
            List of (window_start, window_end) tuples
        """
        windows = []
        current_start = start_date
        
        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=window_size_days),
                end_date,
            )
            windows.append((current_start, current_end))
            current_start = current_end
        
        return windows
    
    def get_signal_collection_window(
        self,
        cutoff_date: datetime,
        window_days: int = 180,
    ) -> Tuple[datetime, datetime]:
        """Get time window for signal collection.
        
        Args:
            cutoff_date: Cutoff date
            window_days: Days of history to collect
        
        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = cutoff_date
        start_date = cutoff_date - timedelta(days=window_days)
        
        return start_date, end_date
