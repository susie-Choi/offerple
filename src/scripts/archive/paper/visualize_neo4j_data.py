"""Visualize Neo4j data for midterm report."""
import os
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'Malgun Gothic'  # Korean font
plt.rcParams['axes.unicode_minus'] = False

def create_visualizations():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # 1. Node Count Bar Chart
        print("Creating node count visualization...")
        result = session.run("""
            MATCH (n) 
            RETURN labels(n)[0] as label, count(*) as count 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        labels = []
        counts = []
        for record in result:
            labels.append(record['label'])
            counts.append(record['count'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(labels, counts, color=sns.color_palette("viridis", len(labels)))
        ax.set_xlabel('Count', fontsize=12)
        ax.set_title('Neo4j Database: Node Counts by Type', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        
        # Add value labels
        for i, (label, count) in enumerate(zip(labels, counts)):
            ax.text(count + max(counts)*0.01, i, f'{count:,}', 
                   va='center', fontsize=10)
        
        plt.tight_layout()
        plt.savefig('docs/images/neo4j_node_counts.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: docs/images/neo4j_node_counts.png")
        plt.close()
        
        # 2. CVE Severity Distribution (Pie Chart)
        print("Creating CVE severity distribution...")
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
        
        severities = []
        severity_counts = []
        colors = {'CRITICAL': '#d32f2f', 'HIGH': '#f57c00', 
                 'MEDIUM': '#fbc02d', 'LOW': '#388e3c'}
        severity_colors = []
        
        for record in result:
            sev = record['severity']
            severities.append(sev)
            severity_counts.append(record['count'])
            severity_colors.append(colors.get(sev, '#999999'))
        
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(severity_counts, labels=severities, 
                                           autopct='%1.1f%%', startangle=90,
                                           colors=severity_colors,
                                           textprops={'fontsize': 12})
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)
        
        ax.set_title('CVE Severity Distribution (CVSS v3)', 
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig('docs/images/cve_severity_distribution.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: docs/images/cve_severity_distribution.png")
        plt.close()
        
        # 3. Top CWEs Bar Chart
        print("Creating top CWEs visualization...")
        result = session.run("""
            MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
            RETURN cwe.id as cwe_id, count(cve) as cve_count
            ORDER BY cve_count DESC
            LIMIT 10
        """)
        
        cwe_ids = []
        cwe_counts = []
        for record in result:
            cwe_ids.append(record['cwe_id'])
            cwe_counts.append(record['cve_count'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(cwe_ids, cwe_counts, color=sns.color_palette("rocket", len(cwe_ids)))
        ax.set_xlabel('Number of CVEs', fontsize=12)
        ax.set_title('Top 10 CWEs by CVE Count', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        
        # Add value labels
        for i, (cwe, count) in enumerate(zip(cwe_ids, cwe_counts)):
            ax.text(count + max(cwe_counts)*0.01, i, str(count), 
                   va='center', fontsize=10)
        
        plt.tight_layout()
        plt.savefig('docs/images/top_cwes.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: docs/images/top_cwes.png")
        plt.close()
        
        # 4. Relationship Types
        print("Creating relationship types visualization...")
        result = session.run("""
            MATCH ()-[r]->() 
            RETURN type(r) as type, count(*) as count 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        rel_types = []
        rel_counts = []
        for record in result:
            rel_types.append(record['type'])
            rel_counts.append(record['count'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(rel_types, rel_counts, color=sns.color_palette("mako", len(rel_types)))
        ax.set_xlabel('Count', fontsize=12)
        ax.set_title('Neo4j Database: Relationship Counts by Type', 
                    fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        
        # Add value labels
        for i, (rel, count) in enumerate(zip(rel_types, rel_counts)):
            ax.text(count + max(rel_counts)*0.01, i, f'{count:,}', 
                   va='center', fontsize=10)
        
        plt.tight_layout()
        plt.savefig('docs/images/neo4j_relationship_counts.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: docs/images/neo4j_relationship_counts.png")
        plt.close()
        
        # 5. CVSS Score Distribution (Histogram)
        print("Creating CVSS score distribution...")
        result = session.run("""
            MATCH (cve:CVE)
            WHERE cve.cvss_v3_score IS NOT NULL
            RETURN cve.cvss_v3_score as score
        """)
        
        scores = [record['score'] for record in result]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        n, bins, patches = ax.hist(scores, bins=20, color='steelblue', 
                                   edgecolor='black', alpha=0.7)
        
        # Color bars by severity
        for i, patch in enumerate(patches):
            bin_center = (bins[i] + bins[i+1]) / 2
            if bin_center >= 9.0:
                patch.set_facecolor('#d32f2f')
            elif bin_center >= 7.0:
                patch.set_facecolor('#f57c00')
            elif bin_center >= 4.0:
                patch.set_facecolor('#fbc02d')
            else:
                patch.set_facecolor('#388e3c')
        
        ax.set_xlabel('CVSS v3 Score', fontsize=12)
        ax.set_ylabel('Number of CVEs', fontsize=12)
        ax.set_title('CVSS v3 Score Distribution', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Add severity lines
        ax.axvline(x=4.0, color='gray', linestyle='--', alpha=0.5, label='Medium threshold')
        ax.axvline(x=7.0, color='gray', linestyle='--', alpha=0.5, label='High threshold')
        ax.axvline(x=9.0, color='gray', linestyle='--', alpha=0.5, label='Critical threshold')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig('docs/images/cvss_score_distribution.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: docs/images/cvss_score_distribution.png")
        plt.close()
        
        # 6. Top Affected Products
        print("Creating top affected products visualization...")
        result = session.run("""
            MATCH (cve:CVE)-[:AFFECTS]->(prod:Product)
            RETURN prod.name as product, count(cve) as cve_count
            ORDER BY cve_count DESC
            LIMIT 10
        """)
        
        products = []
        product_counts = []
        for record in result:
            products.append(record['product'][:30])  # Truncate long names
            product_counts.append(record['cve_count'])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(products, product_counts, 
                      color=sns.color_palette("coolwarm", len(products)))
        ax.set_xlabel('Number of CVEs', fontsize=12)
        ax.set_title('Top 10 Most Affected Products', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        
        # Add value labels
        for i, (prod, count) in enumerate(zip(products, product_counts)):
            ax.text(count + max(product_counts)*0.01, i, str(count), 
                   va='center', fontsize=10)
        
        plt.tight_layout()
        plt.savefig('docs/images/top_affected_products.png', dpi=300, bbox_inches='tight')
        print("✅ Saved: docs/images/top_affected_products.png")
        plt.close()
    
    driver.close()
    
    print("\n" + "=" * 80)
    print("✅ All visualizations created successfully!")
    print("=" * 80)

if __name__ == "__main__":
    # Create images directory if it doesn't exist
    os.makedirs('docs/images', exist_ok=True)
    create_visualizations()
