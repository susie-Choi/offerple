"""Base classes and helpers for external data sources."""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

import requests


@dataclass
class SourceResult:
    """Result of a data collection call."""

    source: str
    package: str
    collected_at: datetime
    payload: Dict[str, Any]


class DataSourceError(RuntimeError):
    """Raised when a data source cannot be reached or returns invalid data."""


class BaseDataSource:
    """Common functionality for API-based data sources."""

    source_name: str

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        rate_limit_sleep: float = 1.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.timeout = timeout
        self.rate_limit_sleep = rate_limit_sleep
        self.session = session or requests.Session()

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Perform an HTTP request with basic error handling."""

        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if response.status_code == 429:
            time.sleep(self.rate_limit_sleep)
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if not response.ok:
            raise DataSourceError(
                f"{self.source_name} request failed: {response.status_code} {response.text[:200]}"
            )
        return response

    def collect(self, package: str, *, cutoff: datetime) -> SourceResult:
        """Collect data for a single package.

        Sub-classes must implement this method.
        """

        raise NotImplementedError

    def collect_many(self, packages: Iterable[str], *, cutoff: datetime) -> Iterable[SourceResult]:
        """Convenience method to iterate over multiple packages."""

        for package in packages:
            yield self.collect(package, cutoff=cutoff)


__all__ = ["BaseDataSource", "SourceResult", "DataSourceError"]
