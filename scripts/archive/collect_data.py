"""Command line entry point for running the data collection pipeline."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from zero_day_defense.config import load_config
from zero_day_defense.pipeline import create_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Zero-Day Defense data collection")
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the YAML configuration file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    config = load_config(args.config)
    pipeline = create_pipeline(config)
    logging.info(
        "Starting data collection for %d packages with cutoff %s",
        len(config.packages),
        config.cutoff_date.isoformat(),
    )
    pipeline.run()
    logging.info("Data collection finished; outputs stored in %s", config.output_dir)


if __name__ == "__main__":
    main()
