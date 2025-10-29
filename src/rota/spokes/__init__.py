"""
Spokes - Data Collection Module

Collects vulnerability data from multiple sources:
- CVE/NVD: Vulnerability database
- EPSS: Exploit prediction scores
- KEV: Known exploited vulnerabilities
- CWE: Common Weakness Enumeration
- GitHub Advisory: Package-level advisories
- Exploit-DB: Public exploit database
"""

from .base import BaseCollector
from .cve import CVECollector
from .epss import EPSSCollector
from .exploit_db import ExploitDBCollector
from .github import GitHubSignalsCollector
from .github_advisory import GitHubAdvisoryCollector
from .kev import KEVCollector
from .cwe import CWECollector
from .package import PackageCollector, DependencyCollector

__all__ = [
    'BaseCollector',
    'CVECollector',
    'EPSSCollector',
    'ExploitDBCollector',
    'GitHubSignalsCollector',
    'GitHubAdvisoryCollector',
    'KEVCollector',
    'CWECollector',
    'PackageCollector',
    'DependencyCollector',
]
