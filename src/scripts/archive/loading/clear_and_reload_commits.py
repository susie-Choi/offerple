"""
Clear all commits from Neo4j and reload only CVE-related commits with time filtering.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from neo4j import GraphDatabase
from tqdm import tqdm

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def clear_all_commits():
    """Delete all commit nodes from Neo4j."""
    print("\n" + "="*80)
    print("Clearing all commits from Neo4j...")
    print("="*80)
    
    with driver.session() as session:
        # Count first
        result = session.run("MATCH (c:Commit) RETURN count(c) as cnt")
        count = result.single()["cnt"]
        print(f"Found {count:,} commits to delete")
        
        if count == 0:
            print("No commits to delete")
            return
        
        # Delete in batches
        batch_size = 10000
        deleted = 0
        
        while True:
            result = session.run(f"""
                MATCH (c:Commit)
                WITH c LIMIT {batch_size}
                DETACH DELETE c
                RETURN count(c) as deleted
            """)
            batch_deleted = result.single()["deleted"]
            deleted += batch_deleted
            print(f"Deleted {deleted:,} / {count:,} commits...")
            
            if batch_deleted == 0:
                break
        
        print(f"✅ Deleted all {deleted:,} commits")

def get_cve_published_date(cve_id):
    """Get published date for a CVE."""
    with driver.session() as session:
        result = session.run("""
            MATCH (cve:CVE {id: $cve_id})
            RETURN cve.published as pub_date
        """, cve_id=cve_id)
        record = result.single()
        if record and record["pub_date"]:
            pub_date = record["pub_date"]
            if isinstance(pub_date, str):
                return datetime.fromisoformat(pub_date.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                return pub_date.to_native().replace(tzinfo=None)
    return None

def load_cve_commits_with_filter(time_window_days=180, batch_size=1000):
    """Load commits from commits_by_cve directory with time filtering."""
    print("\n" + "="*80)
    print(f"Loading CVE commits (±{time_window_days} days window)...")
    print("="*80)
    
    commits_dir = Path("data/raw/github/commits_by_cve")
    
    if not commits_dir.exists():
        print(f"Directory not found: {commits_dir}")
        return
    
    commit_files = list(commits_dir.glob("*.jsonl"))
    print(f"Found {len(commit_files)} CVE commit files")
    
    total_loaded = 0
    total_filtered = 0
    
    for file_path in tqdm(commit_files, desc="Processing CVE files"):
        cve_id = file_path.stem.replace("_commits", "")
        
        # Get CVE published date
        pub_date = get_cve_published_date(cve_id)
        if not pub_date:
            print(f"\n⚠️  No published date for {cve_id}, skipping...")
            continue
        
        # Calculate time window
        start_date = pub_date - timedelta(days=time_window_days)
        end_date = pub_date + timedelta(days=time_window_days)
        
        # Read and filter commits
        batch = []
        file_total = 0
        file_filtered = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    file_total += 1
                    
                    # Extract commit info
                    payload = data['payload']
                    commit_date_str = payload['commit']['author']['date']
                    commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    
                    # Check if within time window
                    if start_date <= commit_date <= end_date:
                        commit_data = {
                            'sha': payload['sha'],
                            'repo': data['repo'],
                            'date': commit_date_str,
                            'author': payload['commit']['author']['name'],
                            'message': payload['commit']['message'],
                            'cve_id': cve_id
                        }
                        batch.append(commit_data)
                        
                        # Insert batch
                        if len(batch) >= batch_size:
                            insert_commit_batch(batch)
                            total_loaded += len(batch)
                            batch = []
                    else:
                        file_filtered += 1
                
                except (KeyError, json.JSONDecodeError) as e:
                    continue
        
        # Insert remaining
        if batch:
            insert_commit_batch(batch)
            total_loaded += len(batch)
        
        total_filtered += file_filtered
        print(f"\n  {cve_id}: loaded {file_total - file_filtered:,}, filtered {file_filtered:,}")
    
    print(f"\n{'='*80}")
    print(f"✅ Loaded {total_loaded:,} commits (filtered out {total_filtered:,})")
    print(f"{'='*80}")

def insert_commit_batch(batch):
    """Insert a batch of commits with CVE relationship."""
    with driver.session() as session:
        session.run("""
            UNWIND $commits as commit
            MERGE (c:Commit {sha: commit.sha})
            SET c.repo = commit.repo,
                c.date = commit.date,
                c.author = commit.author,
                c.message = commit.message
            WITH c, commit
            MATCH (cve:CVE {id: commit.cve_id})
            MERGE (cve)-[:HAS_COMMIT]->(c)
        """, commits=batch)

def verify_results():
    """Verify the loaded data."""
    print("\n" + "="*80)
    print("Verification")
    print("="*80)
    
    with driver.session() as session:
        # Count commits
        result = session.run("MATCH (c:Commit) RETURN count(c) as cnt")
        commit_count = result.single()["cnt"]
        print(f"Total commits: {commit_count:,}")
        
        # Count CVE-commit relationships
        result = session.run("MATCH (:CVE)-[:HAS_COMMIT]->(:Commit) RETURN count(*) as cnt")
        rel_count = result.single()["cnt"]
        print(f"CVE-Commit relationships: {rel_count:,}")
        
        # Show CVEs with commits
        result = session.run("""
            MATCH (cve:CVE)-[:HAS_COMMIT]->(c:Commit)
            RETURN cve.id as cve_id, count(c) as commit_count
            ORDER BY commit_count DESC
        """)
        print("\nCVEs with commits:")
        for record in result:
            print(f"  {record['cve_id']}: {record['commit_count']:,} commits")

if __name__ == "__main__":
    try:
        # Step 1: Clear all commits
        clear_all_commits()
        
        # Step 2: Reload with filtering
        load_cve_commits_with_filter(time_window_days=180)
        
        # Step 3: Verify
        verify_results()
        
    finally:
        driver.close()
