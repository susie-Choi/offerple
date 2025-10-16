"""Time series storage for signals."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Union

from ..models import CommitSignal, PRSignal, IssueSignal, ReleaseSignal
from ..exceptions import SignalCollectionError

Signal = Union[CommitSignal, PRSignal, IssueSignal, ReleaseSignal]


class TimeSeriesStore:
    """Store time-series signals in JSONL format."""
    
    def save_signals(
        self,
        package: str,
        signals: List[Signal],
        output_dir: Path,
        signal_type: str = None,
    ) -> Path:
        """Save signals to JSONL file.
        
        Args:
            package: Package name
            signals: List of signal objects
            output_dir: Output directory
            signal_type: Type of signal (auto-detected if not provided)
            
        Returns:
            Path to saved file
            
        Raises:
            SignalCollectionError: If signals cannot be saved
        """
        if not signals:
            raise SignalCollectionError("No signals to save")
        
        # Auto-detect signal type if not provided
        if signal_type is None:
            first_signal = signals[0]
            if isinstance(first_signal, CommitSignal):
                signal_type = "commit"
            elif isinstance(first_signal, PRSignal):
                signal_type = "pr"
            elif isinstance(first_signal, IssueSignal):
                signal_type = "issue"
            elif isinstance(first_signal, ReleaseSignal):
                signal_type = "release"
            else:
                raise SignalCollectionError(f"Unknown signal type: {type(first_signal)}")
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename: package_signaltype_timestamp.jsonl
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_package = package.replace("/", "_").replace(":", "_")
        filename = f"{safe_package}_{signal_type}_{timestamp}.jsonl"
        output_path = output_dir / filename
        
        # Write signals to JSONL
        try:
            with output_path.open("w", encoding="utf-8") as f:
                for signal in signals:
                    signal_dict = asdict(signal)
                    # Convert datetime objects to ISO format strings
                    signal_dict = self._serialize_datetimes(signal_dict)
                    f.write(json.dumps(signal_dict) + "\n")
        except Exception as e:
            raise SignalCollectionError(f"Failed to save signals: {e}")
        
        return output_path
    
    def load_signals(
        self,
        package: str,
        signal_type: str,
        input_dir: Path,
        latest: bool = True,
    ) -> List[Signal]:
        """Load signals from JSONL file.
        
        Args:
            package: Package name
            signal_type: Type of signal (commit, pr, issue, release)
            input_dir: Input directory
            latest: If True, load only the latest file for this package/type
            
        Returns:
            List of signal objects
            
        Raises:
            SignalCollectionError: If signals cannot be loaded
        """
        input_dir = Path(input_dir)
        if not input_dir.exists():
            raise SignalCollectionError(f"Input directory does not exist: {input_dir}")
        
        # Find matching files
        safe_package = package.replace("/", "_").replace(":", "_")
        pattern = f"{safe_package}_{signal_type}_*.jsonl"
        matching_files = sorted(input_dir.glob(pattern))
        
        if not matching_files:
            raise SignalCollectionError(
                f"No signal files found for package={package}, type={signal_type}"
            )
        
        # Use latest file if requested
        if latest:
            matching_files = [matching_files[-1]]
        
        # Load signals from file(s)
        signals = []
        for file_path in matching_files:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        signal_dict = json.loads(line)
                        signal_dict = self._deserialize_datetimes(signal_dict)
                        
                        # Convert dict back to appropriate signal type
                        if signal_type == "commit":
                            signals.append(CommitSignal(**signal_dict))
                        elif signal_type == "pr":
                            signals.append(PRSignal(**signal_dict))
                        elif signal_type == "issue":
                            signals.append(IssueSignal(**signal_dict))
                        elif signal_type == "release":
                            signals.append(ReleaseSignal(**signal_dict))
                        else:
                            raise SignalCollectionError(f"Unknown signal type: {signal_type}")
            except Exception as e:
                raise SignalCollectionError(f"Failed to load signals from {file_path}: {e}")
        
        return signals
    
    def _serialize_datetimes(self, obj):
        """Recursively convert datetime objects to ISO format strings."""
        if isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    def _deserialize_datetimes(self, obj):
        """Recursively convert ISO format strings back to datetime objects."""
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                # Known datetime fields
                if k in ["timestamp", "created_at", "merged_at", "closed_at", "published_at"]:
                    if v is not None and isinstance(v, str):
                        result[k] = datetime.fromisoformat(v)
                    else:
                        result[k] = v
                else:
                    result[k] = self._deserialize_datetimes(v)
            return result
        elif isinstance(obj, list):
            return [self._deserialize_datetimes(item) for item in obj]
        else:
            return obj
