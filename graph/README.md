# Zero-Day Defense: LLM 기반 잠재 위협 사전 탐지 시스템

**사후 대응이 아닌 사전 방어**: CVE 공개 전에 잠재적 취약점을 예측하는 AI 시스템

## 프로젝트 개요

이 프로젝트는 **제로데이 공격을 사전에 방어**하는 새로운 패러다임을 제시합니다. LLM과 그래프 분석을 결합하여 아직 발견되지 않은 잠재적 취약점을 예측하고, 치명적인 위협이 발생할 가능성이 높은 영역을 선제적으로 식별합니다.

### 핵심 아이디어

- **문제**: CVE 공개 후 패치까지의 시간 동안 치명적 피해 발생 (Log4Shell, Equifax 등)
- **해결책**: CVE 정보 없이 관찰 가능한 **사전 신호**만으로 잠재 위험 예측
- **방법**: 다차원 신호 분석 + LLM 유추 추론
- **검증**: Log4Shell, Equifax 등 실제 사고를 사전에 탐지할 수 있었는지 Historical Validation

## 주요 기능

### 4단계 방법론

1. **Phase 1: 데이터 수집**
   - 패키지 생태계 데이터 (PyPI, Maven, npm)
   - 과거 취약점 이력 (NVD, GitHub Advisory)
   - 코드 및 개발 활동 데이터

2. **Phase 2: 사전 신호 추출**
   - 그래프 중심성 분석 (PageRank, Betweenness)
   - 과거 취약점 패턴 분석
   - 코드 레벨 위험 신호
   - 유지보수 활동 패턴

3. **Phase 3: 위협 군집 분석**
   - 핵심 노드 식별
   - 커뮤니티 탐지
   - 군집 내 연관성 분석

4. **Phase 4: LLM 기반 예측**
   - 다차원 신호 통합
   - 유추 기반 추론
   - 잠재 위험 점수 계산

### Historical Validation

- **Log4Shell (CVE-2021-44228)**: 2021년 11월 시점에 탐지 가능했는지 검증
- **Equifax (CVE-2017-5638)**: 2017년 2월 시점에 탐지 가능했는지 검증
- **평가 지표**: Precision@K, Recall@K, Lead Time

## 설치 및 실행

### 최소 요구사항

- **Python**: 3.9 이상
- **메모리**: 4GB 이상 (소규모 데이터셋)
- **API 키**: OpenAI 또는 Anthropic (LLM 사용 시)

### 선택사항

- **Neo4j**: 대규모 그래프 분석 시 (10,000+ 패키지)
- **Docker**: Neo4j 및 API 서버 컨테이너 실행

### 환경 설정

```powershell
# Python 가상환경 생성 (uv 사용)
uv venv zero-day-defense-env
zero-day-defense-env\Scripts\activate

# 의존성 설치
uv pip install -r requirements.txt
```

### 환경 변수 설정

`.env` 파일 생성:

```env
# 필수: LLM API 키 (둘 중 하나)
OPENAI_API_KEY=your_openai_api_key
# 또는
ANTHROPIC_API_KEY=your_anthropic_api_key

# 선택사항: NVD API 키 (없으면 rate limit 적용)
NVD_API_KEY=your_nvd_api_key

# 선택사항: Neo4j (대규모 그래프 분석 시)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=zero-day-defense
```

### Neo4j 설정 (선택사항)

**Neo4j는 선택사항입니다!** 소규모 데이터셋(~10,000 패키지)은 NetworkX만으로 충분합니다.

대규모 분석이 필요한 경우에만:

```powershell
# Docker로 Neo4j 시작
docker-compose up -d neo4j

# 브라우저에서 확인
# http://localhost:7474
# 로그인: neo4j / zero-day-defense
```

### 전체 파이프라인 실행

```powershell
# 방법 1: 통합 스크립트 사용 (권장)
python scripts/run_full_pipeline.py --provider openai --model gpt-4 --top-k 100

# 방법 2: 단계별 실행
python scripts/phase1_collect_data.py
python scripts/phase2_extract_signals.py
python scripts/phase4_llm_prediction.py --provider openai --model gpt-4 --top-k 100
```

### Historical Validation 실행

```powershell
# Log4Shell 검증 (2021-11-01 시점)
python scripts/run_full_pipeline.py --cutoff-date 2021-11-01
python scripts/validate_log4shell.py
```

## 프로젝트 구조

