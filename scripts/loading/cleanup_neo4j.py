"""Clean up unnecessary data from Neo4j."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def cleanup(driver):
    """Clean up unnecessary data."""
    
    with driver.session() as session:
        # Check current state
        print("="*80)
        print("BEFORE CLEANUP")
        print("="*80)
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count ORDER BY count DESC")
        total_before = 0
        for record in result:
            count = record['count']
            total_before += count
            print(f"  {record['labels']}: {count:,}")
        print(f"\nTotal nodes: {total_before:,}")
        
        # 1. Delete commits NOT connected to CVE
        print("\n" + "="*80)
        print("STEP 1: Deleting commits not connected to CVE...")
        print("="*80)
        result = session.run("""
            MATCH (c:Commit)
            WHERE NOT (c)-[]-(:CVE)
            WITH count(c) as count
            RETURN count
        """)
        unconnected_commits = result.single()['count']
        print(f"Found {unconnected_commits:,} commits not connected to CVE")
        
        if unconnected_commits > 0:
            confirm = input(f"Delete {unconnected_commits:,} unconnected commits? (yes/no): ")
            if confirm.lower() == 'yes':
                session.run("""
                    MATCH (c:Commit)
                    WHERE NOT (c)-[]-(:CVE)
                    DETACH DELETE c
                """)
                print(f"✅ Deleted {unconnected_commits:,} commits")
        
        # 2. Delete Reference nodes
        print("\n" + "="*80)
        print("STEP 2: Deleting Reference nodes...")
        print("="*80)
        result = session.run("MATCH (r:Reference) RETURN count(r) as count")
        ref_count = result.single()['count']
        print(f"Found {ref_count:,} Reference nodes")
        
        if ref_count > 0:
            confirm = input(f"Delete {ref_count:,} Reference nodes? (yes/no): ")
            if confirm.lower() == 'yes':
                session.run("MATCH (r:Reference) DETACH DELETE r")
                print(f"✅ Deleted {ref_count:,} Reference nodes")
        
        # 3. Delete CPE nodes
        print("\n" + "="*80)
        print("STEP 3: Deleting CPE nodes...")
        print("="*80)
        result = session.run("MATCH (c:CPE) RETURN count(c) as count")
        cpe_count = result.single()['count']
        print(f"Found {cpe_count:,} CPE nodes")
        
        if cpe_count > 0:
            confirm = input(f"Delete {cpe_count:,} CPE nodes? (yes/no): ")
            if confirm.lower() == 'yes':
                session.run("MATCH (c:CPE) DETACH DELETE c")
                print(f"✅ Deleted {cpe_count:,} CPE nodes")
        
        # 4. Delete Consequence nodes
        print("\n" + "="*80)
        print("STEP 4: Deleting Consequence nodes...")
        print("="*80)
        result = session.run("MATCH (c:Consequence) RETURN count(c) as count")
        cons_count = result.single()['count']
        print(f"Found {cons_count:,} Consequence nodes")
        
        if cons_count > 0:
            confirm = input(f"Delete {cons_count:,} Consequence nodes? (yes/no): ")
            if confirm.lower() == 'yes':
                session.run("MATCH (c:Consequence) DETACH DELETE c")
                print(f"✅ Deleted {cons_count:,} Consequence nodes")
        
        # Check final state
        print("\n" + "="*80)
        print("AFTER CLEANUP")
        print("="*80)
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count ORDER BY count DESC")
        total_after = 0
        for record in result:
            count = record['count']
            total_after += count
            print(f"  {record['labels']}: {count:,}")
        print(f"\nTotal nodes: {total_after:,}")
        print(f"Freed up: {total_before - total_after:,} nodes ({(total_before - total_after) / total_before * 100:.1f}%)")


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        cleanup(driver)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
