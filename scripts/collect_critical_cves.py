"""Collect CRITICAL severity CVEs for training.

This script collects high-severity CVEs to build a robust training dataset.
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

def main():
    parser = argparse.ArgumentParser(description="Collect critical CVEs")
    parser.add_argument("--years", type=int, default=3, help="Years of CVE history")
    parser.add_argument("--min-cvss", type=float, default=9.0, help="Minimum CVSS score")
    parser.add_argument("--output", default="data/critical_cves.jsonl", help="Output file")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Critical CVE Collection")
    print("=" * 80)
    print()
    print(f"Parameters:")
    print(f"  Years: {args.years}")
    print(f"  Min CVSS: {args.min_cvss}")
    print(f"  Output: {args.output}")
    print()
    
    # Initialize collector
    api_key = os.getenv("NVD_API_KEY")
    collector = CVEDataSource(api_key=api_key, verify_ssl=False)
    
    # Time range
    cutoff = datetime.now(timezone.utc)
    start_date = cutoff - timedelta(days=365 * args.years)
    
    print(f"📡 Collecting CVEs from {start_date.strftime('%Y-%m-%d')} to {cutoff.strftime('%Y-%m-%d')}")
    print()
    
    # Collect by keywords for major projects
    keywords = [
        "apache", "log4j", "spring", "struts",
        "openssl", "heartbleed",
        "linux", "kernel",
        "windows", "microsoft",
        "java", "jdk",
        "python", "django", "flask",
        "node", "npm", "express",
        "docker", "kubernetes",
        "postgresql", "mysql", "mongodb",
        "redis", "elasticsearch",
    ]
    
    all_cves = {}
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    for keyword in keywords:
        print(f"🔍 Searching: {keyword}")
        try:
            result = collector.collect_by_keyword(
                keyword,
                cutoff=cutoff,
                max_results=100
            )
            
            # Filter by CVSS score
            for vuln in result.payload.get("vulnerabilities", []):
                cve_data = vuln.get("cve", {})
                cve_id = cve_data.get("id")
                
                if not cve_id or cve_id in all_cves:
                    continue
                
                # Get CVSS score
                metrics = cve_data.get("metrics", {})
                cvss_score = None
                
                for metric_type in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                    metric_list = metrics.get(metric_type, [])
                    if metric_list:
                        cvss_score = metric_list[0].get("cvssData", {}).get("baseScore")
                        break
                
                # Filter by score
                if cvss_score and cvss_score >= args.min_cvss:
                    all_cves[cve_id] = {
                        "cve_id": cve_id,
                        "cvss_score": cvss_score,
                        "published": cve_data.get("published"),
                        "description": cve_data.get("descriptions", [{}])[0].get("value", ""),
                        "data": cve_data,
                    }
                    print(f"   ✓ {cve_id} (CVSS: {cvss_score})")
            
            time.sleep(6)  # Rate limiting
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            continue
    
    print()
    print(f"📊 Summary:")
    print(f"   Total Critical CVEs: {len(all_cves)}")
    print()
    
    # Save to file
    print(f"💾 Saving to {output_path}")
    with output_path.open("w", encoding="utf-8") as f:
        for cve_data in all_cves.values():
            f.write(json.dumps(cve_data) + "\n")
    
    print(f"   ✓ Saved {len(all_cves)} CVEs")
    print()
    
    # Statistics
    cvss_scores = [c["cvss_score"] for c in all_cves.values()]
    if cvss_scores:
        print("📈 CVSS Score Distribution:")
        print(f"   Min: {min(cvss_scores):.1f}")
        print(f"   Max: {max(cvss_scores):.1f}")
        print(f"   Avg: {sum(cvss_scores)/len(cvss_scores):.1f}")
        print()
    
    print("✅ Collection complete!")
    print()
    print("Next steps:")
    print("  1. Load CVEs into Neo4j: python scripts/load_cve_to_neo4j.py data/critical_cves.jsonl")
    print("  2. Collect GitHub signals for affected repositories")
    print("  3. Train prediction model")
    print()

if __name__ == "__main__":
    main()