```
zero-day-defense/
├── src/
│   ├── data_collection/       # 데이터 수집 모듈
│   │   ├── package_collector.py
│   │   └── vulnerability_collector.py
│   ├── signal_extraction/     # 신호 추출 모듈
│   │   └── vulnerability_patterns.py
│   ├── graph_analysis/        # 그래프 분석 모듈 (NetworkX 기반)
│   │   └── dependency_graph.py
│   ├── llm_reasoning/         # LLM 추론 모듈
│   │   └── risk_predictor.py
│   ├── risk_scoring/          # 위험 점수 계산
│   │   └── latent_risk_calculator.py
│   ├── validation/            # Historical Validation
│   │   └── historical_validator.py
│   └── api/                   # REST API
│       └── main.py
├── scripts/                   # 실행 스크립트
│   ├── phase1_collect_data.py
│   ├── phase2_extract_signals.py
│   ├── phase4_llm_prediction.py
│   ├── run_full_pipeline.py
│   └── validate_log4shell.py
├── configs/                   # 설정 파일
│   ├── llm_config.yaml
│   └── signal_weights.yaml
├── tests/                     # 테스트
├── data/                      # 데이터 디렉토리 (자동 생성)
├── requirements.txt
├── docker-compose.yml         # Neo4j 등 (선택사항)
├── README.md
└── QUICKSTART.md
```

## API 사용법

### API 서버 시작

```powershell
uvicorn src.api.main:app --reload --port 8000
```

### 주요 엔드포인트

```bash
# 특정 패키지 위험 점수 조회
GET http://localhost:8000/api/v1/risk/{package_name}

# 상위 K개 고위험 패키지
GET http://localhost:8000/api/v1/risks/top?k=100&min_score=0.5

# 패키지 검색
GET http://localhost:8000/api/v1/risks/search?query=flask&limit=20

# 그래프 메트릭 조회
GET http://localhost:8000/api/v1/graph/{package_name}

# 전체 통계
GET http://localhost:8000/api/v1/stats
```

API 문서: http://localhost:8000/docs

## 핵심 제약 사항

### 정보 사용 제약

**사용 가능한 정보** (CVE 공개 전 관찰 가능):
- 그래프 구조 (의존성 관계, 중심성)
- 과거 취약점 이력 및 패턴
- 코드 레벨 특징 (위험 함수, 복잡도)
- 개발 활동 패턴 (커밋, 이슈, PR)

**사용 불가능한 정보** (미래 정보):
- CVSS 점수 (CVE 공개 후에만 존재)
- 공격 벡터 세부사항
- 실제 공격 사례 및 피해 규모

### 시간적 엄밀성

- 모든 예측은 해당 시점에 실제로 알 수 있었던 정보만 사용
- "미래를 보고 과거를 예측"하는 Data Leakage 절대 금지
- Historical Validation 시 시간 순서 엄격히 준수

## 평가 지표

- **Precision@K**: 상위 K개 예측 중 실제 취약점 발생 비율
- **Recall@K**: 실제 취약점 중 상위 K개에 포함된 비율
- **Lead Time**: CVE 공개 대비 얼마나 일찍 탐지했는지
- **False Positive Rate**: 잘못된 경보 비율

## 비용 최적화

### LLM API 비용 절감

1. **상위 K개만 예측**: 핵심 노드만 LLM 분석
   ```powershell
   python scripts/phase4_llm_prediction.py --top-k 50
   ```

2. **저렴한 모델 사용**: GPT-3.5-turbo 사용
   ```powershell
   python scripts/phase4_llm_prediction.py --model gpt-3.5-turbo
   ```

3. **신호만 사용**: LLM 없이 Phase 1-2만 실행

### NVD API Rate Limit

- API 키 없으면 30초당 5개 요청으로 제한
- API 키 발급: https://nvd.nist.gov/developers/request-an-api-key

## 테스트

```powershell
# 전체 테스트
pytest tests/ -v

# 특정 테스트
pytest tests/test_graph_analysis.py -v
```

## 연구 목표

- **최종 목표**: NeurIPS, ICML, ICLR 등 top-tier AI 학회 논문 투고
- **핵심 기여**: 제로데이 공격의 잠재 위험 지대를 선제적으로 식별하는 AI 시스템
- **실용적 가치**: 제한된 보안 자원을 가장 치명적인 위협에 집중 배치

## FAQ

### Q: Neo4j가 필수인가요?
**A**: 아니요! 소규모 데이터셋(~10,000 패키지)은 NetworkX만으로 충분합니다. Neo4j는 대규모 분석 시에만 권장됩니다.

### Q: LLM API 비용이 얼마나 드나요?
**A**: 상위 100개 패키지 분석 시 약 $5-10 (GPT-4 기준). `--top-k` 옵션으로 조절 가능합니다.

### Q: 실제 데이터 없이 테스트할 수 있나요?
**A**: 네, `tests/` 디렉토리의 단위 테스트로 기능 검증 가능합니다.

## 라이선스

MIT License

## 기여

이슈 및 PR 환영합니다!

## 참고 자료

- [QUICKSTART.md](QUICKSTART.md): 빠른 시작 가이드
- [NVD API](https://nvd.nist.gov/)
- [PyPI](https://pypi.org/)
- [NetworkX](https://networkx.org/)
- [OpenAI API](https://platform.openai.com/docs)

---

**면책 조항**: 이 시스템은 연구 목적으로 개발되었습니다. 발견한 잠재 위험은 책임감 있게 보고해야 하며, Responsible Disclosure 원칙을 준수해야 합니다.
