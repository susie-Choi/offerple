# Zero-Day Defense 연구 방법론

## 연구의 Input/Output 정의

### Input (입력 데이터)
**시간 제약**: 특정 시점 t 이전의 데이터만 사용 (예: 2021년 11월 1일 이전)

**1. 패키지 생태계 데이터**
- 패키지 메타데이터 (이름, 버전, 설명, 라이선스)
- 의존성 관계 (A depends on B)
- 다운로드 통계 (일별/월별 다운로드 수)
- 패키지 크기, 파일 수

**2. 과거 취약점 이력 (t 이전에 공개된 CVE만)**
- CVE ID 및 공개 날짜
- CVSS 점수 및 심각도
- 취약점 유형 (RCE, XSS, SQL Injection 등)
- 영향받는 버전 범위

**3. 코드 레벨 데이터**
- 소스코드 (GitHub에서 수집)
- 위험 함수 사용 빈도 (strcpy, eval, exec, deserialize 등)
- 코드 복잡도 (Cyclomatic Complexity, Lines of Code)
- 코드 변경 이력 (커밋 로그)

**4. 개발 활동 데이터**
- GitHub 커밋 빈도 및 패턴
- 이슈 생성/해결 속도
- Pull Request 활동
- 보안 관련 이슈/PR 비율
- 개발자 수 및 활동 패턴

**5. 커뮤니티 신호**
- GitHub Stars, Forks, Watchers
- 커뮤니티 크기 (contributors 수)
- 최근 활동 변화 (급증/급감)

### Output (출력 결과)
**시간 제약**: 시점 t 이후에 발생할 취약점 예측

**1. 잠재 위험 점수 (Latent Risk Score)**
- 각 패키지에 대한 0-1 사이의 위험 점수
- 높을수록 향후 Critical/High 취약점 발생 가능성 높음

**2. 위험 순위 리스트**
- 상위 K개 고위험 패키지 목록 (K = 전체의 1-5%)
- 각 패키지별 위험 근거 (어떤 신호가 위험을 나타내는지)

**3. 위협 군집 (Threat Clusters)**
- 유사한 위험 패턴을 가진 패키지 그룹
- 각 군집의 특징 및 공통 패턴

**4. 3D 위험 지도**
- X, Y축: 패키지 간 유사도 기반 2D 배치
- Z축: 잠재 위험 점수
- 시각적으로 "위험 지대" 식별 가능

**5. 예측 근거 (Explainability)**
- 각 패키지가 고위험으로 분류된 이유
- 주요 기여 신호들 (과거 이력, 코드 패턴, 활동 변화 등)

---

## 연구 방법론: 단계별 상세 설명

### Phase 1: 데이터 수집 및 전처리

**Step 1.1: 패키지 생태계 데이터 수집**
- **입력**: 없음 (초기 단계)
- **처리**:
  - PyPI API를 통해 모든 패키지 메타데이터 수집
  - 의존성 관계 파싱 (requirements.txt, setup.py)
  - 다운로드 통계 수집 (pypistats)
- **출력**: `packages.json` (패키지 메타데이터), `dependencies.json` (의존성 관계)
- **도구**: `requests`, `packaging`, `pypistats`

**Step 1.2: 과거 취약점 이력 수집**
- **입력**: 시간 cutoff (예: 2021-11-01)
- **처리**:
  - NVD API에서 cutoff 이전 CVE 데이터 수집
  - GitHub Advisory Database 크롤링
  - CVE와 패키지 매칭 (CPE, package name)
- **출력**: `vulnerabilities.json` (CVE 이력)
- **도구**: `python-nvd`, `requests`, `beautifulsoup4`
- **중요**: cutoff 이후 데이터는 절대 사용 금지 (Data Leakage 방지)

**Step 1.3: 코드 데이터 수집**
- **입력**: 패키지 목록, GitHub 저장소 URL
- **처리**:
  - GitHub API로 저장소 클론
  - 소스코드 정적 분석
  - 위험 함수 탐지 (정규표현식, AST 파싱)
  - 복잡도 계산 (radon, mccabe)
- **출력**: `code_features.json` (코드 레벨 특징)
- **도구**: `tree-sitter`, `radon`, `bandit`, `ast`

