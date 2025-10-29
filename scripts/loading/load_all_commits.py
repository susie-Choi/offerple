"""Load all GitHub commits from all directories."""
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from tqdm import tqdm

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def load_commits_from_directory(driver, directory, batch_size=1000):
    """Load commits from a directory using bulk insert."""
    commit_dir = Path(directory)
    if not commit_dir.exists():
        logger.warning(f"Directory not found: {directory}")
        return 0
    
    # Get all jsonl files
    jsonl_files = list(commit_dir.glob("**/*.jsonl"))
    logger.info(f"Found {len(jsonl_files)} files in {directory}")
    
    # Get existing commit SHAs
    logger.info("Fetching existing commit SHAs...")
    with driver.session() as session:
        result = session.run("MATCH (c:Commit) RETURN c.sha as sha")
        existing_shas = {record['sha'] for record in result}
    logger.info(f"Found {len(existing_shas):,} existing commits")
    
    count = 0
    skipped = 0
    batch = []
    
    for file_path in tqdm(jsonl_files, desc=f"Loading from {commit_dir.name}"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        repo = data.get('repo', data.get('repository', ''))
                        commit = data.get('payload', data.get('commit', {}))
                        
                        # Handle None commit
                        if commit is None:
                            continue
                        
                        sha = commit.get('sha')
                        if not sha:
                            continue
                        
                        # Skip if already exists
                        if sha in existing_shas:
                            skipped += 1
                            continue
                        
                        # Extract nested commit data safely
                        commit_data = commit.get('commit', {}) or {}
                        author_data = commit_data.get('author', {}) or commit.get('author', {}) or {}
                        
                        # Add to batch
                        batch.append({
                            'sha': sha,
                            'message': commit_data.get('message', commit.get('message', '')),
                            'author': author_data.get('name', ''),
                            'date': author_data.get('date', ''),
                            'repo': repo,
                        })
                        
                        # Insert batch when full
                        if len(batch) >= batch_size:
                            with driver.session() as session:
                                session.run("""
                                    UNWIND $commits AS commit
                                    MERGE (c:Commit {sha: commit.sha})
                                    SET c.message = commit.message,
                                        c.author = commit.author,
                                        c.date = commit.date,
                                        c.repo = commit.repo
                                """, commits=batch)
                            count += len(batch)
                            batch = []
                        
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.warning(f"Error processing commit: {e}")
                        continue
                        
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            continue
    
    # Insert remaining batch
    if batch:
        with driver.session() as session:
            session.run("""
                UNWIND $commits AS commit
                MERGE (c:Commit {sha: commit.sha})
                SET c.message = commit.message,
                    c.author = commit.author,
                    c.date = commit.date,
                    c.repo = commit.repo
            """, commits=batch)
        count += len(batch)
    
    logger.info(f"Loaded {count:,} new commits from {directory} (skipped {skipped:,} existing)")
    return count


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # Check existing commits
        with driver.session() as session:
            result = session.run("MATCH (c:Commit) RETURN count(c) as count")
            existing_count = result.single()['count']
            logger.info(f"Existing commits in Neo4j: {existing_count:,}")
        
        # Load from all directories
        directories = [
            "data/raw/github/commits",
            "data/raw/github/commits_by_cve",
            "data/raw/github/commits_smart/top_repos",
            "data/raw/github/commits_smart/python_ecosystem",
            "data/raw/github/commits_smart/fix_commits",
        ]
        
        total_loaded = 0
        for directory in directories:
            if Path(directory).exists():
                loaded = load_commits_from_directory(driver, directory)
                total_loaded += loaded
            else:
                logger.warning(f"Directory not found: {directory}")
        
        # Final count
        with driver.session() as session:
            result = session.run("MATCH (c:Commit) RETURN count(c) as count")
            final_count = result.single()['count']
        
        logger.info("\n" + "="*60)
        logger.info("Commit loading complete!")
        logger.info(f"  Before: {existing_count:,}")
        logger.info(f"  Loaded: {total_loaded:,}")
        logger.info(f"  After: {final_count:,}")
        logger.info("="*60)
        
    finally:
        driver.close()


if __name__ == "__main__":
    main()
