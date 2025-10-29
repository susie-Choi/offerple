"""Check actual property names in Neo4j database."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def check_properties():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        print("=" * 80)
        print("Checking CVE Node Properties")
        print("=" * 80)
        
        # Get sample CVE with all properties
        result = session.run("""
            MATCH (cve:CVE)
            RETURN cve
            LIMIT 1
        """)
        
        for record in result:
            cve = record['cve']
            print("\nSample CVE properties:")
            for key, value in cve.items():
                print(f"  {key}: {value}")
        
        print("\n" + "=" * 80)
        print("Checking CWE Node Properties")
        print("=" * 80)
        
        result = session.run("""
            MATCH (cwe:CWE)
            RETURN cwe
            LIMIT 1
        """)
        
        for record in result:
            cwe = record['cwe']
            print("\nSample CWE properties:")
            for key, value in cwe.items():
                print(f"  {key}: {value}")
        
        print("\n" + "=" * 80)
        print("Checking Package Node Properties")
        print("=" * 80)
        
        result = session.run("""
            MATCH (p:Package)
            RETURN p
            LIMIT 1
        """)
        
        for record in result:
            pkg = record['p']
            print("\nSample Package properties:")
            for key, value in pkg.items():
                print(f"  {key}: {value}")
    
    driver.close()

if __name__ == "__main__":
    check_properties()