**Step 1.4: 개발 활동 데이터 수집**
- **입력**: GitHub 저장소 URL, cutoff 날짜
- **처리**:
  - GitHub API로 커밋, 이슈, PR 데이터 수집
  - 시간별 활동 패턴 분석
  - 보안 관련 키워드 필터링 (security, vulnerability, CVE)
- **출력**: `activity_data.json` (개발 활동 데이터)
- **도구**: `PyGithub`, `pandas`

**Step 1.5: 의존성 그래프 구축**
- **입력**: `dependencies.json`
- **처리**:
  - NetworkX로 방향 그래프 생성
  - 노드: 패키지, 엣지: 의존성 관계
  - Neo4j에 저장 (대규모 그래프 쿼리용)
- **출력**: `dependency_graph.gpickle`, Neo4j 데이터베이스
- **도구**: `networkx`, `neo4j`, `py2neo`

---

### Phase 2: 사전 신호 추출

**Step 2.1: 그래프 구조 신호 추출**
- **입력**: `dependency_graph.gpickle`
- **처리**:
  - PageRank 계산 (전역 중요도)
  - Betweenness Centrality (병목 지점)
  - In-degree (얼마나 많은 패키지가 의존하는지)
  - Downstream Impact (하류 영향 범위)
- **출력**: `graph_signals.json`
  ```json
  {
    "package_name": {
      "pagerank": 0.0023,
      "betweenness": 0.0015,
      "in_degree": 1523,
      "downstream_impact": 45231
    }
  }
  ```
- **도구**: `networkx`

**Step 2.2: 과거 취약점 패턴 신호 추출**
- **입력**: `vulnerabilities.json`, cutoff 날짜
- **처리**:
  - 각 패키지의 과거 취약점 빈도 계산
  - 취약점 유형 분포 (RCE, XSS 등)
  - 평균 CVSS 점수
  - 최근 취약점 발생 추세 (증가/감소)
  - 취약점 간 시간 간격 (평균, 표준편차)
- **출력**: `vulnerability_patterns.json`
  ```json
  {
    "package_name": {
      "total_cves": 7,
      "critical_cves": 3,
      "avg_cvss": 8.2,
      "rce_count": 5,
      "last_cve_days_ago": 180,
      "cve_frequency": 1.4  // per year
    }
  }
  ```
- **도구**: `pandas`, `numpy`

**Step 2.3: 코드 레벨 위험 신호 추출**
- **입력**: `code_features.json`
- **처리**:
  - 위험 함수 사용 빈도 정규화
  - 복잡도 점수 계산
  - 최근 코드 변경 규모 (LOC changed)
  - 보안 관련 코드 영역 변경 여부
- **출력**: `code_risk_signals.json`
  ```json
  {
    "package_name": {
      "dangerous_functions": 23,
      "complexity_score": 45.2,
      "recent_changes_loc": 1523,
      "security_area_changed": true
    }
  }
  ```
- **도구**: `radon`, `bandit`, custom scripts

**Step 2.4: 유지보수 활동 신호 추출**
- **입력**: `activity_data.json`
- **처리**:
  - 커밋 빈도 계산 (최근 3개월, 6개월, 1년)
  - 이슈 해결 속도 (평균 해결 시간)
  - 보안 이슈 비율
  - 개발자 활동 변화 (급증/급감)
- **출력**: `activity_signals.json`
  ```json
  {
    "package_name": {
      "commit_frequency_3m": 45,
      "issue_resolution_days": 12.3,
      "security_issue_ratio": 0.15,
      "activity_trend": "declining"
    }
  }
  ```
- **도구**: `pandas`, `scipy`

**Step 2.5: 커뮤니티 신호 추출**
- **입력**: GitHub 통계, 다운로드 통계
- **처리**:
  - Stars, Forks 변화율
  - 다운로드 수 변화율
  - Contributors 수 변화
- **출력**: `community_signals.json`
- **도구**: `pandas`

---

### Phase 3: 위협 군집 분석

