"""Bulk collect GitHub commits for repositories linked to CVEs."""
import argparse
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from rota.spokes.github import GitHubSignalsCollector as GitHubDataSource

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Bulk collect GitHub commits for CVE-linked repositories"
    )
    parser.add_argument(
        "--repos-file",
        type=Path,
        default=Path("data/processed/github_repos_from_cve.txt"),
        help="File containing list of GitHub repos (owner/repo format)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/github/commits"),
        help="Output directory for commit data",
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        help="Maximum number of repos to process",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Skip first N repos (for resuming)",
    )
    parser.add_argument(
        "--commits-per-repo",
        type=int,
        default=1000,
        help="Maximum commits to collect per repo",
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
    
    # Load repos list
    if not args.repos_file.exists():
        logger.error(f"Repos file not found: {args.repos_file}")
        return
    
    with open(args.repos_file, 'r') as f:
        all_repos = [line.strip() for line in f if line.strip()]
    
    # Apply skip and max
    repos = all_repos[args.skip:]
    if args.max_repos:
        repos = repos[:args.max_repos]
    
    logger.info(f"Total repos in file: {len(all_repos)}")
    logger.info(f"Processing repos: {len(repos)} (skipped {args.skip})")
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize GitHub data source
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        logger.info(f"Using GitHub token: {github_token[:20]}...")
    else:
        logger.warning("No GitHub token found - using public rate limits!")
    
    github_source = GitHubDataSource(
        timeout=30.0,
        rate_limit_sleep=1.0,
        github_token=github_token,
    )
    
    # Statistics
    stats = {
        "total_repos": len(repos),
        "successful": 0,
        "failed": 0,
        "total_commits": 0,
        "start_time": datetime.now().isoformat(),
    }
    
    # Process each repo
    for i, repo in enumerate(tqdm(repos, desc="Collecting commits")):
        try:
            owner, repo_name = repo.split('/')
            
            # Output file for this repo
            output_file = args.output_dir / f"{owner}_{repo_name}_commits.jsonl"
            
            # Skip if already collected
            if output_file.exists():
                logger.info(f"Skipping {repo} (already collected)")
                stats["successful"] += 1
                continue
            
            logger.info(f"[{i+1}/{len(repos)}] Collecting: {repo}")
            
            # Collect commits with streaming
            commit_count = 0
            with open(output_file, 'w', encoding='utf-8') as f:
                try:
                    for commit in github_source.collect_commits_streaming(
                        owner=owner,
                        repo=repo_name,
                        max_commits=args.commits_per_repo
                    ):
                        record = {
                            "source": "github_commits",
                            "repo": repo,
                            "collected_at": datetime.now().isoformat(),
                            "payload": commit,
                        }
                        f.write(json.dumps(record, ensure_ascii=False) + '\n')
                        f.flush()
                        commit_count += 1
                    
                    logger.info(f"  → Collected {commit_count} commits")
                    stats["successful"] += 1
                    stats["total_commits"] += commit_count
                    
                except Exception as e:
                    logger.error(f"  → Error: {e}")
                    stats["failed"] += 1
                    # Keep partial data
                    if commit_count > 0:
                        logger.info(f"  → Saved {commit_count} partial commits")
                        stats["total_commits"] += commit_count
            
            # Rate limiting
            time.sleep(1.0)
            
        except Exception as e:
            logger.error(f"Failed to process {repo}: {e}")
            stats["failed"] += 1
            continue
    
    # Save statistics
    stats["end_time"] = datetime.now().isoformat()
    stats_file = args.output_dir / "collection_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Collection complete!")
    logger.info(f"  Successful: {stats['successful']}")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info(f"  Total commits: {stats['total_commits']:,}")
    logger.info(f"  Output directory: {args.output_dir}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
