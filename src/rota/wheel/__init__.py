"""
Wheel - Clustering and Pattern Analysis Module

Discovers vulnerability patterns through:
- Feature extraction
- Clustering algorithms
- Pattern discovery
- Visualization
"""

from .clusterer import VulnerabilityClusterer
from .features import FeatureExtractor

__all__ = ['VulnerabilityClusterer', 'FeatureExtractor']
