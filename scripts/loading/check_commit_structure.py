"""Check commit node structure and relationships."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

with driver.session() as session:
    # Check commit properties
    result = session.run("MATCH (c:Commit) RETURN c LIMIT 1")
    commit = list(result)[0]["c"]
    print("Sample Commit properties:")
    for key, value in commit.items():
        print(f"  {key}: {value}")
    
    # Check commit relationships
    print("\nCommit relationships:")
    result = session.run("""
        MATCH (c:Commit)-[r]-()
        RETURN type(r) as rel_type, count(*) as cnt
        ORDER BY cnt DESC
    """)
    for record in result:
        print(f"  {record['rel_type']}: {record['cnt']}")
    
    # Check if commits have repo info
    print("\nSample commit with repo:")
    result = session.run("""
        MATCH (c:Commit)
        WHERE c.repo IS NOT NULL
        RETURN c.repo as repo, c.sha as sha, c.date as date
        LIMIT 5
    """)
    for record in result:
        print(f"  {record['repo']} - {record['sha'][:8]} - {record['date']}")

driver.close()
