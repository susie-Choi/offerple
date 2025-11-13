"""Check what data exists in Neo4j database."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def check_data():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Check node counts by label
        print("=" * 80)
        print("Node Counts by Label")
        print("=" * 80)
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count")
        for record in result:
            print(f"  {record['labels']}: {record['count']}")
        
        # Check relationship counts
        print("\n" + "=" * 80)
        print("Relationship Counts by Type")
        print("=" * 80)
        result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count")
        for record in result:
            print(f"  {record['type']}: {record['count']}")
        
        # Sample some GitHubSignal nodes
        print("\n" + "=" * 80)
        print("Sample GitHubSignal Nodes (first 5)")
        print("=" * 80)
        result = session.run("""
            MATCH (s:GitHubSignal)
            RETURN s.collected_at as collected_at, s.days as days, 
                   s.commit_count as commit_count, s.security_commits as security_commits
            LIMIT 5
        """)
        for record in result:
            print(f"  Collected: {record['collected_at']}")
            print(f"    Days: {record['days']}")
            print(f"    Commits: {record['commit_count']}")
            print(f"    Security Commits: {record['security_commits']}")
            print()
        
        # Sample some Package nodes
        print("=" * 80)
        print("Sample Package Nodes (first 5)")
        print("=" * 80)
        result = session.run("""
            MATCH (p:Package)
            RETURN p.name as name
            LIMIT 5
        """)
        for record in result:
            print(f"  {record['name']}")
    
    driver.close()
    print("\n" + "=" * 80)
    print("✅ Data check completed!")
    print("=" * 80)

if __name__ == "__main__":
    check_data()
