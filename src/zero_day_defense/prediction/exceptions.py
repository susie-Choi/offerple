"""Custom exceptions for the prediction system."""


class PredictionSystemError(Exception):
    """Base exception for prediction system errors."""


# Signal Collection Errors
class SignalCollectionError(PredictionSystemError):
    """Base exception for signal collection errors."""


class GitHubRateLimitError(SignalCollectionError):
    """GitHub API rate limit exceeded."""


class RepositoryNotFoundError(SignalCollectionError):
    """Repository not found or not accessible."""


class TimeRangeError(SignalCollectionError):
    """Invalid time range specified."""


# Feature Engineering Errors
class FeatureExtractionError(PredictionSystemError):
    """Base exception for feature extraction errors."""


class InsufficientDataError(FeatureExtractionError):
    """Not enough data to extract features."""


class EmbeddingError(FeatureExtractionError):
    """LLM embedding generation failed."""


# Prediction Errors
class PredictionError(PredictionSystemError):
    """Base exception for prediction errors."""


class ClusterNotFoundError(PredictionError):
    """Cluster model not trained or loaded."""


class InvalidVectorError(PredictionError):
    """Feature vector has invalid dimensions."""


# Validation Errors
class ValidationError(PredictionSystemError):
    """Base exception for validation errors."""


class InvalidOutcomeError(ValidationError):
    """Invalid validation outcome specified."""
