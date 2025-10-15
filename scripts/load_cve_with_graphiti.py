"""Load CVE data into Neo4j using Graphiti for automatic entity/relationship extraction."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
except ImportError:
    print("graphiti-core not installed. Run: pip install graphiti-core")
    exit(1)

from neo4j import GraphDatabase


logger = logging.getLogger(__name__)


def extract_cve_text(cve_data: Dict[str, Any]) -> str:
    """Extract meaningful text from CVE data for Graphiti processing."""
    cve_id = cve_data.get("id", "Unknown")
    
    # Get English description
    descriptions = cve_data.get("descriptions", [])
    description = ""
    for desc in descriptions:
        if desc.get("lang") == "en":
            description = desc.get("value", "")
            break
    
    # Get CVSS info
    metrics = cve_data.get("metrics", {})
    cvss_info = ""
    for metric_type in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
        metric_list = metrics.get(metric_type, [])
        if metric_list:
            cvss_data = metric_list[0].get("cvssData", {})
            score = cvss_data.get("baseScore", "N/A")
            severity = cvss_data.get("baseSeverity", "N/A")
            cvss_info = f"CVSS Score: {score}, Severity: {severity}"
            break
    
    # Get CWE info
    weaknesses = cve_data.get("weaknesses", [])
    cwe_list = []
    for weakness in weaknesses:
        for desc in weakness.get("description", []):
            cwe_id = desc.get("value")
            if cwe_id and cwe_id.startswith("CWE-"):
                cwe_list.append(cwe_id)
    cwe_info = f"Weaknesses: {', '.join(cwe_list)}" if cwe_list else ""
    
    # Get affected products
    configurations = cve_data.get("configurations", [])
    products = set()
    for config in configurations:
        for node in config.get("nodes", []):
            for cpe_match in node.get("cpeMatch", []):
                if cpe_match.get("vulnerable"):
                    cpe_uri = cpe_match.get("criteria", "")
                    if cpe_uri:
                        parts = cpe_uri.split(":")
                        if len(parts) >= 5:
                            vendor = parts[3]
                            product = parts[4]
                            products.add(f"{vendor}/{product}")
    
    products_info = f"Affected products: {', '.join(list(products)[:10])}" if products else ""
    
    # Combine all information
    text = f"""
CVE ID: {cve_id}

Description:
{description}

{cvss_info}

{cwe_info}

{products_info}

Published: {cve_data.get('published', 'N/A')}
Last Modified: {cve_data.get('lastModified', 'N/A')}
Status: {cve_data.get('vulnStatus', 'N/A')}
"""
    
    return text.strip()


async def load_cve_with_graphiti(
    jsonl_path: Path,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    openai_api_key: str,
):
    """Load CVE data using Graphiti for automatic graph construction."""
    
    logger.info(f"Initializing Graphiti with Neo4j at {neo4j_uri}")
    
    # Initialize Graphiti
    graphiti = Graphiti(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        openai_api_key=openai_api_key,
    )
    
    logger.info(f"Loading CVE data from {jsonl_path}")
    
    count = 0
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            payload = record.get("payload", {})
            vulnerabilities = payload.get("vulnerabilities", [])
            
            for vuln in vulnerabilities:
                cve_data = vuln.get("cve", {})
                cve_id = cve_data.get("id")
                
                if not cve_id:
                    continue
                
                try:
                    # Extract text representation of CVE
                    cve_text = extract_cve_text(cve_data)
                    
                    logger.info(f"Processing {cve_id}...")
                    
                    # Add episode to Graphiti (it will extract entities and relationships)
                    await graphiti.add_episode(
                        name=cve_id,
                        episode_body=cve_text,
                        source_description=f"CVE vulnerability data from NVD",
                        episode_type=EpisodeType.text,
                    )
                    
                    count += 1
                    logger.info(f"  ✓ Added {cve_id} to graph")
                    
                except Exception as e:
                    logger.error(f"Error processing {cve_id}: {e}")
                    continue
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Graphiti processing complete!")
    logger.info(f"  Total CVEs processed: {count}")
    logger.info(f"\nGraphiti has automatically extracted entities and relationships.")
    logger.info(f"You can now query the graph using Neo4j Browser or Cypher queries.")
    
    await graphiti.close()


def main():
    parser = argparse.ArgumentParser(
        description="Load CVE data into Neo4j using Graphiti"
    )
    parser.add_argument("jsonl_file", type=Path, help="Path to CVE JSONL file")
    parser.add_argument("--uri", default="neo4j+s://26e236b3.databases.neo4j.io", help="Neo4j URI")
    parser.add_argument("--username", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", required=True, help="Neo4j password")
    parser.add_argument("--openai-api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Get OpenAI API key
    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OpenAI API key required. Set --openai-api-key or OPENAI_API_KEY env var")
        return
    
    # Run async function
    import asyncio
    asyncio.run(
        load_cve_with_graphiti(
            args.jsonl_file,
            args.uri,
            args.username,
            args.password,
            openai_api_key,
        )
    )


if __name__ == "__main__":
    main()
