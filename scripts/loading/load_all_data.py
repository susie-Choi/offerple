"""Load all collected data to Neo4j."""
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from tqdm import tqdm

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Neo4jLoader:
    """Load data into Neo4j."""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, password]):
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set")
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        logger.info(f"Connected to Neo4j at {uri}")
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear all data from Neo4j."""
        logger.warning("Clearing all data from Neo4j...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Database cleared")
    
    def create_indexes(self):
        """Create indexes for better performance."""
        logger.info("Creating indexes...")
        with self.driver.session() as session:
            indexes = [
                "CREATE INDEX cve_id IF NOT EXISTS FOR (c:CVE) ON (c.id)",
                "CREATE INDEX exploit_id IF NOT EXISTS FOR (e:Exploit) ON (e.edb_id)",
                "CREATE INDEX advisory_id IF NOT EXISTS FOR (a:Advisory) ON (a.ghsa_id)",
                "CREATE INDEX package_name IF NOT EXISTS FOR (p:Package) ON (p.name)",
                "CREATE INDEX commit_sha IF NOT EXISTS FOR (c:Commit) ON (c.sha)",
            ]
            for index in indexes:
                session.run(index)
        logger.info("Indexes created")
    
    def load_cves(self, file_path):
        """Load CVE data."""
        logger.info(f"Loading CVEs from {file_path}")
        
        if not Path(file_path).exists():
            logger.warning(f"File not found: {file_path}")
            return 0
        
        # Check if CVEs already exist
        with self.driver.session() as session:
            result = session.run("MATCH (c:CVE) RETURN count(c) as count")
            existing_count = result.single()['count']
            if existing_count > 0:
                logger.info(f"Found {existing_count} existing CVEs, skipping CVE loading")
                return existing_count
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Loading CVEs"):
                data = json.loads(line)
                payload = data.get('payload', {})
                vulns = payload.get('vulnerabilities', [])
                
                if not vulns:
                    continue
                
                cve_data = vulns[0].get('cve', {})
                cve_id = cve_data.get('id')
                
                if not cve_id:
                    continue
                
                # Extract metrics
                metrics = cve_data.get('metrics', {})
                cvss_v31 = metrics.get('cvssMetricV31', [{}])[0] if metrics.get('cvssMetricV31') else {}
                cvss_data = cvss_v31.get('cvssData', {})
                
                with self.driver.session() as session:
                    session.run("""
                        MERGE (c:CVE {id: $id})
                        SET c.description = $description,
                            c.published = $published,
                            c.lastModified = $lastModified,
                            c.cvssScore = $cvssScore,
                            c.cvssSeverity = $cvssSeverity,
                            c.vectorString = $vectorString
                    """, {
                        'id': cve_id,
                        'description': cve_data.get('descriptions', [{}])[0].get('value', ''),
                        'published': cve_data.get('published', ''),
                        'lastModified': cve_data.get('lastModified', ''),
                        'cvssScore': cvss_data.get('baseScore'),
                        'cvssSeverity': cvss_data.get('baseSeverity'),
                        'vectorString': cvss_data.get('vectorString'),
                    })
                count += 1
        
        logger.info(f"Loaded {count} CVEs")
        return count
    
    def load_epss(self, file_path):
        """Load EPSS scores."""
        logger.info(f"Loading EPSS from {file_path}")
        
        if not Path(file_path).exists():
            logger.warning(f"File not found: {file_path}")
            return 0
        
        # Check if EPSS data already loaded
        with self.driver.session() as session:
            result = session.run("MATCH (c:CVE) WHERE c.epss_score IS NOT NULL RETURN count(c) as count")
            existing_count = result.single()['count']
            if existing_count > 0:
                logger.info(f"Found {existing_count} CVEs with EPSS scores, skipping EPSS loading")
                return existing_count
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Loading EPSS"):
                try:
                    data = json.loads(line)
                    payload = data.get('payload', {})
                    
                    # Handle batch format
                    if 'epss_data' in payload:
                        epss_list = payload['epss_data']
                        for item in epss_list:
                            cve_id = item.get('cve')
                            epss = item.get('epss')
                            percentile = item.get('percentile')
                            
                            if not cve_id:
                                continue
                            
                            with self.driver.session() as session:
                                session.run("""
                                    MERGE (c:CVE {id: $id})
                                    SET c.epss_score = $epss,
                                        c.epss_percentile = $percentile
                                """, {
                                    'id': cve_id,
                                    'epss': float(epss) if epss else None,
                                    'percentile': float(percentile) if percentile else None,
                                })
                            count += 1
                    
                    # Handle single CVE format
                    elif 'cve_id' in payload:
                        epss_list = payload.get('epss_data', [])
                        for item in epss_list:
                            cve_id = item.get('cve')
                            epss = item.get('epss')
                            percentile = item.get('percentile')
                            
                            if not cve_id:
                                continue
                            
                            with self.driver.session() as session:
                                session.run("""
                                    MERGE (c:CVE {id: $id})
                                    SET c.epss_score = $epss,
                                        c.epss_percentile = $percentile
                                """, {
                                    'id': cve_id,
                                    'epss': float(epss) if epss else None,
                                    'percentile': float(percentile) if percentile else None,
                                })
                            count += 1
                
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON line: {e}")
                    continue
        
        logger.info(f"Loaded {count} EPSS scores")
        return count
    
    def load_exploits(self, file_path):
        """Load exploits."""
        logger.info(f"Loading exploits from {file_path}")
        
        if not Path(file_path).exists():
            logger.warning(f"File not found: {file_path}")
            return 0
        
        # Check if exploits already loaded
        with self.driver.session() as session:
            result = session.run("MATCH (e:Exploit) RETURN count(e) as count")
            existing_count = result.single()['count']
            if existing_count > 0:
                logger.info(f"Found {existing_count} existing exploits, skipping exploit loading")
                return existing_count
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Loading Exploits"):
                data = json.loads(line)
                exploit = data.get('exploit', {})
                
                edb_id = exploit.get('id')
                if not edb_id:
                    continue
                
                # Create exploit node
                with self.driver.session() as session:
                    session.run("""
                        MERGE (e:Exploit {edb_id: $edb_id})
                        SET e.description = $description,
                            e.date = $date,
                            e.author = $author,
                            e.type = $type,
                            e.platform = $platform
                    """, {
                        'edb_id': edb_id,
                        'description': exploit.get('description', ''),
                        'date': exploit.get('date', ''),
                        'author': exploit.get('author', ''),
                        'type': exploit.get('type', ''),
                        'platform': exploit.get('platform', ''),
                    })
                    
                    # Link to CVEs
                    codes = exploit.get('codes', '')
                    if codes:
                        cve_ids = [c.strip() for c in codes.split(';') if c.strip().startswith('CVE-')]
                        for cve_id in cve_ids:
                            session.run("""
                                MERGE (c:CVE {id: $cve_id})
                                MERGE (e:Exploit {edb_id: $edb_id})
                                MERGE (c)-[:HAS_EXPLOIT]->(e)
                            """, {'cve_id': cve_id, 'edb_id': edb_id})
                
                count += 1
        
        logger.info(f"Loaded {count} exploits")
        return count
    
    def load_kev(self, file_path):
        """Load KEV catalog."""
        logger.info(f"Loading KEV from {file_path}")
        
        if not Path(file_path).exists():
            logger.warning(f"File not found: {file_path}")
            return 0
        
        # Check if KEV data already loaded
        with self.driver.session() as session:
            result = session.run("MATCH (c:CVE) WHERE c.kev_listed = true RETURN count(c) as count")
            existing_count = result.single()['count']
            if existing_count > 0:
                logger.info(f"Found {existing_count} CVEs in KEV, skipping KEV loading")
                return existing_count
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Loading KEV"):
                data = json.loads(line)
                payload = data.get('payload', {})
                vulnerabilities = payload.get('vulnerabilities', [])
                
                for vuln in vulnerabilities:
                    cve_id = vuln.get('cveID')
                    if not cve_id:
                        continue
                    
                    with self.driver.session() as session:
                        session.run("""
                            MERGE (c:CVE {id: $cve_id})
                            SET c.kev_listed = true,
                                c.kev_name = $name,
                                c.kev_date_added = $date_added,
                                c.kev_due_date = $due_date,
                                c.kev_action = $action
                        """, {
                            'cve_id': cve_id,
                            'name': vuln.get('vulnerabilityName', ''),
                            'date_added': vuln.get('dateAdded', ''),
                            'due_date': vuln.get('dueDate', ''),
                            'action': vuln.get('requiredAction', ''),
                        })
                    count += 1
        
        logger.info(f"Loaded {count} KEV entries")
        return count
    
    def load_github_commits(self, directory):
        """Load GitHub commits."""
        logger.info(f"Loading GitHub commits from {directory}")
        
        commit_dir = Path(directory)
        if not commit_dir.exists():
            logger.warning(f"Directory not found: {directory}")
            return 0
        
        # Check if commits already loaded
        with self.driver.session() as session:
            result = session.run("MATCH (c:Commit) RETURN count(c) as count")
            existing_count = result.single()['count']
            if existing_count > 0:
                logger.info(f"Found {existing_count} existing commits, skipping commit loading")
                return existing_count
        
        count = 0
        for file_path in tqdm(list(commit_dir.glob("**/*.jsonl")), desc="Loading Commits"):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    repo = data.get('repo', '')
                    commit = data.get('payload', {})
                    
                    sha = commit.get('sha')
                    if not sha:
                        continue
                    
                    with self.driver.session() as session:
                        # Create commit node
                        session.run("""
                            MERGE (c:Commit {sha: $sha})
                            SET c.message = $message,
                                c.author = $author,
                                c.date = $date,
                                c.repo = $repo
                        """, {
                            'sha': sha,
                            'message': commit.get('commit', {}).get('message', ''),
                            'author': commit.get('commit', {}).get('author', {}).get('name', ''),
                            'date': commit.get('commit', {}).get('author', {}).get('date', ''),
                            'repo': repo,
                        })
                    count += 1
        
        logger.info(f"Loaded {count} commits")
        return count


def main():
    loader = Neo4jLoader()
    
    try:
        # Create indexes (safe to run multiple times)
        loader.create_indexes()
        
        # Load data
        stats = {}
        
        stats['cves'] = loader.load_cves("data/raw/bulk_cve_data.jsonl")
        stats['epss'] = loader.load_epss("data/raw/bulk_epss_data.jsonl")
        stats['exploits'] = loader.load_exploits("data/raw/bulk_exploits_data.jsonl")
        stats['kev'] = loader.load_kev("data/raw/kev_catalog.jsonl")
        stats['commits'] = loader.load_github_commits("data/raw/github/commits_smart/top_repos")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Loading complete!")
        logger.info(f"  CVEs: {stats['cves']:,}")
        logger.info(f"  EPSS scores: {stats['epss']:,}")
        logger.info(f"  Exploits: {stats['exploits']:,}")
        logger.info(f"  KEV entries: {stats['kev']:,}")
        logger.info(f"  Commits: {stats['commits']:,}")
        logger.info("="*60)
        
    finally:
        loader.close()


if __name__ == "__main__":
    main()
