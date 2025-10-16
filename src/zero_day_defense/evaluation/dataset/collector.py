"""Dataset collector for paper experiments."""
from __future__ import annotations

import json
import logging
import os
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from tqdm import tqdm

from ...data_sources.cve import CVEDataSource
from ...data_sources.github_advisory import GitHubAdvisoryDataSource


logger = logging.getLogger(__name__)


# Known open-source projects with GitHub repositories
OPENSOURCE_PROJECTS = {
    # Web Frameworks
    "django": "django/django",
    "flask": "pallets/flask",
    "fastapi": "tiangolo/fastapi",
    "express": "expressjs/express",
    "spring": "spring-projects/spring-framework",
    "struts": "apache/struts",
    "rails": "rails/rails",
    
    # Logging & Monitoring
    "log4j": "apache/logging-log4j2",
    "logback": "qos-ch/logback",
    
    # Security & Crypto
    "openssl": "openssl/openssl",
    "bouncycastle": "bcgit/bc-java",
    
    # Databases
    "postgresql": "postgres/postgres",
    "mysql": "mysql/mysql-server",
    "mongodb": "mongodb/mongo",
    "redis": "redis/redis",
    
    # Container & Orchestration
    "docker": "moby/moby",
    "kubernetes": "kubernetes/kubernetes",
    
    # Languages & Runtimes
    "python": "python/cpython",
    "node": "nodejs/node",
    "ruby": "ruby/ruby",
    
    # Package Managers
    "npm": "npm/cli",
    "pip": "pypa/pip",
    "maven": "apache/maven",
    
    # Web Servers
    "nginx": "nginx/nginx",
    "apache": "apache/httpd",
    "tomcat": "apache/tomcat",
    
    # Libraries
    "jackson": "FasterXML/jackson-databind",
    "gson": "google/gson",
    "requests": "psf/requests",
    "axios": "axios/axios",
    "lodash": "lodash/lodash",
    "moment": "moment/moment",
    
    # Additional high-profile projects
    "jenkins": "jenkinsci/jenkins",
    "elasticsearch": "elastic/elasticsearch",
    "kafka": "apache/kafka",
    "spark": "apache/spark",
    "hadoop": "apache/hadoop",
    "tensorflow": "tensorflow/tensorflow",
    "pytorch": "pytorch/pytorch",
    "react": "facebook/react",
    "vue": "vuejs/vue",
    "angular": "angular/angular",
}


