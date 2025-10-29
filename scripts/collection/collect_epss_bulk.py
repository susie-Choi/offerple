"""Collect EPSS scores for a list of CVE IDs."""
import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm

from rota.spokes.epss import EPSSCollector as EPSSDataSource

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Collect EPSS scores for CVE IDs"
    )
    parser.add_argument(
        "cve_list",
        type=Path,
        help="Path to file containing CVE IDs (one per line)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/bulk_epss_data.jsonl"),
        help="Output JSONL file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    
    # Read CVE IDs
    with args.cve_list.open("r") as f:
        cve_ids = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Loaded {len(cve_ids)} CVE IDs")
    
    # Initialize EPSS data source
    epss_source = EPSSDataSource(timeout=30.0)
    
    # Collect EPSS scores in batches of 100
    args.output.parent.mkdir(parents=True, exist_ok=True)
    collected = 0
    errors = 0
    batch_size = 100
    
    with args.output.open("w", encoding="utf-8") as f:
        for i in tqdm(range(0, len(cve_ids), batch_size), desc="Collecting EPSS batches"):
            batch = cve_ids[i:i+batch_size]
            
            try:
                result = epss_source.collect_multiple_cves(
                    batch, 
                    cutoff=datetime.now(timezone.utc)
                )
                
                record = {
                    "source": result.source,
                    "package": result.package,
                    "collected_at": result.collected_at.isoformat(),
                    "payload": result.payload,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                collected += len(batch)
                
            except Exception as e:
                logger.error(f"Error collecting batch {i//batch_size}: {e}")
                errors += len(batch)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"EPSS Collection Complete")
    logger.info(f"  Collected: {collected}")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Output: {args.output}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
