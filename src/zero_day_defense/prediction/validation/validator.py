"""Prediction validator."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from ..models import ThreatScore, ValidationResult, PerformanceMetrics


class PredictionValidator:
    """Validate predictions against actual CVE disclosures."""
    
    def validate_prediction(
        self,
        prediction: ThreatScore,
        actual_cve: Optional[str],
        validation_date: datetime,
    ) -> ValidationResult:
        """Validate a single prediction.
        
        Args:
            prediction: ThreatScore object
            actual_cve: Actual CVE ID if disclosed, None otherwise
            validation_date: Date of validation
            
        Returns:
            ValidationResult object
        """
        # Determine outcome
        predicted_high_risk = prediction.score >= 0.6
        
        if actual_cve and predicted_high_risk:
            outcome = "TP"  # True Positive
            time_to_disclosure = (validation_date - prediction.predicted_at).days
            accuracy = 1.0
        elif actual_cve and not predicted_high_risk:
            outcome = "FN"  # False Negative
            time_to_disclosure = (validation_date - prediction.predicted_at).days
            accuracy = 0.0
        elif not actual_cve and predicted_high_risk:
            outcome = "FP"  # False Positive
            time_to_disclosure = None
            accuracy = 0.0
        else:  # not actual_cve and not predicted_high_risk
            outcome = "TN"  # True Negative
            time_to_disclosure = None
            accuracy = 1.0
        
        return ValidationResult(
            prediction_id=f"{prediction.package}_{prediction.predicted_at.isoformat()}",
            outcome=outcome,
            accuracy=accuracy,
            time_to_disclosure=time_to_disclosure,
            actual_cve=actual_cve,
            validation_date=validation_date,
        )
    
    def calculate_metrics(
        self,
        validation_results: List[ValidationResult],
    ) -> PerformanceMetrics:
        """Calculate overall performance metrics.
        
        Args:
            validation_results: List of ValidationResult objects
            
        Returns:
            PerformanceMetrics object
        """
        if not validation_results:
            return PerformanceMetrics(
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                accuracy=0.0,
                confusion_matrix=[[0, 0], [0, 0]],
                total_predictions=0,
            )
        
        # Count outcomes
        tp = sum(1 for r in validation_results if r.outcome == "TP")
        fp = sum(1 for r in validation_results if r.outcome == "FP")
        tn = sum(1 for r in validation_results if r.outcome == "TN")
        fn = sum(1 for r in validation_results if r.outcome == "FN")
        
        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / len(validation_results)
        
        confusion_matrix = [
            [tn, fp],  # Actual Negative
            [fn, tp],  # Actual Positive
        ]
        
        return PerformanceMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            accuracy=accuracy,
            confusion_matrix=confusion_matrix,
            total_predictions=len(validation_results),
        )
    
    def save_metrics(
        self,
        metrics: PerformanceMetrics,
        driver,
    ) -> None:
        """Save metrics to Neo4j.
        
        Args:
            metrics: PerformanceMetrics object
            driver: Neo4j driver
        """
        with driver.session() as session:
            session.run(
                """
                CREATE (m:PerformanceMetrics {
                    timestamp: datetime($timestamp),
                    precision: $precision,
                    recall: $recall,
                    f1_score: $f1_score,
                    accuracy: $accuracy,
                    total_predictions: $total_predictions,
                    confusion_matrix: $confusion_matrix
                })
                """,
                timestamp=metrics.timestamp.isoformat(),
                precision=metrics.precision,
                recall=metrics.recall,
                f1_score=metrics.f1_score,
                accuracy=metrics.accuracy,
                total_predictions=metrics.total_predictions,
                confusion_matrix=str(metrics.confusion_matrix),
            )
