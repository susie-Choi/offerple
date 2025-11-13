"""
Load selected CVEs into Neo4j based on criteria.

This script loads only important CVEs to stay within Neo4j free tier limits (200K nodes).

Selection criteria:
- KEV (Known Exploited Vulnerabilities)
- High EPSS score (top 10%)
- Recent (2020-2024)
- High severity (CRITICAL/HIGH)
- Specific CWE types (for research)

Usage:
    python scripts/loading/load_selected_cves.py --all
    python scripts/loading/load_selected_cves.py --kev-only
    python scripts/loading/load_selected_cves.py --recent-years 5
"""
import os
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class SelectiveCVELoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.kev_ids = self.load_kev_ids()
        self.epss_data = self.load_epss_data()
    
    def close(self):
        self.driver.close()
    
    def load_kev_ids(self):
        """Load KEV CVE IDs."""
        kev_file = Path("data/raw/kev_catalog.jsonl")
        if not kev_file.exists():
            return set()
        
        kev_ids = set()
        with open(kev_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                vulns = data.get('payload', {}).get('vulnerabilities', [])
                for vuln in vulns:
                    cve_id = vuln.get('cveID')
                    if cve_id:
                        kev_ids.add(cve_id)
        
        logger.info(f"Loaded {len(kev_ids)} KEV CVE IDs")
        return kev_ids
    
    def load_epss_data(self):
        """Load EPSS scores."""
        epss_file = Path("data/raw/bulk_epss_data.jsonl")
        if not epss_file.exists():
            return {}
        
        epss_dict = {}
        with open(epss_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                epss_list = data.get('payload', {}).get('epss_data', [])
                for item in epss_list:
                    cve_id = item.get('cve')
                    epss = item.get('epss')
                    if cve_id and epss:
                        epss_dict[cve_id] = float(epss)
        
        logger.info(f"Loaded EPSS scores for {len(epss_dict)} CVEs")
        return epss_dict
    
    def should_include(self, cve_data, criteria):
        """Determine if CVE should be included based on criteria."""
        cve_id = cve_data.get('id')
        
        # Always include KEV
        if cve_id in self.kev_ids:
            return True, "KEV"
        
        # Check EPSS
        if criteria.get('epss_threshold'):
            epss = self.epss_data.get(cve_id, 0)
            if epss >= criteria['epss_threshold']:
                return True, f"EPSS={epss:.4f}"
        
        # Check year
        if criteria.get('min_year'):
            try:
                published = cve_data.get('published', '')
                year = datetime.fromisoformat(published.replace('Z', '+00:00')).year
                if year >= criteria['min_year']:
                    # Also check severity for recent CVEs
                    if criteria.get('severity_filter'):
                        metrics = cve_data.get('metrics', {})
                        cvss_v31 = metrics.get('cvssMetricV31', [{}])[0]
                        severity = cvss_v31.get('cvssData', {}).get('baseSeverity', '')
                        if severity in criteria['severity_filter']:
                            return True, f"Recent+{severity}"
                    else:
                        return True, f"Year={year}"
            except:
                pass
        
        # Check CWE types
        if criteria.get('cwe_filter'):
            weaknesses = cve_data.get('weaknesses', [])
            for weakness in weaknesses:
                for desc in weakness.get('description', []):
                    cwe_id = desc.get('value', '')
                    if cwe_id in criteria['cwe_filter']:
                        return True, f"CWE={cwe_id}"
        
        return False, None
    
    def load_cve(self, cve_data):
        """Load a single CVE into Neo4j (same as before)."""
        cve_id = cve_data.get('id')
        if not cve_id:
            return
        
        with self.driver.session() as session:
            # Create CVE node
            session.run("""
                MERGE (c:CVE {id: $id})
                SET c.sourceIdentifier = $sourceIdentifier,
                    c.published = datetime($published),
                    c.lastModified = datetime($lastModified),
                    c.vulnStatus = $vulnStatus
            """,
                id=cve_id,
                sourceIdentifier=cve_data.get('sourceIdentifier'),
                published=cve_data.get('published'),
                lastModified=cve_data.get('lastModified'),
                vulnStatus=cve_data.get('vulnStatus')
            )
            
            # Add description
            descriptions = cve_data.get('descriptions', [])
            for desc in descriptions:
                if desc.get('lang') == 'en':
                    session.run("""
                        MATCH (c:CVE {id: $id})
                        SET c.description = $description
                    """, id=cve_id, description=desc.get('value', ''))
                    break
            
            # Add CVSS
            metrics = cve_data.get('metrics', {})
            for metric_type in ['cvssMetricV31', 'cvssMetricV30', 'cvssMetricV2']:
                metric_list = metrics.get(metric_type, [])
                if metric_list:
                    metric = metric_list[0]
                    cvss_data = metric.get('cvssData', {})
                    session.run("""
                        MATCH (c:CVE {id: $id})
                        SET c.cvssVersion = $version,
                            c.cvssScore = $score,
                            c.cvssSeverity = $severity,
                            c.cvssVector = $vector
                    """,
                        id=cve_id,
                        version=cvss_data.get('version'),
                        score=cvss_data.get('baseScore'),
                        severity=cvss_data.get('baseSeverity'),
                        vector=cvss_data.get('vectorString')
                    )
                    break
            
            # Add CWE relationships
            weaknesses = cve_data.get('weaknesses', [])
            for weakness in weaknesses:
                for desc in weakness.get('description', []):
                    cwe_id = desc.get('value')
                    if cwe_id and cwe_id.startswith('CWE-'):
                        session.run("""
                            MERGE (w:CWE {id: $cwe_id})
                            ON CREATE SET w.source = $source, w.type = $type
                            WITH w
                            MATCH (c:CVE {id: $cve_id})
                            MERGE (c)-[:HAS_WEAKNESS]->(w)
                        """,
                            cve_id=cve_id,
                            cwe_id=cwe_id,
                            source=weakness.get('source', ''),
                            type=weakness.get('type', '')
                        )
    
    def load_from_jsonl(self, jsonl_path, criteria, max_cves=None):
        """Load selected CVEs from JSONL file."""
        logger.info(f"Loading CVEs from {jsonl_path}")
        logger.info(f"Criteria: {criteria}")
        
        stats = {
            'total_scanned': 0,
            'selected': 0,
            'loaded': 0,
            'reasons': {}
        }
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Scanning CVEs"):
                stats['total_scanned'] += 1
                
                record = json.loads(line)
                vulns = record.get('payload', {}).get('vulnerabilities', [])
                
                if not vulns:
                    continue
                
                cve_data = vulns[0].get('cve', {})
                should_load, reason = self.should_include(cve_data, criteria)
                
                if should_load:
                    stats['selected'] += 1
                    stats['reasons'][reason] = stats['reasons'].get(reason, 0) + 1
                    
                    try:
                        self.load_cve(cve_data)
                        stats['loaded'] += 1
                    except Exception as e:
                        logger.error(f"Error loading {cve_data.get('id')}: {e}")
                    
                    if max_cves and stats['loaded'] >= max_cves:
                        logger.info(f"Reached max CVEs limit: {max_cves}")
                        break
        
        return stats


def main():
    parser = argparse.ArgumentParser(description="Load selected CVEs into Neo4j")
    parser.add_argument('--input', default='data/raw/cve/all_cves_complete.jsonl',
                       help='Input JSONL file')
    parser.add_argument('--kev-only', action='store_true',
                       help='Load only KEV CVEs')
    parser.add_argument('--recent-years', type=int, default=5,
                       help='Include CVEs from recent N years')
    parser.add_argument('--epss-threshold', type=float, default=0.1,
                       help='Minimum EPSS score (0.0-1.0)')
    parser.add_argument('--max-cves', type=int,
                       help='Maximum number of CVEs to load')
    parser.add_argument('--all', action='store_true',
                       help='Load all CVEs (use with caution)')
    
    args = parser.parse_args()
    
    # Build criteria
    criteria = {}
    
    if not args.kev_only:
        current_year = datetime.now().year
        criteria['min_year'] = current_year - args.recent_years
        criteria['epss_threshold'] = args.epss_threshold
        criteria['severity_filter'] = ['CRITICAL', 'HIGH']
    
    loader = SelectiveCVELoader()
    
    try:
        stats = loader.load_from_jsonl(
            Path(args.input),
            criteria,
            max_cves=args.max_cves
        )
        
        logger.info("=" * 80)
        logger.info("Loading Complete!")
        logger.info(f"Total scanned: {stats['total_scanned']:,}")
        logger.info(f"Selected: {stats['selected']:,}")
        logger.info(f"Loaded: {stats['loaded']:,}")
        logger.info("\nSelection reasons:")
        for reason, count in sorted(stats['reasons'].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {reason}: {count:,}")
        logger.info("=" * 80)
        
    finally:
        loader.close()


if __name__ == "__main__":
    main()
