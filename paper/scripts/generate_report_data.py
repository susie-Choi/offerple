"""Generate detailed statistics and visualizations for midterm report."""
import os
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase
from collections import defaultdict

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def generate_report_data():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    report_data = {}
    
    with driver.session() as session:
        # 1. Overall Statistics
        print("=" * 80)
        print("1. Overall Database Statistics")
        print("=" * 80)
        
        stats = {}
        result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY count DESC")
        for record in result:
            label = record['label']
            count = record['count']
            stats[label] = count
            print(f"  {label}: {count:,}")
        
        report_data['node_counts'] = stats
        
        # 2. Top CWEs by CVE count
        print("\n" + "=" * 80)
        print("2. Top 10 CWEs by CVE Count")
        print("=" * 80)
        
        result = session.run("""
            MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
            RETURN cwe.id as cwe_id, cwe.name as cwe_name, count(cve) as cve_count
            ORDER BY cve_count DESC
            LIMIT 10
        """)
        
        top_cwes = []
        for record in result:
            cwe_data = {
                'id': record['cwe_id'],
                'name': record['cwe_name'],
                'count': record['cve_count']
            }
            top_cwes.append(cwe_data)
            print(f"  {record['cwe_id']}: {record['cwe_name']} ({record['cve_count']} CVEs)")
        
        report_data['top_cwes'] = top_cwes
        
        # 3. CVE Severity Distribution
        print("\n" + "=" * 80)
        print("3. CVE Severity Distribution (CVSS v3)")
        print("=" * 80)
        
        result = session.run("""
            MATCH (cve:CVE)
            WHERE cve.cvss_v3_score IS NOT NULL
            WITH cve,
                 CASE
                   WHEN cve.cvss_v3_score >= 9.0 THEN 'CRITICAL'
                   WHEN cve.cvss_v3_score >= 7.0 THEN 'HIGH'
                   WHEN cve.cvss_v3_score >= 4.0 THEN 'MEDIUM'
                   ELSE 'LOW'
                 END as severity
            RETURN severity, count(*) as count
            ORDER BY 
                CASE severity
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'MEDIUM' THEN 3
                    WHEN 'LOW' THEN 4
                END
        """)
        
        severity_dist = {}
        for record in result:
            severity = record['severity']
            count = record['count']
            severity_dist[severity] = count
            print(f"  {severity}: {count}")
        
        report_data['severity_distribution'] = severity_dist
        
        # 4. Top Affected Products
        print("\n" + "=" * 80)
        print("4. Top 10 Most Affected Products")
        print("=" * 80)
        
        result = session.run("""
            MATCH (cve:CVE)-[:AFFECTS]->(prod:Product)
            RETURN prod.name as product, count(cve) as cve_count
            ORDER BY cve_count DESC
            LIMIT 10
        """)
        
        top_products = []
        for record in result:
            prod_data = {
                'name': record['product'],
                'cve_count': record['cve_count']
            }
            top_products.append(prod_data)
            print(f"  {record['product']}: {record['cve_count']} CVEs")
        
        report_data['top_products'] = top_products
        
        # 5. KEV Statistics
        print("\n" + "=" * 80)
        print("5. Known Exploited Vulnerabilities (KEV) Statistics")
        print("=" * 80)
        
        result = session.run("""
            MATCH (kev:KEV)
            RETURN count(kev) as total_kev
        """)
        total_kev = result.single()['total_kev']
        print(f"  Total KEV entries: {total_kev:,}")
        
        result = session.run("""
            MATCH (cve:CVE)-[:HAS_KEV]->(kev:KEV)
            RETURN count(DISTINCT cve) as cves_with_kev
        """)
        cves_with_kev = result.single()['cves_with_kev']
        print(f"  CVEs with KEV: {cves_with_kev}")
        
        report_data['kev_stats'] = {
            'total_kev': total_kev,
            'cves_with_kev': cves_with_kev
        }
        
        # 6. Package Dependencies
        print("\n" + "=" * 80)
        print("6. Package Dependency Statistics")
        print("=" * 80)
        
        result = session.run("""
            MATCH (p:Package)
            RETURN count(p) as total_packages
        """)
        total_packages = result.single()['total_packages']
        print(f"  Total packages: {total_packages}")
        
        result = session.run("""
            MATCH (p1:Package)-[:DEPENDS_ON]->(p2:Package)
            RETURN count(*) as total_dependencies
        """)
        total_deps = result.single()['total_dependencies']
        print(f"  Total dependencies: {total_deps}")
        
        result = session.run("""
            MATCH (p:Package)
            OPTIONAL MATCH (p)-[:DEPENDS_ON]->(dep:Package)
            RETURN p.name as package, count(dep) as dep_count
            ORDER BY dep_count DESC
            LIMIT 5
        """)
        
        print("\n  Top packages by dependency count:")
        for record in result:
            print(f"    {record['package']}: {record['dep_count']} dependencies")
        
        report_data['package_stats'] = {
            'total_packages': total_packages,
            'total_dependencies': total_deps
        }
        
        # 7. Exploit Statistics
        print("\n" + "=" * 80)
        print("7. Exploit Statistics")
        print("=" * 80)
        
        result = session.run("""
            MATCH (e:Exploit)
            RETURN count(e) as total_exploits
        """)
        total_exploits = result.single()['total_exploits']
        print(f"  Total exploits: {total_exploits}")
        
        result = session.run("""
            MATCH (cve:CVE)-[:HAS_EXPLOIT]->(e:Exploit)
            RETURN count(DISTINCT cve) as cves_with_exploits
        """)
        cves_with_exploits = result.single()['cves_with_exploits']
        print(f"  CVEs with exploits: {cves_with_exploits}")
        
        report_data['exploit_stats'] = {
            'total_exploits': total_exploits,
            'cves_with_exploits': cves_with_exploits
        }
        
        # 8. Sample CVE with full context
        print("\n" + "=" * 80)
        print("8. Sample CVE with Full Context (for RAG demonstration)")
        print("=" * 80)
        
        result = session.run("""
            MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
            WHERE cve.cvss_v3_score IS NOT NULL
            OPTIONAL MATCH (cve)-[:HAS_KEV]->(kev:KEV)
            OPTIONAL MATCH (cve)-[:HAS_EXPLOIT]->(exp:Exploit)
            RETURN cve.id as cve_id, cve.description as description,
                   cve.cvss_v3_score as cvss_score,
                   collect(DISTINCT cwe.id) as cwes,
                   count(DISTINCT kev) as has_kev,
                   count(DISTINCT exp) as exploit_count
            ORDER BY cve.cvss_v3_score DESC
            LIMIT 3
        """)
        
        sample_cves = []
        for record in result:
            cve_data = {
                'id': record['cve_id'],
                'description': record['description'][:200] + '...' if len(record['description']) > 200 else record['description'],
                'cvss_score': record['cvss_score'],
                'cwes': record['cwes'],
                'has_kev': record['has_kev'] > 0,
                'exploit_count': record['exploit_count']
            }
            sample_cves.append(cve_data)
            print(f"\n  {record['cve_id']} (CVSS: {record['cvss_score']})")
            print(f"    CWEs: {', '.join(record['cwes'])}")
            print(f"    KEV: {'Yes' if record['has_kev'] > 0 else 'No'}")
            print(f"    Exploits: {record['exploit_count']}")
            print(f"    Description: {cve_data['description']}")
        
        report_data['sample_cves'] = sample_cves
    
    driver.close()
    
    # Save to JSON
    output_file = 'docs/report_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"✅ Report data saved to: {output_file}")
    print("=" * 80)
    
    return report_data

if __name__ == "__main__":
    generate_report_data()
