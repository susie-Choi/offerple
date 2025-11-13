"""
Check the actual temporal coverage of collected CVE data.
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

print("=" * 80)
print("CVE Data Temporal Coverage Analysis")
print("=" * 80)

with driver.session() as session:
    # Overall year distribution
    result = session.run("""
        MATCH (cve:CVE)
        WHERE cve.published IS NOT NULL
        WITH cve, datetime(cve.published).year as year
        RETURN year, COUNT(*) as count
        ORDER BY year DESC
    """)
    
    print("\nAll CVEs by Year:")
    print("-" * 80)
    
    year_data = list(result)
    total = sum(r['count'] for r in year_data)
    
    for record in year_data:
        year = record['year']
        count = record['count']
        pct = count / total * 100
        bar = "#" * int(pct / 2)
        print(f"{year}: {count:>5} ({pct:>5.1f}%) {bar}")
    
    print(f"\nTotal: {total:,} CVEs")
    
    # CVEs with CWE by year
    print("\n" + "=" * 80)
    print("CVEs with CWE by Year")
    print("=" * 80)
    
    result = session.run("""
        MATCH (cve:CVE)-[:HAS_WEAKNESS]->(:CWE)
        WHERE cve.published IS NOT NULL
        WITH cve, datetime(cve.published).year as year
        RETURN year, COUNT(DISTINCT cve) as count
        ORDER BY year DESC
    """)
    
    cwe_year_data = list(result)
    cwe_total = sum(r['count'] for r in cwe_year_data)
    
    for record in cwe_year_data:
        year = record['year']
        count = record['count']
        pct = count / cwe_total * 100
        bar = "#" * int(pct / 2)
        print(f"{year}: {count:>5} ({pct:>5.1f}%) {bar}")
    
    print(f"\nTotal with CWE: {cwe_total:,} CVEs")
    
    # Check if there's a collection bias
    print("\n" + "=" * 80)
    print("CWE Coverage Rate by Year")
    print("=" * 80)
    
    year_dict = {r['year']: r['count'] for r in year_data}
    cwe_year_dict = {r['year']: r['count'] for r in cwe_year_data}
    
    print(f"\n{'Year':<6} {'Total CVEs':<12} {'With CWE':<12} {'Coverage %'}")
    print("-" * 80)
    
    for year in sorted(year_dict.keys(), reverse=True):
        total_cves = year_dict[year]
        cwe_cves = cwe_year_dict.get(year, 0)
        coverage = cwe_cves / total_cves * 100 if total_cves > 0 else 0
        print(f"{year:<6} {total_cves:<12,} {cwe_cves:<12,} {coverage:>6.1f}%")
    
    # Check recent years specifically
    print("\n" + "=" * 80)
    print("Recent Years (2020-2025)")
    print("=" * 80)
    
    result = session.run("""
        MATCH (cve:CVE)
        WHERE cve.published IS NOT NULL
        WITH cve, datetime(cve.published).year as year
        WHERE year >= 2020
        RETURN year, COUNT(*) as total,
               SUM(CASE WHEN EXISTS((cve)-[:HAS_WEAKNESS]->(:CWE)) THEN 1 ELSE 0 END) as with_cwe
        ORDER BY year DESC
    """)
    
    print(f"\n{'Year':<6} {'Total':<8} {'With CWE':<10} {'Coverage'}")
    print("-" * 80)
    
    for record in result:
        year = record['year']
        total = record['total']
        with_cwe = record['with_cwe']
        coverage = with_cwe / total * 100 if total > 0 else 0
        print(f"{year:<6} {total:<8} {with_cwe:<10} {coverage:>6.1f}%")

driver.close()

print("\n" + "=" * 80)
print("Conclusion:")
print("=" * 80)
print("If 2017-2020 has much higher coverage than 2021-2025,")
print("then the temporal trend is a data collection artifact.")
print("=" * 80)
