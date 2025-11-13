"""
Supply Chain Analysis - Track dependencies and impact propagation.

Analyzes how vulnerabilities in one package affect the entire ecosystem.
"""
import os
import requests
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)


@dataclass
class DependencyNode:
    """A node in the dependency graph."""
    name: str
    ecosystem: str  # pypi, npm, maven, etc.
    version: Optional[str] = None
    direct_dependents: int = 0
    total_dependents: int = 0
    risk_score: float = 0.0


@dataclass
class ImpactAnalysis:
    """Result of supply chain impact analysis."""
    package: str
    ecosystem: str
    direct_dependents: List[str]
    total_dependents: int
    critical_dependents: List[str]  # High-profile projects
    depth_levels: Dict[int, List[str]]  # Dependency depth
    blast_radius: int  # Total affected projects


class SupplyChainAnalyzer:
    """
    Analyzes supply chain dependencies and impact propagation.
    
    Tracks how a vulnerability in one package affects downstream projects.
    """
    
    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        github_token: Optional[str] = None
    ):
        """
        Initialize supply chain analyzer.
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            github_token: GitHub API token
        """
        neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI")
        neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        
        if neo4j_uri and neo4j_password:
            self.driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_user, neo4j_password)
            )
        else:
            logger.warning("Neo4j credentials not provided")
            self.driver = None
        
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if self.github_token:
            self.headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        else:
            self.headers = {}
    
    def analyze_impact(
        self,
        package: str,
        ecosystem: str = "pypi",
        max_depth: int = 3
    ) -> ImpactAnalysis:
        """
        Analyze the impact of a vulnerability in a package.
        
        Args:
            package: Package name
            ecosystem: Package ecosystem (pypi, npm, maven)
            max_depth: Maximum dependency depth to analyze
            
        Returns:
            ImpactAnalysis with dependency information
        """
        logger.info(f"Analyzing supply chain impact for {package} ({ecosystem})")
        
        # Get direct dependents
        direct_dependents = self._get_direct_dependents(package, ecosystem)
        
        # Get all dependents (recursive)
        all_dependents = self._get_all_dependents(package, ecosystem, max_depth)
        
        # Identify critical dependents (high-profile projects)
        critical_dependents = self._identify_critical_dependents(all_dependents)
        
        # Calculate depth levels
        depth_levels = self._calculate_depth_levels(package, ecosystem, max_depth)
        
        return ImpactAnalysis(
            package=package,
            ecosystem=ecosystem,
            direct_dependents=direct_dependents,
            total_dependents=len(all_dependents),
            critical_dependents=critical_dependents,
            depth_levels=depth_levels,
            blast_radius=len(all_dependents)
        )
    
    def get_package_popularity(
        self,
        package: str,
        ecosystem: str = "pypi"
    ) -> Dict[str, Any]:
        """
        Get package popularity metrics.
        
        Args:
            package: Package name
            ecosystem: Package ecosystem
            
        Returns:
            Popularity metrics (downloads, stars, etc.)
        """
        if ecosystem == "pypi":
            return self._get_pypi_popularity(package)
        elif ecosystem == "npm":
            return self._get_npm_popularity(package)
        else:
            return {}
    
    def build_dependency_graph(
        self,
        package: str,
        ecosystem: str = "pypi"
    ) -> Dict[str, Any]:
        """
        Build a dependency graph for a package.
        
        Args:
            package: Package name
            ecosystem: Package ecosystem
            
        Returns:
            Graph structure with nodes and edges
        """
        logger.info(f"Building dependency graph for {package}")
        
        # Get popularity metrics
        popularity = self.get_package_popularity(package, ecosystem)
        
        if ecosystem == "pypi":
            graph = self._build_pypi_graph(package)
        elif ecosystem == "npm":
            graph = self._build_npm_graph(package)
        else:
            raise ValueError(f"Unsupported ecosystem: {ecosystem}")
        
        # Add popularity to graph
        graph['popularity'] = popularity
        return graph
    
    def load_dependencies_to_neo4j(
        self,
        package: str,
        ecosystem: str = "pypi"
    ) -> Dict[str, int]:
        """
        Load dependency graph into Neo4j.
        
        Args:
            package: Package name
            ecosystem: Package ecosystem
            
        Returns:
            Statistics (nodes_created, relationships_created)
        """
        if not self.driver:
            raise ValueError("Neo4j connection not available")
        
        logger.info(f"Loading dependencies for {package} into Neo4j")
        
        graph = self.build_dependency_graph(package, ecosystem)
        
        nodes_created = 0
        relationships_created = 0
        
        with self.driver.session() as session:
            # Create package node
            session.run("""
                MERGE (p:Package {name: $name, ecosystem: $ecosystem})
                ON CREATE SET p.created_at = datetime()
                ON MATCH SET p.updated_at = datetime()
            """, name=package, ecosystem=ecosystem)
            nodes_created += 1
            
            # Create dependency relationships
            for dep_name, dep_info in graph.get('dependencies', {}).items():
                # Create dependency node
                session.run("""
                    MERGE (d:Package {name: $name, ecosystem: $ecosystem})
                    ON CREATE SET d.created_at = datetime()
                """, name=dep_name, ecosystem=ecosystem)
                nodes_created += 1
                
                # Create DEPENDS_ON relationship
                session.run("""
                    MATCH (p:Package {name: $package, ecosystem: $ecosystem})
                    MATCH (d:Package {name: $dependency, ecosystem: $ecosystem})
                    MERGE (p)-[r:DEPENDS_ON]->(d)
                    ON CREATE SET r.created_at = datetime()
                """, package=package, dependency=dep_name, ecosystem=ecosystem)
                relationships_created += 1
        
        logger.info(f"Created {nodes_created} nodes and {relationships_created} relationships")
        
        return {
            'nodes_created': nodes_created,
            'relationships_created': relationships_created
        }
    
    def _get_direct_dependents(
        self,
        package: str,
        ecosystem: str
    ) -> List[str]:
        """Get packages that directly depend on this package."""
        if ecosystem == "pypi":
            return self._get_pypi_dependents(package)
        elif ecosystem == "npm":
            return self._get_npm_dependents(package)
        else:
            return []
    
    def _get_all_dependents(
        self,
        package: str,
        ecosystem: str,
        max_depth: int
    ) -> Set[str]:
        """Recursively get all dependents up to max_depth."""
        all_dependents = set()
        to_process = [(package, 0)]
        processed = set()
        
        while to_process:
            current_pkg, depth = to_process.pop(0)
            
            if current_pkg in processed or depth >= max_depth:
                continue
            
            processed.add(current_pkg)
            
            dependents = self._get_direct_dependents(current_pkg, ecosystem)
            for dep in dependents:
                if dep not in all_dependents:
                    all_dependents.add(dep)
                    to_process.append((dep, depth + 1))
        
        return all_dependents
    
    def _identify_critical_dependents(
        self,
        dependents: Set[str]
    ) -> List[str]:
        """Identify high-profile projects in dependents."""
        critical = []
        
        # Check GitHub stars for each dependent
        for dep in list(dependents)[:20]:  # Limit to avoid rate limits
            try:
                # Try to find GitHub repo
                repo = self._find_github_repo(dep)
                if repo:
                    stars = repo.get('stargazers_count', 0)
                    if stars > 1000:  # High-profile threshold
                        critical.append(dep)
            except Exception as e:
                logger.debug(f"Could not check {dep}: {e}")
        
        return critical
    
    def _calculate_depth_levels(
        self,
        package: str,
        ecosystem: str,
        max_depth: int
    ) -> Dict[int, List[str]]:
        """Calculate dependency depth levels."""
        depth_levels = {i: [] for i in range(max_depth + 1)}
        depth_levels[0] = [package]
        
        for depth in range(1, max_depth + 1):
            for pkg in depth_levels[depth - 1]:
                dependents = self._get_direct_dependents(pkg, ecosystem)
                depth_levels[depth].extend(dependents)
        
        return depth_levels
    
    def _get_pypi_popularity(self, package: str) -> Dict[str, Any]:
        """Get PyPI package popularity."""
        try:
            # Get from PyPI stats API (pypistats.org)
            response = requests.get(f"https://pypistats.org/api/packages/{package}/recent")
            if response.status_code == 200:
                data = response.json()
                return {
                    'downloads_last_month': data.get('data', {}).get('last_month', 0),
                    'downloads_last_week': data.get('data', {}).get('last_week', 0),
                }
        except Exception as e:
            logger.debug(f"Could not get PyPI stats: {e}")
        
        return {'downloads_last_month': 0, 'downloads_last_week': 0}
    
    def _get_npm_popularity(self, package: str) -> Dict[str, Any]:
        """Get npm package popularity."""
        try:
            response = requests.get(f"https://api.npmjs.org/downloads/point/last-month/{package}")
            if response.status_code == 200:
                data = response.json()
                return {
                    'downloads_last_month': data.get('downloads', 0)
                }
        except Exception as e:
            logger.debug(f"Could not get npm stats: {e}")
        
        return {'downloads_last_month': 0}
    
    def _build_pypi_graph(self, package: str) -> Dict[str, Any]:
        """Build dependency graph for PyPI package."""
        try:
            # Get package info from PyPI
            response = requests.get(f"https://pypi.org/pypi/{package}/json")
            response.raise_for_status()
            data = response.json()
            
            # Extract dependencies
            info = data.get('info', {})
            requires_dist = info.get('requires_dist', []) or []
            
            dependencies = {}
            for req in requires_dist:
                # Parse requirement (e.g., "requests>=2.0.0")
                dep_name = req.split('[')[0].split('>')[0].split('<')[0].split('=')[0].split('!')[0].strip()
                if dep_name:
                    dependencies[dep_name] = {'version': None}
            
            return {
                'package': package,
                'ecosystem': 'pypi',
                'version': info.get('version'),
                'dependencies': dependencies
            }
        except Exception as e:
            logger.error(f"Failed to build PyPI graph for {package}: {e}")
            return {'package': package, 'ecosystem': 'pypi', 'dependencies': {}}
    
    def _build_npm_graph(self, package: str) -> Dict[str, Any]:
        """Build dependency graph for npm package."""
        try:
            response = requests.get(f"https://registry.npmjs.org/{package}")
            response.raise_for_status()
            data = response.json()
            
            # Get latest version dependencies
            latest_version = data.get('dist-tags', {}).get('latest')
            if latest_version:
                version_data = data.get('versions', {}).get(latest_version, {})
                dependencies = version_data.get('dependencies', {})
                
                return {
                    'package': package,
                    'ecosystem': 'npm',
                    'version': latest_version,
                    'dependencies': {k: {'version': v} for k, v in dependencies.items()}
                }
        except Exception as e:
            logger.error(f"Failed to build npm graph for {package}: {e}")
        
        return {'package': package, 'ecosystem': 'npm', 'dependencies': {}}
    
    def _get_pypi_dependents(self, package: str) -> List[str]:
        """Get PyPI packages that depend on this package."""
        # Note: PyPI doesn't have a direct API for reverse dependencies
        # We would need to use libraries.io API or similar
        # For now, return empty list
        logger.warning("PyPI reverse dependencies require external API (libraries.io)")
        return []
    
    def _get_npm_dependents(self, package: str) -> List[str]:
        """Get npm packages that depend on this package."""
        # npm also doesn't have direct reverse dependency API
        logger.warning("npm reverse dependencies require external API")
        return []
    
    def _find_github_repo(self, package: str) -> Optional[Dict]:
        """Find GitHub repository for a package."""
        if not self.github_token:
            return None
        
        try:
            # Search GitHub for the package
            response = requests.get(
                f"https://api.github.com/search/repositories",
                headers=self.headers,
                params={'q': package, 'per_page': 1}
            )
            response.raise_for_status()
            
            items = response.json().get('items', [])
            if items:
                return items[0]
        except Exception as e:
            logger.debug(f"Could not find GitHub repo for {package}: {e}")
        
        return None
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()


__all__ = ['SupplyChainAnalyzer', 'ImpactAnalysis', 'DependencyNode']
