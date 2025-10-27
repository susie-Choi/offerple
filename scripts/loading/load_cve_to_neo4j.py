"""Load CVE data into Neo4j graph database."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    from neo4j import GraphDatabase
except ImportError:
    print("neo4j driver not installed. Run: pip install neo4j")
    exit(1)

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


logger = logging.getLogger(__name__)


class CVEGraphLoader:
    """Load CVE data into Neo4j with relationships."""

    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        """Create uniqueness constraints for better performance."""
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT cve_id IF NOT EXISTS FOR (c:CVE) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT cpe_uri IF NOT EXISTS FOR (p:CPE) REQUIRE p.uri IS UNIQUE",
                "CREATE CONSTRAINT cwe_id IF NOT EXISTS FOR (w:CWE) REQUIRE w.id IS UNIQUE",
                "CREATE CONSTRAINT vendor_name IF NOT EXISTS FOR (v:Vendor) REQUIRE v.name IS UNIQUE",
                "CREATE CONSTRAINT product_name IF NOT EXISTS FOR (p:Product) REQUIRE (p.vendor, p.name) IS UNIQUE",
            ]
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")

    def load_cve(self, cve_data: Dict[str, Any]) -> None:
        """Load a single CVE and its relationships into Neo4j."""
        cve_id = cve_data.get("id")
        if not cve_id:
            logger.warning("CVE without ID, skipping")
            return

        with self.driver.session() as session:
            # Create CVE node
            session.run(
                """
                MERGE (c:CVE {id: $id})
                SET c.sourceIdentifier = $sourceIdentifier,
                    c.published = datetime($published),
                    c.lastModified = datetime($lastModified),
                    c.vulnStatus = $vulnStatus
                """,
                id=cve_id,
                sourceIdentifier=cve_data.get("sourceIdentifier"),
                published=cve_data.get("published"),
                lastModified=cve_data.get("lastModified"),
                vulnStatus=cve_data.get("vulnStatus"),
            )

            # Add descriptions
            descriptions = cve_data.get("descriptions", [])
            for desc in descriptions:
                if desc.get("lang") == "en":
                    session.run(
                        """
                        MATCH (c:CVE {id: $id})
                        SET c.description = $description
                        """,
                        id=cve_id,
                        description=desc.get("value", ""),
                    )
                    break

            # Add CVSS metrics
            metrics = cve_data.get("metrics", {})
            for metric_type in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                metric_list = metrics.get(metric_type, [])
                if metric_list:
                    metric = metric_list[0]
                    cvss_data = metric.get("cvssData", {})
                    session.run(
                        f"""
                        MATCH (c:CVE {{id: $id}})
                        SET c.cvssVersion = $version,
                            c.cvssScore = $score,
                            c.cvssSeverity = $severity,
                            c.cvssVector = $vector
                        """,
                        id=cve_id,
                        version=cvss_data.get("version"),
                        score=cvss_data.get("baseScore"),
                        severity=cvss_data.get("baseSeverity"),
                        vector=cvss_data.get("vectorString"),
                    )
                    break

            # Add CWE relationships
            weaknesses = cve_data.get("weaknesses", [])
            for weakness in weaknesses:
                for desc in weakness.get("description", []):
                    cwe_id = desc.get("value")
                    if cwe_id and cwe_id.startswith("CWE-"):
                        session.run(
                            """
                            MERGE (w:CWE {id: $cwe_id})
                            WITH w
                            MATCH (c:CVE {id: $cve_id})
                            MERGE (c)-[:HAS_WEAKNESS]->(w)
                            """,
                            cve_id=cve_id,
                            cwe_id=cwe_id,
                        )

            # Add CPE (affected products) relationships
            configurations = cve_data.get("configurations", [])
            for config in configurations:
                for node in config.get("nodes", []):
                    for cpe_match in node.get("cpeMatch", []):
                        if cpe_match.get("vulnerable"):
                            cpe_uri = cpe_match.get("criteria")
                            if cpe_uri:
                                # Parse CPE to extract vendor and product
                                parts = cpe_uri.split(":")
                                if len(parts) >= 5:
                                    vendor = parts[3]
                                    product = parts[4]
                                    version = parts[5] if len(parts) > 5 else "*"

                                    session.run(
                                        """
                                        MERGE (v:Vendor {name: $vendor})
                                        MERGE (p:Product {vendor: $vendor, name: $product})
                                        MERGE (v)-[:PRODUCES]->(p)
                                        MERGE (cpe:CPE {uri: $cpe_uri})
                                        SET cpe.version = $version,
                                            cpe.versionStartIncluding = $versionStartIncluding,
                                            cpe.versionEndExcluding = $versionEndExcluding
                                        MERGE (p)-[:HAS_VERSION]->(cpe)
                                        WITH cpe
                                        MATCH (c:CVE {id: $cve_id})
                                        MERGE (c)-[:AFFECTS]->(cpe)
                                        """,
                                        cve_id=cve_id,
                                        vendor=vendor,
                                        product=product,
                                        cpe_uri=cpe_uri,
                                        version=version,
                                        versionStartIncluding=cpe_match.get("versionStartIncluding"),
                                        versionEndExcluding=cpe_match.get("versionEndExcluding"),
                                    )

            # Add references
            references = cve_data.get("references", [])
            for ref in references:
                url = ref.get("url")
                if url:
                    session.run(
                        """
                        MERGE (r:Reference {url: $url})
                        SET r.source = $source
                        WITH r
                        MATCH (c:CVE {id: $cve_id})
                        MERGE (c)-[:HAS_REFERENCE]->(r)
                        """,
                        cve_id=cve_id,
                        url=url,
                        source=ref.get("source"),
                    )

    def load_from_jsonl(self, jsonl_path: Path) -> None:
        """Load CVE data from a JSONL file."""
        logger.info(f"Loading CVE data from {jsonl_path}")
        count = 0

        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                payload = record.get("payload", {})
                vulnerabilities = payload.get("vulnerabilities", [])

                for vuln in vulnerabilities:
                    cve_data = vuln.get("cve", {})
                    try:
                        self.load_cve(cve_data)
                        count += 1
                        if count % 10 == 0:
                            logger.info(f"Loaded {count} CVEs...")
                    except Exception as e:
                        logger.error(f"Error loading CVE: {e}")

        logger.info(f"Finished loading {count} CVEs")


def main():
    parser = argparse.ArgumentParser(description="Load CVE data into Neo4j")
    parser.add_argument("jsonl_file", type=Path, help="Path to CVE JSONL file")
    parser.add_argument(
        "--uri",
        help="Neo4j URI (default: from NEO4J_URI env var or bolt://localhost:7687)",
    )
    parser.add_argument(
        "--username",
        help="Neo4j username (default: from NEO4J_USERNAME env var or 'neo4j')",
    )
    parser.add_argument(
        "--password",
        help="Neo4j password (default: from NEO4J_PASSWORD env var)",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    # Get Neo4j credentials from args or env
    neo4j_uri = args.uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_username = args.username or os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = args.password or os.getenv("NEO4J_PASSWORD")
    
    if not neo4j_password:
        logger.error("Neo4j password required. Set --password or NEO4J_PASSWORD env var")
        return

    loader = CVEGraphLoader(neo4j_uri, neo4j_username, neo4j_password)
    try:
        logger.info("Creating constraints...")
        loader.create_constraints()
        loader.load_from_jsonl(args.jsonl_file)
    finally:
        loader.close()


if __name__ == "__main__":
    main()
