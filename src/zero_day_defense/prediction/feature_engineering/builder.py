"""Feature vector builder."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple

import numpy as np
from sklearn.preprocessing import StandardScaler

from ..models import FeatureVector
from ..exceptions import FeatureExtractionError


class FeatureVectorBuilder:
    """Build unified feature vectors from all sources."""
    
    def __init__(self):
        """Initialize builder with scaler."""
        self.scaler = StandardScaler()
        self._is_fitted = False
        self._feature_names = None
    
    def build_vector(
        self,
        package: str,
        time_window: Tuple[datetime, datetime],
        structural_features: Dict[str, float],
        semantic_embeddings: np.ndarray,
        metadata: Optional[Dict] = None,
    ) -> FeatureVector:
        """Build and normalize feature vector.
        
        Args:
            package: Package name
            time_window: (start, end) datetime tuple
            structural_features: Dictionary of structural features
            semantic_embeddings: Semantic embedding vector
            metadata: Additional metadata
            
        Returns:
            FeatureVector object
            
        Raises:
            FeatureExtractionError: If vector building fails
        """
        if not structural_features:
            raise FeatureExtractionError("No structural features provided")
        
        if semantic_embeddings is None or len(semantic_embeddings) == 0:
            raise FeatureExtractionError("No semantic embeddings provided")
        
        # Normalize structural features
        normalized_structural = self.normalize_features(structural_features)
        
        # Convert to numpy array
        structural_array = np.array(list(normalized_structural.values()))
        
        # Normalize semantic embeddings (L2 normalization)
        semantic_norm = semantic_embeddings / (np.linalg.norm(semantic_embeddings) + 1e-10)
        
        # Combine structural and semantic features
        combined = np.concatenate([structural_array, semantic_norm])
        
        # Generate unique ID
        vector_id = str(uuid.uuid4())
        
        return FeatureVector(
            id=vector_id,
            package=package,
            time_window=time_window,
            structural=normalized_structural,
            semantic=semantic_norm,
            combined=combined,
            metadata=metadata or {},
        )
    
    def normalize_features(
        self,
        features: Dict[str, float],
    ) -> Dict[str, float]:
        """Normalize features using StandardScaler.
        
        Args:
            features: Dictionary of feature names to values
            
        Returns:
            Dictionary of normalized features
            
        Raises:
            FeatureExtractionError: If normalization fails
        """
        if not features:
            raise FeatureExtractionError("No features to normalize")
        
        # Ensure consistent feature ordering
        if self._feature_names is None:
            self._feature_names = sorted(features.keys())
        
        # Check that all expected features are present
        missing_features = set(self._feature_names) - set(features.keys())
        if missing_features:
            raise FeatureExtractionError(
                f"Missing features: {missing_features}"
            )
        
        # Extract values in consistent order
        values = np.array([features[name] for name in self._feature_names]).reshape(1, -1)
        
        # Fit scaler on first call
        if not self._is_fitted:
            self.scaler.fit(values)
            self._is_fitted = True
        
        # Transform values
        try:
            normalized_values = self.scaler.transform(values)[0]
        except Exception as e:
            # If transformation fails, use partial fit and retry
            self.scaler.partial_fit(values)
            normalized_values = self.scaler.transform(values)[0]
        
        # Return as dictionary
        return {
            name: float(value)
            for name, value in zip(self._feature_names, normalized_values)
        }
    
    def fit_scaler(self, feature_dicts: list[Dict[str, float]]) -> None:
        """Fit scaler on multiple feature dictionaries.
        
        Args:
            feature_dicts: List of feature dictionaries
            
        Raises:
            FeatureExtractionError: If fitting fails
        """
        if not feature_dicts:
            raise FeatureExtractionError("No feature dictionaries provided for fitting")
        
        # Ensure consistent feature ordering
        if self._feature_names is None:
            self._feature_names = sorted(feature_dicts[0].keys())
        
        # Extract all values
        all_values = []
        for features in feature_dicts:
            values = [features[name] for name in self._feature_names]
            all_values.append(values)
        
        # Fit scaler
        self.scaler.fit(np.array(all_values))
        self._is_fitted = True
    
    def reset_scaler(self) -> None:
        """Reset the scaler to unfitted state."""
        self.scaler = StandardScaler()
        self._is_fitted = False
        self._feature_names = None
