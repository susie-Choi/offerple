# Zero-Day Defense 예측 시스템 - 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 1단계: 환경 설정

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
# .env 파일 생성
cat > .env << EOF
GITHUB_TOKEN=your_github_personal_access_token
GEMINI_API_KEY=your_gemini_api_key
EOF
```

**API 키 발급 방법:**
- **GitHub Token**: https://github.com/settings/tokens (repo 권한 필요)
- **Gemini API Key**: https://makersuite.google.com/app/apikey

### 2단계: 첫 번째 분석 실행

```bash
# 간단한 데모 실행 (Apache Log4j 예시)
python scripts/run_prediction_demo.py --repo apache/log4j --days 30
```

**출력 예시:**
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

### 3단계: Python API로 직접 사용

```python
from datetime import datetime, timedelta
from zero_day_defense.prediction.signal_collectors import GitHubSignalCollector
from zero_day_defense.prediction.feature_engineering import (
    FeatureExtractor,
    LLMEmbedder,
    FeatureVectorBuilder,
)

# 1. 신호 수집
collector = GitHubSignalCollector()
until = datetime.utcnow()
since = until - timedelta(days=30)

commits = collector.collect_commit_history("owner/repo", since, until)
print(f"수집된 커밋: {len(commits)}개")

# 2. 특징 추출
extractor = FeatureExtractor()
features = extractor.extract_commit_features(commits)
print(f"추출된 특징: {len(features)}개")

# 3. 임베딩 생성 (Gemini API)
embedder = LLMEmbedder()
embeddings = embedder.embed_commit_messages(commits)
print(f"임베딩 차원: {len(embeddings)}")

# 4. 특징 벡터 생성
builder = FeatureVectorBuilder()
vector = builder.build_vector(
    package="owner/repo",
    time_window=(since, until),
    structural_features=features,
    semantic_embeddings=embeddings,
)
print(f"최종 벡터 차원: {len(vector.combined)}")
```

## 📋 주요 사용 시나리오

### 시나리오 1: 특정 패키지 분석

```bash
# 최근 90일 동안의 활동 분석
python scripts/run_prediction_demo.py --repo tensorflow/tensorflow --days 90

# 최근 7일 동안의 활동 분석 (빠른 체크)
python scripts/run_prediction_demo.py --repo fastapi/fastapi --days 7
```

### 시나리오 2: 여러 패키지 비교

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
    print(f"  커밋 빈도: {features['commit_frequency']:.2f} commits/day")
    print(f"  작성자 수: {int(features['author_diversity'])}")
    print(f"  보안 파일 비율: {features.get('file_type_test', 0):.1%}")
```

### 시나리오 3: LLM Agent로 상세 분석

```python
from zero_day_defense.prediction.agents import (
    SignalAnalyzerAgent,
    ThreatAssessmentAgent,
    RecommendationAgent,
)

# 신호 분석
analyzer = SignalAnalyzerAgent()
analysis = analyzer.analyze_commits(commits, {"package": "owner/repo"})

print("보안 우려사항:")
for concern in analysis.get('security_concerns', []):
    print(f"  - {concern}")

# 위협 시나리오 생성 (가상의 threat_score 사용)
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

print("\n공격 벡터:")
for vector in scenario.attack_vectors:
    print(f"  - {vector}")

# 대응 방안
recommender = RecommendationAgent()
recommendations = recommender.generate_recommendations(
    scenario,
    {"package": "owner/repo", "risk_level": "HIGH"},
)

print("\n즉각 조치:")
for action in recommendations.immediate_actions:
    print(f"  - {action}")
```

## 🔧 고급 사용법

### CVE 클러스터링 (과거 CVE 데이터 필요)

```python
from zero_day_defense.prediction.engine import CVEClusterer

# 1. 과거 CVE 데이터로 클러스터 학습
# (실제로는 Neo4j에서 CVE 데이터를 로드해야 함)
historical_cve_vectors = []  # FeatureVector 리스트

clusterer = CVEClusterer(n_clusters=10, algorithm="kmeans")
clusterer.fit(historical_cve_vectors)

# 2. 새로운 패키지 분류
cluster_id, distance = clusterer.predict_cluster(vector)
print(f"클러스터: {cluster_id}, 거리: {distance:.3f}")

# 3. 클러스터 정보 확인
metadata = clusterer.get_cluster_metadata(cluster_id)
print(f"클러스터 크기: {metadata.size}")
print(f"평균 CVSS: {metadata.avg_cvss:.1f}")
```

### 위협 점수 계산

```python
from zero_day_defense.prediction.engine import PredictionScorer

scorer = PredictionScorer(clusterer, threshold=0.7)
threat_score = scorer.score_package(vector)

print(f"위협 점수: {threat_score.score:.2f}")
print(f"위험 수준: {threat_score.risk_level}")
print(f"신뢰도: {threat_score.confidence:.2f}")

print("\n유사한 CVE:")
for cve_id, similarity in threat_score.similar_cves:
    print(f"  {cve_id}: {similarity:.3f}")
```

## 🐛 문제 해결

### GitHub API Rate Limit

```python
# 현재 rate limit 확인
import requests
response = requests.get(
    "https://api.github.com/rate_limit",
    headers={"Authorization": f"Bearer {your_token}"}
)
print(response.json())
```

**해결책:**
- GITHUB_TOKEN 환경 변수 설정 (5,000 requests/hour)
- 요청 간 딜레이 추가
- 캐싱 사용

### Gemini API 오류

```python
# API 키 테스트
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Hello")
print(response.text)
```

**해결책:**
- GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수 확인
- API 할당량 확인 (Free tier: 15 RPM)
- 요청 간 딜레이 추가

### 메모리 부족

```python
# 배치 처리로 메모리 절약
repos = ["repo1", "repo2", "repo3", ...]

for repo in repos:
    # 각 repo를 개별적으로 처리
    commits = collector.collect_commit_history(repo, since, until)
    # ... 처리 ...
    del commits  # 메모리 해제
```

## 📚 다음 단계

1. **실제 CVE 데이터 수집**: `scripts/collect_cve_data.py` 실행
2. **Neo4j 통합**: CVE 데이터를 Neo4j에 로드
3. **클러스터 학습**: 과거 CVE로 클러스터 모델 학습
4. **자동화**: 정기적인 분석을 위한 스케줄러 설정

## 💡 팁

- **작은 프로젝트부터 시작**: 큰 프로젝트는 API 호출이 많아 시간이 오래 걸립니다
- **캐싱 활용**: 같은 데이터를 반복 분석할 때는 저장된 신호 사용
- **배치 처리**: 여러 패키지를 분석할 때는 배치로 처리
- **로그 확인**: 문제 발생 시 상세 로그 확인

## 🆘 도움말

- 상세 가이드: `docs/prediction_system_guide.md`
- 구현 요약: `docs/IMPLEMENTATION_SUMMARY.md`
- 이슈 리포트: GitHub Issues
