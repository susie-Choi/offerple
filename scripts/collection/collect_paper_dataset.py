"""Collect CVE dataset for paper experiments.

This script collects a large-scale dataset of CVEs from open-source projects
with GitHub repositories for use in paper experiments.

Usage:
    python scripts/collect_paper_dataset.py --min-cves 100 --min-cvss 7.0
"""
import argparse
import json
import logging
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zero_day_defense.evaluation.dataset.collector import PaperDatasetCollector
from zero_day_defense.evaluation.dataset.validator import DatasetValidator
from zero_day_defense.evaluation.dataset.statistics import DatasetStatistics


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Collect CVE dataset for paper experiments"
    )
    parser.add_argument(
        "--min-cves",
        type=int,
        default=100,
        help="Minimum number of CVEs to collect (default: 100)",
    )
    parser.add_argument(
        "--min-cvss",
        type=float,
        default=7.0,
        help="Minimum CVSS score (default: 7.0)",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Years of history to collect (default: 5)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/paper/dataset"),
        help="Output directory (default: results/paper/dataset)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate collected dataset",
    )
    parser.add_argument(
        "--skip-collection",
        action="store_true",
        help="Skip collection, only validate/analyze existing dataset",
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_file = args.output_dir / "cves.jsonl"
    stats_file = args.output_dir / "statistics.json"
    validation_file = args.output_dir / "validation.json"
    
    # Step 1: Collect dataset
    if not args.skip_collection:
        logger.info("=" * 80)
        logger.info("Step 1: Collecting CVE Dataset")
        logger.info("=" * 80)
        
        collector = PaperDatasetCollector(
            min_cvss=args.min_cvss,
            min_cves=args.min_cves,
            years=args.years,
        )
        
        cve_records = collector.collect(output_file=dataset_file)
        
        logger.info(f"\nCollected {len(cve_records)} CVEs")
    else:
        logger.info("Skipping collection, loading existing dataset...")
        
        if not dataset_file.exists():
            logger.error(f"Dataset file not found: {dataset_file}")
            return 1
        
        cve_records = []
        with dataset_file.open("r", encoding="utf-8") as f:
            for line in f:
                cve_records.append(json.loads(line))
        
        logger.info(f"Loaded {len(cve_records)} CVEs from {dataset_file}")
    
    # Step 2: Validate dataset
    if args.validate:
        logger.info("\n" + "=" * 80)
        logger.info("Step 2: Validating Dataset")
        logger.info("=" * 80)
        
        validator = DatasetValidator(
            min_commits=50,
            min_days=180,
            max_days_since_activity=365,
        )
        
        validation_result = validator.validate_dataset(cve_records)
        
        # Save validation results
        with validation_file.open("w", encoding="utf-8") as f:
            json.dump(validation_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nValidation results saved to: {validation_file}")
        
        # Filter to valid CVEs only
        valid_cves = [
            cve_records[i]
            for i, result in enumerate(validation_result["results"])
            if result["valid"]
        ]
        
        logger.info(f"\nValid CVEs: {len(valid_cves)}/{len(cve_records)}")
        
        # Save valid CVEs
        valid_dataset_file = args.output_dir / "cves_valid.jsonl"
        with valid_dataset_file.open("w", encoding="utf-8") as f:
            for cve in valid_cves:
                f.write(json.dumps(cve) + "\n")
        
        logger.info(f"Valid CVEs saved to: {valid_dataset_file}")
        
        # Use valid CVEs for statistics
        cve_records = valid_cves
    
    # Step 3: Calculate statistics
    logger.info("\n" + "=" * 80)
    logger.info("Step 3: Calculating Statistics")
    logger.info("=" * 80)
    
    stats_calculator = DatasetStatistics()
    stats = stats_calculator.calculate(cve_records)
    
    # Save statistics
    stats_calculator.save(stats, stats_file)
    
    # Print summary
    stats_calculator.print_summary(stats)
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("Dataset Collection Complete!")
    logger.info("=" * 80)
    logger.info(f"\nOutput Directory: {args.output_dir}")
    logger.info(f"  Dataset: {dataset_file}")
    if args.validate:
        logger.info(f"  Valid Dataset: {valid_dataset_file}")
        logger.info(f"  Validation: {validation_file}")
    logger.info(f"  Statistics: {stats_file}")
    logger.info("")
    logger.info("Next Steps:")
    logger.info("  1. Review statistics and validation results")
    logger.info("  2. Run historical validation:")
    logger.info(f"     python scripts/run_historical_validation.py {dataset_file}")
    logger.info("  3. Run baseline comparison:")
    logger.info(f"     python scripts/run_baseline_comparison.py {dataset_file}")
    logger.info("")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
