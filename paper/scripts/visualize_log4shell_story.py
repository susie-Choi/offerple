"""Visualize Log4Shell (CVE-2021-44228) story from Neo4j data."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import networkx as nx

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Set Korean font
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def visualize_log4shell_graph():
    """Visualize Log4Shell CVE with all its relationships."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Get Log4Shell and all its relationships
        result = session.run("""
            MATCH (cve:CVE {id: 'CVE-2021-44228'})
            OPTIONAL MATCH (cve)-[:HAS_WEAKNESS]->(cwe:CWE)
            OPTIONAL MATCH (cve)-[:HAS_KEV]->(kev:KEV)
            OPTIONAL MATCH (cve)-[:HAS_EXPLOIT]->(exp:Exploit)
            OPTIONAL MATCH (cve)-[:AFFECTS]->(prod:Product)
            OPTIONAL MATCH (cve)-[:HAS_REFERENCE]->(ref:Reference)
            RETURN cve,
                   collect(DISTINCT cwe) as cwes,
                   collect(DISTINCT kev) as kevs,
                   collect(DISTINCT exp) as exploits,
                   collect(DISTINCT prod) as products,
                   collect(DISTINCT ref) as references
        """)
        
        record = result.single()
        if not record:
            print("❌ Log4Shell CVE not found in database")
            driver.close()
            return
        
        cve = record['cve']
        cwes = record['cwes']
        kevs = record['kevs']
        exploits = record['exploits']
        products = record['products']
        references = record['references']
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add CVE node (center)
        cve_label = f"{cve['id']}\nCVSS: {cve.get('cvssScore', 'N/A')}\n{cve.get('cvssSeverity', 'N/A')}"
        G.add_node('CVE', label=cve_label, node_type='CVE')
        
        # Add CWE nodes
        for i, cwe in enumerate(cwes):
            if cwe:
                cwe_id = cwe.get('id', f'CWE-{i}')
                cwe_name = cwe.get('name', 'Unknown')[:30]
                G.add_node(f'CWE_{i}', label=f"{cwe_id}\n{cwe_name}", node_type='CWE')
                G.add_edge('CVE', f'CWE_{i}', relation='HAS_WEAKNESS')
        
        # Add KEV nodes
        for i, kev in enumerate(kevs):
            if kev:
                kev_label = f"KEV\nAdded: {kev.get('date_added', 'N/A')}"
                G.add_node(f'KEV_{i}', label=kev_label, node_type='KEV')
                G.add_edge('CVE', f'KEV_{i}', relation='HAS_KEV')
        
        # Add Exploit nodes (limit to 3)
        for i, exp in enumerate(exploits[:3]):
            if exp:
                exp_type = exp.get('type', 'Unknown')
                G.add_node(f'EXP_{i}', label=f"Exploit\n{exp_type}", node_type='Exploit')
                G.add_edge('CVE', f'EXP_{i}', relation='HAS_EXPLOIT')
        
        # Add Product nodes (limit to 5 most important)
        for i, prod in enumerate(products[:5]):
            if prod:
                prod_name = prod.get('name', 'Unknown')[:20]
                G.add_node(f'PROD_{i}', label=f"Product\n{prod_name}", node_type='Product')
                G.add_edge('CVE', f'PROD_{i}', relation='AFFECTS')
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(20, 16), facecolor='white')
        
        # Define colors for each node type
        color_map = {
            'CVE': '#d32f2f',      # Red (critical)
            'CWE': '#1976d2',      # Blue
            'KEV': '#f57c00',      # Orange
            'Exploit': '#7b1fa2',  # Purple
            'Product': '#388e3c',  # Green
        }
        
        # Use spring layout for better positioning
        pos = nx.spring_layout(G, k=2.5, iterations=100, seed=42, center=(0, 0))
        
        # Separate nodes by type for different styling
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            node_type = G.nodes[node].get('node_type', 'Unknown')
            node_colors.append(color_map.get(node_type, 'lightgray'))
            if node_type == 'CVE':
                node_sizes.append(4000)
            else:
                node_sizes.append(2500)
        
        # Draw edges with curved arrows
        nx.draw_networkx_edges(
            G, pos,
            edge_color='gray',
            width=2.5,
            alpha=0.5,
            arrows=True,
            arrowsize=25,
            arrowstyle='->',
            connectionstyle='arc3,rad=0.2',
            node_size=node_sizes,
            ax=ax
        )
        
        # Draw nodes
        nx.draw_networkx_nodes(
            G, pos,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.95,
            edgecolors='black',
            linewidths=3,
            ax=ax
        )
        
        # Draw labels
        labels = {node: G.nodes[node].get('label', node) for node in G.nodes()}
        nx.draw_networkx_labels(
            G, pos,
            labels,
            font_size=10,
            font_weight='bold',
            font_color='white',
            ax=ax
        )
        
        # Add legend
        legend_elements = [
            mpatches.Patch(facecolor=color_map['CVE'], edgecolor='black', label='CVE (취약점)'),
            mpatches.Patch(facecolor=color_map['CWE'], edgecolor='black', label='CWE (취약점 유형)'),
            mpatches.Patch(facecolor=color_map['KEV'], edgecolor='black', label='KEV (실제 악용 확인)'),
            mpatches.Patch(facecolor=color_map['Exploit'], edgecolor='black', label='Exploit (공개 익스플로잇)'),
            mpatches.Patch(facecolor=color_map['Product'], edgecolor='black', label='Product (영향받는 제품)'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=11, framealpha=0.9)
        
        # Add title with CVE info
        title = f"Log4Shell (CVE-2021-44228) 관계 그래프\n"
        title += f"CVSS Score: {cve.get('cvssScore', 'N/A')} ({cve.get('cvssSeverity', 'N/A')})"
        if cve.get('is_kev'):
            title += " | ⚠️ CISA KEV 등재"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Add statistics box
        stats_text = f"통계:\n"
        stats_text += f"• CWE: {len([c for c in cwes if c])}개\n"
        stats_text += f"• KEV: {len([k for k in kevs if k])}개\n"
        stats_text += f"• Exploit: {len([e for e in exploits if e])}개\n"
        stats_text += f"• 영향받는 제품: {len([p for p in products if p])}개"
        
        ax.text(0.98, 0.02, stats_text,
               transform=ax.transAxes,
               fontsize=10,
               verticalalignment='bottom',
               horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax.set_xlim(-6, 6)
        ax.set_ylim(-5, 5)
        ax.axis('off')
        plt.tight_layout()
        
        output_file = 'docs/images/log4shell_graph.jpg'
        os.makedirs('docs/images', exist_ok=True)
        plt.savefig(output_file, dpi=300, bbox_inches='tight', format='jpg', facecolor='white')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    driver.close()

if __name__ == "__main__":
    print("=" * 80)
    print("Generating Log4Shell Story Visualization")
    print("=" * 80)
    visualize_log4shell_graph()
    print("=" * 80)
    print("✅ Visualization completed!")
    print("=" * 80)
