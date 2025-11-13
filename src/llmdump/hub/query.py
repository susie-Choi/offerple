"""
Hub Query Module - Retrieve data from Neo4j for analysis.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime


class HubQuery:
    """Query interface for retrieving data from Neo4j hub."""
    
    def __init__(self, driver):
        """
        Initialize query interface.
        
        Args:
            driver: Neo4j driver instance
        """
        self.driver = driver
    
    def get_cve_data(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Get CVE data by ID.
        
        Args:
            cve_id: CVE identifier (e.g., "CVE-2024-1234")
        
        Returns:
            Dictionary with CVE data or None if not found
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:CVE {id: $cve_id})
                OPTIONAL MATCH (c)-[:HAS_CWE]->(cwe:CWE)
                OPTIONAL MATCH (c)-[:AFFECTS]->(cpe:CPE)
                RETURN c.id as id,
                       c.description as description,
                       c.cvss_score as cvss_score,
                       c.severity as severity,
                       c.published as published,
                       c.modified as modified,
                       collect(DISTINCT cwe.id) as cwes,
                       collect(DISTINCT cpe.uri) as affected_products
                LIMIT 1
            """, cve_id=cve_id)
            
            record = result.single()
            if not record:
                return None
            
            return {
                'id': record['id'],
                'description': record['description'],
                'cvss_score': record['cvss_score'],
                'severity': record['severity'],
                'published': record['published'],
                'modified': record['modified'],
                'cwe': record['cwes'][0] if record['cwes'] else None,
                'cwes': record['cwes'],
                'affected_products': record['affected_products'],
            }
    
    def get_epss_data(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Get EPSS score for a CVE.
        
        Args:
            cve_id: CVE identifier
        
        Returns:
            Dictionary with EPSS data or None
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:CVE {id: $cve_id})-[:HAS_EPSS]->(e:EPSS)
                RETURN e.score as epss,
                       e.percentile as percentile,
                       e.date as date
                ORDER BY e.date DESC
                LIMIT 1
            """, cve_id=cve_id)
            
            record = result.single()
            if not record:
                return None
            
            return {
                'epss': record['epss'],
                'percentile': record['percentile'],
                'date': record['date'],
            }
    
    def get_kev_data(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if CVE is in CISA KEV catalog.
        
        Args:
            cve_id: CVE identifier
        
        Returns:
            Dictionary with KEV data or None
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:CVE {id: $cve_id})-[:IN_KEV]->(k:KEV)
                RETURN k.date_added as date_added,
                       k.due_date as due_date,
                       k.known_ransomware as known_ransomware,
                       k.notes as notes
                LIMIT 1
            """, cve_id=cve_id)
            
            record = result.single()
            if not record:
                return {'in_kev': False}
            
            return {
                'in_kev': True,
                'date_added': record['date_added'],
                'due_date': record['due_date'],
                'known_ransomware': record['known_ransomware'],
                'notes': record['notes'],
            }
    
    def get_package_data(self, package: str) -> Optional[Dict[str, Any]]:
        """
        Get package information and CVE history.
        
        Args:
            package: Package name (e.g., "django/django")
        
        Returns:
            Dictionary with package data
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Package {name: $package})
                OPTIONAL MATCH (p)-[:HAS_CVE]->(c:CVE)
                RETURN p.name as name,
                       p.ecosystem as ecosystem,
                       p.description as description,
                       count(c) as total_cves,
                       collect(c.id) as cve_ids
                LIMIT 1
            """, package=package)
            
            record = result.single()
            if not record:
                return None
            
            return {
                'name': record['name'],
                'ecosystem': record['ecosystem'],
                'description': record['description'],
                'total_cves': record['total_cves'],
                'cve_ids': record['cve_ids'],
            }
    
    def get_github_signals(self, package: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get GitHub activity signals for a package.
        
        Args:
            package: Package/repository name
            days: Number of days to look back
        
        Returns:
            Dictionary with GitHub signals
        """
        # This would query GitHub signals stored in Neo4j
        # For now, return None (will be implemented when we add GitHub data collection)
        return None
    
    def search_similar_cves(
        self, 
        cwe_id: Optional[str] = None,
        cvss_min: Optional[float] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar CVEs.
        
        Args:
            cwe_id: Filter by CWE ID
            cvss_min: Minimum CVSS score
            limit: Maximum results
        
        Returns:
            List of CVE dictionaries
        """
        with self.driver.session() as session:
            query = "MATCH (c:CVE)"
            
            conditions = []
            params = {'limit': limit}
            
            if cwe_id:
                query += "-[:HAS_CWE]->(cwe:CWE {id: $cwe_id})"
                params['cwe_id'] = cwe_id
            
            if cvss_min:
                conditions.append("c.cvss_score >= $cvss_min")
                params['cvss_min'] = cvss_min
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += """
                RETURN c.id as id,
                       c.description as description,
                       c.cvss_score as cvss_score,
                       c.severity as severity,
                       c.published as published
                ORDER BY c.published DESC
                LIMIT $limit
            """
            
            result = session.run(query, **params)
            
            return [
                {
                    'id': record['id'],
                    'description': record['description'],
                    'cvss_score': record['cvss_score'],
                    'severity': record['severity'],
                    'published': record['published'],
                }
                for record in result
            ]
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get hub statistics.
        
        Returns:
            Dictionary with node counts
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:CVE)
                WITH count(c) as cve_count
                MATCH (e:EPSS)
                WITH cve_count, count(e) as epss_count
                MATCH (k:KEV)
                WITH cve_count, epss_count, count(k) as kev_count
                MATCH (cwe:CWE)
                RETURN cve_count, epss_count, kev_count, count(cwe) as cwe_count
            """)
            
            record = result.single()
            if not record:
                return {
                    'cve_count': 0,
                    'epss_count': 0,
                    'kev_count': 0,
                    'cwe_count': 0,
                }
            
            return {
                'cve_count': record['cve_count'],
                'epss_count': record['epss_count'],
                'kev_count': record['kev_count'],
                'cwe_count': record['cwe_count'],
            }

    
    def get_dependency_risks(self, package: str, depth: int = 2) -> Dict[str, Any]:
        """
        Get dependency chain vulnerability risks.
        
        Args:
            package: Package name
            depth: Dependency depth to analyze
        
        Returns:
            Dictionary with dependency risk information
        """
        with self.driver.session() as session:
            # Find vulnerabilities in dependency chain
            result = session.run("""
                MATCH (p:Package {name: $package})-[:DEPENDS_ON*1..$depth]->(dep:Package)
                OPTIONAL MATCH (dep)-[:HAS_CVE]->(cve:CVE)
                RETURN dep.name as dependency,
                       count(cve) as cve_count,
                       collect(cve.id) as cve_ids,
                       max(cve.cvss_score) as max_cvss
                ORDER BY cve_count DESC
                LIMIT 10
            """, package=package, depth=depth)
            
            vulnerable_deps = [
                {
                    'dependency': record['dependency'],
                    'cve_count': record['cve_count'],
                    'cve_ids': record['cve_ids'],
                    'max_cvss': record['max_cvss'],
                }
                for record in result
                if record['cve_count'] > 0
            ]
            
            # Get total dependency count
            result = session.run("""
                MATCH (p:Package {name: $package})-[:DEPENDS_ON*1..$depth]->(dep:Package)
                RETURN count(DISTINCT dep) as total_deps
            """, package=package, depth=depth)
            
            record = result.single()
            total_deps = record['total_deps'] if record else 0
            
            return {
                'package': package,
                'total_dependencies': total_deps,
                'vulnerable_dependencies': vulnerable_deps,
                'vulnerability_ratio': len(vulnerable_deps) / total_deps if total_deps > 0 else 0,
            }
    
    def get_package_popularity(self, package: str) -> Optional[Dict[str, Any]]:
        """
        Get package popularity metrics.
        
        Args:
            package: Package name
        
        Returns:
            Dictionary with popularity metrics
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Package {name: $package})
                RETURN p.downloads_last_month as downloads,
                       p.total_releases as releases,
                       p.stars as stars,
                       p.forks as forks
                LIMIT 1
            """, package=package)
            
            record = result.single()
            if not record:
                return None
            
            return {
                'downloads_last_month': record['downloads'],
                'total_releases': record['releases'],
                'stars': record['stars'],
                'forks': record['forks'],
            }
    
    def get_maintainer_history(self, package: str) -> List[Dict[str, Any]]:
        """
        Get vulnerability history of packages by same maintainer.
        
        Args:
            package: Package name
        
        Returns:
            List of other packages and their CVE counts
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Package {name: $package})
                WHERE p.author IS NOT NULL
                MATCH (other:Package)
                WHERE other.author = p.author AND other.name <> p.name
                OPTIONAL MATCH (other)-[:HAS_CVE]->(cve:CVE)
                RETURN other.name as package,
                       count(cve) as cve_count
                ORDER BY cve_count DESC
                LIMIT 5
            """, package=package)
            
            return [
                {
                    'package': record['package'],
                    'cve_count': record['cve_count'],
                }
                for record in result
            ]
