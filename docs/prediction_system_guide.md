# Zero-Day Defense Prediction System Guide

## 개요

Zero-Day Defense 예측 시스템은 소프트웨어 패키지의 시계열 신호를 분석하여 잠재적인 취약점을 사전에 예측하는 LLM 기반 지능형 시스템입니다.

## 시스템 아키텍처

### 주요 컴포넌트

1. **Signal Collection Layer** - GitHub API를 통한 시계열 데이터 수집
   - 커밋 히스토리
   - Pull Request 활동
   - 이슈 토론
   - 릴리즈 히스토리

2. **Feature Engineering Layer** - 신호를 특징 벡터로 변환
   - 구조적 특징 추출 (37개 특징)
   - Gemini API를 통한 의미론적 임베딩
   - 특징 정규화 및 통합

3. **Prediction Engine** - CVE 클러스터 기반 위협 예측
   - K-means/DBSCAN 클러스터링
   - 코사인 유사도 기반 위협 점수 계산
   - Neo4j 그래프 데이터베이스 통합

4. **LLM Agent Layer** - Gemini 기반 지능형 분석
   - SignalAnalyzerAgent: 신호 해석
   - ThreatAssessmentAgent: 위협 시나리오 생성
   - RecommendationAgent: 대응 방안 제시

5. **Validation & Feedback** - 예측 검증 및 모델 개선
   - TP/FP/TN/FN 분류
   - Precision, Recall, F1 Score 계산
   - 모델 재학습

## 설치

### 필수 요구사항

- Python 3.10+
- Neo4j 데이터베이스 (선택사항)
- GitHub Personal Access Token
- Gemini API Key

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 환경 변수 설정

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```bash
# GitHub API
GITHUB_TOKEN=your_github_token

# Gemini API
GEMINI_API_KEY=your_gemini_api_key
# 또는
GOOGLE_API_KEY=your_google_api_key

# Neo4j (선택사항)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

## 사용법

### 1. 데모 실행

간단한 데모로 시스템을 테스트할 수 있습니다:

```bash
python scripts/run_prediction_demo.py --repo owner/repo --days 30
```

예시:
```bash
python scripts/run_prediction_demo.py --repo apache/log4j --days 90
```

### 2. 신호 수집

```python
from datetime import datetime, timedelta
from zero_day_defense.prediction.signal_collectors import GitHubSignalCollector

collector = GitHubSignalCollector()
until = datetime.utcnow()
since = until - timedelta(days=30)

commits = collector.collect_commit_history("owner/repo", since, until)
prs = collector.collect_pr_history("owner/repo", since, until)
issues = collector.collect_issue_history("owner/repo", since, until)
```

### 3. 특징 추출

```python
from zero_day_defense.prediction.feature_engineering import FeatureExtractor

extractor = FeatureExtractor()

commit_features = extractor.extract_commit_features(commits)
pr_features = extractor.extract_pr_features(prs)
issue_features = extractor.extract_issue_features(issues)

# 모든 특징 통합
all_features = {**commit_features, **pr_features, **issue_features}
```

### 4. 임베딩 생성

```python
from zero_day_defense.prediction.feature_engineering import LLMEmbedder

embedder = LLMEmbedder()  # Gemini API 사용
embeddings = embedder.embed_commit_messages(commits)
```

### 5. 특징 벡터 생성

```python
from zero_day_defense.prediction.feature_engineering import FeatureVectorBuilder

builder = FeatureVectorBuilder()
vector = builder.build_vector(
    package="owner/repo",
    time_window=(since, until),
    structural_features=all_features,
    semantic_embeddings=embeddings,
)
```

### 6. CVE 클러스터링

```python
from zero_day_defense.prediction.engine import CVEClusterer

# 과거 CVE 데이터로 학습
clusterer = CVEClusterer(n_clusters=10, algorithm="kmeans")
clusterer.fit(historical_cve_vectors)

# 새로운 패키지 분류
cluster_id, distance = clusterer.predict_cluster(vector)
```

### 7. 위협 점수 계산

```python
from zero_day_defense.prediction.engine import PredictionScorer

scorer = PredictionScorer(clusterer, threshold=0.7)
threat_score = scorer.score_package(vector)

print(f"Threat Score: {threat_score.score:.2f}")
print(f"Risk Level: {threat_score.risk_level}")
print(f"Confidence: {threat_score.confidence:.2f}")
```

### 8. LLM Agent 분석

```python
from zero_day_defense.prediction.agents import (
    SignalAnalyzerAgent,
    ThreatAssessmentAgent,
    RecommendationAgent,
)

# 신호 분석
analyzer = SignalAnalyzerAgent()
signal_analysis = analyzer.analyze_commits(commits, {"package": "owner/repo"})

