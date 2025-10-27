"""ROTA - Real-time Operational Threat Assessment.

AI-powered zero-day vulnerability prediction system.
"""

__version__ = "0.1.1"
__author__ = "Susie Choi"
__email__ = "susie.choi@example.com"

# Legacy data collection API
from .config import DataCollectionConfig, PackageDescriptor, load_config
from .pipeline import DataCollectionPipeline, create_pipeline

# Main prediction API
try:
    from .prediction.signal_collectors.github_signals_fast import analyze_code_push
    from .prediction.feature_engineering.extractor import FeatureExtractor
    from .prediction.engine.scorer import RiskScorer
    
    __all__ = [
        # Main API
        "analyze_code_push",
        "FeatureExtractor", 
        "RiskScorer",
        # Legacy API
        "DataCollectionConfig",
        "PackageDescriptor",
        "load_config",
        "DataCollectionPipeline",
        "create_pipeline",
        # Metadata
        "__version__",
    ]
except ImportError:
    # Fallback if prediction modules not available
    __all__ = [
        "DataCollectionConfig",
        "PackageDescriptor",
        "load_config",
        "DataCollectionPipeline",
        "create_pipeline",
        "__version__",
    ]
