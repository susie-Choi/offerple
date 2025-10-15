"""Package signal collector for registry metadata."""
from __future__ import annotations

from datetime import datetime
from typing import List

from ...data_sources.base import BaseDataSource
from ..models import ReleaseSignal, DependencyDiff


class PackageSignalCollector(BaseDataSource):
    """Collect package metadata from registries."""
    
    source_name = "package_signals"
    
    def collect_version_history(
        self,
        package: str,
        ecosystem: str,
        since: datetime,
        until: datetime,
    ) -> List[ReleaseSignal]:
        """Collect package version release history.
        
        Args:
            package: Package name
            ecosystem: Ecosystem (pypi, npm, maven)
            since: Start of time range
            until: End of time range
            
        Returns:
            List of ReleaseSignal objects
        """
        # TODO: Implement in task 2.4
        raise NotImplementedError("To be implemented in task 2.4")
    
    def collect_dependency_changes(
        self,
        package: str,
        ecosystem: str,
        version_from: str,
        version_to: str,
    ) -> DependencyDiff:
        """Collect dependency changes between versions.
        
        Args:
            package: Package name
            ecosystem: Ecosystem (pypi, npm, maven)
            version_from: Starting version
            version_to: Ending version
            
        Returns:
            DependencyDiff object
        """
        # TODO: Implement in task 2.4
        raise NotImplementedError("To be implemented in task 2.4")
