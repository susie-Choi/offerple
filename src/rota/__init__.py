"""ROTA - Real-time Operational Threat Assessment.

A wheel-themed architecture for zero-day vulnerability prediction:
- Spokes: Data collectors radiating from the hub
- Hub: Central data integration point
- Wheel: Pattern analysis and clustering
- Oracle: Prediction engine
- Axle: Validation framework
"""

__version__ = "0.1.1"
__author__ = "Susie Choi"

# Main API exports
from .oracle.predictor import predict_vulnerability_risk
from .spokes.cve import CVECollector
from .wheel.patterns import PatternAnalyzer

__all__ = [
    "predict_vulnerability_risk",
    "CVECollector",
    "PatternAnalyzer",
    "__version__",
]
