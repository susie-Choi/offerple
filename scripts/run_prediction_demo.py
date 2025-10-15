"""Demo script for Zero-Day Defense prediction system."""
import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from zero_day_defense.prediction.signal_collectors import GitHubSignalCollector, TimeSeriesStore
from zero_day_defense.prediction.feature_engineering import FeatureExtractor, LLMEmbedder, FeatureVectorBuilder
from zero_day_defense.prediction.engine import CVEClusterer, PredictionScorer
from zero_day_defense.prediction.agents import SignalAnalyzerAgent, ThreatAssessmentAgent, RecommendationAgent


def main():
    parser = argparse.ArgumentParser(description="Run Zero-Day Defense prediction demo")
    parser.add_argument("--repo", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--days", type=int, default=30, help="Days of history to analyze")
    parser.add_argument("--output-dir", default="data/signals", help="Output directory for signals")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Zero-Day Defense Prediction System - Demo")
    print("=" * 80)
    print()
    
    # Check for API keys
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not github_token:
        print("⚠️  Warning: GITHUB_TOKEN not set. API rate limits will be restrictive.")
    
    if not gemini_key:
        print("⚠️  Warning: GEMINI_API_KEY not set. LLM features will be disabled.")
    
    print()
    
    # Step 1: Collect signals
    print("📡 Step 1: Collecting signals from GitHub...")
    print(f"   Repository: {args.repo}")
    print(f"   Time range: Last {args.days} days")
    print()
    
    collector = GitHubSignalCollector(github_token=github_token)
    
    from datetime import timezone
    until = datetime.now(timezone.utc)
    since = until - timedelta(days=args.days)
    
    try:
        print("   Collecting commits...")
        commits = collector.collect_commit_history(args.repo, since, until)
        print(f"   ✓ Found {len(commits)} commits")
        
        print("   Collecting pull requests...")
        prs = collector.collect_pr_history(args.repo, since, until)
        print(f"   ✓ Found {len(prs)} pull requests")
        
        print("   Collecting issues...")
        issues = collector.collect_issue_history(args.repo, since, until)
        print(f"   ✓ Found {len(issues)} issues")
        
        print("   Collecting releases...")
        releases = collector.collect_release_history(args.repo, since, until)
        print(f"   ✓ Found {len(releases)} releases")
        print()
        
    except Exception as e:
        print(f"   ✗ Error collecting signals: {e}")
        return
    
    # Step 2: Extract features
    print("🔬 Step 2: Extracting features...")
    
    extractor = FeatureExtractor()
    
    try:
        if commits:
            commit_features = extractor.extract_commit_features(commits)
            print(f"   ✓ Extracted {len(commit_features)} commit features")
        else:
            commit_features = {}
            print("   ⚠️  No commits to analyze")
        
        if prs:
            pr_features = extractor.extract_pr_features(prs)
            print(f"   ✓ Extracted {len(pr_features)} PR features")
        else:
            pr_features = {}
        
        if issues:
            issue_features = extractor.extract_issue_features(issues)
            print(f"   ✓ Extracted {len(issue_features)} issue features")
        else:
            issue_features = {}
        
        # Combine all features
        all_features = {**commit_features, **pr_features, **issue_features}
        print(f"   ✓ Total features: {len(all_features)}")
        print()
        
    except Exception as e:
        print(f"   ✗ Error extracting features: {e}")
        return
    
    # Step 3: Generate embeddings (if Gemini key available)
    if gemini_key and commits:
        print("🧠 Step 3: Generating semantic embeddings...")
        try:
            embedder = LLMEmbedder(api_key=gemini_key)
            embeddings = embedder.embed_commit_messages(commits)
            print(f"   ✓ Generated embedding vector (dim: {len(embeddings)})")
            print()
        except Exception as e:
            print(f"   ⚠️  Embedding generation failed: {e}")
            print("   Using zero vector as fallback")
            import numpy as np
            embeddings = np.zeros(768)
            print()
    else:
        print("⏭️  Step 3: Skipping embeddings (no API key or no commits)")
        import numpy as np
        embeddings = np.zeros(768)
        print()
    
    # Step 4: Build feature vector
    print("🔧 Step 4: Building feature vector...")
    try:
        builder = FeatureVectorBuilder()
        vector = builder.build_vector(
            package=args.repo,
            time_window=(since, until),
            structural_features=all_features,
            semantic_embeddings=embeddings,
        )
        print(f"   ✓ Feature vector created (dim: {len(vector.combined)})")
        print()
    except Exception as e:
        print(f"   ✗ Error building vector: {e}")
        return
    
    # Step 5: Display results
    print("📊 Step 5: Analysis Results")
    print("=" * 80)
    print()
    print(f"Package: {args.repo}")
    print(f"Analysis Period: {since.strftime('%Y-%m-%d')} to {until.strftime('%Y-%m-%d')}")
    print()
    print("Key Metrics:")
    print(f"  • Commits: {len(commits)}")
    print(f"  • Pull Requests: {len(prs)}")
    print(f"  • Issues: {len(issues)}")
    print(f"  • Releases: {len(releases)}")
    print()
    
    if commit_features:
        print("Commit Activity:")
        print(f"  • Frequency: {commit_features.get('commit_frequency', 0):.2f} commits/day")
        print(f"  • Authors: {int(commit_features.get('author_diversity', 0))} unique contributors")
        print(f"  • Lines Added (avg): {commit_features.get('lines_added_avg', 0):.0f}")
        print(f"  • Lines Deleted (avg): {commit_features.get('lines_deleted_avg', 0):.0f}")
        print()
    
    if pr_features:
        print("Pull Request Activity:")
        print(f"  • Frequency: {pr_features.get('pr_frequency', 0):.2f} PRs/week")
        print(f"  • Merge Rate: {pr_features.get('pr_merged_ratio', 0):.1%}")
        print(f"  • Security Labels: {pr_features.get('security_label_ratio', 0):.1%}")
        print()
    
    if issue_features:
        print("Issue Activity:")
        print(f"  • Frequency: {issue_features.get('issue_frequency', 0):.2f} issues/week")
        print(f"  • Security Keywords: {issue_features.get('security_keyword_ratio', 0):.1%}")
        print(f"  • Closed Rate: {issue_features.get('closed_ratio', 0):.1%}")
        print()
    
    print("=" * 80)
    print()
    print("✅ Demo completed successfully!")
    print()
    print("Next steps:")
    print("  1. Train a CVE clusterer with historical CVE data")
    print("  2. Use PredictionScorer to calculate threat scores")
    print("  3. Run LLM agents for detailed threat analysis")
    print("  4. Integrate with Neo4j for data persistence")
    print()


if __name__ == "__main__":
    main()
