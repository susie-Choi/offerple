"""
Axle - Evaluation and Validation Module

Validates predictions and measures performance:
- Temporal validation
- Metrics calculation
- Baseline comparisons
- Statistical analysis
"""

from .validator import TemporalValidator
from .metrics import MetricsCalculator

__all__ = ['TemporalValidator', 'MetricsCalculator']
