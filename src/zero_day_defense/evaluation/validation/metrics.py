"""Performance metrics calculator."""
from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np


logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculate performance metrics for predictions."""
    
    def calculate(self, validation_results: List[Dict]) -> Dict:
        """Calculate comprehensive metrics.
        
        Args:
            validation_results: List of validation results with:
                - predicted: bool
                - true_positive: bool
                - false_positive: bool
                - true_negative: bool
                - false_negative: bool
                - lead_time_days: Optional[int]
        
        Returns:
            Metrics dict
        """
        if not validation_results:
            return self._empty_metrics()
        
        # Count outcomes
        tp = sum(1 for r in validation_results if r.get("true_positive"))
        fp = sum(1 for r in validation_results if r.get("false_positive"))
        tn = sum(1 for r in validation_results if r.get("true_negative"))
        fn = sum(1 for r in validation_results if r.get("false_negative"))
        
        # Calculate basic metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0.0
        
        # Calculate TPR and FPR
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # Same as recall
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        # Calculate lead times
        lead_times = [
            r["lead_time_days"]
            for r in validation_results
            if r.get("lead_time_days") is not None
        ]
        
        avg_lead_time = np.mean(lead_times) if lead_times else 0.0
        median_lead_time = np.median(lead_times) if lead_times else 0.0
        
        # Calculate coverage
        predicted_count = sum(1 for r in validation_results if r.get("predicted"))
        coverage = predicted_count / len(validation_results) if validation_results else 0.0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "accuracy": accuracy,
            "tpr": tpr,
            "fpr": fpr,
            "avg_lead_time": avg_lead_time,
            "median_lead_time": median_lead_time,
            "coverage": coverage,
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "total": len(validation_results),
        }
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics."""
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "accuracy": 0.0,
            "tpr": 0.0,
            "fpr": 0.0,
            "avg_lead_time": 0.0,
            "median_lead_time": 0.0,
            "coverage": 0.0,
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": 0,
            "false_negatives": 0,
            "total": 0,
        }
    
    def print_metrics(self, metrics: Dict, method_name: str = "System") -> None:
        """Print metrics in readable format.
        
        Args:
            metrics: Metrics dict
            method_name: Name of method
        """
        print(f"\n{'='*60}")
        print(f"{method_name} Performance Metrics")
        print(f"{'='*60}")
        print(f"Precision:    {metrics['precision']:.3f}")
        print(f"Recall:       {metrics['recall']:.3f}")
        print(f"F1-Score:     {metrics['f1_score']:.3f}")
        print(f"Accuracy:     {metrics['accuracy']:.3f}")
        print(f"Coverage:     {metrics['coverage']:.3f}")
        print(f"\nLead Time:")
        print(f"  Average:    {metrics['avg_lead_time']:.1f} days")
        print(f"  Median:     {metrics['median_lead_time']:.1f} days")
        print(f"\nConfusion Matrix:")
        print(f"  TP: {metrics['true_positives']:3d}  FP: {metrics['false_positives']:3d}")
        print(f"  FN: {metrics['false_negatives']:3d}  TN: {metrics['true_negatives']:3d}")
        print(f"{'='*60}\n")
