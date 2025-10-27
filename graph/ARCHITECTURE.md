# Zero-Day Defense 아키텍처 설명

## 시스템 구조 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    Zero-Day Defense System                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Phase 1    │───▶│   Phase 2    │───▶│   Phase 4    │
│ 데이터 수집   │    │  신호 추출    │    │  LLM 예측    │
└──────────────┘    └──────────────┘    └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  [Raw Data]         [Signals]          [Risk Scores]
```

## 데이터 흐름

### Phase 1: 데이터 수집
```
PyPI API ──┐
           ├──▶ PackageCollector ──▶ packages.json
GitHub  ───┘

NVD API ───┐
           ├──▶ VulnerabilityCollector ──▶ vulnerabilities.json
GitHub  ───┘
```

**출력**:
- `data/raw/packages.json`: 패키지 메타데이터
- `data/raw/vulnerabilities.json`: CVE 이력
- `data/raw/dependencies.json`: 의존성 관계

### Phase 2: 신호 추출
```
packages.json ──▶ DependencyGraph ──▶ graph_signals.json
                       │
                       ├──▶ PageRank
                       ├──▶ Betweenness Centrality
                       ├──▶ Downstream Impact
                       └──▶ Critical Nodes

vulnerabilities.json ──▶ VulnerabilityPatternExtractor ──▶ vulnerability_patterns.json
                              │
                              ├──▶ CVE 빈도
                              ├──▶ CVSS 평균
                              ├──▶ 취약점 유형
                              └──▶ 추세 분석
```

**출력**:
- `data/processed/signals/graph_signals.json`: 그래프 중심성 메트릭
- `data/processed/signals/vulnerability_patterns.json`: 취약점 패턴
- `data/processed/signals/integrated_signals.json`: 통합 신호
- `data/processed/critical_nodes.json`: 핵심 노드 목록

### Phase 4: LLM 기반 예측
```
integrated_signals.json ──┐
                          ├──▶ LLMRiskPredictor ──▶ llm_predictions.json
critical_nodes.json ──────┘         │
                                    ├──▶ 프롬프트 생성
                                    ├──▶ OpenAI/Anthropic API
                                    └──▶ 응답 파싱

llm_predictions.json ──┐
                       ├──▶ LatentRiskCalculator ──▶ latent_risk_scores.json
integrated_signals ────┘         │
                                 ├──▶ 신호 점수 (60%)
                                 ├──▶ LLM 점수 (40%)
                                 └──▶ 최종 점수 계산
```

**출력**:
- `data/processed/llm_predictions.json`: LLM 예측 결과
- `data/processed/scores/latent_risk_scores.json`: 최종 위험 점수
- `data/processed/scores/top_100_risks.json`: 상위 100개 고위험 패키지

## 핵심 컴포넌트

### 1. PackageCollector (데이터 수집)
```python
collector = PackageCollector(cutoff_date="2021-11-01")
package_data = collector.collect_pypi_package("flask")
```

**기능**:
- PyPI API 호출
- 패키지 메타데이터 수집
- 의존성 관계 파싱
- cutoff 날짜 이전 데이터만 수집 (Historical Validation용)

**외부 의존성**:
- PyPI API (https://pypi.org/pypi/{package}/json)
- 인터넷 연결 필요

### 2. VulnerabilityCollector (취약점 수집)
```python
collector = VulnerabilityCollector(cutoff_date="2021-11-01", nvd_api_key=None)
cves = collector.collect_cves_for_product("log4j")
```

**기능**:
- NVD API 호출
- CVE 데이터 수집
- CVSS 점수 및 취약점 유형 파싱
- cutoff 날짜 이전 CVE만 수집

**외부 의존성**:
- NVD API (https://services.nvd.nist.gov/rest/json/cves/2.0)
- API 키 없으면 rate limit (30초당 5개 요청)

### 3. DependencyGraph (그래프 분석)
```python
dep_graph = DependencyGraph(use_neo4j=False)  # NetworkX만 사용
dep_graph.build_from_packages(packages_data)
metrics = dep_graph.calculate_centrality_metrics()
```

**기능**:
- NetworkX 기반 방향 그래프 구축
- PageRank, Betweenness Centrality 계산
- Downstream Impact (하류 영향 범위) 계산
- 핵심 노드 식별

**외부 의존성**:
- NetworkX (필수)
- Neo4j (선택사항, 대규모 그래프용)

**Neo4j 사용 시**:
```python
dep_graph = DependencyGraph(use_neo4j=True, neo4j_uri="bolt://localhost:7687")
```

### 4. VulnerabilityPatternExtractor (패턴 분석)
```python
extractor = VulnerabilityPatternExtractor(cutoff_date="2021-11-01")
patterns = extractor.extract_patterns(vulnerabilities_data)
```

**기능**:
- CVE 빈도 계산
- 평균 CVSS 점수
- 취약점 유형 분포
- 시간적 추세 분석 (증가/감소/안정)
- 위험 점수 계산 (0-1)

**외부 의존성**: 없음 (순수 Python)

### 5. LLMRiskPredictor (LLM 추론)
```python
predictor = LLMRiskPredictor(provider="openai", model="gpt-4")
prediction = predictor.predict_risk(package_name, signals, cluster_info)
```

**기능**:
- 다차원 신호를 프롬프트로 변환
- LLM API 호출 (OpenAI 또는 Anthropic)
- 응답 파싱 (위험 점수 + 근거)
- 배치 처리 및 캐싱

**외부 의존성**:
- OpenAI API (OPENAI_API_KEY 필요)
- 또는 Anthropic API (ANTHROPIC_API_KEY 필요)
- 비용 발생 (GPT-4: 상위 100개 약 $5-10)

### 6. LatentRiskCalculator (최종 점수)
```python
calculator = LatentRiskCalculator(signal_weight=0.6, llm_weight=0.4)
final_score = calculator.calculate_final_score(package_name, signals, llm_prediction)
```

**기능**:
- 신호 기반 점수 계산 (60%)
- LLM 예측 점수 (40%)
- 가중 평균으로 최종 점수 산출
- 순위 및 백분위 계산

**외부 의존성**: 없음

### 7. HistoricalValidator (검증)
```python
validator = HistoricalValidator(cutoff_date="2021-11-01", validation_cves=cves)
results = validator.validate_predictions(predictions)
```

**기능**:
- Precision@K, Recall@K 계산
- Lead Time 분석
- Log4Shell 특화 검증
- 성능 메트릭 생성

**외부 의존성**: 없음

## 데이터베이스 및 저장소

### NetworkX (기본)
- **용도**: 소규모 그래프 분석 (~10,000 패키지)
- **저장**: pickle 파일 (`dependency_graph.gpickle`)
- **장점**: 설치 불필요, 빠른 시작
- **단점**: 메모리 제약

### Neo4j (선택사항)
- **용도**: 대규모 그래프 분석 (10,000+ 패키지)
- **저장**: Neo4j 데이터베이스
- **장점**: 확장성, 복잡한 쿼리
- **단점**: 별도 설치 필요, 리소스 사용

**Neo4j 사용 시나리오**:
1. 전체 PyPI 생태계 분석 (300,000+ 패키지)
2. 실시간 쿼리 필요
3. 복잡한 그래프 패턴 탐색

## API 서버 아키텍처

```
FastAPI Server (port 8000)
    │
    ├── GET /api/v1/risk/{package_name}
    │   └──▶ latent_risk_scores.json 조회
    │
    ├── GET /api/v1/risks/top?k=100
    │   └──▶ 상위 K개 정렬 및 반환
    │
    ├── GET /api/v1/risks/search?query=flask
    │   └──▶ 패키지명 검색
    │
    └── GET /api/v1/stats
        └──▶ 전체 통계 계산
