"""Version information for ROTA."""

# Version is managed in pyproject.toml
# This file imports it for backward compatibility
try:
    from importlib.metadata import version
    __version__ = version("rota")
except Exception:
    # Fallback for development
    __version__ = "0.2.0"

__title__ = "rota"
__description__ = "Real-time Offensive Threat Assessment - Zero-day vulnerability prediction"
__author__ = "ROTA Research Team"
__license__ = "MIT"
