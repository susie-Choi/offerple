"""Load EPSS scores into existing CVE nodes in Neo4j."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

try:
    from neo4j import GraphDatabase
except ImportError:
    print("neo4j driver not installed. Run: pip install neo4j")
    exit(1)

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EPSSLoader:
    """Load EPSS scores into CVE nodes."""

    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def load_epss_score(self, cve_id: str, epss: float, percentile: float, date: str) -> None:
        """Add EPSS score to a CVE node."""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (c:CVE {id: $cve_id})
                SET c.epss_score = $epss,
                    c.epss_percentile = $percentile,
                    c.epss_date = date($date)
                """,
                cve_id=cve_id,
                epss=epss,
                percentile=percentile,
                date=date,
            )

    def load_from_jsonl(self, jsonl_path: Path) -> None:
        """Load EPSS scores from a JSONL file."""
        logger.info(f"Loading EPSS scores from {jsonl_path}")
        count = 0

        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                payload = record.get("payload", {})
                epss_data = payload.get("epss_data", [])

                for entry in epss_data:
                    cve_id = entry.get("cve")
                    epss = float(entry.get("epss", 0))
                    percentile = float(entry.get("percentile", 0))
                    date = entry.get("date", "")

                    if cve_id:
                        try:
                            self.load_epss_score(cve_id, epss, percentile, date)
                            count += 1
                            if count % 10 == 0:
                                logger.info(f"Loaded {count} EPSS scores...")
                        except Exception as e:
                            logger.error(f"Error loading EPSS for {cve_id}: {e}")

        logger.info(f"Finished loading {count} EPSS scores")


def main():
    parser = argparse.ArgumentParser(description="Load EPSS scores into Neo4j")
    parser.add_argument("jsonl_file", type=Path, help="Path to EPSS JSONL file")
    parser.add_argument("--uri", help="Neo4j URI")
    parser.add_argument("--username", help="Neo4j username")
    parser.add_argument("--password", help="Neo4j password")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    # Get Neo4j credentials
    neo4j_uri = args.uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_username = args.username or os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = args.password or os.getenv("NEO4J_PASSWORD")
    
    if not neo4j_password:
        logger.error("Neo4j password required")
        return

    loader = EPSSLoader(neo4j_uri, neo4j_username, neo4j_password)
    try:
        loader.load_from_jsonl(args.jsonl_file)
    finally:
        loader.close()


if __name__ == "__main__":
    main()
