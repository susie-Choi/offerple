"""Data loader for Neo4j hub."""

from pathlib import Path
from typing import Dict, Any, List
import json
import logging

from .connection import Neo4jConnection

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads data from spokes into Neo4j hub."""
    
    def __init__(self, connection: Neo4jConnection):
        """
        Initialize data loader.
        
        Args:
            connection: Neo4j connection instance
        """
        self.conn = connection
        self.driver = connection.connect()
    
    def load_cve_data(self, jsonl_path: Path) -> Dict[str, int]:
        """
        Load CVE data into Neo4j.
        
        Args:
            jsonl_path: Path to JSONL file with CVE data
            
        Returns:
            Statistics (nodes_created, nodes_updated)
        """
        logger.info(f"Loading CVE data from {jsonl_path}")
        
        raw_entries = self._read_jsonl(jsonl_path)
        
        # Normalize CVE entries to standard format
        cves = []
        for entry in raw_entries:
            if "cve_id" in entry:
                # Already in standard format
                cves.append(entry)
            elif "payload" in entry and "vulnerabilities" in entry["payload"]:
                # NVD API format - extract CVE data
                for vuln in entry["payload"]["vulnerabilities"]:
                    cve_data = vuln.get("cve", {})
                    if "id" in cve_data:
                        normalized = {
                            "cve_id": cve_data["id"],
                            "published": cve_data.get("published"),
                            "last_modified": cve_data.get("lastModified"),
                            "description": self._extract_description(cve_data),
                            "cvss_score": self._extract_cvss_score(cve_data),
                            "cvss_severity": self._extract_cvss_severity(cve_data),
                            "cwe_ids": self._extract_cwe_ids(cve_data),
                            "_collected_at": entry.get("collected_at"),
                            "_source": entry.get("source", "nvd_cve")
                        }
                        cves.append(normalized)
        
        nodes_created = 0
        nodes_updated = 0
        
        with self.driver.session() as session:
            for cve in cves:
                result = session.execute_write(self._create_cve_node, cve)
                if result == "created":
                    nodes_created += 1
                else:
                    nodes_updated += 1
        
        logger.info(f"Created {nodes_created} CVE nodes, updated {nodes_updated}")
        
        return {
            "nodes_created": nodes_created,
            "nodes_updated": nodes_updated,
            "total": len(cves)
        }
    
    def load_epss_data(self, jsonl_path: Path) -> Dict[str, int]:
        """Load EPSS data into Neo4j."""
        logger.info(f"Loading EPSS data from {jsonl_path}")
        
        epss_scores = self._read_jsonl(jsonl_path)
        
        relationships_created = 0
        
        with self.driver.session() as session:
            for score in epss_scores:
                created = session.execute_write(self._create_epss_relationship, score)
                if created:
                    relationships_created += 1
        
        logger.info(f"Created {relationships_created} EPSS relationships")
        
        return {
            "relationships_created": relationships_created,
            "total": len(epss_scores)
        }
    
    def load_kev_data(self, jsonl_path: Path) -> Dict[str, int]:
        """Load KEV data into Neo4j."""
        logger.info(f"Loading KEV data from {jsonl_path}")
        
        kev_entries = self._read_jsonl(jsonl_path)
        
        nodes_created = 0
        cves_enriched = 0
        
        with self.driver.session() as session:
            for entry in kev_entries:
                result = session.execute_write(self._create_kev_node, entry)
                nodes_created += result["node_created"]
                cves_enriched += result["cve_enriched"]
        
        logger.info(f"Created {nodes_created} KEV nodes, enriched {cves_enriched} CVEs")
        
        return {
            "nodes_created": nodes_created,
            "cves_enriched": cves_enriched,
            "total": len(kev_entries)
        }
    
    @staticmethod
    def _extract_description(cve_data: Dict[str, Any]) -> str:
        """Extract description from NVD CVE data."""
        descriptions = cve_data.get("descriptions", [])
        for desc in descriptions:
            if desc.get("lang") == "en":
                return desc.get("value", "")
        return descriptions[0].get("value", "") if descriptions else ""
    
    @staticmethod
    def _extract_cvss_score(cve_data: Dict[str, Any]) -> float:
        """Extract CVSS score from NVD CVE data."""
        metrics = cve_data.get("metrics", {})
        
        # Try CVSS v3.1 first
        if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
            return metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseScore")
        
        # Try CVSS v3.0
        if "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
            return metrics["cvssMetricV30"][0].get("cvssData", {}).get("baseScore")
        
        # Try CVSS v2
        if "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
            return metrics["cvssMetricV2"][0].get("cvssData", {}).get("baseScore")
        
        return None
    
    @staticmethod
    def _extract_cvss_severity(cve_data: Dict[str, Any]) -> str:
        """Extract CVSS severity from NVD CVE data."""
        metrics = cve_data.get("metrics", {})
        
        # Try CVSS v3.1 first
        if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
            return metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseSeverity")
        
        # Try CVSS v3.0
        if "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
            return metrics["cvssMetricV30"][0].get("cvssData", {}).get("baseSeverity")
        
        # Try CVSS v2
        if "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
            return metrics["cvssMetricV2"][0].get("baseSeverity")
        
        return None
    
    @staticmethod
    def _extract_cwe_ids(cve_data: Dict[str, Any]) -> list:
        """Extract CWE IDs from NVD CVE data."""
        weaknesses = cve_data.get("weaknesses", [])
        cwe_ids = []
        
        for weakness in weaknesses:
            for desc in weakness.get("description", []):
                value = desc.get("value", "")
                if value.startswith("CWE-"):
                    cwe_ids.append(value)
        
        return cwe_ids
    
    def load_cwe_data(self, jsonl_path: Path) -> Dict[str, int]:
        """Load CWE data into Neo4j."""
        logger.info(f"Loading CWE data from {jsonl_path}")
        
        cwe_entries = self._read_jsonl(jsonl_path)
        
        nodes_created = 0
        relationships_created = 0
        
        with self.driver.session() as session:
            for entry in cwe_entries:
                result = session.execute_write(self._create_cwe_node, entry)
                nodes_created += result["node_created"]
                relationships_created += result["relationships_created"]
        
        logger.info(f"Created {nodes_created} CWE nodes, {relationships_created} relationships")
        
        return {
            "nodes_created": nodes_created,
            "relationships_created": relationships_created,
            "total": len(cwe_entries)
        }
    
    @staticmethod
    def _create_cve_node(tx, cve: Dict[str, Any]) -> str:
        """Create or update CVE node."""
        query = """
        MERGE (c:CVE {id: $cve_id})
        ON CREATE SET
            c.published = $published,
            c.description = $description,
            c.cvss_score = $cvss_score,
            c.cvss_severity = $cvss_severity,
            c.cwe_ids = $cwe_ids,
            c.created_at = datetime()
        ON MATCH SET
            c.last_modified = $last_modified,
            c.updated_at = datetime()
        RETURN c, 
               CASE WHEN c.created_at = datetime() THEN 'created' ELSE 'updated' END as status
        """
        
        result = tx.run(query,
            cve_id=cve["cve_id"],
            published=cve.get("published"),
            last_modified=cve.get("last_modified"),
            description=cve.get("description"),
            cvss_score=cve.get("cvss_score"),
            cvss_severity=cve.get("cvss_severity"),
            cwe_ids=cve.get("cwe_ids", [])
        )
        
        record = result.single()
        return record["status"] if record else "unknown"
    
    @staticmethod
    def _create_epss_relationship(tx, score: Dict[str, Any]) -> bool:
        """Create EPSS relationship to CVE."""
        query = """
        MATCH (c:CVE {id: $cve_id})
        MERGE (e:EPSS {cve_id: $cve_id, date: $date})
        SET e.score = $score,
            e.percentile = $percentile
        MERGE (c)-[:HAS_EPSS]->(e)
        RETURN count(e) as created
        """
        
        result = tx.run(query,
            cve_id=score["cve_id"],
            score=score["epss_score"],
            percentile=score.get("percentile", 0),
            date=score.get("date", "")
        )
        
        record = result.single()
        return record["created"] > 0 if record else False
    
    @staticmethod
    def _create_kev_node(tx, entry: Dict[str, Any]) -> Dict[str, int]:
        """Create KEV node and enrich CVE."""
        query = """
        MERGE (k:KEV {cve_id: $cve_id})
        SET k.vulnerability_name = $vulnerability_name,
            k.vendor_project = $vendor_project,
            k.product = $product,
            k.date_added = $date_added,
            k.short_description = $short_description,
            k.required_action = $required_action,
            k.due_date = $due_date,
            k.known_ransomware_use = $known_ransomware_use
        
        WITH k
        MATCH (c:CVE {id: $cve_id})
        MERGE (c)-[:HAS_KEV]->(k)
        SET c.is_kev = true,
            c.kev_date_added = $date_added,
            c.kev_ransomware = $known_ransomware_use
        
        RETURN count(k) as node_created, count(c) as cve_enriched
        """
        
        result = tx.run(query,
            cve_id=entry["cve_id"],
            vulnerability_name=entry.get("vulnerability_name", ""),
            vendor_project=entry.get("vendor_project", ""),
            product=entry.get("product", ""),
            date_added=entry.get("date_added", ""),
            short_description=entry.get("short_description", ""),
            required_action=entry.get("required_action", ""),
            due_date=entry.get("due_date", ""),
            known_ransomware_use=entry.get("known_ransomware_use", False)
        )
        
        record = result.single()
        if record:
            return {
                "node_created": record["node_created"],
                "cve_enriched": record["cve_enriched"]
            }
        return {"node_created": 0, "cve_enriched": 0}
    
    @staticmethod
    def _create_cwe_node(tx, entry: Dict[str, Any]) -> Dict[str, int]:
        """Create CWE node and relationships."""
        # Create CWE node
        cwe_query = """
        MERGE (cwe:CWE {id: $cwe_id})
        SET cwe.name = $name,
            cwe.abstraction = $abstraction,
            cwe.structure = $structure,
            cwe.status = $status,
            cwe.description = $description,
            cwe.extended_description = $extended_description,
            cwe.likelihood_of_exploit = $likelihood_of_exploit,
            cwe.applicable_languages = $applicable_languages
        RETURN 1 as created
        """
        
        tx.run(cwe_query,
            cwe_id=entry["cwe_id"],
            name=entry.get("name", ""),
            abstraction=entry.get("abstraction", ""),
            structure=entry.get("structure", ""),
            status=entry.get("status", ""),
            description=entry.get("description", ""),
            extended_description=entry.get("extended_description", ""),
            likelihood_of_exploit=entry.get("likelihood_of_exploit", ""),
            applicable_languages=entry.get("applicable_languages", [])
        )
        
        # Create consequence relationships
        consequence_count = 0
        for consequence in entry.get("consequences", []):
            cons_query = """
            MATCH (cwe:CWE {id: $cwe_id})
            MERGE (c:Consequence {scope: $scope, impact: $impact})
            MERGE (cwe)-[:HAS_CONSEQUENCE]->(c)
            RETURN 1 as created
            """
            tx.run(cons_query,
                cwe_id=entry["cwe_id"],
                scope=consequence.get("scope", ""),
                impact=consequence.get("impact", "")
            )
            consequence_count += 1
        
        # Create related weakness relationships
        related_count = 0
        for related in entry.get("related_weaknesses", []):
            rel_query = """
            MATCH (cwe:CWE {id: $cwe_id})
            MERGE (related_cwe:CWE {id: $related_cwe_id})
            MERGE (cwe)-[:RELATED_TO {nature: $nature}]->(related_cwe)
            RETURN 1 as created
            """
            tx.run(rel_query,
                cwe_id=entry["cwe_id"],
                related_cwe_id=related.get("cwe_id", ""),
                nature=related.get("nature", "")
            )
            related_count += 1
        
        return {
            "node_created": 1,
            "relationships_created": consequence_count + related_count
        }
        
        result = tx.run(query,
            cwe_id=entry["cwe_id"],
            name=entry.get("name", ""),
            abstraction=entry.get("abstraction", ""),
            structure=entry.get("structure", ""),
            status=entry.get("status", ""),
            description=entry.get("description", ""),
            extended_description=entry.get("extended_description", ""),
            likelihood_of_exploit=entry.get("likelihood_of_exploit", ""),
            applicable_languages=entry.get("applicable_languages", []),
            consequences=entry.get("consequences", []),
            related_weaknesses=entry.get("related_weaknesses", [])
        )
        
        record = result.single()
        if record:
            return {
                "node_created": record["node_created"],
                "relationships_created": record["relationships_created"]
            }
        return {"node_created": 0, "relationships_created": 0}
    
    @staticmethod
    def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
        """Read JSONL file."""
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    
    def load_package_data(self, jsonl_path: Path) -> Dict[str, int]:
        """
        Load package metadata into Neo4j.
        
        Args:
            jsonl_path: Path to JSONL file with package data
            
        Returns:
            Statistics (nodes_created, nodes_updated)
        """
        logger.info(f"Loading package data from {jsonl_path}")
        
        packages = self._read_jsonl(jsonl_path)
        
        nodes_created = 0
        nodes_updated = 0
        
        with self.driver.session() as session:
            for pkg in packages:
                metadata = pkg.get('metadata', {})
                stats = pkg.get('statistics', {})
                
                result = session.run("""
                    MERGE (p:Package {name: $name, ecosystem: $ecosystem})
                    ON CREATE SET
                        p.created_at = datetime(),
                        p.version = $version,
                        p.description = $description,
                        p.author = $author,
                        p.license = $license,
                        p.homepage = $homepage,
                        p.downloads_last_month = $downloads_last_month,
                        p.total_releases = $total_releases
                    ON MATCH SET
                        p.updated_at = datetime(),
                        p.version = $version,
                        p.downloads_last_month = $downloads_last_month,
                        p.total_releases = $total_releases
                    RETURN p, 
                           CASE WHEN p.created_at = datetime() THEN 'created' ELSE 'updated' END as action
                """, 
                    name=pkg.get('package'),
                    ecosystem=pkg.get('source'),
                    version=metadata.get('version'),
                    description=metadata.get('description') or metadata.get('summary'),
                    author=metadata.get('author'),
                    license=metadata.get('license'),
                    homepage=metadata.get('home_page') or metadata.get('homepage'),
                    downloads_last_month=stats.get('downloads_last_month', 0),
                    total_releases=stats.get('total_releases', 0)
                )
                
                record = result.single()
                if record and record['action'] == 'created':
                    nodes_created += 1
                else:
                    nodes_updated += 1
        
        logger.info(f"Loaded {nodes_created + nodes_updated} packages ({nodes_created} created, {nodes_updated} updated)")
        
        return {
            'nodes_created': nodes_created,
            'nodes_updated': nodes_updated,
        }
    
    def load_dependency_data(self, jsonl_path: Path) -> Dict[str, int]:
        """
        Load dependency relationships into Neo4j.
        
        Args:
            jsonl_path: Path to JSONL file with dependency data
            
        Returns:
            Statistics (relationships_created)
        """
        logger.info(f"Loading dependency data from {jsonl_path}")
        
        dep_data = self._read_jsonl(jsonl_path)
        
        relationships_created = 0
        
        with self.driver.session() as session:
            for data in dep_data:
                ecosystem = data.get('source')
                dependencies = data.get('dependencies', [])
                
                for dep in dependencies:
                    from_pkg = dep.get('from')
                    to_pkg = dep.get('to')
                    depth = dep.get('depth', 0)
                    requirement = dep.get('requirement') or dep.get('version')
                    
                    # Create dependency relationship
                    result = session.run("""
                        MERGE (p1:Package {name: $from_pkg, ecosystem: $ecosystem})
                        MERGE (p2:Package {name: $to_pkg, ecosystem: $ecosystem})
                        MERGE (p1)-[r:DEPENDS_ON]->(p2)
                        ON CREATE SET
                            r.created_at = datetime(),
                            r.requirement = $requirement,
                            r.depth = $depth
                        ON MATCH SET
                            r.updated_at = datetime(),
                            r.requirement = $requirement
                        RETURN r
                    """,
                        from_pkg=from_pkg,
                        to_pkg=to_pkg,
                        ecosystem=ecosystem,
                        requirement=requirement,
                        depth=depth
                    )
                    
                    if result.single():
                        relationships_created += 1
        
        logger.info(f"Created {relationships_created} dependency relationships")
        
        return {
            'relationships_created': relationships_created,
        }
    
    def load_github_signals(self, jsonl_path: Path) -> Dict[str, int]:
        """
        Load GitHub signals into Neo4j.
        
        Args:
            jsonl_path: Path to JSONL file with GitHub signals
            
        Returns:
            Statistics (nodes_created)
        """
        logger.info(f"Loading GitHub signals from {jsonl_path}")
        
        signals = self._read_jsonl(jsonl_path)
        
        nodes_created = 0
        
        with self.driver.session() as session:
            for signal in signals:
                repo = signal.get('repository')
                
                result = session.run("""
                    MERGE (p:Package {name: $repo})
                    ON CREATE SET p.ecosystem = 'github'
                    
                    CREATE (s:GitHubSignal {
                        collected_at: datetime($collected_at),
                        days: $days,
                        commit_count: $commit_count,
                        security_commits: $security_commits,
                        commit_spike: $commit_spike,
                        open_issues: $open_issues,
                        security_issues: $security_issues,
                        critical_issues: $critical_issues,
                        pr_count: $pr_count,
                        security_prs: $security_prs,
                        emergency_fixes: $emergency_fixes,
                        contributors: $contributors,
                        auth_changes: $auth_changes,
                        db_changes: $db_changes,
                        unusual_patterns: $unusual_patterns
                    })
                    
                    CREATE (p)-[:HAS_SIGNAL]->(s)
                    
                    RETURN s
                """,
                    repo=repo,
                    collected_at=signal.get('collected_at'),
                    days=signal.get('days', 30),
                    commit_count=signal.get('commit_count', 0),
                    security_commits=signal.get('security_commits', 0),
                    commit_spike=signal.get('commit_spike', False),
                    open_issues=signal.get('open_issues', 0),
                    security_issues=signal.get('security_issues', 0),
                    critical_issues=signal.get('critical_issues', 0),
                    pr_count=signal.get('pr_count', 0),
                    security_prs=signal.get('security_prs', 0),
                    emergency_fixes=signal.get('emergency_fixes', 0),
                    contributors=signal.get('contributors', 0),
                    auth_changes=signal.get('auth_changes', False),
                    db_changes=signal.get('db_changes', False),
                    unusual_patterns=signal.get('unusual_patterns', 'None detected')
                )
                
                if result.single():
                    nodes_created += 1
        
        logger.info(f"Created {nodes_created} GitHub signal nodes")
        
        return {
            'nodes_created': nodes_created,
        }


__all__ = ['DataLoader']
