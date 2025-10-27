"""Check what data exists in Neo4j database."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
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
        
        # Sample some Signal nodes
        print("\n" + "=" * 80)
        print("Sample Signal Nodes (first 5)")
        print("=" * 80)
        result = session.run("""
            MATCH (s:Signal)
            RETURN s.signal_id as id, s.signal_type as type, 
                   s.project as project, s.timestamp as timestamp
            LIMIT 5
        """)
        for record in result:
            print(f"  ID: {record['id']}")
            print(f"    Type: {record['type']}")
            print(f"    Project: {record['project']}")
            print(f"    Timestamp: {record['timestamp']}")
            print()
        
        # Sample some Project nodes
        print("=" * 80)
        print("Sample Project Nodes (first 5)")
        print("=" * 80)
        result = session.run("""
            MATCH (p:Project)
            RETURN p.name as name, p.ecosystem as ecosystem
            LIMIT 5
        """)
        for record in result:
            print(f"  {record['name']} ({record['ecosystem']})")
    
    driver.close()
    print("\n" + "=" * 80)
    print("✅ Data check completed!")
    print("=" * 80)

if __name__ == "__main__":
    check_data()
