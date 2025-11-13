"""Analyze collected data for NLP midterm report."""
import json
from pathlib import Path
from collections import defaultdict

def analyze_data():
    print("=" * 80)
    print("Collected Data Analysis for NLP Midterm Report")
    print("=" * 80)
    
    # Analyze CVE data
    print("\n1. CVE Data Analysis")
    print("-" * 80)
    
    cve_file = Path("data/raw/bulk_cve_data.jsonl")
    if cve_file.exists():
        cve_count = 0
        severity_dist = defaultdict(int)
        cvss_scores = []
        
        with cve_file.open("r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                vulns = record.get("payload", {}).get("vulnerabilities", [])
                for vuln in vulns:
                    cve_count += 1
                    cve_data = vuln.get("cve", {})
                    metrics = cve_data.get("metrics", {})
                    
                    # Get CVSS v3 data
                    for metric_type in ["cvssMetricV31", "cvssMetricV30"]:
                        metric_list = metrics.get(metric_type, [])
                        if metric_list:
                            cvss_data = metric_list[0].get("cvssData", {})
                            severity = cvss_data.get("baseSeverity", "UNKNOWN")
                            score = cvss_data.get("baseScore", 0)
                            severity_dist[severity] += 1
                            if score:
                                cvss_scores.append(score)
                            break
        
        print(f"  Total CVEs: {cve_count:,}")
        print(f"\n  Severity Distribution:")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
            count = severity_dist[severity]
            pct = (count / cve_count * 100) if cve_count > 0 else 0
            print(f"    {severity:10s}: {count:5,} ({pct:5.1f}%)")
        
        if cvss_scores:
            avg_score = sum(cvss_scores) / len(cvss_scores)
            print(f"\n  CVSS Score Statistics:")
            print(f"    Average: {avg_score:.2f}")
            print(f"    Min: {min(cvss_scores):.1f}")
            print(f"    Max: {max(cvss_scores):.1f}")
    
    # Analyze EPSS data
    print("\n2. EPSS Data Analysis")
    print("-" * 80)
    
    epss_file = Path("data/raw/bulk_epss_data.jsonl")
    if epss_file.exists():
        epss_count = 0
        epss_scores = []
        high_epss = 0  # EPSS > 0.5
        
        with epss_file.open("r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                epss_data = record.get("payload", {}).get("epss_data", [])
                for entry in epss_data:
                    epss_count += 1
                    score = float(entry.get("epss", 0))
                    epss_scores.append(score)
                    if score > 0.5:
                        high_epss += 1
        
        print(f"  Total EPSS entries: {epss_count:,}")
        if epss_scores:
            avg_epss = sum(epss_scores) / len(epss_scores)
            print(f"  Average EPSS: {avg_epss:.4f}")
            print(f"  High EPSS (>0.5): {high_epss:,} ({high_epss/epss_count*100:.1f}%)")
    
    # Analyze KEV data
    print("\n3. KEV Data Analysis")
    print("-" * 80)
    
    kev_file = Path("data/raw/kev_catalog.jsonl")
    if kev_file.exists():
        with kev_file.open("r", encoding="utf-8") as f:
            record = json.loads(f.readline())
            kev_data = record.get("payload", {})
            vulns = kev_data.get("vulnerabilities", [])
            
            print(f"  Total KEV entries: {len(vulns):,}")
            print(f"  Catalog version: {kev_data.get('catalogVersion')}")
            print(f"  Date released: {kev_data.get('dateReleased')}")
            
            # Analyze vendors
            vendors = defaultdict(int)
            for vuln in vulns:
                vendor = vuln.get("vendorProject", "Unknown")
                vendors[vendor] += 1
            
            print(f"\n  Top 10 Vendors with KEV:")
            for vendor, count in sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"    {vendor:30s}: {count:3,}")
    
    # Analyze Exploit data
    print("\n4. Exploit Data Analysis")
    print("-" * 80)
    
    exploit_file = Path("data/raw/bulk_exploits_data.jsonl")
    if exploit_file.exists():
        exploit_count = 0
        exploit_types = defaultdict(int)
        
        with exploit_file.open("r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                exploit = record.get("payload", {}).get("exploit", {})
                if exploit:
                    exploit_count += 1
                    exploit_type = exploit.get("type", "Unknown")
                    exploit_types[exploit_type] += 1
        
        print(f"  Total Exploits: {exploit_count:,}")
        print(f"  CVEs with exploits: {exploit_count:,} / {cve_count:,} ({exploit_count/cve_count*100:.1f}%)")
        
        print(f"\n  Exploit Types:")
        for exp_type, count in sorted(exploit_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {exp_type:30s}: {count:4,}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary for NLP Report")
    print("=" * 80)
    print(f"""
수집된 데이터 통계:
- CVE: {cve_count:,}개 (CRITICAL/HIGH 중심)
- EPSS: {epss_count:,}개 (악용 가능성 점수)
- KEV: {len(vulns):,}개 (실제 악용 확인, {len(vulns)/cve_count*100:.1f}%)
- Exploit: {exploit_count:,}개 (공개 익스플로잇, {exploit_count/cve_count*100:.1f}%)

이 데이터는 Neo4j 그래프 데이터베이스에 로드되어:
1. CVE-CWE 관계 분석
2. CVE-KEV-Exploit 위험도 평가
3. RAG 기반 역사적 패턴 학습
에 활용됩니다.
    """)
    print("=" * 80)


if __name__ == "__main__":
    analyze_data()
