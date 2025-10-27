"""Collect EPSS scores for CVEs."""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import yaml
from tqdm import tqdm

from zero_day_defense.data_sources.epss import EPSSDataSource


logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Collect EPSS scores")
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

    # Initialize data source
    epss_source = EPSSDataSource(
        timeout=config.get("request_timeout", 15),
        rate_limit_sleep=config.get("rate_limit_sleep", 0.5),
    )

    # Determine output file
    output_file = args.output or (output_dir / "epss_scores.jsonl")
    logger.info(f"Output will be written to: {output_file}")

    # Collect EPSS data
    cve_list = config.get("cve_list", [])
    logger.info(f"Collecting EPSS scores for {len(cve_list)} CVEs")

    collected_count = 0
    error_count = 0

    with output_file.open("w", encoding="utf-8") as f:
        # Batch process CVEs (100 at a time)
        batch_size = 100
        for i in range(0, len(cve_list), batch_size):
            batch = cve_list[i:i+batch_size]
            
            try:
                logger.info(f"Collecting batch {i//batch_size + 1} ({len(batch)} CVEs)...")
                result = epss_source.collect_multiple_cves(batch, cutoff=cutoff_date)

                # Write result as JSONL
                record = {
                    "source": result.source,
                    "package": result.package,
                    "collected_at": result.collected_at.isoformat(),
                    "payload": result.payload,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()

                score_count = result.payload.get("total_results", 0)
                logger.info(f"  → Collected {score_count} EPSS scores")
                collected_count += score_count

            except Exception as e:
                logger.error(f"Error collecting batch: {e}")
                error_count += len(batch)
                continue

    logger.info(f"\n{'='*60}")
    logger.info(f"Collection complete!")
    logger.info(f"  Successfully collected: {collected_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"  Output file: {output_file}")


if __name__ == "__main__":
    main()
