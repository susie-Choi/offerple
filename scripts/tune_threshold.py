"""Threshold tuning for historical validation.

This script tests multiple threshold values to find the optimal one.

Usage:
    python scripts/tune_threshold.py results/paper/validation_improved_test/validation_results.jsonl
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zero_day_defense.evaluation.validation.metrics import MetricsCalculator


def tune_threshold(results, thresholds):
    """Test multiple threshold values.
    
    Args:
        results: List of validation results with scores
        thresholds: List of threshold values to test
    
    Returns:
        Dict mapping threshold to metrics
    """
    metrics_calc = MetricsCalculator()
    threshold_metrics = {}
    
    for threshold in thresholds:
        # Reclassify results with new threshold
        reclassified = []
        for r in results:
            score = r["our_score"]
            predicted = score >= threshold
            actual_positive = r["actual_positive"]
            
            # Determine classification
            if actual_positive and predicted:
                classification = "TP"
            elif actual_positive and not predicted:
                classification = "FN"
            elif not actual_positive and predicted:
                classification = "FP"
            else:
                classification = "TN"
            
            reclassified.append({
                **r,
                "predicted": predicted,
                "true_positive": classification == "TP",
                "false_positive": classification == "FP",
                "true_negative": classification == "TN",
                "false_negative": classification == "FN",
            })
        
        # Calculate metrics
        metrics = metrics_calc.calculate(reclassified)
        threshold_metrics[threshold] = metrics
    
    return threshold_metrics


def main():
    parser = argparse.ArgumentParser(description="Tune prediction threshold")
    parser.add_argument("results", type=Path, help="Path to validation results (JSONL)")
    parser.add_argument("--thresholds", type=float, nargs="+", 
                       default=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95],
                       help="Threshold values to test")
    parser.add_argument("--output", type=Path, help="Output file for results")
    
    args = parser.parse_args()
    
    # Load results
    print(f"Loading results from {args.results}")
    results = []
    with args.results.open("r") as f:
        for line in f:
            results.append(json.loads(line))
    
    print(f"Loaded {len(results)} results")
    
    # Tune threshold
    print(f"\nTesting {len(args.thresholds)} threshold values...")
    threshold_metrics = tune_threshold(results, args.thresholds)
    
    # Print comparison table
    print("\n" + "=" * 100)
    print("THRESHOLD TUNING RESULTS")
    print("=" * 100)
    print(f"{'Threshold':<12} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Accuracy':<12} {'TP':<6} {'FP':<6} {'TN':<6} {'FN':<6}")
    print("-" * 100)
    
    best_f1 = 0
    best_threshold = None
    
    for threshold in sorted(args.thresholds):
        metrics = threshold_metrics[threshold]
        
        print(f"{threshold:<12.2f} {metrics['precision']:<12.3f} {metrics['recall']:<12.3f} "
              f"{metrics['f1_score']:<12.3f} {metrics['accuracy']:<12.3f} "
              f"{metrics['true_positives']:<6} {metrics['false_positives']:<6} "
              f"{metrics['true_negatives']:<6} {metrics['false_negatives']:<6}")
        
        if metrics['f1_score'] > best_f1:
            best_f1 = metrics['f1_score']
            best_threshold = threshold
    
    print("-" * 100)
    print(f"\n🎯 Best threshold: {best_threshold:.2f} (F1-Score: {best_f1:.3f})")
    
    # Find balanced threshold (precision ≈ recall)
    min_diff = float('inf')
    balanced_threshold = None
    
    for threshold in sorted(args.thresholds):
        metrics = threshold_metrics[threshold]
        diff = abs(metrics['precision'] - metrics['recall'])
        if diff < min_diff:
            min_diff = diff
            balanced_threshold = threshold
    
    balanced_metrics = threshold_metrics[balanced_threshold]
    print(f"⚖️  Balanced threshold: {balanced_threshold:.2f} "
          f"(Precision: {balanced_metrics['precision']:.3f}, "
          f"Recall: {balanced_metrics['recall']:.3f})")
    
    # Save results
    if args.output:
        output_data = {
            "thresholds": {str(t): m for t, m in threshold_metrics.items()},
            "best_threshold": best_threshold,
            "best_f1_score": best_f1,
            "balanced_threshold": balanced_threshold,
        }
        
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w") as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n📁 Results saved to {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
