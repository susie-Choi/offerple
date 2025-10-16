 """Prediction scoring engine."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Tuple

import numpy as np

from ..models import FeatureVector, ThreatScore
from .clusterer import CVEClusterer
from ..exceptions import PredictionError


class PredictionScorer:
    """Score packages for potential vulnerability risk."""
    
    def __init__(
        self,
        clusterer: CVEClusterer,
        threshold: float = 0.7,
    ):
        """Initialize scorer.
        
        Args:
            clusterer: Trained CVE clusterer
            threshold: Threat score threshold for flagging
        """
        self.clusterer = clusterer
        self.threshold = threshold
    
    def score_package(
        self,
        vector: FeatureVector,
    ) -> ThreatScore:
        """Calculate threat score for a package.
        
        Args:
            vector: FeatureVector for the package
            
        Returns:
            ThreatScore object
            
        Raises:
            PredictionError: If scoring fails
        """
        # Get cluster assignment
        cluster_id, distance = self.clusterer.predict_cluster(vector)
        
        # Get cluster metadata
        cluster_metadata = self.clusterer.get_cluster_metadata(cluster_id)
        
        # Calculate threat score based on:
        # 1. Distance to cluster centroid (closer = higher risk)
        # 2. Cluster severity (avg CVSS/EPSS)
        
        # Normalize distance (inverse - closer is higher score)
        max_distance = 10.0  # Assumed max distance
        distance_score = max(0, 1 - (distance / max_distance))
        
        # Cluster severity score (based on avg CVSS)
        severity_score = cluster_metadata.avg_cvss / 10.0 if cluster_metadata.avg_cvss > 0 else 0.5
        
        # Combined threat score (weighted average)
        threat_score = 0.6 * distance_score + 0.4 * severity_score
        
        # Calculate confidence based on cluster size and distance
        confidence = min(1.0, cluster_metadata.size / 100.0) * distance_score
        
        # Find similar CVEs
        similar_cves = self.find_similar_cves(vector, top_k=5)
        
        # Determine risk level
        if threat_score >= 0.8:
            risk_level = "CRITICAL"
        elif threat_score >= 0.6:
            risk_level = "HIGH"
        elif threat_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return ThreatScore(
            package=vector.package,
            score=threat_score,
            confidence=confidence,
            nearest_clusters=[(cluster_id, distance)],
            similar_cves=similar_cves,
            risk_level=risk_level,
            predicted_at=datetime.now(timezone.utc),
            metadata={
                "cluster_size": cluster_metadata.size,
                "cluster_avg_cvss": cluster_metadata.avg_cvss,
                "cluster_avg_epss": cluster_metadata.avg_epss,
            },
        )
    
    def calculate_similarity(
        self,
        vector1: FeatureVector,
        vector2: FeatureVector,
    ) -> float:
        """Calculate cosine similarity between vectors.
        
        Args:
            vector1: First feature vector
            vector2: Second feature vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        v1 = vector1.combined
        v2 = vector2.combined
        
        # Cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def find_similar_cves(
        self,
        vector: FeatureVector,
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """Find most similar historical CVEs.
        
        Args:
            vector: FeatureVector to compare
            top_k: Number of similar CVEs to return
            
        Returns:
            List of (cve_id, similarity_score) tuples
        """
        if not self.clusterer.cve_vectors:
            return []
        
        similarities = []
        for cve_vector in self.clusterer.cve_vectors:
            similarity = self.calculate_similarity(vector, cve_vector)
            cve_id = cve_vector.metadata.get('cve_id', cve_vector.package)
            similarities.append((cve_id, similarity))
        
        # Sort by similarity (descending) and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def save_prediction(
        self,
        threat_score: ThreatScore,
        driver,
    ) -> None:
        """Save prediction to Neo4j.
        
        Args:
            threat_score: ThreatScore object to save
            driver: Neo4j driver instance
        """
        with driver.session() as session:
            # Create prediction node
            session.run(
                """
                MERGE (p:Prediction {package: $package, predicted_at: datetime($predicted_at)})
                SET p.score = $score,
                    p.confidence = $confidence,
                    p.risk_level = $risk_level,
                    p.validated = false
                """,
                package=threat_score.package,
                predicted_at=threat_score.predicted_at.isoformat(),
                score=threat_score.score,
                confidence=threat_score.confidence,
                risk_level=threat_score.risk_level,
            )
            
            # Link to nearest clusters
            for cluster_id, distance in threat_score.nearest_clusters:
                session.run(
                    """
                    MATCH (p:Prediction {package: $package, predicted_at: datetime($predicted_at)})
                    MATCH (c:Cluster {id: $cluster_id})
                    MERGE (p)-[r:NEAREST_CLUSTER]->(c)
                    SET r.distance = $distance
                    """,
                    package=threat_score.package,
                    predicted_at=threat_score.predicted_at.isoformat(),
                    cluster_id=str(cluster_id),
                    distance=distance,
                )
            
            # Link to similar CVEs
            for cve_id, similarity in threat_score.similar_cves:
                session.run(
                    """
                    MATCH (p:Prediction {package: $package, predicted_at: datetime($predicted_at)})
                    MERGE (cve:CVE {id: $cve_id})
                    MERGE (p)-[r:SIMILAR_TO_CVE]->(cve)
                    SET r.similarity = $similarity
                    """,
                    package=threat_score.package,
                    predicted_at=threat_score.predicted_at.isoformat(),
                    cve_id=cve_id,
                    similarity=similarity,
                )
