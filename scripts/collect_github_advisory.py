"""Collect GitHub Security Advisory data."""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import yaml
from tqdm import tqdm

from zero_day_defense.data_sources.github_advisory import GitHubAdvisoryDataSource


logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Collect GitHub Security Advisories")
    parser.add_argument(
        "config",
        type=Path,
        help="Path to configuration YAML file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Override output file path",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load configuration
    with args.config.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    cutoff_date = datetime.fromisoformat(config["cutoff_date"])
    output_dir = Path(config.get("output_dir", "data/raw"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get GitHub token
    github_token = config.get("github_token") or os.getenv("GITHUB_TOKEN")
    if github_token:
        logger.info("Using GitHub token (higher rate limits)")
    else:
        logger.warning("No GitHub token provided - using public rate limits")

    # Initialize data source
    advisory_source = GitHubAdvisoryDataSource(
        timeout=config.get("request_timeout", 15),
        rate_limit_sleep=config.get("rate_limit_sleep", 1.0),
        github_token=github_token,
    )

    # Determine output file
    output_file = args.output or (output_dir / "github_advisory.jsonl")
    logger.info(f"Output will be written to: {output_file}")

    # Collect advisory data
    targets = config.get("advisory_targets", [])
    logger.info(f"Collecting {len(targets)} advisory targets with cutoff {cutoff_date.isoformat()}")

    collected_count = 0
    error_count = 0

    with output_file.open("w", encoding="utf-8") as f:
        for target in tqdm(targets, desc="Collecting Advisories"):
            target_id = target.get("id")
            description = target.get("description", "")

            try:
                logger.info(f"Collecting: {target_id} - {description}")
                result = advisory_source.collect(target_id, cutoff=cutoff_date)

                # Write result as JSONL
                record = {
                    "source": result.source,
                    "package": result.package,
                    "collected_at": result.collected_at.isoformat(),
                    "payload": result.payload,
                    "metadata": {
                        "description": description,
                        "target_id": target_id,
                    },
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()

                advisory_count = result.payload.get("total_results", 0)
                logger.info(f"  → Collected {advisory_count} advisories")
                collected_count += 1

            except Exception as e:
                logger.error(f"Error collecting {target_id}: {e}")
                error_count += 1
                continue

    logger.info(f"\n{'='*60}")
    logger.info(f"Collection complete!")
    logger.info(f"  Successfully collected: {collected_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"  Output file: {output_file}")


if __name__ == "__main__":
    main()