# 위협 시나리오 생성
assessor = ThreatAssessmentAgent()
scenario = assessor.generate_threat_scenario(
    threat_score,
    signal_analysis,
    similar_cves=["CVE-2021-44228", "CVE-2021-45046"],
)

# 대응 방안 제시
recommender = RecommendationAgent()
recommendations = recommender.generate_recommendations(
    scenario,
    {"package": "owner/repo", "risk_level": threat_score.risk_level},
)

print("Immediate Actions:")
for action in recommendations.immediate_actions:
    print(f"  - {action}")
```

## 추출되는 특징

### 커밋 특징 (18개)
- commit_frequency: 커밋 빈도 (commits/day)
- lines_added_avg, lines_deleted_avg: 평균 라인 변경
- author_diversity: 고유 작성자 수
- author_concentration: Gini 계수
- commit_hour_morning/afternoon/evening/night: 시간대별 커밋 비율
- file_type_py/js/java/config/test/doc: 파일 타입 분포

### PR 특징 (5개)
- pr_frequency: PR 빈도 (PRs/week)
- pr_merge_time_avg: 평균 머지 시간
- pr_review_count_avg: 평균 리뷰 수
- pr_merged_ratio: 머지 비율
- security_label_ratio: 보안 라벨 비율

### 이슈 특징 (6개)
- issue_frequency: 이슈 빈도 (issues/week)
- security_keyword_ratio: 보안 키워드 비율
- resolution_time_avg: 평균 해결 시간
- participant_count_avg: 평균 참여자 수
- closed_ratio: 종료 비율

### 릴리즈 특징 (5개)
- release_frequency: 릴리즈 빈도
- version_bump_major/minor/patch: 버전 업데이트 패턴
- prerelease_ratio: 프리릴리즈 비율

### 시계열 특징 (3개)
- trend: 선형 회귀 기울기
- volatility: 표준 편차
- recent_activity_ratio: 최근 활동 비율

## Neo4j 스키마

### 노드 타입

- `Signal`: 수집된 신호 데이터
- `FeatureVector`: 특징 벡터
- `Cluster`: CVE 클러스터
- `Prediction`: 위협 예측
- `ThreatScenario`: 위협 시나리오
- `Recommendation`: 대응 방안

### 관계

- `(:Package)-[:HAS_SIGNAL]->(:Signal)`
- `(:Package)-[:HAS_FEATURE_VECTOR]->(:FeatureVector)`
- `(:FeatureVector)-[:BELONGS_TO_CLUSTER]->(:Cluster)`
- `(:Cluster)-[:CONTAINS_CVE]->(:CVE)`
- `(:Package)-[:HAS_PREDICTION]->(:Prediction)`
- `(:Prediction)-[:SIMILAR_TO_CVE]->(:CVE)`
- `(:Prediction)-[:NEAREST_CLUSTER]->(:Cluster)`
- `(:Prediction)-[:HAS_SCENARIO]->(:ThreatScenario)`
- `(:ThreatScenario)-[:HAS_RECOMMENDATION]->(:Recommendation)`

## 성능 고려사항

### API Rate Limits

- **GitHub API**: 
  - 인증 없이: 60 requests/hour
  - 인증 시: 5,000 requests/hour
  - 권장: GITHUB_TOKEN 설정

- **Gemini API**:
  - Free tier: 15 RPM (requests per minute)
  - 권장: 요청 간 딜레이 추가

### 최적화 팁

1. **배치 처리**: 여러 패키지를 병렬로 처리
2. **캐싱**: GitHub API 응답 캐싱
3. **증분 업데이트**: 새로운 신호만 수집
4. **벡터 인덱싱**: Neo4j에서 유사도 검색 최적화

## 문제 해결

### GitHub API Rate Limit 초과

```python
# Rate limit 확인
collector = GitHubSignalCollector()
# 자동으로 rate limit 처리됨
```

### Gemini API 오류

```python
# API 키 확인
import os
print(os.getenv("GEMINI_API_KEY"))

# 대체 모델 사용
embedder = LLMEmbedder(model="models/text-embedding-004")
```

### Neo4j 연결 오류

```python
# 연결 테스트
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)
driver.verify_connectivity()
```

## 다음 단계

1. **대시보드 통합**: Streamlit 대시보드에 예측 결과 표시
2. **자동화**: 스케줄러로 정기적인 분석 실행
3. **알림**: 고위험 패키지 발견 시 알림 전송
4. **모델 개선**: 더 많은 CVE 데이터로 클러스터 재학습

## 참고 자료

- [GitHub API Documentation](https://docs.github.com/en/rest)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [scikit-learn Clustering](https://scikit-learn.org/stable/modules/clustering.html)
