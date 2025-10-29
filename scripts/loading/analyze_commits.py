"""Analyze commit date distribution in Neo4j."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from datetime import datetime

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def analyze_commits():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Total commits
        result = session.run("MATCH (c:Commit) RETURN count(c) as count")
        total = result.single()['count']
        print(f"Total commits: {total:,}")
        
        # Commits by year
        print("\n" + "="*80)
        print("Commits by Year")
        print("="*80)
        result = session.run("""
            MATCH (c:Commit)
            WHERE c.date IS NOT NULL
            WITH substring(c.date, 0, 4) as year, count(*) as count
            RETURN year, count
            ORDER BY year DESC
        """)
        for record in result:
            print(f"  {record['year']}: {record['count']:,}")
        
        # Commits without date
        result = session.run("""
            MATCH (c:Commit)
            WHERE c.date IS NULL OR c.date = ''
            RETURN count(c) as count
        """)
        no_date = result.single()['count']
        print(f"\n  No date: {no_date:,}")
        
        # Commits in last 2 years (2023-2025)
        print("\n" + "="*80)
        print("Recent Commits (2023-2025)")
        print("="*80)
        result = session.run("""
            MATCH (c:Commit)
            WHERE c.date >= '2023-01-01'
            RETURN count(c) as count
        """)
        recent = result.single()['count']
        print(f"  2023-2025: {recent:,} ({recent/total*100:.1f}%)")
        
        # Old commits (before 2023)
        result = session.run("""
            MATCH (c:Commit)
            WHERE c.date < '2023-01-01' OR c.date IS NULL OR c.date = ''
            RETURN count(c) as count
        """)
        old = result.single()['count']
        print(f"  Before 2023: {old:,} ({old/total*100:.1f}%)")
        
        # Sample old commits
        print("\n" + "="*80)
        print("Sample Old Commits (first 5)")
        print("="*80)
        result = session.run("""
            MATCH (c:Commit)
            WHERE c.date < '2023-01-01'
            RETURN c.sha as sha, c.date as date, c.repo as repo, c.message as message
            ORDER BY c.date DESC
            LIMIT 5
        """)
        for record in result:
            print(f"  {record['date'][:10]} - {record['repo']}")
            print(f"    {record['message'][:80]}...")
            print()
    
    driver.close()


if __name__ == "__main__":
    analyze_commits()
