"""Collect CRITICAL CVEs for open-source projects with GitHub repositories.

Focus on CVEs that:
1. Have CRITICAL/HIGH severity (CVSS >= 7.0)
2. Affect open-source projects with GitHub repositories
3. Have sufficient historical data for backtesting
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zero_day_defense.data_sources.cve import CVEDataSource

# Known open-source projects with GitHub repos
OPENSOURCE_PROJECTS = {
    # Web Frameworks
    "django": "django/django",
    "flask": "pallets/flask",
    "fastapi": "tiangolo/fastapi",
    "express": "expressjs/express",
    "spring": "spring-projects/spring-framework",
    "struts": "apache/struts",
    
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
}


def main():
    parser = argparse.ArgumentParser(description="Collect open-source CVEs")
    parser.add_argument("--years", type=int, default=5, help="Years of CVE history")
    parser.add_argument("--min-cvss", type=float, default=7.0, help="Minimum CVSS score")
    parser.add_argument("--output", default="data/opensource_cves.jsonl", help="Output file")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Open-Source CVE Collection (GitHub Projects Only)")
    print("=" * 80)
    print()
    print(f"Parameters:")
    print(f"  Years: {args.years}")
    print(f"  Min CVSS: {args.min_cvss}")
    print(f"  Projects: {len(OPENSOURCE_PROJECTS)}")
    print(f"  Output: {args.output}")
    print()
    
    # Initialize collector
    api_key = os.getenv("NVD_API_KEY")
    collector = CVEDataSource(api_key=api_key, verify_ssl=False)
    
    cutoff = datetime.now(timezone.utc)
    
    all_cves = {}
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    for project_name, github_repo in OPENSOURCE_PROJECTS.items():
        print(f"🔍 {project_name} ({github_repo})")
        
        try:
            result = collector.collect_by_keyword(
                project_name,
                cutoff=cutoff,
                max_results=200
            )
            
            count = 0
            for vuln in result.payload.get("vulnerabilities", []):
                cve_data = vuln.get("cve", {})
                cve_id = cve_data.get("id")
                
                if not cve_id or cve_id in all_cves:
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
                        severity = cvss_data.get("baseSeverity")
                        break
                
                # Filter by score
                if cvss_score and cvss_score >= args.min_cvss:
                    all_cves[cve_id] = {
                        "cve_id": cve_id,
                        "project": project_name,
                        "github_repo": github_repo,
                        "cvss_score": cvss_score,
                        "severity": severity,
                        "published": cve_data.get("published"),
                        "description": cve_data.get("descriptions", [{}])[0].get("value", "")[:200],
                        "data": cve_data,
                    }
                    count += 1
                    print(f"   ✓ {cve_id} (CVSS: {cvss_score}, {severity})")
            
            print(f"   Found {count} CVEs for {project_name}")
            print()
            
            time.sleep(6)  # NVD rate limiting
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            print()
            continue
    
    print("=" * 80)
    print(f"📊 Collection Summary")
    print("=" * 80)
    print()
    print(f"Total CVEs: {len(all_cves)}")
    print()
    
    # Save to file
    print(f"💾 Saving to {output_path}")
    with output_path.open("w", encoding="utf-8") as f:
        for cve_data in all_cves.values():
            f.write(json.dumps(cve_data) + "\n")
    
    print(f"   ✓ Saved {len(all_cves)} CVEs")
    print()
    
    # Statistics
    if all_cves:
        cvss_scores = [c["cvss_score"] for c in all_cves.values()]
        severities = [c["severity"] for c in all_cves.values() if c.get("severity")]
        
        print("📈 Statistics:")
        print(f"   CVSS Range: {min(cvss_scores):.1f} - {max(cvss_scores):.1f}")
        print(f"   CVSS Average: {sum(cvss_scores)/len(cvss_scores):.1f}")
        print()
        
        from collections import Counter
        severity_counts = Counter(severities)
        print("   Severity Distribution:")
        for sev, count in severity_counts.most_common():
            print(f"      {sev}: {count}")
        print()
        
        project_counts = Counter(c["project"] for c in all_cves.values())
        print("   Top Projects:")
        for proj, count in project_counts.most_common(10):
            print(f"      {proj}: {count} CVEs")
        print()
    
    print("✅ Collection complete!")
    print()
    print("🚀 Next steps:")
    print("   1. Load into Neo4j:")
    print(f"      python scripts/load_cve_to_neo4j.py {args.output}")
    print()
    print("   2. Collect GitHub signals for each CVE:")
    print("      python scripts/collect_cve_signals.py")
    print()
    print("   3. Train prediction model:")
    print("      python scripts/train_prediction_model.py")
    print()

if __name__ == "__main__":
    main()
