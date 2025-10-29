"""Visualize Neo4j graph data for the midterm report."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Set Korean font for matplotlib
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def visualize_cve_cwe_network():
    """Visualize CVE-CWE relationship network."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Get top CVEs and their CWEs
        result = session.run("""
            MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
            WHERE cve.cvssScore IS NOT NULL
            WITH cve, cwe
            ORDER BY cve.cvssScore DESC
            LIMIT 20
            RETURN cve.id as cve_id, cve.cvssScore as score,
                   collect(cwe.id) as cwe_ids
        """)
        
        # Build graph
        G = nx.Graph()
        
        for record in result:
            cve_id = record['cve_id']
            score = record['score']
            cwe_ids = record['cwe_ids']
            
            # Add CVE node
            G.add_node(cve_id, node_type='CVE', score=score)
            
            # Add CWE nodes and edges
            for cwe_id in cwe_ids:
                G.add_node(cwe_id, node_type='CWE')
                G.add_edge(cve_id, cwe_id)
        
        # Create visualization
        plt.figure(figsize=(16, 12))
        
        # Separate nodes by type
        cve_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'CVE']
        cwe_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'CWE']
        
        # Use spring layout
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        
        # Draw CWE nodes (larger, blue)
        nx.draw_networkx_nodes(G, pos, nodelist=cwe_nodes, 
                              node_color='lightblue', 
                              node_size=1500,
                              alpha=0.8,
                              label='CWE')
        
        # Draw CVE nodes (smaller, red, size by CVSS score)
        cve_sizes = [G.nodes[n].get('score', 5) * 100 for n in cve_nodes]
        nx.draw_networkx_nodes(G, pos, nodelist=cve_nodes,
                              node_color='lightcoral',
                              node_size=cve_sizes,
                              alpha=0.7,
                              label='CVE')
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, alpha=0.3, width=1)
        
        # Draw labels (only for CWE nodes to avoid clutter)
        cwe_labels = {n: n for n in cwe_nodes}
        nx.draw_networkx_labels(G, pos, cwe_labels, font_size=8, font_weight='bold')
        
        plt.title('CVE-CWE Relationship Network\n(CVE node size = CVSS score)', 
                 fontsize=16, fontweight='bold')
        plt.legend(loc='upper right', fontsize=12)
        plt.axis('off')
        plt.tight_layout()
        
        output_file = 'docs/images/cve_cwe_network.jpg'
        os.makedirs('docs/images', exist_ok=True)
        plt.savefig(output_file, dpi=300, bbox_inches='tight', format='jpg')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    driver.close()


