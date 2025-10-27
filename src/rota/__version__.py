"""Version information for ROTA."""

try:
    from ._version import version as __version__
except ImportError:
    # Fallback for development without installation
    __version__ = "0.2.0.dev0"

__title__ = "rota"
__description__ = "Real-time Offensive Threat Assessment - Zero-day vulnerability prediction"
__author__ = "ROTA Research Team"
__license__ = "MIT"
