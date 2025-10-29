"""Bulk collect GitHub Security Advisory data using the bulk method."""
import argparse
import json
import logging
import os
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from rota.spokes.github_advisory import GitHubAdvisoryCollector as GitHubAdvisoryDataSource

# Load environment variables
load_dotenv()


logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Bulk collect GitHub Security Advisories"
    )
    parser.add_argument(
        "--ecosystem",
        choices=["npm", "pip", "maven", "nuget", "rubygems", "go", "rust", "composer"],
        help="Filter by ecosystem",
    )
    parser.add_argument(
        "--severity",
        choices=["low", "medium", "high", "critical"],
        help="Filter by severity",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Maximum number of pages to collect",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/advisory/github_advisory_bulk.jsonl"),
        help="Output file path",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    
    # Create output directory
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize data source
    advisory_source = GitHubAdvisoryDataSource(
        timeout=15.0,
        rate_limit_sleep=1.0,
        github_token=github_token,
    )
    
    logger.info(f"Starting bulk collection...")
    logger.info(f"  Ecosystem: {args.ecosystem or 'all'}")
    logger.info(f"  Severity: {args.severity or 'all'}")
    logger.info(f"  Max pages: {args.max_pages or 'unlimited'}")
    
    start_time = time.time()
    
    # Open file for streaming write
    logger.info(f"Streaming data to {args.output}")
    collected_count = 0
    
    with args.output.open("w", encoding="utf-8") as f:
        # Collect with streaming callback
        for advisory in advisory_source.collect_bulk_streaming(
            ecosystem=args.ecosystem,
            severity=args.severity,
            max_pages=args.max_pages
        ):
            record = {
                "source": "github_advisory",
                "ghsa_id": advisory["ghsa_id"],
                "collected_at": datetime.now().isoformat(),
                "payload": advisory,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()  # Ensure data is written immediately
            collected_count += 1
    
    elapsed = time.time() - start_time
    advisories = []  # For stats calculation below
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Collection complete!")
    logger.info(f"  Total advisories: {collected_count:,}")
    logger.info(f"  Time elapsed: {elapsed:.1f}s")
    logger.info(f"  Output file: {args.output}")
    logger.info(f"  File size: {args.output.stat().st_size / 1024 / 1024:.2f} MB")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