**Step 3.1: 핵심 노드 식별**
- **입력**: 모든 신호 데이터 (`*_signals.json`)
- **처리**:
  - 다차원 신호를 종합하여 "중요도 점수" 계산
  - 상위 10% 노드를 "핵심 노드"로 선정
  - 기준: 높은 중심성 + 과거 취약점 이력 + 높은 영향력
- **출력**: `critical_nodes.json` (핵심 노드 목록)
- **도구**: `scikit-learn`, `numpy`

**Step 3.2: 위협 군집 탐지**
- **입력**: `dependency_graph.gpickle`, `critical_nodes.json`
- **처리**:
  - 그래프 커뮤니티 탐지 알고리즘 적용 (Louvain, Label Propagation)
  - 핵심 노드들이 속한 커뮤니티 추출
  - 각 커뮤니티의 특징 분석
- **출력**: `threat_clusters.json`
  ```json
  {
    "cluster_1": {
      "packages": ["pkg1", "pkg2", "pkg3"],
      "common_patterns": ["uses libX", "file upload handling"],
      "avg_risk_score": 0.75
    }
  }
  ```
- **도구**: `networkx`, `python-louvain`

**Step 3.3: 군집 내 연관성 분석**
- **입력**: `threat_clusters.json`, 코드 데이터
- **처리**:
  - 군집 내 패키지들의 공통점 찾기
    - 공통 의존성
    - 유사한 코드 패턴 (Code Embedding 유사도)
    - 동일 개발자/조직
  - 과거 취약점 패턴 유사도
- **출력**: `cluster_patterns.json`
- **도구**: `sentence-transformers` (코드 임베딩), `scikit-learn`

---

### Phase 4: LLM 기반 잠재 위협 예측

**Step 4.1: 신호 통합 및 정규화**
- **입력**: 모든 신호 데이터
- **처리**:
  - 각 신호를 0-1 범위로 정규화
  - 결측값 처리 (평균, 중앙값 대체)
  - 신호 간 상관관계 분석
- **출력**: `normalized_signals.json`
- **도구**: `scikit-learn`, `pandas`

**Step 4.2: LLM 프롬프트 생성**
- **입력**: `normalized_signals.json`, `cluster_patterns.json`
- **처리**:
  - 각 패키지에 대한 컨텍스트 생성
  - 프롬프트 템플릿:
    ```
    패키지: {package_name}
    
    과거 취약점 이력:
    - 총 {total_cves}개 CVE, 평균 CVSS {avg_cvss}
    - 주요 유형: {vulnerability_types}
    
    코드 특징:
    - 위험 함수 {dangerous_functions}개 사용
    - 복잡도: {complexity_score}
    - 최근 {recent_changes_loc} 라인 변경
    
    생태계 위치:
    - {downstream_impact}개 패키지가 의존
    - PageRank: {pagerank}
    
    유사 패키지 패턴:
    - 동일 군집의 {similar_package}도 과거 {similar_cve_type} 취약점 발생
    
    질문: 이 패키지에서 향후 Critical/High 취약점이 발생할 가능성은?
    근거와 함께 0-1 사이의 점수로 답하시오.
    ```
- **출력**: `llm_prompts.json`
- **도구**: `jinja2` (템플릿 엔진)

**Step 4.3: LLM 유추 추론 실행**
- **입력**: `llm_prompts.json`
- **처리**:
  - OpenAI API 또는 Claude API 호출
  - 각 패키지에 대해 LLM의 위험 평가 수집
  - 응답 파싱 (점수 추출, 근거 추출)
- **출력**: `llm_predictions.json`
  ```json
  {
    "package_name": {
      "risk_score": 0.82,
      "reasoning": "과거 5번의 RCE 취약점 + 최근 네트워크 코드 대폭 변경 + 유사 패키지에서 최근 취약점 발생",
      "confidence": 0.75
    }
  }
  ```
- **도구**: `openai`, `anthropic`

**Step 4.4: 잠재 위험 점수 계산**
- **입력**: `normalized_signals.json`, `llm_predictions.json`
- **처리**:
  - 신호 기반 점수와 LLM 점수를 가중 평균
  - 가중치: 신호 60%, LLM 40% (실험적으로 조정)
  - 최종 Latent Risk Score 계산
