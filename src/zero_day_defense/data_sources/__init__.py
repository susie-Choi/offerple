"""Data source implementations for the Zero-Day Defense pipeline."""

from .base import BaseDataSource, DataSourceError, SourceResult
from .github import GitHubDataSource
from .maven import MavenCentralDataSource
from .npm import NPMDataSource
from .pypi import PyPIDataSource

__all__ = [
    "BaseDataSource",
    "DataSourceError",
    "SourceResult",
    "GitHubDataSource",
    "MavenCentralDataSource",
    "NPMDataSource",
    "PyPIDataSource",
]
