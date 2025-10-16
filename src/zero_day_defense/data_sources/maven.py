"""Maven Central metadata collector."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from .base import BaseDataSource, SourceResult


class MavenCentralDataSource(BaseDataSource):
    """Collect metadata about Java artifacts from search.maven.org."""

    source_name = "maven"
    SEARCH_URL = "https://search.maven.org/solrsearch/select"

    def _split_coordinates(self, package: str) -> Tuple[str, str]:
        if ":" not in package:
            raise ValueError(
                "Maven packages must use 'groupId:artifactId' notation;"
                f" received '{package}'"
            )
        group_id, artifact_id = package.split(":", 1)
        return group_id, artifact_id

    def collect(self, package: str, *, cutoff: datetime) -> SourceResult:
        group_id, artifact_id = self._split_coordinates(package)
        params = {
            "q": f"g:\"{group_id}\" AND a:\"{artifact_id}\"",
            "rows": 200,
            "core": "gav",
            "wt": "json",
            "sort": "v desc",
        }
        response = self._request("GET", self.SEARCH_URL, params=params)
        payload: Dict[str, Any] = response.json()
        docs = payload.get("response", {}).get("docs", [])
        filtered_docs = [doc for doc in docs if self._doc_within_cutoff(doc, cutoff)]
        payload["response"]["docs"] = filtered_docs
        return SourceResult(
            source=self.source_name,
            package=package,
            collected_at=datetime.now(timezone.utc),
            payload=payload,
        )

    @staticmethod
    def _doc_within_cutoff(doc: Dict[str, Any], cutoff: datetime) -> bool:
        timestamp = doc.get("timestamp")
        if not timestamp:
            return True
        if isinstance(timestamp, (int, float)):
            doc_time = datetime.utcfromtimestamp(timestamp / 1000.0)
        else:
            doc_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return doc_time <= cutoff


__all__ = ["MavenCentralDataSource"]
