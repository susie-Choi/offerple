# Technology Stack

## Development Environment
- **IDE**: VS Code with Kiro AI assistant integration
- **AI Tools**: Kiro agent for development assistance (MCP disabled by default)

## 프로젝트 현황
Zero-Day Defense 연구 프로젝트 초기 단계. 사전 신호 기반 잠재 위협 탐지 시스템 개발 중.

## 핵심 기술 스택

### 주 개발 언어 및 프레임워크
- **Python**: 메인 개발 언어 (그래프 분석, LLM, 신호 처리)
- **LLM 프레임워크**: LangChain, OpenAI API, Anthropic Claude
- **그래프 분석**: NetworkX, Neo4j, PyTorch Geometric
- **데이터 분석**: pandas, numpy, scikit-learn
- **시각화**: Plotly, Matplotlib (3D 위험 지도)
- **웹 프레임워크**: FastAPI (API 서버), Streamlit (데모 UI)

### 필수 라이브러리
- **AI/ML**: transformers, torch, openai, langchain, anthropic
- **그래프 분석**: networkx, neo4j, py2neo, graph-tool, torch-geometric
- **데이터 처리**: pandas, numpy, scipy, requests
- **코드 분석**: tree-sitter, radon (복잡도 측정), bandit (보안 패턴)
- **보안 데이터**: python-nvd, github (API), pypi-simple, ossindex
- **시각화**: plotly, matplotlib, seaborn, networkx (그래프 시각화)

### 데이터 소스

**패키지 생태계 데이터**:
- **PyPI**: Python 패키지 메타데이터, 의존성 정보
- **Maven Central**: Java 패키지 생태계
- **npm registry**: JavaScript 패키지 생태계
- **Libraries.io**: 크로스 플랫폼 패키지 데이터

**취약점 데이터 (과거 이력용)**:
- **NVD (National Vulnerability Database)**: CVE 데이터 및 CVSS 점수
- **GitHub Advisory Database**: GitHub 보안 권고
- **OSS Index**: Sonatype의 오픈소스 취약점 DB
- **Snyk Vulnerability DB**: 상세한 취약점 정보

**코드 및 활동 데이터**:
- **GitHub API**: 커밋, 이슈, PR, 개발자 활동
- **SourceRank**: 패키지 품질 및 활동 지표
- **Code Analysis**: 정적 분석을 통한 코드 패턴 추출

**Historical Validation 데이터**:
- **Log4Shell (CVE-2021-44228)**: 2021년 11월 이전 데이터로 검증
- **Equifax (CVE-2017-5638)**: 2017년 2월 이전 데이터로 검증
- **기타 Critical CVE**: 2015-2024년 CVSS 9.0+ 취약점들

### 연구 및 개발 도구
- **실험 관리**: Weights & Biases (wandb) 또는 MLflow
- **버전 관리**: Git with DVC for large datasets
- **문서화**: Jupyter notebooks, Sphinx, LaTeX (논문 작성)
- **CI/CD**: GitHub Actions, Docker
- **모니터링**: Prometheus, Grafana (시스템 성능 측정)

## 주요 명령어

