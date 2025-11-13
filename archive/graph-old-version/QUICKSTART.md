# Zero-Day Defense 빠른 시작 가이드

이 가이드는 Zero-Day Defense 시스템을 빠르게 설정하고 실행하는 방법을 안내합니다.

## 1. 환경 설정 (5분)

### Python 가상환경 생성

```powershell
# uv를 사용한 가상환경 생성
uv venv zero-day-defense-env

# 가상환경 활성화
zero-day-defense-env\Scripts\activate

# 의존성 설치
uv pip install -r requirements.txt
```

### 환경 변수 설정

`.env` 파일 생성:

```powershell
# .env.example을 복사
copy .env.example .env

# .env 파일을 편집하여 API 키 입력
notepad .env
```

필수 항목:
- `OPENAI_API_KEY`: OpenAI API 키 (GPT-4 사용)
- `ANTHROPIC_API_KEY`: Anthropic API 키 (Claude 사용, 선택사항)

선택 항목:
- `NVD_API_KEY`: NVD API 키 (없으면 rate limit 적용)
- `GITHUB_TOKEN`: GitHub API 토큰 (코드 수집 시 필요)

## 2. Neo4j 시작 (선택사항)

```powershell
# Docker로 Neo4j 시작
docker-compose up -d neo4j

# 브라우저에서 확인
# http://localhost:7474
# 로그인: neo4j / zero-day-defense
```

## 3. 전체 파이프라인 실행 (30분~1시간)

### 방법 1: 통합 스크립트 사용 (권장)

```powershell
# 전체 파이프라인 한 번에 실행
python scripts/run_full_pipeline.py --provider openai --model gpt-4 --top-k 100
```

### 방법 2: 단계별 실행

```powershell
# Phase 1: 데이터 수집 (10-20분)
python scripts/phase1_collect_data.py

# Phase 2: 사전 신호 추출 (5-10분)
python scripts/phase2_extract_signals.py

# Phase 4: LLM 기반 예측 (10-30분, API 비용 발생)
python scripts/phase4_llm_prediction.py --provider openai --model gpt-4 --top-k 100
```

## 4. 결과 확인

### 파일로 확인

```powershell
# 상위 100개 고위험 패키지
type data\processed\scores\top_100_risks.json

# 전체 위험 점수
type data\processed\scores\latent_risk_scores.json
```

### API 서버로 확인

```powershell
# API 서버 시작
uvicorn src.api.main:app --reload --port 8000

# 브라우저에서 API 문서 확인
# http://localhost:8000/docs
```

API 사용 예시:

```powershell
# 상위 10개 고위험 패키지
curl http://localhost:8000/api/v1/risks/top?k=10

# 특정 패키지 위험 점수
curl http://localhost:8000/api/v1/risk/flask

# 패키지 검색
curl http://localhost:8000/api/v1/risks/search?query=django

# 전체 통계
curl http://localhost:8000/api/v1/stats
```

## 5. Historical Validation (Log4Shell)

Log4Shell 사태를 사전에 탐지할 수 있었는지 검증:

```powershell
# 2021-11-01 시점 데이터로 전체 파이프라인 실행
python scripts/run_full_pipeline.py --cutoff-date 2021-11-01

# Log4Shell 검증
python scripts/validate_log4shell.py

# 결과 확인
type data\results\log4shell_validation_results.json
```

## 6. 테스트 실행

```powershell
# 전체 테스트
pytest tests/ -v

# 특정 테스트만
pytest tests/test_graph_analysis.py -v
pytest tests/test_signal_extraction.py -v
```

## 비용 최적화 팁

### LLM API 비용 절감

1. **상위 K개만 예측**: `--top-k` 옵션으로 핵심 노드만 LLM 분석
   ```powershell
   python scripts/phase4_llm_prediction.py --top-k 50  # 100개 대신 50개만
   ```

2. **저렴한 모델 사용**: GPT-4 대신 GPT-3.5-turbo 사용
   ```powershell
   python scripts/phase4_llm_prediction.py --model gpt-3.5-turbo
   ```

3. **신호만 사용**: LLM 없이 신호 기반 점수만 사용
   - Phase 1, 2만 실행하고 Phase 4는 건너뛰기
   - `signal_score`만으로도 어느 정도 예측 가능

### NVD API Rate Limit 회피

1. **API 키 발급**: https://nvd.nist.gov/developers/request-an-api-key
2. `.env`에 `NVD_API_KEY` 설정
3. API 키 없으면 30초당 5개 요청으로 제한됨 (매우 느림)

## 문제 해결

### 1. 메모리 부족

```powershell
# 패키지 수를 줄여서 실행
# phase1_collect_data.py의 target_packages 목록 축소
```

### 2. LLM API 오류

```powershell
# API 키 확인
echo %OPENAI_API_KEY%

# Rate limit 오류 시 배치 크기 줄이기
# configs/llm_config.yaml의 batch.size 조정
```

### 3. Neo4j 연결 오류

```powershell
# Neo4j 상태 확인
docker ps

# Neo4j 재시작
docker-compose restart neo4j
```

## 다음 단계

1. **실험 노트북**: `experiments/` 디렉토리에서 Jupyter 노트북으로 분석
2. **커스터마이징**: `configs/` 디렉토리에서 가중치 및 설정 조정
3. **새로운 신호 추가**: `src/signal_extraction/`에 새로운 신호 추출기 구현
4. **다른 생태계**: Maven, npm 등 다른 패키지 생태계로 확장

## 참고 자료

- [README.md](README.md): 전체 프로젝트 개요
- [API 문서](http://localhost:8000/docs): FastAPI 자동 생성 문서
- [Steering 문서](.kiro/steering/): AI 어시스턴트 가이드

## 지원

문제가 발생하면 GitHub Issues에 등록해주세요.
