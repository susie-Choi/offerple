"""
Package Metadata Collector - Collect package information from various ecosystems.
"""
import os
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from .base import BaseCollector


class PackageCollector(BaseCollector):
    """
    Collect package metadata from various ecosystems.
    
    Supports:
    - PyPI (Python)
    - npm (JavaScript)
    - Maven (Java)
    """
    
    def __init__(self, output_dir: str = "data/raw/packages"):
        """Initialize package collector."""
        super().__init__(output_dir)
    
    def collect(
        self,
        package_name: str,
        ecosystem: str = "pypi",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Collect package metadata.
        
        Args:
            package_name: Package name
            ecosystem: Package ecosystem (pypi, npm, maven)
        
        Returns:
            Statistics dictionary
        """
        self.logger.info(f"Collecting package metadata for {package_name} ({ecosystem})")
        
        if ecosystem.lower() == "pypi":
            data = self._collect_pypi(package_name)
        elif ecosystem.lower() == "npm":
            data = self._collect_npm(package_name)
        elif ecosystem.lower() == "maven":
            data = self._collect_maven(package_name)
        else:
            raise ValueError(f"Unsupported ecosystem: {ecosystem}")
        
        # Save to file
        output_file = self.output_dir / f"{ecosystem}_{package_name.replace('/', '_')}.jsonl"
        self._save_jsonl([data], output_file)
        
        return {
            'package': package_name,
            'ecosystem': ecosystem,
            'output_file': str(output_file),
        }
    
    def _collect_pypi(self, package_name: str) -> Dict[str, Any]:
        """Collect PyPI package metadata."""
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        info = data.get('info', {})
        releases = data.get('releases', {})
        
        # Get download stats from pypistats.org
        downloads = self._get_pypi_downloads(package_name)
        
        # Analyze releases
        release_dates = []
        for version, files in releases.items():
            if files:
                upload_time = files[0].get('upload_time_iso_8601')
                if upload_time:
                    release_dates.append(upload_time)
        
        return {
            'source': 'pypi',
            'package': package_name,
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'metadata': {
                'name': info.get('name'),
                'version': info.get('version'),
                'summary': info.get('summary'),
                'description': info.get('description'),
                'author': info.get('author'),
                'author_email': info.get('author_email'),
                'maintainer': info.get('maintainer'),
                'maintainer_email': info.get('maintainer_email'),
                'license': info.get('license'),
                'home_page': info.get('home_page'),
                'project_urls': info.get('project_urls', {}),
                'requires_python': info.get('requires_python'),
                'classifiers': info.get('classifiers', []),
            },
            'statistics': {
                'total_releases': len(releases),
                'latest_version': info.get('version'),
                'downloads_last_month': downloads.get('last_month', 0),
                'downloads_last_week': downloads.get('last_week', 0),
                'downloads_last_day': downloads.get('last_day', 0),
            },
            'dependencies': {
                'requires_dist': info.get('requires_dist', []),
            },
            'releases': release_dates[:10],  # Last 10 releases
        }
    
    def _get_pypi_downloads(self, package_name: str) -> Dict[str, int]:
        """Get PyPI download statistics."""
        try:
            url = f"https://pypistats.org/api/packages/{package_name}/recent"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return {
                'last_day': data.get('data', {}).get('last_day', 0),
                'last_week': data.get('data', {}).get('last_week', 0),
                'last_month': data.get('data', {}).get('last_month', 0),
            }
        except Exception as e:
            self.logger.warning(f"Could not fetch download stats: {e}")
            return {'last_day': 0, 'last_week': 0, 'last_month': 0}
    
    def _collect_npm(self, package_name: str) -> Dict[str, Any]:
        """Collect npm package metadata."""
        url = f"https://registry.npmjs.org/{package_name}"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        latest_version = data.get('dist-tags', {}).get('latest')
        latest_info = data.get('versions', {}).get(latest_version, {})
        
        # Get download stats
        downloads = self._get_npm_downloads(package_name)
        
        return {
            'source': 'npm',
            'package': package_name,
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'metadata': {
                'name': data.get('name'),
                'version': latest_version,
                'description': latest_info.get('description'),
                'author': latest_info.get('author'),
                'maintainers': data.get('maintainers', []),
                'license': latest_info.get('license'),
                'homepage': latest_info.get('homepage'),
                'repository': latest_info.get('repository'),
                'keywords': latest_info.get('keywords', []),
            },
            'statistics': {
                'total_releases': len(data.get('versions', {})),
                'latest_version': latest_version,
                'downloads_last_month': downloads.get('downloads', 0),
            },
            'dependencies': {
                'dependencies': latest_info.get('dependencies', {}),
                'devDependencies': latest_info.get('devDependencies', {}),
                'peerDependencies': latest_info.get('peerDependencies', {}),
            },
            'time': data.get('time', {}),
        }
    
    def _get_npm_downloads(self, package_name: str) -> Dict[str, int]:
        """Get npm download statistics."""
        try:
            url = f"https://api.npmjs.org/downloads/point/last-month/{package_name}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return {'downloads': data.get('downloads', 0)}
        except Exception as e:
            self.logger.warning(f"Could not fetch download stats: {e}")
            return {'downloads': 0}
    
    def _collect_maven(self, package_name: str) -> Dict[str, Any]:
        """
        Collect Maven package metadata.
        
        Args:
            package_name: In format "groupId:artifactId"
        """
        if ':' not in package_name:
            raise ValueError("Maven package must be in format 'groupId:artifactId'")
        
        group_id, artifact_id = package_name.split(':', 1)
        
        # Search Maven Central
        url = "https://search.maven.org/solrsearch/select"
        params = {
            'q': f'g:"{group_id}" AND a:"{artifact_id}"',
            'rows': 1,
            'wt': 'json'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        docs = data.get('response', {}).get('docs', [])
        
        if not docs:
            raise ValueError(f"Package not found: {package_name}")
        
        doc = docs[0]
        
        return {
            'source': 'maven',
            'package': package_name,
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'metadata': {
                'group_id': doc.get('g'),
                'artifact_id': doc.get('a'),
                'version': doc.get('latestVersion'),
                'packaging': doc.get('p'),
                'timestamp': doc.get('timestamp'),
            },
            'statistics': {
                'total_releases': doc.get('versionCount', 0),
                'latest_version': doc.get('latestVersion'),
            },
            'repository': {
                'repository_id': doc.get('repositoryId'),
            },
        }


class DependencyCollector(BaseCollector):
    """
    Collect dependency information for packages.
    
    Builds dependency graphs for vulnerability analysis.
    """
    
    def __init__(self, output_dir: str = "data/raw/dependencies"):
        """Initialize dependency collector."""
        super().__init__(output_dir)
    
    def collect(
        self,
        package_name: str,
        ecosystem: str = "pypi",
        depth: int = 2,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Collect dependency tree.
        
        Args:
            package_name: Package name
            ecosystem: Package ecosystem
            depth: Dependency depth to traverse
        
        Returns:
            Statistics dictionary
        """
        self.logger.info(f"Collecting dependencies for {package_name} ({ecosystem}, depth={depth})")
        
        if ecosystem.lower() == "pypi":
            deps = self._collect_pypi_dependencies(package_name, depth)
        elif ecosystem.lower() == "npm":
            deps = self._collect_npm_dependencies(package_name, depth)
        else:
            raise ValueError(f"Unsupported ecosystem: {ecosystem}")
        
        # Save to file
        output_file = self.output_dir / f"{ecosystem}_{package_name.replace('/', '_')}_deps.jsonl"
        self._save_jsonl([deps], output_file)
        
        return {
            'package': package_name,
            'ecosystem': ecosystem,
            'total_dependencies': len(deps.get('dependencies', [])),
            'output_file': str(output_file),
        }
    
    def _collect_pypi_dependencies(self, package_name: str, depth: int) -> Dict[str, Any]:
        """Collect PyPI dependencies recursively."""
        visited = set()
        dependencies = []
        
        def collect_recursive(pkg: str, current_depth: int):
            if current_depth > depth or pkg in visited:
                return
            
            visited.add(pkg)
            
            try:
                url = f"https://pypi.org/pypi/{pkg}/json"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                
                data = response.json()
                requires = data.get('info', {}).get('requires_dist', [])
                
                if requires:
                    for req in requires:
                        # Parse requirement (e.g., "requests>=2.0.0")
                        dep_name = req.split('[')[0].split(';')[0].split('>=')[0].split('==')[0].split('<')[0].strip()
                        
                        dependencies.append({
                            'from': pkg,
                            'to': dep_name,
                            'requirement': req,
                            'depth': current_depth,
                        })
                        
                        # Recurse
                        if current_depth < depth:
                            collect_recursive(dep_name, current_depth + 1)
            
            except Exception as e:
                self.logger.warning(f"Could not fetch dependencies for {pkg}: {e}")
        
        collect_recursive(package_name, 0)
        
        return {
            'source': 'pypi',
            'package': package_name,
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'depth': depth,
            'dependencies': dependencies,
            'total_packages': len(visited),
        }
    
    def _collect_npm_dependencies(self, package_name: str, depth: int) -> Dict[str, Any]:
        """Collect npm dependencies recursively."""
        visited = set()
        dependencies = []
        
        def collect_recursive(pkg: str, current_depth: int):
            if current_depth > depth or pkg in visited:
                return
            
            visited.add(pkg)
            
            try:
                url = f"https://registry.npmjs.org/{pkg}"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                
                data = response.json()
                latest_version = data.get('dist-tags', {}).get('latest')
                latest_info = data.get('versions', {}).get(latest_version, {})
                
                deps = latest_info.get('dependencies', {})
                
                for dep_name, version in deps.items():
                    dependencies.append({
                        'from': pkg,
                        'to': dep_name,
                        'version': version,
                        'depth': current_depth,
                    })
                    
                    # Recurse
                    if current_depth < depth:
                        collect_recursive(dep_name, current_depth + 1)
            
            except Exception as e:
                self.logger.warning(f"Could not fetch dependencies for {pkg}: {e}")
        
        collect_recursive(package_name, 0)
        
        return {
            'source': 'npm',
            'package': package_name,
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'depth': depth,
            'dependencies': dependencies,
            'total_packages': len(visited),
        }
