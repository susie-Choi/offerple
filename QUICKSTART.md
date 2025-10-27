# ROTA Prediction System - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Environment Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
# Create .env file
cat > .env << EOF
GITHUB_TOKEN=your_github_personal_access_token
GEMINI_API_KEY=your_gemini_api_key
EOF
```

**API Key Setup:**
- **GitHub Token**: https://github.com/settings/tokens (requires repo permission)
- **Gemini API Key**: https://makersuite.google.com/app/apikey

### Step 2: Run Your First Analysis

```bash
# Run simple demo (Apache Log4j example)
python scripts/run_prediction_demo.py --repo apache/log4j --days 30
```

**Expected Output:**
```
================================================================================
Zero-Day Defense Prediction System - Demo
================================================================================

📡 Step 1: Collecting signals from GitHub...
   Repository: apache/log4j
   Time range: Last 30 days

   Collecting commits...
   ✓ Found 45 commits
   Collecting pull requests...
   ✓ Found 12 pull requests
   Collecting issues...
   ✓ Found 23 issues
   Collecting releases...
   ✓ Found 2 releases

🔬 Step 2: Extracting features...
   ✓ Extracted 18 commit features
   ✓ Extracted 5 PR features
   ✓ Extracted 6 issue features
   ✓ Total features: 29

🧠 Step 3: Generating semantic embeddings...
   ✓ Generated embedding vector (dim: 768)

🔧 Step 4: Building feature vector...
   ✓ Feature vector created (dim: 797)

📊 Step 5: Analysis Results
================================================================================

Package: apache/log4j
Analysis Period: 2024-09-15 to 2024-10-15

Key Metrics:
  • Commits: 45
  • Pull Requests: 12
  • Issues: 23
  • Releases: 2

Commit Activity:
  • Frequency: 1.50 commits/day
  • Authors: 8 unique contributors
  • Lines Added (avg): 125
  • Lines Deleted (avg): 43

Pull Request Activity:
  • Frequency: 2.80 PRs/week
  • Merge Rate: 83.3%
  • Security Labels: 16.7%

Issue Activity:
  • Frequency: 5.36 issues/week
  • Security Keywords: 21.7%
  • Closed Rate: 65.2%

================================================================================

✅ Demo completed successfully!
```

### Step 3: Use Python API Directly

```python
from datetime import datetime, timedelta
from zero_day_defense.prediction.signal_collectors import GitHubSignalCollector
from zero_day_defense.prediction.feature_engineering import (
    FeatureExtractor,
    LLMEmbedder,
    FeatureVectorBuilder,
)

# 1. Collect signals
collector = GitHubSignalCollector()
until = datetime.utcnow()
since = until - timedelta(days=30)

commits = collector.collect_commit_history("owner/repo", since, until)
print(f"Collected commits: {len(commits)}")

# 2. Extract features
extractor = FeatureExtractor()
features = extractor.extract_commit_features(commits)
print(f"Extracted features: {len(features)}")

# 3. Generate embeddings (Gemini API)
embedder = LLMEmbedder()
embeddings = embedder.embed_commit_messages(commits)
print(f"Embedding dimension: {len(embeddings)}")

# 4. Build feature vector
builder = FeatureVectorBuilder()
vector = builder.build_vector(
    package="owner/repo",
    time_window=(since, until),
    structural_features=features,
    semantic_embeddings=embeddings,
)
print(f"Final vector dimension: {len(vector.combined)}")
```

## 📋 Common Use Cases

### Use Case 1: Analyze Specific Package

```bash
# Analyze last 90 days of activity
python scripts/run_prediction_demo.py --repo tensorflow/tensorflow --days 90

# Quick check for last 7 days
python scripts/run_prediction_demo.py --repo fastapi/fastapi --days 7
```

### Use Case 2: Compare Multiple Packages

```python
from zero_day_defense.prediction.signal_collectors import GitHubSignalCollector
from zero_day_defense.prediction.feature_engineering import FeatureExtractor
from datetime import datetime, timedelta

repos = ["django/django", "flask/flask", "fastapi/fastapi"]
collector = GitHubSignalCollector()
extractor = FeatureExtractor()

until = datetime.utcnow()
since = until - timedelta(days=30)

for repo in repos:
    commits = collector.collect_commit_history(repo, since, until)
    features = extractor.extract_commit_features(commits)
    
    print(f"\n{repo}:")
    print(f"  Commit frequency: {features['commit_frequency']:.2f} commits/day")
    print(f"  Authors: {int(features['author_diversity'])}")
    print(f"  Security file ratio: {features.get('file_type_test', 0):.1%}")
