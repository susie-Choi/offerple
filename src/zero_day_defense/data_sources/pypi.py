"""PyPI metadata collector."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .base import BaseDataSource, SourceResult


def _parse_iso8601(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


class PyPIDataSource(BaseDataSource):
    """Collect metadata about Python packages from the PyPI JSON API."""

    source_name = "pypi"
    BASE_URL = "https://pypi.org/pypi/{package}/json"

    def collect(self, package: str, *, cutoff: datetime) -> SourceResult:
        response = self._request("GET", self.BASE_URL.format(package=package))
        payload: Dict[str, Any] = response.json()
        releases = payload.get("releases", {})
        filtered_releases = {
            version: [
                file_info
                for file_info in files
                if file_info.get("upload_time_iso_8601")
                and _parse_iso8601(file_info["upload_time_iso_8601"]) <= cutoff
            ]
            for version, files in releases.items()
        }
        payload["releases"] = {
            version: files
            for version, files in filtered_releases.items()
            if files
        }
        return SourceResult(
            source=self.source_name,
            package=package,
            collected_at=datetime.utcnow(),
            payload=payload,
        )


__all__ = ["PyPIDataSource"]
