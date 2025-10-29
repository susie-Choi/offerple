"""Collect CISA KEV (Known Exploited Vulnerabilities) catalog."""
import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def main():
    parser = argparse.ArgumentParser(
        description="Collect CISA KEV catalog"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/kev_catalog.jsonl"),
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
    
    logger.info("Downloading CISA KEV catalog...")
    
    try:
        response = requests.get(KEV_URL, timeout=30, verify=False)
        response.raise_for_status()
        
        kev_data = response.json()
        vulnerabilities = kev_data.get("vulnerabilities", [])
        
        logger.info(f"Downloaded {len(vulnerabilities)} KEV entries")
        
        # Save to JSONL
        args.output.parent.mkdir(parents=True, exist_ok=True)
        
        with args.output.open("w", encoding="utf-8") as f:
            record = {
                "source": "cisa_kev",
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "payload": kev_data,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"KEV Collection Complete")
        logger.info(f"  Total KEV entries: {len(vulnerabilities)}")
        logger.info(f"  Output: {args.output}")
        logger.info(f"  Catalog version: {kev_data.get('catalogVersion')}")
        logger.info(f"  Date released: {kev_data.get('dateReleased')}")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error collecting KEV: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
