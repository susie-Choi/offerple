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
from .kev import KEVCollector
from .cwe import CWECollector

__all__ = [
    'BaseCollector',
    'CVECollector',
    'EPSSCollector',
    'KEVCollector',
    'CWECollector',
]
