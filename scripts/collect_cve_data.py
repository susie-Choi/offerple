"""Collect CVE data from NVD for Neo4j graph analysis."""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import yaml
from tqdm import tqdm

from zero_day_defense.data_sources.cve import CVEDataSource


logger = logging.getLogger(__name__)


def load_cve_config(config_path: Path) -> dict:
    """Load CVE collection configuration."""
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Collect CVE data from NVD")
    parser.add_argument(
        "config",
        type=Path,
        help="Path to CVE configuration YAML file",
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
        help="Override output file path (default: data/raw/cve_data.jsonl)",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load configuration
    config = load_cve_config(args.config)
    cutoff_date = datetime.fromisoformat(config["cutoff_date"])
    output_dir = Path(config.get("output_dir", "data/raw"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get API key from config or environment
    api_key = config.get("nvd_api_key") or os.getenv("NVD_API_KEY")
    if api_key:
        logger.info("Using NVD API key (faster rate limits)")
    else:
        logger.warning("No NVD API key provided - using slower public rate limits")
        logger.warning("Set NVD_API_KEY environment variable or add to config for faster collection")

    # Initialize CVE data source
    cve_source = CVEDataSource(
        timeout=config.get("request_timeout", 30),
        rate_limit_sleep=config.get("rate_limit_sleep", 6.0),
        api_key=api_key,
        verify_ssl=False,  # Disable SSL verification for corporate proxies
    )

    # Determine output file
    output_file = args.output or (output_dir / "cve_data.jsonl")
    logger.info(f"Output will be written to: {output_file}")

    # Collect CVE data
    cve_targets = config.get("cve_targets", [])
    logger.info(f"Collecting {len(cve_targets)} CVE targets with cutoff {cutoff_date.isoformat()}")

    collected_count = 0
    error_count = 0

    with output_file.open("w", encoding="utf-8") as f:
        for target in tqdm(cve_targets, desc="Collecting CVEs"):
            cve_id = target.get("id")
            description = target.get("description", "")

            try:
                logger.info(f"Collecting: {cve_id} - {description}")
                result = cve_source.collect(cve_id, cutoff=cutoff_date)

                # Write result as JSONL
                record = {
                    "source": result.source,
                    "package": result.package,
                    "collected_at": result.collected_at.isoformat(),
                    "payload": result.payload,
                    "metadata": {
                        "description": description,
                        "target_id": cve_id,
                    },
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()

                vuln_count = result.payload.get("total_results", 0)
                logger.info(f"  → Collected {vuln_count} vulnerabilities")
                collected_count += 1

            except Exception as e:
                logger.error(f"Error collecting {cve_id}: {e}")
                error_count += 1
                continue

    logger.info(f"\n{'='*60}")
    logger.info(f"Collection complete!")
    logger.info(f"  Successfully collected: {collected_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"  Output file: {output_file}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Install Neo4j: https://neo4j.com/download/")
    logger.info(f"  2. Install neo4j driver: pip install neo4j")
    logger.info(f"  3. Load data: python scripts/load_cve_to_neo4j.py {output_file} --password <neo4j-password>")


if __name__ == "__main__":
    main()
