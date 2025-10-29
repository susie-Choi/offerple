"""
Analyze commit files by CVE to understand data distribution.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def get_cve_published_dates():
    """Get published dates for all CVEs from Neo4j."""
    with driver.session() as session:
        result = session.run("""
            MATCH (cve:CVE)
            WHERE cve.published IS NOT NULL
            RETURN cve.id as cve_id, cve.published as pub_date
        """)
        return {r["cve_id"]: r["pub_date"] for r in result}

def analyze_commit_files():
    """Analyze commit files to understand CVE-commit relationships."""
    
    commits_dir = Path("data/raw/github/commits_by_cve")
    
    if not commits_dir.exists():
        print(f"Directory not found: {commits_dir}")
        return
    
    # Get CVE published dates
    print("Loading CVE published dates from Neo4j...")
    cve_dates = get_cve_published_dates()
    print(f"Found {len(cve_dates)} CVEs with published dates\n")
    
    # Analyze files
    commit_files = list(commits_dir.glob("*.jsonl"))
    print(f"Found {len(commit_files)} commit files\n")
    
    cve_stats = []
    total_commits = 0
    
    for file_path in commit_files:
        cve_id = file_path.stem.replace("_commits", "")
        
        if cve_id not in cve_dates:
            continue
        
        pub_date_str = cve_dates[cve_id]
        if isinstance(pub_date_str, str):
            pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
        else:
            # Neo4j datetime object
            pub_date = pub_date_str.to_native().replace(tzinfo=None)
        
        # Count commits and analyze time windows
        commits = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    commit_date_str = data['payload']['commit']['author']['date']
                    commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    commits.append(commit_date)
                except (KeyError, json.JSONDecodeError):
                    continue
        
        if not commits:
            continue
        
        total_commits += len(commits)
        
        # Analyze time windows
        before_counts = {30: 0, 90: 0, 180: 0, 365: 0}
        after_counts = {30: 0, 90: 0, 180: 0, 365: 0}
        
        for commit_date in commits:
            days_diff = (pub_date - commit_date).days
            
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
            'total': len(commits),
            'before': before_counts,
            'after': after_counts
        })
    
    # Sort by total commits
    cve_stats.sort(key=lambda x: x['total'], reverse=True)
    
    # Print summary
    print(f"{'='*80}")
    print(f"CVE-Commit File Analysis")
    print(f"{'='*80}")
    print(f"CVEs with commits: {len(cve_stats)}")
    print(f"Total commits: {total_commits:,}")
    
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
    
    # Show top CVEs
    print(f"\n{'='*80}")
    print(f"Top 20 CVEs by Commit Count")
    print(f"{'='*80}")
    
    for i, stat in enumerate(cve_stats[:20], 1):
        print(f"\n{i}. {stat['cve_id']} ({stat['pub_date'].strftime('%Y-%m-%d')})")
        print(f"   Total: {stat['total']:,}")
        print(f"   ±90d: {stat['before'][90] + stat['after'][90]:,} "
              f"(before: {stat['before'][90]}, after: {stat['after'][90]})")
        print(f"   ±180d: {stat['before'][180] + stat['after'][180]:,} "
              f"(before: {stat['before'][180]}, after: {stat['after'][180]})")
    
    # Calculate what we'd keep with different strategies
    print(f"\n{'='*80}")
    print(f"Data Reduction Strategies")
    print(f"{'='*80}")
    
    for window in [90, 180, 365]:
        kept = sum(stat['before'][window] + stat['after'][window] for stat in cve_stats)
        removed = total_commits - kept
        pct_kept = (kept / total_commits * 100) if total_commits > 0 else 0
        pct_removed = (removed / total_commits * 100) if total_commits > 0 else 0
        
        print(f"\nKeep only ±{window} days around CVE:")
        print(f"  Keep:   {kept:,} commits ({pct_kept:.1f}%)")
        print(f"  Remove: {removed:,} commits ({pct_removed:.1f}%)")

if __name__ == "__main__":
    try:
        analyze_commit_files()
    finally:
        driver.close()
