"""
Analyze attack patterns from CVE-CWE data in Neo4j.
"""
import os
from collections import defaultdict
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv
import json

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class AttackPatternAnalyzer:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        # Attack type categorization
        self.attack_categories = {
            "XSS": ["CWE-79", "CWE-80", "CWE-85", "CWE-87", "CWE-692"],
            "CSRF": ["CWE-352"],
            "SQLi": ["CWE-89", "CWE-564"],
            "Command Injection": ["CWE-77", "CWE-78", "CWE-88"],
            "Code Injection": ["CWE-94", "CWE-95", "CWE-96"],
            "Path Traversal": ["CWE-22", "CWE-23", "CWE-24", "CWE-25", "CWE-26", "CWE-27", 
                              "CWE-28", "CWE-29", "CWE-30", "CWE-31", "CWE-32", "CWE-33",
                              "CWE-34", "CWE-35", "CWE-36", "CWE-37", "CWE-38", "CWE-39", "CWE-40"],
            "SSRF": ["CWE-918"],
            "XXE": ["CWE-611"],
            "Deserialization": ["CWE-502"],
            "File Upload": ["CWE-434"],
            "Authentication": ["CWE-287", "CWE-288", "CWE-289"],
            "Authorization": ["CWE-285", "CWE-862", "CWE-863"],
        }
    
    def close(self):
        self.driver.close()
    
    def analyze_by_attack_type(self):
        """Analyze CVE distribution by attack type."""
        print("\n" + "=" * 80)
        print("Attack Type Analysis")
        print("=" * 80)
        
        results = {}
        
        with self.driver.session() as session:
            for attack_type, cwe_ids in self.attack_categories.items():
                # Get CVE count
                result = session.run("""
                    MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
                    WHERE cwe.id IN $cwe_ids
                    RETURN COUNT(DISTINCT cve) as count
                """, cwe_ids=cwe_ids)
                
                count = result.single()['count']
                
                if count > 0:
                    # Get severity distribution
                    severity_result = session.run("""
                        MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
                        WHERE cwe.id IN $cwe_ids AND cve.cvssSeverity IS NOT NULL
                        RETURN cve.cvssSeverity as severity, COUNT(*) as count
                        ORDER BY count DESC
                    """, cwe_ids=cwe_ids)
                    
                    severities = {r['severity']: r['count'] for r in severity_result}
                    
                    # Get KEV count
                    kev_result = session.run("""
                        MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
                        WHERE cwe.id IN $cwe_ids AND cve.kev_listed = true
                        RETURN COUNT(DISTINCT cve) as count
                    """, cwe_ids=cwe_ids)
                    
                    kev_count = kev_result.single()['count']
                    
                    # Get average EPSS score
                    epss_result = session.run("""
                        MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
                        WHERE cwe.id IN $cwe_ids AND cve.epss_score IS NOT NULL
                        RETURN AVG(cve.epss_score) as avg_epss, 
                               MAX(cve.epss_score) as max_epss,
                               COUNT(*) as count_with_epss
                    """, cwe_ids=cwe_ids)
                    
                    epss_data = epss_result.single()
                    
                    results[attack_type] = {
                        'total': count,
                        'severities': severities,
                        'kev_count': kev_count,
                        'avg_epss': epss_data['avg_epss'],
                        'max_epss': epss_data['max_epss'],
                        'count_with_epss': epss_data['count_with_epss']
                    }
        
        # Print results
        print(f"\n{'Attack Type':<20} {'Total':<8} {'KEV':<6} {'Avg EPSS':<10} {'Top Severity'}")
        print("-" * 80)
        
        for attack_type in sorted(results.keys(), key=lambda x: results[x]['total'], reverse=True):
            data = results[attack_type]
            top_severity = max(data['severities'].items(), key=lambda x: x[1])[0] if data['severities'] else 'N/A'
            avg_epss = f"{data['avg_epss']:.4f}" if data['avg_epss'] else "N/A"
            
            print(f"{attack_type:<20} {data['total']:<8} {data['kev_count']:<6} {avg_epss:<10} {top_severity}")
        
        return results
    
    def analyze_temporal_trends(self):
        """Analyze temporal trends by attack type."""
        print("\n" + "=" * 80)
        print("Temporal Trends (by Year)")
        print("=" * 80)
        
        with self.driver.session() as session:
            for attack_type, cwe_ids in self.attack_categories.items():
                result = session.run("""
                    MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
                    WHERE cwe.id IN $cwe_ids AND cve.published IS NOT NULL
                    WITH cve, datetime(cve.published).year as year
                    RETURN year, COUNT(*) as count
                    ORDER BY year DESC
                    LIMIT 10
                """, cwe_ids=cwe_ids)
                
                trends = list(result)
                
                if trends:
                    print(f"\n{attack_type}:")
                    for record in trends:
                        year = record['year']
                        count = record['count']
                        bar = "#" * (count // 5)
                        print(f"  {year}: {count:>4} {bar}")
    
    def analyze_top_cves_by_type(self, attack_type, limit=10):
        """Get top CVEs for a specific attack type."""
        print("\n" + "=" * 80)
        print(f"Top {limit} {attack_type} CVEs (by CVSS Score)")
        print("=" * 80)
        
        cwe_ids = self.attack_categories.get(attack_type, [])
        
        if not cwe_ids:
            print(f"Unknown attack type: {attack_type}")
            return
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
                WHERE cwe.id IN $cwe_ids AND cve.cvssScore IS NOT NULL
                RETURN cve.id as cve_id,
                       cve.cvssScore as score,
                       cve.cvssSeverity as severity,
                       cve.description as description,
                       cve.published as published,
                       cve.kev_listed as kev,
                       cve.epss_score as epss
                ORDER BY cve.cvssScore DESC
                LIMIT $limit
            """, cwe_ids=cwe_ids, limit=limit)
            
            print(f"\n{'CVE ID':<20} {'Score':<7} {'Severity':<10} {'KEV':<5} {'EPSS':<8} {'Year'}")
            print("-" * 80)
            
            for record in result:
                cve_id = record['cve_id']
                score = record['score']
                severity = record['severity'] or 'N/A'
                kev = 'Y' if record['kev'] else ''
                epss = f"{record['epss']:.4f}" if record['epss'] else 'N/A'
                
                # Extract year from published date
                try:
                    year = datetime.fromisoformat(record['published'].replace('Z', '+00:00')).year
                except:
                    year = 'N/A'
                
                print(f"{cve_id:<20} {score:<7.1f} {severity:<10} {kev:<5} {epss:<8} {year}")
                
                # Print description (truncated)
                desc = record['description']
                if desc:
                    desc_short = desc[:100] + "..." if len(desc) > 100 else desc
                    print(f"  > {desc_short}\n")
    
    def analyze_cwe_combinations(self):
        """Analyze common CWE combinations in CVEs."""
        print("\n" + "=" * 80)
        print("Common CWE Combinations")
        print("=" * 80)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
                WITH cve, COLLECT(cwe.id) as cwe_list
                WHERE SIZE(cwe_list) > 1
                RETURN cwe_list, COUNT(*) as count
                ORDER BY count DESC
                LIMIT 20
            """)
            
            print(f"\n{'CWE Combination':<60} {'Count'}")
            print("-" * 80)
            
            for record in result:
                cwe_list = sorted(record['cwe_list'])
                count = record['count']
                cwe_str = ", ".join(cwe_list)
                print(f"{cwe_str:<60} {count}")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        print("\n" + "=" * 80)
        print("ATTACK PATTERN ANALYSIS SUMMARY")
        print("=" * 80)
        
        # Collect all data
        report_lines = []
        report_lines.append("# Attack Pattern Analysis Report")
        report_lines.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        with self.driver.session() as session:
            # Overall statistics
            total_cves = session.run("MATCH (c:CVE) RETURN COUNT(c) as count").single()['count']
            cves_with_cwe = session.run("""
                MATCH (c:CVE)-[:HAS_WEAKNESS]->(:CWE) 
                RETURN COUNT(DISTINCT c) as count
            """).single()['count']
            
            total_kev = session.run("""
                MATCH (c:CVE) WHERE c.kev_listed = true 
                RETURN COUNT(c) as count
            """).single()['count']
            
            print(f"\nOverall Statistics:")
            print(f"  Total CVEs: {total_cves:,}")
            print(f"  CVEs with CWE: {cves_with_cwe:,} ({cves_with_cwe/total_cves*100:.1f}%)")
            print(f"  CVEs in KEV: {total_kev:,}")
            
            report_lines.append("## Overall Statistics\n")
            report_lines.append(f"- **Total CVEs**: {total_cves:,}")
            report_lines.append(f"- **CVEs with CWE**: {cves_with_cwe:,} ({cves_with_cwe/total_cves*100:.1f}%)")
            report_lines.append(f"- **CVEs in KEV**: {total_kev:,}\n")
        
        # Attack type analysis
        attack_results = self.analyze_by_attack_type()
        
        report_lines.append("## Attack Type Distribution\n")
        report_lines.append("| Attack Type | Total CVEs | KEV Listed | Avg EPSS | Top Severity |")
        report_lines.append("|-------------|------------|------------|----------|--------------|")
        
        for attack_type in sorted(attack_results.keys(), key=lambda x: attack_results[x]['total'], reverse=True):
            data = attack_results[attack_type]
            top_severity = max(data['severities'].items(), key=lambda x: x[1])[0] if data['severities'] else 'N/A'
            avg_epss = f"{data['avg_epss']:.4f}" if data['avg_epss'] else "N/A"
            report_lines.append(f"| {attack_type} | {data['total']} | {data['kev_count']} | {avg_epss} | {top_severity} |")
        
        report_lines.append("")
        
        # Temporal trends
        self.analyze_temporal_trends()
        
        # CWE combinations
        self.analyze_cwe_combinations()
        
        # Save JSON
        output_json = "data/analysis/attack_pattern_summary.json"
        os.makedirs("data/analysis", exist_ok=True)
        
        with open(output_json, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_cves': total_cves,
                'cves_with_cwe': cves_with_cwe,
                'total_kev': total_kev,
                'attack_types': attack_results
            }, f, indent=2)
        
        # Save Markdown
        output_md = "paper/analysis/ATTACK_PATTERNS.md"
        os.makedirs("paper/analysis", exist_ok=True)
        
        with open(output_md, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"\n[OK] JSON summary saved to: {output_json}")
        print(f"[OK] Markdown report saved to: {output_md}")
        
        return attack_results


