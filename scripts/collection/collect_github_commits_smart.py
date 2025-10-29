"""Smart GitHub commit collection with mixed strategy."""
import argparse
import json
import logging
import os
import re
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from rota.spokes.github import GitHubSignalsCollector as GitHubDataSource

load_dotenv()

logger = logging.getLogger(__name__)


def extract_commit_sha(text):
    """Extract commit SHA from text (40 hex chars)."""
    pattern = r'\b[0-9a-f]{40}\b'
    return re.findall(pattern, text.lower())


def main():
    parser = argparse.ArgumentParser(
        description="Smart GitHub commit collection (mixed strategy)"
    )
    parser.add_argument(
        "--strategy",
        choices=["top-repos", "fix-commits", "python-only", "all"],
        default="all",
        help="Collection strategy",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=50,
        help="Number of top repos to collect (for top-repos strategy)",
    )
    parser.add_argument(
        "--commits-per-repo",
        type=int,
        default=1000,
        help="Max commits per repo (for top-repos strategy)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/github/commits_smart"),
        help="Output directory",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize GitHub data source
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN not found!")
        return
    
    logger.info(f"Using GitHub token: {github_token[:20]}...")
    github_source = GitHubDataSource(
        timeout=30.0,
        rate_limit_sleep=1.0,
        github_token=github_token,
    )
    
    stats = {
        "strategy": args.strategy,
        "total_repos": 0,
        "total_commits": 0,
        "start_time": datetime.now().isoformat(),
    }
    
    # Strategy 1: Top repos
    if args.strategy in ["top-repos", "all"]:
        logger.info(f"\n{'='*60}")
        logger.info("Strategy 1: Top {args.top_n} repos by CVE count")
        logger.info(f"{'='*60}")
        
        # Load CVE to repo mapping
        mapping_file = Path("data/processed/cve_github_mapping.jsonl")
        repos_counter = Counter()
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                for repo in data['repos']:
                    repos_counter[repo] += 1
        
        top_repos = [repo for repo, count in repos_counter.most_common(args.top_n)]
        logger.info(f"Top {len(top_repos)} repos:")
        for i, (repo, count) in enumerate(repos_counter.most_common(args.top_n), 1):
            logger.info(f"  {i:2d}. {repo:40s} ({count} CVEs)")
        
        # Collect commits from top repos
        for repo in tqdm(top_repos, desc="Collecting top repos"):
            try:
                owner, repo_name = repo.split('/')
                output_file = args.output_dir / "top_repos" / f"{owner}_{repo_name}.jsonl"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                if output_file.exists():
                    logger.info(f"Skipping {repo} (already collected)")
                    continue
                
                commit_count = 0
                with open(output_file, 'w', encoding='utf-8') as f:
                    for commit in github_source.collect_commits_streaming(
                        owner=owner,
                        repo=repo_name,
                        max_commits=args.commits_per_repo
                    ):
                        record = {
                            "source": "top_repos",
                            "repo": repo,
                            "collected_at": datetime.now().isoformat(),
                            "payload": commit,
                        }
                        f.write(json.dumps(record, ensure_ascii=False) + '\n')
                        f.flush()
                        commit_count += 1
                
                logger.info(f"  {repo}: {commit_count} commits")
                stats["total_commits"] += commit_count
                stats["total_repos"] += 1
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error with {repo}: {e}")
                continue
    
    # Strategy 2: Fix commits
    if args.strategy in ["fix-commits", "all"]:
        logger.info(f"\n{'='*60}")
        logger.info("Strategy 2: CVE fix commits")
        logger.info(f"{'='*60}")
        
        # Load CVE data and extract commit SHAs
        cve_file = Path("data/raw/bulk_cve_data.jsonl")
        fix_commits = []
        
        logger.info("Extracting commit SHAs from CVE references...")
        with open(cve_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                payload = data.get('payload', {})
                vulns = payload.get('vulnerabilities', [])
                
                if not vulns:
                    continue
                
                cve_data = vulns[0].get('cve', {})
                cve_id = cve_data.get('id')
                references = cve_data.get('references', [])
                
                for ref in references:
                    url = ref.get('url', '')
                    # Look for GitHub commit URLs
                    if 'github.com' in url and '/commit/' in url:
                        match = re.search(r'github\.com/([^/]+)/([^/]+)/commit/([0-9a-f]{40})', url)
                        if match:
                            owner, repo, sha = match.groups()
                            fix_commits.append({
                                'cve_id': cve_id,
                                'repo': f"{owner}/{repo}",
                                'sha': sha,
                                'url': url
                            })
        
        logger.info(f"Found {len(fix_commits)} fix commits")
        
        # Collect fix commits
        output_file = args.output_dir / "fix_commits" / "all_fix_commits.jsonl"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for fix_info in tqdm(fix_commits[:100], desc="Collecting fix commits"):  # Limit to 100
                try:
                    owner, repo = fix_info['repo'].split('/')
                    sha = fix_info['sha']
                    
                    # Get the specific commit
                    response = github_source._request(
                        "GET",
                        f"{github_source.API_URL}/repos/{owner}/{repo}/commits/{sha}",
                        headers=github_source._headers()
                    )
                    commit = response.json()
                    
                    record = {
                        "source": "fix_commit",
                        "cve_id": fix_info['cve_id'],
                        "repo": fix_info['repo'],
                        "sha": sha,
                        "collected_at": datetime.now().isoformat(),
                        "payload": commit,
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
                    f.flush()
                    stats["total_commits"] += 1
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error with {fix_info['repo']}/{sha}: {e}")
                    continue
    
    # Strategy 3: Python ecosystem
    if args.strategy in ["python-only", "all"]:
        logger.info(f"\n{'='*60}")
        logger.info("Strategy 3: Python ecosystem projects")
        logger.info(f"{'='*60}")
        
        # Find Python-related CVEs
        python_keywords = ['python', 'pip', 'pypi', 'django', 'flask', 'requests']
        python_repos = set()
        
        mapping_file = Path("data/processed/cve_github_mapping.jsonl")
        cve_file = Path("data/raw/bulk_cve_data.jsonl")
        
        # Load CVE descriptions
        cve_descriptions = {}
        with open(cve_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                payload = data.get('payload', {})
                vulns = payload.get('vulnerabilities', [])
                if vulns:
                    cve_data = vulns[0].get('cve', {})
                    cve_id = cve_data.get('id')
                    descriptions = cve_data.get('descriptions', [])
                    if descriptions:
                        desc = descriptions[0].get('value', '').lower()
                        cve_descriptions[cve_id] = desc
        
        # Find Python-related repos
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                cve_id = data['cve_id']
                desc = cve_descriptions.get(cve_id, '')
                
                if any(keyword in desc for keyword in python_keywords):
                    python_repos.update(data['repos'])
        
        python_repos = list(python_repos)[:20]  # Limit to 20
        logger.info(f"Found {len(python_repos)} Python-related repos")
        
        # Collect commits
        for repo in tqdm(python_repos, desc="Collecting Python repos"):
            try:
                owner, repo_name = repo.split('/')
                output_file = args.output_dir / "python_ecosystem" / f"{owner}_{repo_name}.jsonl"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                if output_file.exists():
                    continue
                
                commit_count = 0
                with open(output_file, 'w', encoding='utf-8') as f:
                    for commit in github_source.collect_commits_streaming(
                        owner=owner,
                        repo=repo_name,
                        max_commits=500
                    ):
                        record = {
                            "source": "python_ecosystem",
                            "repo": repo,
                            "collected_at": datetime.now().isoformat(),
                            "payload": commit,
                        }
                        f.write(json.dumps(record, ensure_ascii=False) + '\n')
                        f.flush()
                        commit_count += 1
                
                logger.info(f"  {repo}: {commit_count} commits")
                stats["total_commits"] += commit_count
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error with {repo}: {e}")
                continue
    
    # Save statistics
    stats["end_time"] = datetime.now().isoformat()
    stats_file = args.output_dir / "collection_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Collection complete!")
    logger.info(f"  Total repos: {stats['total_repos']}")
    logger.info(f"  Total commits: {stats['total_commits']:,}")
    logger.info(f"  Output directory: {args.output_dir}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
