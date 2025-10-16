"""npm registry metadata collector."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseDataSource, SourceResult


class NPMDataSource(BaseDataSource):
    """Collect metadata about JavaScript packages from the npm registry."""

    source_name = "npm"
    BASE_URL = "https://registry.npmjs.org/{package}"

    def collect(self, package: str, *, cutoff: datetime) -> SourceResult:
        response = self._request("GET", self.BASE_URL.format(package=package))
        payload: Dict[str, Any] = response.json()
        time_map = payload.get("time", {})
        filtered_time = {
            version: timestamp
            for version, timestamp in time_map.items()
            if self._within_cutoff(timestamp, cutoff)
        }
        payload["time"] = filtered_time
        return SourceResult(
            source=self.source_name,
            package=package,
            collected_at=datetime.now(timezone.utc),
            payload=payload,
        )

    @staticmethod
    def _within_cutoff(timestamp: str, cutoff: datetime) -> bool:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return False
        return dt <= cutoff


__all__ = ["NPMDataSource"]
