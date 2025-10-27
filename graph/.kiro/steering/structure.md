# Project Structure

## Current Organization

```
graph/
├── .kiro/
│   └── steering/          # AI assistant guidance documents
│       ├── product.md     # Product overview and philosophy
│       ├── tech.md        # Technology stack and tooling
│       └── structure.md   # This file - project organization
└── .vscode/
    └── settings.json      # VS Code configuration
```

## Zero-Day Defense 연구 프로젝트 구조

### 핵심 디렉토리
- `src/` - 메인 소스 코드
  - `data_collection/` - 패키지 및 취약점 데이터 수집
  - `signal_extraction/` - 사전 신호 추출 엔진
  - `graph_analysis/` - 그래프 분석 및 군집 탐지
  - `llm_reasoning/` - LLM 기반 유추 추론
  - `risk_scoring/` - 잠재 위험 점수 계산
  - `visualization/` - 3D 위험 지도 생성
  - `api/` - FastAPI 기반 REST API
  - `demo/` - Streamlit 기반 데모 인터페이스
  - `utils/` - 공통 유틸리티 함수들
- `data/` - 수집된 데이터 및 중간 결과
  - `raw/` - 원본 데이터
    - `packages/` - 패키지 메타데이터
    - `vulnerabilities/` - CVE 데이터
    - `code/` - 소스코드
    - `activity/` - GitHub 활동 데이터
  - `processed/` - 전처리된 데이터
    - `signals/` - 추출된 신호 데이터
    - `clusters/` - 위협 군집 데이터
    - `scores/` - 잠재 위험 점수
  - `graphs/` - 의존성 그래프 (NetworkX, Neo4j)
  - `historical/` - Historical Validation용 과거 데이터
- `experiments/` - 실험 노트북 및 결과 분석
  - `signal_analysis/` - 신호 분석 실험
  - `historical_validation/` - Log4Shell, Equifax 검증
  - `ablation_studies/` - 각 컴포넌트 기여도 분석
  - `llm_experiments/` - LLM 프롬프트 실험
- `configs/` - 설정 파일
  - `data_sources.yaml` - 데이터 소스 설정
  - `signal_weights.yaml` - 신호 가중치
  - `llm_config.yaml` - LLM API 설정
- `scripts/` - 실행 스크립트 (Phase 1-6)
- `tests/` - 단위/통합 테스트
- `docs/` - 문서화 및 논문 초안
- `results/` - 실험 결과 및 시각화

### 설정 파일
- `requirements.txt` - Python 의존성 관리
- `docker-compose.yml` - Neo4j 및 기타 서비스 컨테이너 설정
- `setup.py` - 패키지 설치 설정
- `.env` - 환경 변수 (API 키, DB 연결 정보 등)
- `.gitignore` - 버전 관리 제외 파일 (데이터, 로그, 캐시 등)
- `README.md` - 프로젝트 개요, 설치 및 실행 방법
- `configs/` - 시스템 설정 파일들
  - `agent_config.yaml` - AI 에이전트 설정
  - `neo4j_config.yaml` - Neo4j 연결 및 쿼리 설정
  - `data_sources.yaml` - 데이터 소스 설정

### 명명 규칙
- 디렉토리: 소문자와 언더스코어 사용 (`signal_extraction/`, `graph_analysis/`)
- 파일명: 명확하고 설명적인 이름 사용
- 실험 파일: 날짜와 실험명 포함 (`20241226_log4shell_validation.ipynb`)
- 신호 파일: 신호 유형 명시 (`graph_signals.json`, `vulnerability_patterns.json`)
- 설정 파일: 목적에 따른 명명 (`signal_weights.yaml`, `llm_config.yaml`)
- 스크립트 파일: Phase와 Step 명시 (`phase1_collect_packages.py`, `phase2_extract_signals.py`)
- 데이터 파일: cutoff 날짜 포함 (`packages_2021-11-01.json`, `historical_log4j.json`)
- 테스트 파일: `test_` 접두사 사용 (`test_signal_extraction.py`)
- 가능한 평면적 구조 유지, 과도한 중첩 방지

### 파일 조직 원칙
- **관심사 분리**: 데이터 수집, 그래프 구축, AI 에이전트, 평가 등 각 기능별로 분리
- **논리적 그룹화**: 관련 기능들을 같은 디렉토리에 배치 (예: 모든 평가 관련 코드는 `evaluation/`에)
- **재현성**: 모든 실험과 결과를 재현할 수 있도록 설정 파일과 스크립트 버전 관리
- **확장성**: 새로운 데이터 소스나 평가 메트릭 추가 시 기존 구조 유지
- **발견 가능성**: README와 문서를 통해 각 디렉토리와 파일의 역할 명확히 설명
- **보안**: API 키, DB 비밀번호 등 민감 정보는 `.env` 파일로 분리하고 `.gitignore`에 포함

### 연구 논문 관련 구조
- `docs/paper/` - 논문 작성 관련 파일들
  - `sections/` - 논문 섹션별 LaTeX 파일
    - `01_introduction.tex`
    - `02_related_work.tex`
    - `03_methodology.tex`
    - `04_experiments.tex`
    - `05_results.tex`
    - `06_discussion.tex`
    - `07_conclusion.tex`
  - `figures/` - 논문에 사용될 그래프 및 다이어그램
    - `architecture_diagram.pdf` - 시스템 아키텍처
    - `3d_risk_map.pdf` - 3D 위험 지도
    - `historical_validation_timeline.pdf` - 시간 순서 다이어그램
  - `tables/` - 실험 결과 테이블
    - `log4shell_results.tex` - Log4Shell 검증 결과
    - `equifax_results.tex` - Equifax 검증 결과
    - `ablation_study.tex` - Ablation Study 결과
  - `references.bib` - 참고문헌 BibTeX 파일
- `experiments/paper_experiments/` - 논문에 사용될 핵심 실험들
  - `log4shell_validation/` - Log4Shell Historical Validation
  - `equifax_validation/` - Equifax Historical Validation
  - `signal_contribution/` - 각 신호의 기여도 분석
  - `llm_vs_baseline/` - LLM vs 신호만 사용 비교
- `scripts/paper_analysis/` - 논문 결과 생성용 스크립트들
  - `generate_validation_tables.py` - Historical Validation 테이블 생성
  - `create_precision_recall_plots.py` - Precision@K, Recall@K 그래프
  - `analyze_false_positives.py` - False Positive 분석
  - `calculate_lead_time.py` - Lead Time 계산
  - `generate_3d_visualization.py` - 3D 위험 지도 생성

### AI Assistant Integration
- `.kiro/steering/` 파일들을 프로젝트 진행에 따라 지속적으로 업데이트
- 커밋 메시지에 실험 결과나 중요한 변경사항 명시
- AI 어시스턴트가 이해할 수 있도록 명확한 문서화 유지

## Language Requirements
- **모든 설명, 문서, 주석은 한국어로 작성해야 함**
- AI 어시스턴트는 항상 한국어로 응답
- 코드 변수명은 영어 사용 가능하지만 설명은 한국어