"""
Oracle - Prediction and Risk Assessment Module

Predicts vulnerability exploitation risk:
- Risk scoring
- Threat prediction
- Confidence estimation
- Recommendation generation
"""

from .predictor import VulnerabilityPredictor
from .scorer import RiskScorer

__all__ = ['VulnerabilityPredictor', 'RiskScorer']
