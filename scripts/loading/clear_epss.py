"""Clear EPSS scores from Neo4j."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def clear_epss():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Check current count
        result = session.run("MATCH (c:CVE) WHERE c.epss_score IS NOT NULL RETURN count(c) as count")
        before_count = result.single()['count']
        print(f"Found {before_count} CVEs with EPSS scores")
        
        # Clear EPSS scores
        print("Clearing EPSS scores...")
        session.run("""
            MATCH (c:CVE)
            WHERE c.epss_score IS NOT NULL
            SET c.epss_score = NULL, c.epss_percentile = NULL
        """)
        
        # Verify
        result = session.run("MATCH (c:CVE) WHERE c.epss_score IS NOT NULL RETURN count(c) as count")
        after_count = result.single()['count']
        print(f"After clearing: {after_count} CVEs with EPSS scores")
        print(f"✅ Cleared {before_count - after_count} EPSS scores")
    
    driver.close()

if __name__ == "__main__":
    clear_epss()
