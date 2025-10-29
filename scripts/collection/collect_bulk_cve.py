"""Collect CVEs in bulk from NVD by CVSS severity."""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm

from rota.spokes.cve import CVECollector as CVEDataSource

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Collect CVEs in bulk from NVD by CVSS severity"
    )
    parser.add_argument(
        "--severity",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        help="Filter by CVSS v3 severity level",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        help="Minimum CVSS v3 score (0.0-10.0)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="Maximum number of CVEs to collect (default: all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/bulk_cve_data.jsonl"),
        help="Output JSONL file path",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Get API key from environment
    api_key = os.getenv("NVD_API_KEY")
    if api_key:
        logger.info("✓ Using NVD API key (50 requests per 30 seconds)")
    else:
        logger.warning("⚠ No NVD API key - using slower public rate limits (5 requests per 30 seconds)")
        logger.warning("  Set NVD_API_KEY environment variable for 10x faster collection")

    # Initialize CVE data source
    cve_source = CVEDataSource(
        timeout=30.0,
        api_key=api_key,
        verify_ssl=False,
    )

    # Build filter description
    filter_desc = []
    if args.severity:
        filter_desc.append(f"severity={args.severity}")
    if args.min_score:
        filter_desc.append(f"min_score={args.min_score}")
    if args.max_results:
        filter_desc.append(f"max={args.max_results}")
    
    filter_str = ", ".join(filter_desc) if filter_desc else "all CVEs"
    logger.info(f"Collecting CVEs with filters: {filter_str}")

    # Collect CVEs
    try:
        logger.info("Starting bulk collection...")
        vulnerabilities = cve_source.collect_bulk(
            cvss_v3_severity=args.severity,
            cvss_v3_score_min=args.min_score,
            max_results=args.max_results,
        )
        
        logger.info(f"✓ Collected {len(vulnerabilities)} CVEs")
        
        # Save to JSONL
        args.output.parent.mkdir(parents=True, exist_ok=True)
        
        with args.output.open("w", encoding="utf-8") as f:
            for vuln in tqdm(vulnerabilities, desc="Writing to file"):
                record = {
                    "source": "nvd_cve",
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "vulnerabilities": [vuln],
                        "total_results": 1,
                    },
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        logger.info(f"✓ Saved to: {args.output}")
        
        # Print statistics
        logger.info("\n" + "=" * 60)
        logger.info("Collection Summary:")
        logger.info(f"  Total CVEs collected: {len(vulnerabilities)}")
        logger.info(f"  Output file: {args.output}")
        logger.info(f"  File size: {args.output.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Analyze severity distribution
        severity_counts = {}
        for vuln in vulnerabilities:
            cve_data = vuln.get("cve", {})
            metrics = cve_data.get("metrics", {})
            
            # Try CVSS v3.1 first, then v3.0
            for metric_type in ["cvssMetricV31", "cvssMetricV30"]:
                metric_list = metrics.get(metric_type, [])
                if metric_list:
                    severity = metric_list[0].get("cvssData", {}).get("baseSeverity", "UNKNOWN")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    break
        
        if severity_counts:
            logger.info("\n  Severity Distribution:")
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    logger.info(f"    {severity}: {count}")
        
        logger.info("\nNext steps:")
        logger.info(f"  Load into Neo4j:")
        logger.info(f"    python scripts/loading/load_cve_to_neo4j.py {args.output}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during collection: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