- **출력**: `latent_risk_scores.json`
  ```json
  {
    "package_name": {
      "final_score": 0.78,
      "signal_score": 0.75,
      "llm_score": 0.82,
      "rank": 23  // 전체 중 순위
    }
  }
  ```
- **도구**: `numpy`, `pandas`

---

### Phase 5: Historical Validation

**Step 5.1: 시간 분할 설정**
- **입력**: 검증할 사건 (예: Log4Shell)
- **처리**:
  - Training cutoff: CVE 공개 1-3개월 전
  - Prediction time: cutoff 시점
  - Validation time: CVE 공개 시점
- **출력**: 시간 분할 설정 파일

**Step 5.2: 과거 시점 데이터 재구성**
- **입력**: 전체 데이터, cutoff 날짜
- **처리**:
  - cutoff 이후 데이터 모두 제거
  - 해당 시점에 실제로 알 수 있었던 정보만 남김
- **출력**: `historical_data_{cutoff}.json`
- **중요**: 철저한 Data Leakage 방지

**Step 5.3: 예측 실행**
- **입력**: `historical_data_{cutoff}.json`
- **처리**:
  - Phase 1-4 전체 파이프라인 실행
  - 해당 시점의 상위 K개 고위험 패키지 예측
- **출력**: `historical_predictions_{cutoff}.json`

**Step 5.4: 실제 결과와 비교**
- **입력**: `historical_predictions_{cutoff}.json`, 실제 CVE 데이터
- **처리**:
  - 예측한 패키지에서 실제로 취약점 발생했는지 확인
  - Precision@K, Recall@K 계산
  - Lead Time 계산 (예측 시점 - CVE 공개 시점)
- **출력**: `validation_results.json`
  ```json
  {
    "log4shell": {
      "predicted_rank": 15,
      "actual_cve": "CVE-2021-44228",
      "lead_time_days": 30,
      "precision_at_100": 0.23,
      "recall_at_100": 0.67
    }
  }
  ```
- **도구**: `scikit-learn`, `pandas`

---

### Phase 6: 3D 시각화

**Step 6.1: 차원 축소**
- **입력**: `normalized_signals.json` (고차원 데이터)
- **처리**:
  - t-SNE 또는 UMAP으로 2D 축소
  - 패키지 간 유사도 보존
- **출력**: `2d_coordinates.json` (X, Y 좌표)
- **도구**: `scikit-learn`, `umap-learn`

**Step 6.2: 3D 위험 지도 생성**
- **입력**: `2d_coordinates.json`, `latent_risk_scores.json`
- **처리**:
  - X, Y: 2D 좌표
  - Z: 잠재 위험 점수
  - Plotly로 인터랙티브 3D 그래프 생성
- **출력**: `risk_map_3d.html`
- **도구**: `plotly`, `matplotlib`

---

## 데이터 흐름 다이어그램

```
[패키지 생태계] → [수집] → packages.json
[NVD/GitHub] → [수집] → vulnerabilities.json
[GitHub Code] → [분석] → code_features.json
[GitHub API] → [수집] → activity_data.json
                          ↓
                [의존성 그래프 구축]
                          ↓
                dependency_graph.gpickle
                          ↓
        [사전 신호 추출] (Phase 2)
                          ↓
    ┌─────────────────────┴─────────────────────┐
    ↓                     ↓                     ↓
graph_signals    vulnerability_patterns    code_risk_signals
    └─────────────────────┬─────────────────────┘
                          ↓
            [위협 군집 분석] (Phase 3)
                          ↓
              threat_clusters.json
                          ↓
        [LLM 기반 예측] (Phase 4)
                          ↓
          latent_risk_scores.json
                          ↓
    ┌───────────────────┴───────────────────┐
    ↓                                       ↓
[Historical Validation]            [3D 시각화]
    ↓                                       ↓
validation_results.json            risk_map_3d.html
```

---

## 핵심 제약 사항

1. **시간적 엄밀성**: cutoff 이후 데이터 절대 사용 금지
2. **재현 가능성**: 모든 랜덤 시드 고정, 버전 명시
3. **확장성**: 10만+ 패키지 처리 가능해야 함
4. **실용성**: False Positive Rate < 80% 목표