def visualize_supply_chain():
    """Visualize package dependency supply chain."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Get package dependencies
        result = session.run("""
            MATCH (p1:Package)-[:DEPENDS_ON]->(p2:Package)
            RETURN p1.name as source, p2.name as target
        """)
        
        # Build directed graph
        G = nx.DiGraph()
        
        for record in result:
            source = record['source']
            target = record['target']
            G.add_edge(source, target)
        
        if len(G.nodes()) == 0:
            print("⚠️  No package dependency data found")
            driver.close()
            return
        
        # Create visualization
        plt.figure(figsize=(14, 10))
        
        # Use hierarchical layout
        pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, 
                              node_color='lightgreen',
                              node_size=2000,
                              alpha=0.8)
        
        # Draw edges with arrows
        nx.draw_networkx_edges(G, pos, 
                              edge_color='gray',
                              arrows=True,
                              arrowsize=20,
                              arrowstyle='->',
                              width=2,
                              alpha=0.6)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
        
        plt.title('Package Dependency Supply Chain', 
                 fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        output_file = 'docs/images/supply_chain.jpg'
        plt.savefig(output_file, dpi=300, bbox_inches='tight', format='jpg')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    driver.close()


def visualize_severity_distribution():
    """Visualize CVE severity distribution."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        result = session.run("""
            MATCH (cve:CVE)
            WHERE cve.cvssScore IS NOT NULL
            WITH cve,
                 CASE
                   WHEN cve.cvssScore >= 9.0 THEN 'CRITICAL'
                   WHEN cve.cvssScore >= 7.0 THEN 'HIGH'
                   WHEN cve.cvssScore >= 4.0 THEN 'MEDIUM'
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
        counts = []
        colors = []
        
        color_map = {
            'CRITICAL': '#d32f2f',
            'HIGH': '#f57c00',
            'MEDIUM': '#fbc02d',
            'LOW': '#388e3c'
        }
        
        for record in result:
            severity = record['severity']
            count = record['count']
            severities.append(severity)
            counts.append(count)
            colors.append(color_map.get(severity, 'gray'))
        
        # Create bar chart
        plt.figure(figsize=(10, 6))
        bars = plt.bar(severities, counts, color=colors, alpha=0.8, edgecolor='black')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.xlabel('Severity Level', fontsize=12, fontweight='bold')
        plt.ylabel('Number of CVEs', fontsize=12, fontweight='bold')
        plt.title('CVE Severity Distribution (CVSS v3)', 
                 fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        output_file = 'docs/images/severity_distribution.jpg'
        plt.savefig(output_file, dpi=300, bbox_inches='tight', format='jpg')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    driver.close()


def visualize_top_cwes():
    """Visualize top CWEs by CVE count."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        result = session.run("""
            MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
            RETURN cwe.id as cwe_id, count(cve) as cve_count
            ORDER BY cve_count DESC
            LIMIT 10
        """)
        
        cwe_ids = []
        cve_counts = []
        
        for record in result:
            cwe_id = record['cwe_id']
            cve_count = record['cve_count']
            cwe_ids.append(cwe_id)
            cve_counts.append(cve_count)
        
        # Create horizontal bar chart
        plt.figure(figsize=(12, 8))
        bars = plt.barh(cwe_ids, cve_counts, color='steelblue', alpha=0.8, edgecolor='black')
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2.,
                    f'{int(width)}',
                    ha='left', va='center', fontsize=10, fontweight='bold')
        
        plt.xlabel('Number of CVEs', fontsize=12, fontweight='bold')
        plt.ylabel('CWE ID', fontsize=12, fontweight='bold')
        plt.title('Top 10 CWEs by CVE Count', 
                 fontsize=14, fontweight='bold')
        plt.gca().invert_yaxis()
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        
        output_file = 'docs/images/top_cwes.jpg'
        plt.savefig(output_file, dpi=300, bbox_inches='tight', format='jpg')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    driver.close()


def visualize_database_schema():
    """Visualize Neo4j database schema."""
    # Create a simple schema diagram
    G = nx.DiGraph()
    
    # Add nodes (entity types)
    entities = ['CVE', 'CWE', 'KEV', 'Product', 'Package', 'Exploit', 'EPSS']
    for entity in entities:
        G.add_node(entity)
    
    # Add relationships
    relationships = [
        ('CVE', 'CWE', 'HAS_WEAKNESS'),
        ('CVE', 'KEV', 'HAS_KEV'),
        ('CVE', 'Product', 'AFFECTS'),
        ('CVE', 'Exploit', 'HAS_EXPLOIT'),
        ('CVE', 'EPSS', 'HAS_EPSS'),
        ('Package', 'Package', 'DEPENDS_ON'),
    ]
    
    for source, target, label in relationships:
        G.add_edge(source, target, label=label)
    
    plt.figure(figsize=(14, 10))
    
    # Use circular layout for schema
    pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos,
                          node_color='lightblue',
                          node_size=3000,
                          alpha=0.9,
                          edgecolors='black',
                          linewidths=2)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos,
                          edge_color='gray',
                          arrows=True,
                          arrowsize=20,
                          arrowstyle='->',
                          width=2,
                          alpha=0.6)
    
    # Draw node labels
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold')
    
    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)
    
    plt.title('Neo4j Database Schema', 
             fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    output_file = 'docs/images/database_schema.jpg'
    os.makedirs('docs/images', exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight', format='jpg')
    print(f"✅ Saved: {output_file}")
    plt.close()


if __name__ == "__main__":
    print("=" * 80)
    print("Generating Neo4j Visualizations for Midterm Report")
    print("=" * 80)
    
    print("\n1. Database Schema...")
    visualize_database_schema()
    
    print("\n2. CVE Severity Distribution...")
    visualize_severity_distribution()
    
    print("\n3. Top CWEs...")
    visualize_top_cwes()
    
    print("\n4. CVE-CWE Network...")
    visualize_cve_cwe_network()
    
    print("\n5. Supply Chain...")
    visualize_supply_chain()
    
    print("\n" + "=" * 80)
    print("✅ All visualizations completed!")
    print("=" * 80)
