"""Analyze all commit data sources to understand what we have."""
import json
from pathlib import Path
from collections import defaultdict

def count_commits_in_files(directory):
    """Count commits in jsonl files."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return 0, 0
    
    files = list(dir_path.glob("**/*.jsonl"))
    total_commits = 0
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    json.loads(line)
                    total_commits += 1
                except:
                    pass
    
    return len(files), total_commits

print("="*80)
print("Commit Data Source Analysis")
print("="*80)

# Check each directory
directories = [
    "data/raw/github/commits",
    "data/raw/github/commits_by_cve",
    "data/raw/github/commits_smart",
]

total_files = 0
total_commits = 0

for directory in directories:
    file_count, commit_count = count_commits_in_files(directory)
    total_files += file_count
    total_commits += commit_count
    print(f"\n{directory}:")
    print(f"  Files: {file_count:,}")
    print(f"  Commits: {commit_count:,}")

print(f"\n{'='*80}")
print(f"Total:")
print(f"  Files: {total_files:,}")
print(f"  Commits in files: {total_commits:,}")
print(f"  Commits in Neo4j: 183,917")
print(f"{'='*80}")
