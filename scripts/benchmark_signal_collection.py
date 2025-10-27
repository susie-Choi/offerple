"""Benchmark signal collection speed.

Compare old vs new (fast) signal collector.

Usage:
    python scripts/benchmark_signal_collection.py django/django
"""
import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zero_day_defense.prediction.signal_collectors.github_signals import GitHubSignalCollector
from zero_day_defense.prediction.signal_collectors.github_signals_fast import FastGitHubSignalCollector


def benchmark_old_collector(repo: str, days: int = 30):
    """Benchmark old collector.
    
    Args:
        repo: Repository name
        days: Days to look back
        
    Returns:
        Tuple of (commits, elapsed_time)
    """
    print(f"\n{'='*60}")
    print("OLD COLLECTOR (with detailed commit info)")
    print(f"{'='*60}")
    
    collector = GitHubSignalCollector()
    
    until = datetime.now()
    since = until - timedelta(days=days)
    
    start = time.time()
    commits = collector.collect_commit_history(repo, since, until)
    elapsed = time.time() - start
    
    print(f"✓ Collected {len(commits)} commits in {elapsed:.2f} seconds")
    print(f"  Average: {elapsed/len(commits):.2f} seconds per commit")
    
    return commits, elapsed


def benchmark_fast_collector(repo: str, days: int = 30):
    """Benchmark fast collector.
    
    Args:
        repo: Repository name
        days: Days to look back
        
    Returns:
        Tuple of (commits, elapsed_time)
    """
    print(f"\n{'='*60}")
    print("FAST COLLECTOR (basic info only, with caching)")
    print(f"{'='*60}")
    
    collector = FastGitHubSignalCollector()
    
    start = time.time()
    commits = collector.collect_recent_commits(repo, days=days)
    elapsed = time.time() - start
    
    print(f"✓ Collected {len(commits)} commits in {elapsed:.2f} seconds")
    if len(commits) > 0:
        print(f"  Average: {elapsed/len(commits):.3f} seconds per commit")
    
    return commits, elapsed


def benchmark_fast_collector_cached(repo: str, days: int = 30):
    """Benchmark fast collector with cache hit.
    
    Args:
        repo: Repository name
        days: Days to look back
        
    Returns:
        Tuple of (commits, elapsed_time)
    """
    print(f"\n{'='*60}")
    print("FAST COLLECTOR (2nd run - from cache)")
    print(f"{'='*60}")
    
    collector = FastGitHubSignalCollector()
    
    start = time.time()
    commits = collector.collect_recent_commits(repo, days=days)
    elapsed = time.time() - start
    
    print(f"✓ Collected {len(commits)} commits in {elapsed:.2f} seconds")
    if len(commits) > 0:
        print(f"  Average: {elapsed/len(commits):.3f} seconds per commit")
    
    return commits, elapsed


def main():
    parser = argparse.ArgumentParser(description="Benchmark signal collection")
    parser.add_argument("repo", help="Repository in format owner/repo")
    parser.add_argument("--days", type=int, default=7, help="Days to look back")
    parser.add_argument("--skip-old", action="store_true", help="Skip old collector (slow)")
    
    args = parser.parse_args()
    
    print(f"\n🔍 Benchmarking signal collection for {args.repo}")
    print(f"   Looking back {args.days} days")
    
    results = {}
    
    # Benchmark fast collector first (to populate cache)
    try:
        commits_fast, time_fast = benchmark_fast_collector(args.repo, args.days)
        results["fast"] = {"commits": len(commits_fast), "time": time_fast}
    except Exception as e:
        print(f"❌ Fast collector failed: {e}")
        return 1
    
    # Benchmark fast collector again (cache hit)
    try:
        commits_cached, time_cached = benchmark_fast_collector_cached(args.repo, args.days)
        results["cached"] = {"commits": len(commits_cached), "time": time_cached}
    except Exception as e:
        print(f"❌ Cached collector failed: {e}")
        return 1
    
    # Benchmark old collector (optional, can be very slow)
    if not args.skip_old:
        try:
            commits_old, time_old = benchmark_old_collector(args.repo, args.days)
            results["old"] = {"commits": len(commits_old), "time": time_old}
        except Exception as e:
            print(f"❌ Old collector failed: {e}")
            print("   (This is expected if there are many commits)")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    print(f"\n{'Method':<20} {'Commits':<10} {'Time (s)':<12} {'Speed':<15}")
    print("-" * 60)
    
    for method, data in results.items():
        commits = data["commits"]
        elapsed = data["time"]
        speed = f"{commits/elapsed:.1f} commits/s" if elapsed > 0 else "N/A"
        print(f"{method.upper():<20} {commits:<10} {elapsed:<12.2f} {speed:<15}")
    
    # Calculate speedup
    if "old" in results and "fast" in results:
        speedup = results["old"]["time"] / results["fast"]["time"]
        print(f"\n🚀 Speedup: {speedup:.1f}x faster")
    
    if "fast" in results and "cached" in results:
        cache_speedup = results["fast"]["time"] / results["cached"]["time"]
        print(f"💾 Cache speedup: {cache_speedup:.1f}x faster")
    
    # Real-time prediction estimate
    if "cached" in results:
        time_per_prediction = results["cached"]["time"]
        print(f"\n⚡ Real-time prediction estimate: ~{time_per_prediction:.2f} seconds per push")
        
        if time_per_prediction < 1.0:
            print("   ✅ Fast enough for real-time CI/CD integration!")
        elif time_per_prediction < 5.0:
            print("   ⚠️  Acceptable for pre-commit hooks")
        else:
            print("   ❌ Too slow for real-time use")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