def main():
    analyzer = AttackPatternAnalyzer()
    
    try:
        # Generate full report
        attack_results = analyzer.generate_summary_report()
        
        # Detailed analysis for top attack types
        print("\n" + "=" * 80)
        print("DETAILED ANALYSIS")
        print("=" * 80)
        
        detailed_report = []
        detailed_report.append("# Detailed Attack Pattern Analysis\n")
        detailed_report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for attack_type in ["SQLi", "XSS", "Command Injection", "Path Traversal", "SSRF", "Deserialization"]:
            analyzer.analyze_top_cves_by_type(attack_type, limit=5)
            
            # Add to detailed report
            detailed_report.append(f"\n## Top {attack_type} CVEs\n")
            
            cwe_ids = analyzer.attack_categories.get(attack_type, [])
            with analyzer.driver.session() as session:
                result = session.run("""
                    MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
                    WHERE cwe.id IN $cwe_ids AND cve.cvssScore IS NOT NULL
                    RETURN cve.id as cve_id,
                           cve.cvssScore as score,
                           cve.cvssSeverity as severity,
                           cve.description as description,
                           cve.published as published,
                           cve.kev_listed as kev,
                           cve.epss_score as epss
                    ORDER BY cve.cvssScore DESC
                    LIMIT 5
                """, cwe_ids=cwe_ids)
                
                detailed_report.append("| CVE ID | CVSS | Severity | KEV | EPSS | Year |")
                detailed_report.append("|--------|------|----------|-----|------|------|")
                
                for record in result:
                    cve_id = record['cve_id']
                    score = record['score']
                    severity = record['severity'] or 'N/A'
                    kev = 'Y' if record['kev'] else ''
                    epss = f"{record['epss']:.4f}" if record['epss'] else 'N/A'
                    
                    try:
                        year = datetime.fromisoformat(record['published'].replace('Z', '+00:00')).year
                    except:
                        year = 'N/A'
                    
                    detailed_report.append(f"| {cve_id} | {score:.1f} | {severity} | {kev} | {epss} | {year} |")
                    
                    # Add description
                    desc = record['description']
                    if desc:
                        desc_short = desc[:200] + "..." if len(desc) > 200 else desc
                        detailed_report.append(f"\n**Description**: {desc_short}\n")
        
        # Save detailed report
        output_detailed = "paper/analysis/ATTACK_PATTERNS_DETAILED.md"
        with open(output_detailed, 'w', encoding='utf-8') as f:
            f.write('\n'.join(detailed_report))
        
        print(f"\n[OK] Detailed report saved to: {output_detailed}")
        
        # Generate key findings
        key_findings = []
        key_findings.append("# Key Findings: Attack Pattern Analysis\n")
        key_findings.append(f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d')}\n")
        key_findings.append("## Top 5 Most Common Attack Types\n")
        
        sorted_attacks = sorted(attack_results.items(), key=lambda x: x[1]['total'], reverse=True)[:5]
        for i, (attack_type, data) in enumerate(sorted_attacks, 1):
            key_findings.append(f"{i}. **{attack_type}**: {data['total']} CVEs")
            key_findings.append(f"   - KEV Listed: {data['kev_count']}")
            key_findings.append(f"   - Avg EPSS: {data['avg_epss']:.4f}" if data['avg_epss'] else "   - Avg EPSS: N/A")
            key_findings.append("")
        
        key_findings.append("## Highest Risk Attack Types (by EPSS)\n")
        sorted_by_epss = sorted(
            [(k, v) for k, v in attack_results.items() if v['avg_epss']], 
            key=lambda x: x[1]['avg_epss'], 
            reverse=True
        )[:5]
        
        for i, (attack_type, data) in enumerate(sorted_by_epss, 1):
            key_findings.append(f"{i}. **{attack_type}**: EPSS {data['avg_epss']:.4f}")
            key_findings.append(f"   - Total CVEs: {data['total']}")
            key_findings.append(f"   - KEV Listed: {data['kev_count']}")
            key_findings.append("")
        
        key_findings.append("## Most Exploited Attack Types (KEV)\n")
        sorted_by_kev = sorted(attack_results.items(), key=lambda x: x[1]['kev_count'], reverse=True)[:5]
        
        for i, (attack_type, data) in enumerate(sorted_by_kev, 1):
            if data['kev_count'] > 0:
                key_findings.append(f"{i}. **{attack_type}**: {data['kev_count']} in KEV")
                key_findings.append(f"   - Total CVEs: {data['total']}")
                key_findings.append(f"   - KEV Rate: {data['kev_count']/data['total']*100:.1f}%")
                key_findings.append("")
        
        # Save key findings
        output_findings = "paper/analysis/KEY_FINDINGS.md"
        with open(output_findings, 'w', encoding='utf-8') as f:
            f.write('\n'.join(key_findings))
        
        print(f"[OK] Key findings saved to: {output_findings}")
        
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
