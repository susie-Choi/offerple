"""CVE clustering engine."""
from __future__ import annotations

import pickle
from typing import Dict, List, Tuple

import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score

from ..models import FeatureVector, ClusterMetadata
from ..exceptions import ClusterNotFoundError, InvalidVectorError


class CVEClusterer:
    """Cluster historical CVE data by vulnerability patterns."""
    
    def __init__(
        self,
        n_clusters: int = 10,
        algorithm: str = "kmeans",
        random_state: int = 42,
    ):
        """Initialize clusterer.
        
        Args:
            n_clusters: Number of clusters (for kmeans)
            algorithm: Clustering algorithm (kmeans, dbscan)
            random_state: Random state for reproducibility
        """
        self.n_clusters = n_clusters
        self.algorithm = algorithm
        self.random_state = random_state
        self.model = None
        self.cluster_metadata: Dict[int, ClusterMetadata] = {}
        self.cve_vectors: List[FeatureVector] = []
        self.is_fitted = False
    
    def fit(
        self,
        cve_vectors: List[FeatureVector],
    ) -> "CVEClusterer":
        """Fit clustering model on historical CVE vectors.
        
        Args:
            cve_vectors: List of FeatureVector objects for CVEs
            
        Returns:
            Self for method chaining
            
        Raises:
            InvalidVectorError: If vectors are invalid
        """
        if not cve_vectors:
            raise InvalidVectorError("No CVE vectors provided for clustering")
        
        self.cve_vectors = cve_vectors
        
        # Extract combined vectors
        X = np.array([v.combined for v in cve_vectors])
        
        # Fit clustering model
        if self.algorithm == "kmeans":
            self.model = KMeans(
                n_clusters=self.n_clusters,
                random_state=self.random_state,
                n_init=10,
            )
            self.model.fit(X)
        elif self.algorithm == "dbscan":
            self.model = DBSCAN(eps=0.5, min_samples=5)
            self.model.fit(X)
            # Update n_clusters based on DBSCAN results
            self.n_clusters = len(set(self.model.labels_)) - (1 if -1 in self.model.labels_ else 0)
        else:
            raise InvalidVectorError(f"Unknown clustering algorithm: {self.algorithm}")
        
        # Build cluster metadata
        self._build_cluster_metadata()
        
        self.is_fitted = True
        return self
    
    def predict_cluster(
        self,
        vector: FeatureVector,
    ) -> Tuple[int, float]:
        """Predict cluster assignment and distance to centroid.
        
        Args:
            vector: FeatureVector to classify
            
        Returns:
            Tuple of (cluster_id, distance_to_centroid)
            
        Raises:
            ClusterNotFoundError: If model not fitted
            InvalidVectorError: If vector is invalid
        """
        if not self.is_fitted or self.model is None:
            raise ClusterNotFoundError("Clustering model not fitted. Call fit() first.")
        
        X = vector.combined.reshape(1, -1)
        
        if self.algorithm == "kmeans":
            cluster_id = int(self.model.predict(X)[0])
            # Calculate distance to centroid
            centroid = self.model.cluster_centers_[cluster_id]
            distance = float(np.linalg.norm(vector.combined - centroid))
        elif self.algorithm == "dbscan":
            # For DBSCAN, find nearest cluster
            distances = []
            for cluster_id in range(self.n_clusters):
                cluster_vectors = [
                    v.combined for i, v in enumerate(self.cve_vectors)
                    if self.model.labels_[i] == cluster_id
                ]
                if cluster_vectors:
                    centroid = np.mean(cluster_vectors, axis=0)
                    dist = float(np.linalg.norm(vector.combined - centroid))
                    distances.append((cluster_id, dist))
            
            if distances:
                cluster_id, distance = min(distances, key=lambda x: x[1])
            else:
                cluster_id, distance = -1, float('inf')
        else:
            raise InvalidVectorError(f"Unknown algorithm: {self.algorithm}")
        
        return cluster_id, distance
    
    def get_cluster_metadata(
        self,
        cluster_id: int,
    ) -> ClusterMetadata:
        """Get cluster characteristics.
        
        Args:
            cluster_id: Cluster identifier
            
        Returns:
            ClusterMetadata object
            
        Raises:
            ClusterNotFoundError: If cluster not found
        """
        if cluster_id not in self.cluster_metadata:
            raise ClusterNotFoundError(f"Cluster {cluster_id} not found")
        
        return self.cluster_metadata[cluster_id]
    
    def _build_cluster_metadata(self) -> None:
        """Build metadata for each cluster."""
        labels = self.model.labels_ if hasattr(self.model, 'labels_') else self.model.predict(
            np.array([v.combined for v in self.cve_vectors])
        )
        
        for cluster_id in range(self.n_clusters):
            # Get vectors in this cluster
            cluster_indices = [i for i, label in enumerate(labels) if label == cluster_id]
            cluster_vectors = [self.cve_vectors[i] for i in cluster_indices]
            
            if not cluster_vectors:
                continue
            
            # Calculate centroid
            centroid = np.mean([v.combined for v in cluster_vectors], axis=0)
            
            # Extract CVE IDs (from metadata)
            cve_ids = [v.metadata.get('cve_id', v.package) for v in cluster_vectors]
            
            # Get dominant CWE types (placeholder - would need actual CVE data)
            dominant_cwe = []
            
            # Calculate average CVSS and EPSS (placeholder - would need actual CVE data)
            avg_cvss = 0.0
            avg_epss = 0.0
            
            # Create metadata
            self.cluster_metadata[cluster_id] = ClusterMetadata(
                cluster_id=cluster_id,
                centroid=centroid,
                size=len(cluster_vectors),
                dominant_cwe=dominant_cwe,
                avg_cvss=avg_cvss,
                avg_epss=avg_epss,
                example_cves=cve_ids[:5],  # First 5 as examples
            )
    
    def save_to_neo4j(self, driver) -> None:
        """Save cluster model and metadata to Neo4j.
        
        Args:
            driver: Neo4j driver instance
            
        Raises:
            ClusterNotFoundError: If model not fitted
        """
        if not self.is_fitted:
            raise ClusterNotFoundError("Model not fitted. Call fit() first.")
        
        with driver.session() as session:
            # Save each cluster
            for cluster_id, metadata in self.cluster_metadata.items():
                session.run(
                    """
                    MERGE (c:Cluster {id: $cluster_id})
                    SET c.algorithm = $algorithm,
                        c.size = $size,
                        c.avg_cvss = $avg_cvss,
                        c.avg_epss = $avg_epss,
                        c.dominant_cwe = $dominant_cwe,
                        c.example_cves = $example_cves,
                        c.centroid = $centroid
                    """,
                    cluster_id=str(cluster_id),
                    algorithm=self.algorithm,
                    size=metadata.size,
                    avg_cvss=metadata.avg_cvss,
                    avg_epss=metadata.avg_epss,
                    dominant_cwe=metadata.dominant_cwe,
                    example_cves=metadata.example_cves,
                    centroid=metadata.centroid.tolist(),
                )
            
            # Link CVEs to clusters
            labels = self.model.labels_ if hasattr(self.model, 'labels_') else self.model.predict(
                np.array([v.combined for v in self.cve_vectors])
            )
            
            for i, vector in enumerate(self.cve_vectors):
                cluster_id = int(labels[i])
                cve_id = vector.metadata.get('cve_id', vector.package)
                
                session.run(
                    """
                    MATCH (c:Cluster {id: $cluster_id})
                    MERGE (cve:CVE {id: $cve_id})
                    MERGE (c)-[:CONTAINS_CVE]->(cve)
                    """,
                    cluster_id=str(cluster_id),
                    cve_id=cve_id,
                )
    
    def save_model(self, filepath: str) -> None:
        """Save clustering model to file.
        
        Args:
            filepath: Path to save model
        """
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'algorithm': self.algorithm,
                'n_clusters': self.n_clusters,
                'cluster_metadata': self.cluster_metadata,
                'is_fitted': self.is_fitted,
            }, f)
    
    def load_model(self, filepath: str) -> None:
        """Load clustering model from file.
        
        Args:
            filepath: Path to load model from
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.algorithm = data['algorithm']
            self.n_clusters = data['n_clusters']
            self.cluster_metadata = data['cluster_metadata']
            self.is_fitted = data['is_fitted']
