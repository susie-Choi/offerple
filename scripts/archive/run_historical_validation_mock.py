"""Run historical validation with mock data (no GitHub API needed).

This is for testing the framework without API rate limits.

Usage:
    python scripts/run_historical_validation_mock.py results/paper/dataset_test3/cves.jsonl
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zero_day_defense.evaluation.validation.temporal_splitter import TemporalSplitter
from zero_day_defense.evaluation.validation.metrics import MetricsCalculator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def generate_mock_signals(cve_id: str, github_repo: str, seed: int = 42):
    """Generate mock signals for testing."""
    rng = Random(seed + hash(cve_id))
    
    # Simulate some features based on CVE characteristics
    # Higher scores for certain patterns
    base_score = rng.uniform(0.3, 0.8)
    
    # Add some randomness
    noise = rng.gauss(0, 0.1)
    score = max(0.0, min(1.0, base_score + noise))
    
    return {
        "commit_frequency": rng.uniform(0.5, 2.0),
        "lines_added_avg": rng.uniform(10, 100),
        "security_keywords": rng.uniform(0, 0.3),
        "author_diversity": rng.uniform(2, 10),
        "score": score,
    }


def main():
    parser = argparse.ArgumentParser(description="Run historical validation (MOCK)")
    parser.add_argument("dataset", type=Path, help="Path to CVE dataset (JSONL)")
    parser.add_argument("--output-dir", type=Path, default=Path("results/paper/validation_mock"))
    parser.add_argument("--prediction-window", type=int, default=90, help="Days before CVE")
    parser.add_argument("--top-k", type=int, default=50, help="Top-K predictions to consider")
    parser.add_argument("--max-cves", type=int, help="Max CVEs to validate (for testing)")
    parser.add_argument("--threshold", type=float, default=0.6, help="Prediction threshold")
    
    args = parser.parse_args()
    
    # Load dataset
    logger.info(f"Loading dataset from {args.dataset}")
    cves = []
    with args.dataset.open("r") as f:
        for line in f:
            cves.append(json.loads(line))
            if args.max_cves and len(cves) >= args.max_cves:
                break
    
    logger.info(f"Loaded {len(cves)} CVEs")
    logger.info("=" * 60)
    logger.info("MOCK MODE: Using simulated signals (no GitHub API)")
    logger.info("=" * 60)
    
    # Initialize components
    splitter = TemporalSplitter(prediction_window_days=args.prediction_window)
    metrics_calc = MetricsCalculator()
    
    # Run validation
    results = []
    for i, cve in enumerate(cves, 1):
        logger.info(f"[{i}/{len(cves)}] Validating {cve['cve_id']}")
        
        # Create temporal split
        split = splitter.create_validation_split(cve)
        if not split.get("valid"):
            logger.warning(f"  Skipping: {split.get('reason')}")
            continue
        
        cutoff_date = split["cutoff_date"]
        github_repo = cve["github_repo"]
        
        try:
            # Generate mock signals (no API call)
            mock_signals = generate_mock_signals(cve["cve_id"], github_repo)
            score = mock_signals["score"]
            
            # Determine if predicted (threshold-based)
            predicted = score >= args.threshold
            
            # Calculate lead time
            lead_time = (split["disclosure_date"] - cutoff_date).days
            
            # Classify result
            # In mock mode, we assume all CVEs are "true" vulnerabilities
            # So predicted = TP, not predicted = FN
            result = {
                "cve_id": cve["cve_id"],
                "github_repo": github_repo,
                "cvss_score": cve.get("cvss_score"),
                "cutoff_date": cutoff_date.isoformat(),
                "disclosure_date": split["disclosure_date"].isoformat(),
                "predicted": predicted,
                "score": score,
                "lead_time_days": lead_time if predicted else None,
                "true_positive": predicted,
                "false_positive": False,
                "true_negative": False,
                "false_negative": not predicted,
                "mock_signals": mock_signals,
            }
            
            results.append(result)
            logger.info(f"  Score: {score:.3f}, Predicted: {predicted}, Lead Time: {lead_time} days")
            
        except Exception as e:
            logger.error(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Calculate metrics
    logger.info("\n" + "=" * 60)
    logger.info("Calculating metrics...")
    logger.info("=" * 60)
    metrics = metrics_calc.calculate(results)
    metrics_calc.print_metrics(metrics, "Historical Validation (MOCK)")
    
    # Save results
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = args.output_dir / "validation_results.jsonl"
    with results_file.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    
    metrics_file = args.output_dir / "metrics.json"
    with metrics_file.open("w") as f:
        json.dump(metrics, f, indent=2)
    
    # Generate summary
    summary = {
        "total_cves": len(results),
        "predicted_cves": sum(1 for r in results if r["predicted"]),
        "avg_score": sum(r["score"] for r in results) / len(results) if results else 0,
        "avg_lead_time": metrics["avg_lead_time"],
        "metrics": metrics,
        "config": {
            "prediction_window": args.prediction_window,
            "threshold": args.threshold,
            "top_k": args.top_k,
        },
    }
    
    summary_file = args.output_dir / "summary.json"
    with summary_file.open("w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\nResults saved to {args.output_dir}")
    logger.info(f"  Validation results: {results_file}")
    logger.info(f"  Metrics: {metrics_file}")
    logger.info(f"  Summary: {summary_file}")
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total CVEs validated: {len(results)}")
    logger.info(f"Predicted (score >= {args.threshold}): {summary['predicted_cves']}")
    logger.info(f"Average score: {summary['avg_score']:.3f}")
    logger.info(f"Average lead time: {summary['avg_lead_time']:.1f} days")
    logger.info("")
    logger.info("NOTE: This is MOCK data for testing the framework.")
    logger.info("For real results, use run_historical_validation.py with GitHub token.")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
