"""
Analyze commits in relation to their CVEs' published dates.
"""
import os
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def analyze_cve_commits():
    """Analyze commits relative to CVE published dates."""
    
    with driver.session() as session:
        # Get CVEs with their published dates and commit counts
        query = """
        MATCH (cve:CVE)
        OPTIONAL MATCH (cve)-[:AFFECTS]->(pkg:Package)-[:HAS_COMMIT]->(c:Commit)
        WHERE c.committed_date IS NOT NULL
        WITH cve, 
             cve.published_date as pub_date,
             collect(c) as commits
        WHERE pub_date IS NOT NULL AND size(commits) > 0
        RETURN cve.id as cve_id,
               pub_date,
               size(commits) as commit_count,
               commits
        ORDER BY commit_count DESC
        """
        
        result = session.run(query)
        
        cve_stats = []
        total_commits = 0
        commits_by_window = defaultdict(int)
        
        for record in result:
            cve_id = record["cve_id"]
            pub_date = datetime.fromisoformat(record["pub_date"].replace('Z', '+00:00'))
            commit_count = record["commit_count"]
            commits = record["commits"]
            
            total_commits += commit_count
            
            # Analyze time windows for each commit
            before_counts = {30: 0, 90: 0, 180: 0, 365: 0}
            after_counts = {30: 0, 90: 0, 180: 0, 365: 0}
            
            for commit in commits:
                commit_date_str = commit.get("committed_date")
                if not commit_date_str:
                    continue
                    
                commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
                days_diff = (pub_date - commit_date).days
                
                # Count commits in different windows
                if days_diff > 0:  # Before CVE
                    for window in [30, 90, 180, 365]:
                        if days_diff <= window:
                            before_counts[window] += 1
                else:  # After CVE
                    days_after = abs(days_diff)
                    for window in [30, 90, 180, 365]:
                        if days_after <= window:
                            after_counts[window] += 1
            
            cve_stats.append({
                'cve_id': cve_id,
                'pub_date': pub_date,
                'total': commit_count,
                'before': before_counts,
                'after': after_counts
            })
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"CVE-Commit Analysis")
        print(f"{'='*80}")
        print(f"Total CVEs with commits: {len(cve_stats)}")
        print(f"Total commits analyzed: {total_commits:,}")
        
        # Aggregate statistics
        print(f"\n{'='*80}")
        print(f"Commits by Time Window (relative to CVE published date)")
        print(f"{'='*80}")
        
        for window in [30, 90, 180, 365]:
            before_total = sum(stat['before'][window] for stat in cve_stats)
            after_total = sum(stat['after'][window] for stat in cve_stats)
            total_in_window = before_total + after_total
            pct = (total_in_window / total_commits * 100) if total_commits > 0 else 0
            
            print(f"\n±{window} days window:")
            print(f"  Before CVE: {before_total:,}")
            print(f"  After CVE:  {after_total:,}")
            print(f"  Total:      {total_in_window:,} ({pct:.1f}% of all commits)")
        
        # Show top CVEs by commit count
        print(f"\n{'='*80}")
        print(f"Top 10 CVEs by Commit Count")
        print(f"{'='*80}")
        
        for i, stat in enumerate(cve_stats[:10], 1):
            print(f"\n{i}. {stat['cve_id']} ({stat['pub_date'].strftime('%Y-%m-%d')})")
            print(f"   Total commits: {stat['total']:,}")
            print(f"   ±90 days: {stat['before'][90] + stat['after'][90]:,}")
            print(f"   ±180 days: {stat['before'][180] + stat['after'][180]:,}")

if __name__ == "__main__":
    try:
        analyze_cve_commits()
    finally:
        driver.close()
