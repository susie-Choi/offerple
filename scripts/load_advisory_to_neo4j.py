"""Load GitHub Advisory data into Neo4j graph database."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

try:
    from neo4j import GraphDatabase
except ImportError:
    print("neo4j driver not installed. Run: pip install neo4j")
    exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AdvisoryGraphLoader:
    """Load GitHub Advisory data into Neo4j with relationships."""

    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        """Create uniqueness constraints."""
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT advisory_id IF NOT EXISTS FOR (a:Advisory) REQUIRE a.ghsa_id IS UNIQUE",
                "CREATE CONSTRAINT package_name IF NOT EXISTS FOR (p:Package) REQUIRE (p.ecosystem, p.name) IS UNIQUE",
            ]
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")

    def load_advisory(self, advisory_data: Dict[str, Any]) -> None:
        """Load a single advisory and its relationships into Neo4j."""
        ghsa_id = advisory_data.get("ghsa_id")
        if not ghsa_id:
            logger.warning("Advisory without GHSA ID, skipping")
            return

        with self.driver.session() as session:
            # Create Advisory node
            session.run(
                """
                MERGE (a:Advisory {ghsa_id: $ghsa_id})
                SET a.summary = $summary,
                    a.description = $description,
                    a.severity = $severity,
                    a.published = datetime($published),
                    a.updated = datetime($updated),
                    a.withdrawn = datetime($withdrawn),
                    a.url = $url
                """,
                ghsa_id=ghsa_id,
                summary=advisory_data.get("summary"),
                description=advisory_data.get("description"),
                severity=advisory_data.get("severity"),
                published=advisory_data.get("published_at"),
                updated=advisory_data.get("updated_at"),
                withdrawn=advisory_data.get("withdrawn_at"),
                url=advisory_data.get("html_url"),
            )

            # Link to CVEs
            cves = advisory_data.get("cve_id")
            if cves:
                # cve_id can be a single string or null
                if isinstance(cves, str):
                    session.run(
                        """
                        MATCH (a:Advisory {ghsa_id: $ghsa_id})
                        MERGE (c:CVE {id: $cve_id})
                        MERGE (a)-[:REFERENCES]->(c)
                        """,
                        ghsa_id=ghsa_id,
                        cve_id=cves,
                    )

            # Link to affected packages
            vulnerabilities = advisory_data.get("vulnerabilities", [])
            for vuln in vulnerabilities:
                package_info = vuln.get("package", {})
                ecosystem = package_info.get("ecosystem")
                package_name = package_info.get("name")
                
                if ecosystem and package_name:
                    # Get affected versions
                    vulnerable_version_range = vuln.get("vulnerable_version_range")
                    patched_versions = vuln.get("patched_versions")
                    
                    session.run(
                        """
                        MERGE (p:Package {ecosystem: $ecosystem, name: $package_name})
                        WITH p
                        MATCH (a:Advisory {ghsa_id: $ghsa_id})
                        MERGE (p)-[r:HAS_ADVISORY]->(a)
                        SET r.vulnerable_version_range = $vulnerable_version_range,
                            r.patched_versions = $patched_versions
                        """,
                        ghsa_id=ghsa_id,
                        ecosystem=ecosystem,
                        package_name=package_name,
                        vulnerable_version_range=vulnerable_version_range,
                        patched_versions=patched_versions,
                    )

            # Add CWEs
            cwes = advisory_data.get("cwes", [])
            for cwe in cwes:
                cwe_id = cwe.get("cwe_id")
                if cwe_id:
                    session.run(
                        """
                        MERGE (w:CWE {id: $cwe_id})
                        SET w.name = $cwe_name
                        WITH w
                        MATCH (a:Advisory {ghsa_id: $ghsa_id})
                        MERGE (a)-[:HAS_WEAKNESS]->(w)
                        """,
                        ghsa_id=ghsa_id,
                        cwe_id=cwe_id,
                        cwe_name=cwe.get("name"),
                    )

    def load_from_jsonl(self, jsonl_path: Path) -> None:
        """Load advisory data from a JSONL file."""
        logger.info(f"Loading advisory data from {jsonl_path}")
        count = 0

        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                payload = record.get("payload", {})
                advisories = payload.get("advisories", [])

                for advisory in advisories:
                    try:
                        self.load_advisory(advisory)
                        count += 1
                        if count % 10 == 0:
                            logger.info(f"Loaded {count} advisories...")
                    except Exception as e:
                        logger.error(f"Error loading advisory: {e}")

        logger.info(f"Finished loading {count} advisories")


def main():
    parser = argparse.ArgumentParser(description="Load GitHub Advisory data into Neo4j")
    parser.add_argument("jsonl_file", type=Path, help="Path to advisory JSONL file")
    parser.add_argument("--uri", help="Neo4j URI (default: from NEO4J_URI env var)")
    parser.add_argument("--username", help="Neo4j username (default: from NEO4J_USERNAME env var)")
    parser.add_argument("--password", help="Neo4j password (default: from NEO4J_PASSWORD env var)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    # Get Neo4j credentials
    neo4j_uri = args.uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_username = args.username or os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = args.password or os.getenv("NEO4J_PASSWORD")
    
    if not neo4j_password:
        logger.error("Neo4j password required. Set --password or NEO4J_PASSWORD env var")
        return

    loader = AdvisoryGraphLoader(neo4j_uri, neo4j_username, neo4j_password)
    try:
        logger.info("Creating constraints...")
        loader.create_constraints()
        loader.load_from_jsonl(args.jsonl_file)
    finally:
        loader.close()


if __name__ == "__main__":
    main()