```

### Use Case 3: Detailed Analysis with LLM Agents

```python
from zero_day_defense.prediction.agents import (
    SignalAnalyzerAgent,
    ThreatAssessmentAgent,
    RecommendationAgent,
)

# Signal analysis
analyzer = SignalAnalyzerAgent()
analysis = analyzer.analyze_commits(commits, {"package": "owner/repo"})

print("Security concerns:")
for concern in analysis.get('security_concerns', []):
    print(f"  - {concern}")

# Generate threat scenario
from zero_day_defense.prediction.models import ThreatScore

threat_score = ThreatScore(
    package="owner/repo",
    score=0.75,
    confidence=0.8,
    nearest_clusters=[(0, 0.3)],
    similar_cves=[("CVE-2021-44228", 0.85)],
    risk_level="HIGH",
    predicted_at=datetime.utcnow(),
)

assessor = ThreatAssessmentAgent()
scenario = assessor.generate_threat_scenario(
    threat_score,
    analysis,
    ["CVE-2021-44228", "CVE-2021-45046"],
)

print("\nAttack vectors:")
for vector in scenario.attack_vectors:
    print(f"  - {vector}")

# Recommendations
recommender = RecommendationAgent()
recommendations = recommender.generate_recommendations(
    scenario,
    {"package": "owner/repo", "risk_level": "HIGH"},
)

print("\nImmediate actions:")
for action in recommendations.immediate_actions:
    print(f"  - {action}")
```

## 🔧 Advanced Usage

### CVE Clustering (Requires Historical CVE Data)

```python
from zero_day_defense.prediction.engine import CVEClusterer

# 1. Train clusters with historical CVE data
# (In practice, load CVE data from Neo4j)
historical_cve_vectors = []  # List of FeatureVector

clusterer = CVEClusterer(n_clusters=10, algorithm="kmeans")
clusterer.fit(historical_cve_vectors)

# 2. Classify new package
cluster_id, distance = clusterer.predict_cluster(vector)
print(f"Cluster: {cluster_id}, Distance: {distance:.3f}")

# 3. Check cluster information
metadata = clusterer.get_cluster_metadata(cluster_id)
print(f"Cluster size: {metadata.size}")
print(f"Average CVSS: {metadata.avg_cvss:.1f}")
```

### Threat Score Calculation

```python
from zero_day_defense.prediction.engine import PredictionScorer

scorer = PredictionScorer(clusterer, threshold=0.7)
threat_score = scorer.score_package(vector)

print(f"Threat score: {threat_score.score:.2f}")
print(f"Risk level: {threat_score.risk_level}")
print(f"Confidence: {threat_score.confidence:.2f}")

print("\nSimilar CVEs:")
for cve_id, similarity in threat_score.similar_cves:
    print(f"  {cve_id}: {similarity:.3f}")
```

## 🐛 Troubleshooting

### GitHub API Rate Limit

```python
# Check current rate limit
import requests
response = requests.get(
    "https://api.github.com/rate_limit",
    headers={"Authorization": f"Bearer {your_token}"}
)
print(response.json())
```

**Solutions:**
- Set GITHUB_TOKEN environment variable (5,000 requests/hour)
- Add delay between requests
- Use caching

### Gemini API Errors

```python
# Test API key
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Hello")
print(response.text)
```

**Solutions:**
- Check GEMINI_API_KEY or GOOGLE_API_KEY environment variable
- Check API quota (Free tier: 15 RPM)
- Add delay between requests

### Out of Memory

```python
# Use batch processing to save memory
repos = ["repo1", "repo2", "repo3", ...]

for repo in repos:
    # Process each repo individually
    commits = collector.collect_commit_history(repo, since, until)
    # ... process ...
    del commits  # Free memory
```

## 📚 Next Steps

1. **Collect Real CVE Data**: Run `scripts/collect_cve_data.py`
2. **Neo4j Integration**: Load CVE data into Neo4j
3. **Train Clusters**: Train cluster model with historical CVEs
4. **Automation**: Set up scheduler for regular analysis

## 💡 Tips

- **Start with Small Projects**: Large projects require many API calls and take longer
- **Use Caching**: Reuse saved signals when analyzing same data repeatedly
- **Batch Processing**: Process multiple packages in batches
- **Check Logs**: Review detailed logs when issues occur

## 🆘 Help

- Detailed Guide: `docs/guides/prediction_system_guide.md`
- Implementation Summary: `docs/IMPLEMENTATION_SUMMARY.md`
- Report Issues: GitHub Issues