```bash
# 환경 설정 (uv 사용)
uv venv zero-day-defense-env
source zero-day-defense-env/bin/activate  # Linux/Mac
# zero-day-defense-env\Scripts\activate  # Windows
uv pip install -r requirements.txt
docker-compose up -d neo4j  # Neo4j 그래프 데이터베이스 시작

# Phase 1: 데이터 수집 및 그래프 구축
python scripts/collect_package_metadata.py --source pypi  # 패키지 메타데이터 수집
python scripts/collect_vulnerability_history.py  # 과거 취약점 이력 수집
python scripts/collect_github_activity.py  # GitHub 활동 데이터 수집
python scripts/build_dependency_graph.py  # 의존성 그래프 구축

# Phase 2: 사전 신호 추출
python scripts/extract_graph_signals.py  # 그래프 중심성, 영향력 계산
python scripts/extract_code_signals.py  # 코드 레벨 위험 신호 추출
python scripts/extract_activity_signals.py  # 유지보수 활동 신호 추출
python scripts/extract_community_signals.py  # 커뮤니티 신호 추출

# Phase 3: 위협 군집 분석
python scripts/identify_critical_nodes.py  # 핵심 노드 식별
python scripts/cluster_threat_groups.py  # 위협 군집 탐지
python scripts/analyze_cluster_patterns.py  # 군집 내 패턴 분석

# Phase 4: LLM 기반 잠재 위협 예측
python scripts/train_signal_integration.py  # 신호 통합 모델 학습
python scripts/llm_analogy_reasoning.py  # LLM 유추 추론 실행
python scripts/calculate_latent_risk_scores.py  # 잠재 위험 점수 계산

# Historical Validation
python scripts/validate_log4shell.py --cutoff-date 2021-11-01  # Log4Shell 검증
python scripts/validate_equifax.py --cutoff-date 2017-02-01  # Equifax 검증
python scripts/validate_historical_cves.py  # 전체 Historical CVE 검증

# 3D 시각화
python scripts/generate_3d_risk_map.py  # 3D 위험 지도 생성
streamlit run src/demo/risk_visualization.py  # 인터랙티브 시각화

# 평가 및 분석
python scripts/evaluate_detection_performance.py  # Precision@K, Recall@K 계산
python scripts/evaluate_lead_time.py  # Lead Time 분석
python scripts/analyze_false_positives.py  # False Positive 분석

# 실험 노트북
jupyter notebook experiments/signal_analysis.ipynb  # 신호 분석
jupyter notebook experiments/historical_validation.ipynb  # 과거 검증 분석
jupyter notebook experiments/llm_reasoning_analysis.ipynb  # LLM 추론 분석

# 테스트
python -m pytest tests/test_signal_extraction.py
python -m pytest tests/test_graph_analysis.py
python -m pytest tests/test_llm_reasoning.py
```

## 연구 개발 워크플로우

### 1단계: 데이터 수집 및 전처리
- 패키지 생태계 데이터 수집 (PyPI, Maven, npm)
- 과거 취약점 이력 수집 (NVD, GitHub Advisory)
- GitHub 활동 데이터 수집 (커밋, 이슈, PR)
- 시간 순서 엄격히 준수 (Data Leakage 방지)

### 2단계: 사전 신호 추출
- 그래프 구조 분석 (중심성, 영향력)
- 코드 레벨 위험 신호 추출 (위험 함수, 복잡도)
- 유지보수 활동 패턴 분석
- 커뮤니티 신호 수집

### 3단계: 위협 군집 분석
- 핵심 노드 식별 (Critical Node Identification)
- 위협 군집 탐지 (Community Detection)
- 군집 내 연관성 분석 (공통 패턴 발견)

### 4단계: LLM 기반 예측
- 다차원 신호 통합
- 유추 기반 추론 (Analogy Reasoning)
- 잠재 위험 점수 계산

### 5단계: Historical Validation
- Log4Shell, Equifax 등 과거 사고 재현
- 시간적 제약 엄격히 준수
- Precision@K, Recall@K, Lead Time 측정

### 6단계: 논문 작성
- 실험 결과 정리 및 통계 분석
- 시각화 및 그래프 생성
- 학술 논문 작성 및 투고

## 비교 대상 (Baseline Systems)

### 기존 취약점 탐지 도구
- **OWASP Dependency-Check**: 알려진 CVE 기반 탐지 (사후 대응)
- **Snyk**: 상용 취약점 스캐너 (CVE 데이터베이스 기반)
- **GitHub Dependabot**: 의존성 업데이트 알림 (CVE 공개 후)
- **Sonatype Nexus IQ**: 엔터프라이즈 보안 스캐너

### 학술 연구 Baseline
- **그래프 중심성만 사용**: PageRank, Betweenness Centrality만으로 예측
- **과거 이력만 사용**: 과거 취약점 빈도만으로 예측
- **랜덤 베이스라인**: 무작위 선택 대비 성능 비교
- **전문가 판단**: 보안 전문가의 수동 위험 평가

### 차별점
- **기존 도구**: CVE 공개 후 대응 (Reactive)
- **우리 연구**: CVE 공개 전 예측 (Proactive)
- **핵심 차이**: 사전 신호 기반 잠재 위협 탐지

## Communication Standards
- **모든 설명과 문서화는 반드시 한국어로 작성**
- 코드 주석도 가능한 한 한국어로 작성
- 사용자 대면 메시지와 오류 메시지는 한국어로 작성