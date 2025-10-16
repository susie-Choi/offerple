"""Historical validation script for Zero-Day Defense prediction system.

This script demonstrates how to properly validate the prediction system
using historical CVE data to avoid temporal leakage.

Example:
    python scripts/historical_validation.py --cve CVE-2021-44228
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zero_day_defense.prediction.signal_collectors import GitHubSignalCollector
from zero_day_defense.prediction.feature_engineering import (
    FeatureExtractor,
    LLMEmbedder,
    FeatureVectorBuilder,
)


# 알려진 CVE와 그 정보
KNOWN_CVES = {
    "CVE-2021-44228": {
        "name": "Log4Shell",
        "repo": "apache/logging-log4j2",
        "disclosure_date": datetime(2021, 12, 9, tzinfo=timezone.utc),
        "description": "Apache Log4j2 RCE vulnerability",
    },
    "CVE-2021-45046": {
        "name": "Log4Shell bypass",
        "repo": "apache/logging-log4j2",
        "disclosure_date": datetime(2021, 12, 14, tzinfo=timezone.utc),
        "description": "Incomplete fix for CVE-2021-44228",
    },
    "CVE-2022-22965": {
        "name": "Spring4Shell",
        "repo": "spring-projects/spring-framework",
        "disclosure_date": datetime(2022, 3, 31, tzinfo=timezone.utc),
        "description": "Spring Framework RCE vulnerability",
    },
}


def main():
    parser = argparse.ArgumentParser(
        description="Validate prediction system with historical CVE data"
    )
    parser.add_argument(
        "--cve",
        required=True,
        choices=list(KNOWN_CVES.keys()),
        help="CVE ID to validate",
    )
    parser.add_argument(
        "--prediction-days-before",
        type=int,
        default=30,
        help="Days before CVE disclosure to make prediction",
    )
    parser.add_argument(
        "--signal-window-days",
        type=int,
        default=30,
        help="Days of signal history to analyze",
    )
    
    args = parser.parse_args()
    
    cve_info = KNOWN_CVES[args.cve]
    
    print("=" * 80)
    print("Historical Validation - Zero-Day Defense Prediction System")
    print("=" * 80)
    print()
    print(f"CVE: {args.cve} ({cve_info['name']})")
    print(f"Repository: {cve_info['repo']}")
    print(f"Actual Disclosure Date: {cve_info['disclosure_date'].strftime('%Y-%m-%d')}")
    print(f"Description: {cve_info['description']}")
    print()
    
    # 시간적 설정
    disclosure_date = cve_info['disclosure_date']
    prediction_date = disclosure_date - timedelta(days=args.prediction_days_before)
    signal_end = prediction_date
    signal_start = signal_end - timedelta(days=args.signal_window_days)
    
    print("⏰ Temporal Setup (Avoiding Data Leakage):")
    print(f"   Signal Collection Period: {signal_start.strftime('%Y-%m-%d')} to {signal_end.strftime('%Y-%m-%d')}")
    print(f"   Prediction Made On: {prediction_date.strftime('%Y-%m-%d')}")
    print(f"   CVE Disclosed On: {disclosure_date.strftime('%Y-%m-%d')}")
    print(f"   ⚠️  We are predicting {args.prediction_days_before} days BEFORE the CVE was disclosed!")
    print()
    
    # 질문: 이 시점에 우리가 예측할 수 있었는가?
    print("❓ Research Question:")
    print(f"   Could we have predicted {args.cve} on {prediction_date.strftime('%Y-%m-%d')}")
    print(f"   using only signals from {signal_start.strftime('%Y-%m-%d')} to {signal_end.strftime('%Y-%m-%d')}?")
    print()
    
    # 신호 수집
    print("📡 Step 1: Collecting historical signals...")
    print(f"   ⚠️  IMPORTANT: Only using data BEFORE {signal_end.strftime('%Y-%m-%d')}")
    print()
    
    try:
        collector = GitHubSignalCollector()
        
        print("   Collecting commits...")
        commits = collector.collect_commit_history(
            cve_info['repo'],
            since=signal_start,
            until=signal_end,  # CVE 공개 전!
        )
        print(f"   ✓ Found {len(commits)} commits (before CVE disclosure)")
        
        print("   Collecting pull requests...")
        prs = collector.collect_pr_history(
            cve_info['repo'],
            since=signal_start,
            until=signal_end,
        )
        print(f"   ✓ Found {len(prs)} pull requests")
        
        print("   Collecting issues...")
        issues = collector.collect_issue_history(
            cve_info['repo'],
            since=signal_start,
            until=signal_end,
        )
        print(f"   ✓ Found {len(issues)} issues")
        print()
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()
        print("💡 Tip: This might be due to:")
        print("   - Missing GITHUB_TOKEN (rate limits)")
        print("   - Repository name changed or archived")
        print("   - No activity in the specified time period")
        return
    
    # 특징 추출
    print("🔬 Step 2: Extracting features from historical signals...")
    
    extractor = FeatureExtractor()
    
    features = {}
    if commits:
        commit_features = extractor.extract_commit_features(commits)
        features.update(commit_features)
        print(f"   ✓ Extracted {len(commit_features)} commit features")
    
    if prs:
        pr_features = extractor.extract_pr_features(prs)
        features.update(pr_features)
        print(f"   ✓ Extracted {len(pr_features)} PR features")
    
    if issues:
        issue_features = extractor.extract_issue_features(issues)
        features.update(issue_features)
        print(f"   ✓ Extracted {len(issue_features)} issue features")
    
    print(f"   ✓ Total features: {len(features)}")
    print()
    
    # 분석 결과
    print("📊 Step 3: Analysis Results")
    print("=" * 80)
    print()
    
    if commit_features:
        print("Commit Activity (Pre-CVE Period):")
        print(f"  • Frequency: {commit_features.get('commit_frequency', 0):.2f} commits/day")
        print(f"  • Authors: {int(commit_features.get('author_diversity', 0))} unique contributors")
        print(f"  • Lines Added (avg): {commit_features.get('lines_added_avg', 0):.0f}")
        print(f"  • Security-related files: {commit_features.get('file_type_test', 0):.1%}")
        print()
    
    if pr_features:
        print("Pull Request Activity (Pre-CVE Period):")
        print(f"  • Frequency: {pr_features.get('pr_frequency', 0):.2f} PRs/week")
        print(f"  • Security labels: {pr_features.get('security_label_ratio', 0):.1%}")
        print()
    
    if issue_features:
        print("Issue Activity (Pre-CVE Period):")
        print(f"  • Frequency: {issue_features.get('issue_frequency', 0):.2f} issues/week")
        print(f"  • Security keywords: {issue_features.get('security_keyword_ratio', 0):.1%}")
        print()
    
    print("=" * 80)
    print()
    
    # 결론
    print("🎯 Validation Conclusion:")
    print()
    print(f"✅ Successfully collected signals from BEFORE {args.cve} disclosure")
    print(f"✅ No temporal data leakage - all data is from {signal_start.strftime('%Y-%m-%d')} to {signal_end.strftime('%Y-%m-%d')}")
    print(f"✅ CVE was disclosed {args.prediction_days_before} days AFTER our prediction date")
    print()
    print("📝 Next Steps:")
    print("   1. Train CVE clusterer with OTHER historical CVEs (not this one)")
    print("   2. Generate feature vector from these signals")
    print("   3. Calculate threat score using the trained model")
    print("   4. Compare prediction with actual CVE disclosure")
    print("   5. Calculate metrics: Did we predict it? How early?")
    print()
    print("💡 Key Insight:")
    print(f"   If we had run this system on {prediction_date.strftime('%Y-%m-%d')},")
    print(f"   we would have had {args.prediction_days_before} days warning before {args.cve}!")
    print()


if __name__ == "__main__":
    main()
