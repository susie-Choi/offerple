"""Collect GitHub commits around CVE publication dates."""
import argparse
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from rota.spokes.github import GitHubSignalsCollector as GitHubDataSource

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def parse_cve_date(date_str):
    """Parse CVE date string to datetime."""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Collect GitHub commits around CVE publication dates"
    )
    parser.add_argument(
        "--cve-mapping",
        type=Path,
        default=Path("data/processed/cve_github_mapping.jsonl"),
        help="CVE to GitHub repo mapping file",
    )
    parser.add_argument(
        "--cve-data",
        type=Path,
        default=Path("data/raw/bulk_cve_data.jsonl"),
        help="CVE data file with dates",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/github/commits_by_cve"),
        help="Output directory",
    )
    parser.add_argument(
        "--max-cves",
        type=int,
        help="Maximum number of CVEs to process",
    )
    parser.add_argument(
        "--days-before",
        type=int,
        default=365,
        help="Days before CVE publication to collect commits",
    )
    parser.add_argument(
        "--days-after",
        type=int,
        default=30,
        help="Days after CVE publication to collect commits",
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
    
    # Load CVE to repo mapping
    logger.info("Loading CVE to GitHub mapping...")
    cve_repos = {}
    with open(args.cve_mapping, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            cve_repos[data['cve_id']] = data['repos']
    
    logger.info(f"Loaded {len(cve_repos)} CVEs with GitHub links")
    
    # Load CVE dates
    logger.info("Loading CVE publication dates...")
    cve_dates = {}
    with open(args.cve_data, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            payload = data.get('payload', {})
            vulns = payload.get('vulnerabilities', [])
            if vulns:
                cve_data = vulns[0].get('cve', {})
                cve_id = cve_data.get('id')
                published = cve_data.get('published')
                if cve_id and published:
                    pub_date = parse_cve_date(published)
                    if pub_date:
                        cve_dates[cve_id] = pub_date
    
    logger.info(f"Loaded {len(cve_dates)} CVE dates")
    
    # Match CVEs with both repos and dates
    cves_to_process = []
    for cve_id in cve_repos:
        if cve_id in cve_dates:
            cves_to_process.append({
                'cve_id': cve_id,
                'repos': cve_repos[cve_id],
                'published': cve_dates[cve_id]
            })
    
    logger.info(f"Found {len(cves_to_process)} CVEs with both GitHub links and dates")
    
    if args.max_cves:
        cves_to_process = cves_to_process[:args.max_cves]
        logger.info(f"Processing first {args.max_cves} CVEs")
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize GitHub data source
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        logger.info(f"Using GitHub token: {github_token[:20]}...")
    else:
        logger.warning("No GitHub token - rate limits will be strict!")
    
    github_source = GitHubDataSource(
        timeout=30.0,
        rate_limit_sleep=1.0,
        github_token=github_token,
    )
    
    # Statistics
    stats = {
        "total_cves": len(cves_to_process),
        "successful": 0,
        "failed": 0,
        "total_commits": 0,
    }
    
    # Process each CVE
    for cve_info in tqdm(cves_to_process, desc="Processing CVEs"):
        cve_id = cve_info['cve_id']
        pub_date = cve_info['published']
        repos = cve_info['repos']
        
        # Calculate date range
        since = pub_date - timedelta(days=args.days_before)
        until = pub_date + timedelta(days=args.days_after)
        
        logger.info(f"Processing {cve_id} (published: {pub_date.date()})")
        logger.info(f"  Date range: {since.date()} to {until.date()}")
        logger.info(f"  Repos: {repos}")
        
        # Output file for this CVE
        output_file = args.output_dir / f"{cve_id}_commits.jsonl"
        
        if output_file.exists():
            logger.info(f"  Skipping (already collected)")
            stats["successful"] += 1
            continue
        
        commit_count = 0
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for repo in repos:
                    try:
                        owner, repo_name = repo.split('/')
                        
                        # Collect commits in date range
                        for commit in github_source.collect_commits_in_range(
                            owner=owner,
                            repo=repo_name,
                            since=since,
                            until=until
                        ):
                            record = {
                                "cve_id": cve_id,
                                "repo": repo,
                                "collected_at": datetime.now().isoformat(),
                                "payload": commit,
                            }
                            f.write(json.dumps(record, ensure_ascii=False) + '\n')
                            f.flush()
                            commit_count += 1
                        
                    except Exception as e:
                        logger.error(f"  Error with repo {repo}: {e}")
                        continue
            
            logger.info(f"  → Collected {commit_count} commits")
            stats["successful"] += 1
            stats["total_commits"] += commit_count
            
        except Exception as e:
            logger.error(f"  Failed: {e}")
            stats["failed"] += 1
        
        time.sleep(1.0)
    
    # Save statistics
    stats_file = args.output_dir / "collection_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Collection complete!")
    logger.info(f"  Successful CVEs: {stats['successful']}")
    logger.info(f"  Failed CVEs: {stats['failed']}")
    logger.info(f"  Total commits: {stats['total_commits']:,}")
    logger.info(f"  Output directory: {args.output_dir}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