class PaperDatasetCollector:
    """Collect large-scale CVE dataset for paper experiments.
    
    This collector focuses on:
    1. CVEs with GitHub repositories (for signal collection)
    2. High-severity CVEs (CVSS >= 7.0)
    3. Diverse projects and vulnerability types
    4. Sufficient historical data for validation
    """
    
    def __init__(
        self,
        *,
        min_cvss: float = 7.0,
        min_cves: int = 100,
        years: int = 5,
        nvd_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
    ):
        """Initialize dataset collector.
        
        Args:
            min_cvss: Minimum CVSS score (default: 7.0)
            min_cves: Minimum number of CVEs to collect (default: 100)
            years: Years of history to collect (default: 5)
            nvd_api_key: NVD API key for faster collection
            github_token: GitHub token for API access
        """
        self.min_cvss = min_cvss
        self.min_cves = min_cves
        self.years = years
        
        self.nvd_api_key = nvd_api_key or os.getenv("NVD_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        
        self.cve_source = CVEDataSource(
            api_key=self.nvd_api_key,
            verify_ssl=False,
        )
        
        self.github_source = GitHubAdvisoryDataSource(
            github_token=self.github_token,
        )
    
    def collect(
        self,
        output_file: Path,
        projects: Optional[Dict[str, str]] = None,
    ) -> List[Dict]:
        """Collect CVE dataset.
        
        Args:
            output_file: Path to save collected dataset
            projects: Optional dict of project_name -> github_repo
                     (default: use OPENSOURCE_PROJECTS)
        
        Returns:
            List of CVE records
        """
        if projects is None:
            projects = OPENSOURCE_PROJECTS
        
        logger.info("=" * 80)
        logger.info("Paper Dataset Collection")
        logger.info("=" * 80)
        logger.info(f"Target CVEs: {self.min_cves}+")
        logger.info(f"Min CVSS: {self.min_cvss}")
        logger.info(f"Years: {self.years}")
        logger.info(f"Projects: {len(projects)}")
        logger.info("")
        
        # Use timezone-aware datetime
        cutoff = datetime.now(timezone.utc)
        all_cves = {}
        
        # Collect CVEs for each project
        for project_name, github_repo in tqdm(
            projects.items(),
            desc="Collecting CVEs",
        ):
            try:
                cves = self._collect_project_cves(
                    project_name,
                    github_repo,
                    cutoff,
                )
                
                for cve in cves:
                    cve_id = cve["cve_id"]
                    if cve_id not in all_cves:
                        all_cves[cve_id] = cve
                
                logger.info(f"  {project_name}: {len(cves)} CVEs")
                
                # Rate limiting
                time.sleep(6 if not self.nvd_api_key else 0.6)
                
            except Exception as e:
                logger.error(f"  Error collecting {project_name}: {e}")
                continue
            
            # Stop if we have enough CVEs
            if len(all_cves) >= self.min_cves:
                logger.info(f"\nReached target of {self.min_cves} CVEs")
                break
        
        # Convert to list and save
        cve_list = list(all_cves.values())
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"Collection Summary")
        logger.info("=" * 80)
        logger.info(f"Total CVEs: {len(cve_list)}")
        
        # Statistics
        if cve_list:
            cvss_scores = [c["cvss_score"] for c in cve_list if c.get("cvss_score")]
            severities = [c["severity"] for c in cve_list if c.get("severity")]
            projects_count = Counter(c["project"] for c in cve_list)
            
            logger.info(f"CVSS Range: {min(cvss_scores):.1f} - {max(cvss_scores):.1f}")
            logger.info(f"CVSS Average: {sum(cvss_scores)/len(cvss_scores):.1f}")
            logger.info("")
            
            logger.info("Severity Distribution:")
            for sev, count in Counter(severities).most_common():
                logger.info(f"  {sev}: {count}")
            logger.info("")
            
            logger.info("Top Projects:")
            for proj, count in projects_count.most_common(10):
                logger.info(f"  {proj}: {count} CVEs")
            logger.info("")
        
        # Save to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as f:
            for cve in cve_list:
                f.write(json.dumps(cve) + "\n")
        
        logger.info(f"Saved to: {output_file}")
        logger.info("")
        
        return cve_list
    
    def _collect_project_cves(
        self,
        project_name: str,
        github_repo: str,
        cutoff: datetime,
    ) -> List[Dict]:
        """Collect CVEs for a single project.
        
        Args:
            project_name: Project name (for keyword search)
            github_repo: GitHub repository (owner/repo)
            cutoff: Cutoff date for collection
        
        Returns:
            List of CVE records
        """
        cves = []
        
        try:
            result = self.cve_source.collect_by_keyword(
                project_name,
                cutoff=cutoff,
                max_results=200,
            )
            
            for vuln in result.payload.get("vulnerabilities", []):
                cve_data = vuln.get("cve", {})
                cve_id = cve_data.get("id")
                
                if not cve_id:
                    continue
                
                # Get CVSS score
                metrics = cve_data.get("metrics", {})
                cvss_score = None
                severity = None
                
                for metric_type in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                    metric_list = metrics.get(metric_type, [])
                    if metric_list:
                        cvss_data = metric_list[0].get("cvssData", {})
                        cvss_score = cvss_data.get("baseScore")
                        severity = cvss_data.get("baseSeverity") or "UNKNOWN"
                        break
                
                # Filter by CVSS score
                if not cvss_score or cvss_score < self.min_cvss:
                    continue
                
                # Get vulnerability type from CWE
                cwe_ids = self._extract_cwe_ids(cve_data)
                vuln_type = self._classify_vulnerability_type(
                    cve_data.get("descriptions", [{}])[0].get("value", ""),
                    cwe_ids,
                )
                
                # Get published date
                published = cve_data.get("published", "")
                published_date = None
                if published:
                    try:
                        published_date = datetime.fromisoformat(
                            published.replace("Z", "+00:00")
                        )
                    except:
                        pass
                
                cves.append({
                    "cve_id": cve_id,
                    "project": project_name,
                    "github_repo": github_repo,
                    "cvss_score": cvss_score,
                    "severity": severity,
                    "vulnerability_type": vuln_type,
                    "cwe_ids": cwe_ids,
                    "published": published,
                    "published_date": published_date.isoformat() if published_date else None,
                    "description": cve_data.get("descriptions", [{}])[0].get("value", "")[:500],
                    "data": cve_data,
                })
        
        except Exception as e:
            logger.error(f"Error collecting CVEs for {project_name}: {e}")
        
        return cves
    
    def _extract_cwe_ids(self, cve_data: Dict) -> List[str]:
        """Extract CWE IDs from CVE data.
        
        Args:
            cve_data: CVE data from NVD
        
        Returns:
            List of CWE IDs
        """
        cwe_ids = []
        
        weaknesses = cve_data.get("weaknesses", [])
        for weakness in weaknesses:
            for desc in weakness.get("description", []):
                cwe_id = desc.get("value", "")
                if cwe_id.startswith("CWE-"):
                    cwe_ids.append(cwe_id)
        
        return cwe_ids
    
    def _classify_vulnerability_type(
        self,
        description: str,
        cwe_ids: List[str],
    ) -> str:
        """Classify vulnerability type from description and CWE IDs.
        
        Args:
            description: CVE description
            cwe_ids: List of CWE IDs
        
        Returns:
            Vulnerability type string
        """
        desc_lower = description.lower()
        
        # RCE (Remote Code Execution)
        if any(keyword in desc_lower for keyword in [
            "remote code execution", "rce", "arbitrary code", "code injection"
        ]):
            return "RCE"
        
        # SQL Injection
        if any(keyword in desc_lower for keyword in ["sql injection", "sqli"]):
            return "SQL_INJECTION"
        
        # XSS
        if any(keyword in desc_lower for keyword in ["cross-site scripting", "xss"]):
            return "XSS"
        
        # Memory Corruption
        if any(keyword in desc_lower for keyword in [
            "buffer overflow", "memory corruption", "use after free", "heap overflow"
        ]):
            return "MEMORY_CORRUPTION"
        
        # Deserialization
        if any(keyword in desc_lower for keyword in ["deserialization", "unsafe deserialization"]):
            return "DESERIALIZATION"
        
        # Path Traversal
        if any(keyword in desc_lower for keyword in ["path traversal", "directory traversal"]):
            return "PATH_TRAVERSAL"
        
        # Authentication Bypass
        if any(keyword in desc_lower for keyword in ["authentication bypass", "auth bypass"]):
            return "AUTH_BYPASS"
        
        # Privilege Escalation
        if any(keyword in desc_lower for keyword in ["privilege escalation", "escalation of privilege"]):
            return "PRIVILEGE_ESCALATION"
        
        # CSRF
        if any(keyword in desc_lower for keyword in ["cross-site request forgery", "csrf"]):
            return "CSRF"
        
        # DoS
        if any(keyword in desc_lower for keyword in ["denial of service", "dos"]):
            return "DOS"
        
        return "OTHER"
