"""Spokes - Data collection modules.

Like spokes on a wheel, these collectors radiate out to gather data
from various sources and feed it back to the hub.
"""

from .cve import CVECollector
from .advisory import AdvisoryCollector
from .epss import EPSSCollector

__all__ = [
    "CVECollector",
    "AdvisoryCollector", 
    "EPSSCollector",
]
