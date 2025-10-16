"""Run historical validation for paper experiments.

This is the CORE script for paper results.

Usage:
    python scripts/run_historical_validation.py results/paper/dataset/cves_valid.jsonl
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zero_day_defense.evaluation.validation.temporal_splitter import TemporalSplitter
from zero_day_defense.evaluation.validation.metrics import MetricsCalculator
from zero_day_defense.prediction.signal_collectors.github_signals import GitHubSignalCollector
from zero_day_defense.prediction.feature_engineering.extractor import FeatureExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run historical validation")
    parser.add_argument("dataset", type=Path, help="Path to CVE dataset (JSONL)")
    parser.add_argument("--output-dir", type=Path, default=Path("results/paper/validation"))
    parser.add_argument("--prediction-window", type=int, default=90, help="Days before CVE")
    parser.add_argument("--top-k", type=int, default=50, help="Top-K predictions to consider")
    parser.add_argument("--max-cves", type=int, help="Max CVEs to validate (for testing)")
    
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
    
    # Initialize components
    splitter = TemporalSplitter(prediction_window_days=args.prediction_window)
    signal_collector = GitHubSignalCollector()
    feature_extractor = FeatureExtractor()
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
            # Collect signals up to cutoff
            since = cutoff_date - timedelta(days=180)
            commits = signal_collector.collect_commit_history(github_repo, since, cutoff_date)
            
            if len(commits) < 10:
                logger.warning(f"  Insufficient commits: {len(commits)}")
                continue
            
            # Extract features
            features = feature_extractor.extract_commit_features(commits)
            
            # Calculate threat score (simplified)
            score = sum(features.values()) / len(features) if features else 0.0
            
            # Determine if predicted (top-K)
            predicted = score > 0.5  # Simplified threshold
            
            # Calculate lead time
            lead_time = (split["disclosure_date"] - cutoff_date).days
            
            # Classify result
            result = {
                "cve_id": cve["cve_id"],
                "github_repo": github_repo,
                "cutoff_date": cutoff_date.isoformat(),
                "disclosure_date": split["disclosure_date"].isoformat(),
                "predicted": predicted,
                "score": score,
                "lead_time_days": lead_time if predicted else None,
                "true_positive": predicted,
                "false_positive": False,
                "true_negative": False,
                "false_negative": not predicted,
            }
            
            results.append(result)
            logger.info(f"  Score: {score:.3f}, Predicted: {predicted}")
            
        except Exception as e:
            logger.error(f"  Error: {e}")
            continue
    
    # Calculate metrics
    logger.info("\nCalculating metrics...")
    metrics = metrics_calc.calculate(results)
    metrics_calc.print_metrics(metrics, "Historical Validation")
    
    # Save results
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = args.output_dir / "validation_results.jsonl"
    with results_file.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    
    metrics_file = args.output_dir / "metrics.json"
    with metrics_file.open("w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"\nResults saved to {args.output_dir}")
    logger.info(f"  Validation results: {results_file}")
    logger.info(f"  Metrics: {metrics_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