```

**특징**:
- 서버 시작 시 데이터 로드 (메모리 캐싱)
- 빠른 응답 속도
- CORS 지원 (프론트엔드 연동 가능)

## 비용 및 리소스

### 컴퓨팅 리소스
- **CPU**: 2코어 이상 권장
- **메모리**: 
  - 소규모 (~1,000 패키지): 2GB
  - 중규모 (~10,000 패키지): 4GB
  - 대규모 (10,000+ 패키지): 8GB+
- **디스크**: 1GB (데이터 + 그래프)

### API 비용 (예상)
- **NVD API**: 무료 (API 키 없으면 느림)
- **PyPI API**: 무료
- **OpenAI GPT-4**: 
  - 상위 100개 패키지: $5-10
  - 상위 1,000개 패키지: $50-100
- **Anthropic Claude**: 유사한 비용

### 실행 시간 (예상)
- **Phase 1** (100개 패키지): 10-20분
- **Phase 2**: 5-10분
- **Phase 4** (100개 패키지, GPT-4): 10-30분
- **전체**: 약 30분~1시간

## 확장성

### 수평 확장
- 데이터 수집: 병렬 처리 가능 (multiprocessing)
- LLM 예측: 배치 처리 및 비동기 호출
- API 서버: 로드 밸런서 + 다중 인스턴스

### 수직 확장
- 메모리 증가: 더 큰 그래프 처리
- CPU 증가: 병렬 처리 속도 향상

## 보안 고려사항

### API 키 관리
- `.env` 파일 사용 (Git에 커밋 금지)
- 환경 변수로 주입
- 프로덕션: AWS Secrets Manager, Azure Key Vault 등

### 데이터 보안
- 민감한 취약점 정보 암호화
- Responsible Disclosure 원칙 준수
- 발견한 잠재 위험은 해당 프로젝트에 책임감 있게 보고

## 모니터링 및 로깅

### 로깅
- Python `logging` 모듈 사용
- 레벨: INFO (기본), DEBUG (상세)
- 출력: 콘솔 + 파일 (선택사항)

### 메트릭
- 데이터 수집 진행률
- LLM API 호출 횟수 및 비용
- 예측 성능 (Precision@K, Recall@K)

## 문제 해결

### 메모리 부족
- 패키지 수 줄이기
- 배치 크기 줄이기
- Neo4j 사용 고려

### LLM API 오류
- Rate limit: 배치 크기 줄이기
- 비용 초과: `--top-k` 줄이기
- API 키 확인

### 느린 실행
- NVD API 키 발급
- 병렬 처리 활성화
- 캐싱 활용

## 향후 개선 방향

1. **추가 신호**: 코드 분석, GitHub 활동 패턴
2. **3D 시각화**: Plotly 기반 인터랙티브 위험 지도
3. **실시간 모니터링**: 새로운 패키지 자동 분석
4. **다중 생태계**: Maven, npm, RubyGems 지원
5. **모델 파인튜닝**: 도메인 특화 LLM 학습
