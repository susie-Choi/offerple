"""
CLI - Command Line Interface

ROTA command-line interface organized by module:
- spokes: Data collection commands
- hub: Data integration commands
- wheel: Clustering commands
- oracle: Prediction commands
- axle: Evaluation commands
"""

from .main import cli

__all__ = ['cli']
