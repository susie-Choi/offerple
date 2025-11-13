# Zero-Day Defense Agent 배포 및 운영 가이드

## Agent 아키텍처 개요

이 프로젝트는 사전 신호 기반 잠재 위협 탐지를 수행하는 LLM 에이전트를 클라우드 환경에서 운영하는 것을 목표로 합니다.

### 핵심 컴포넌트
- **Signal Extraction Engine**: 다차원 사전 신호 추출 시스템
- **Graph Analysis Module**: NetworkX/Neo4j 기반 의존성 그래프 분석
- **LLM Reasoning Agent**: 유추 기반 추론을 수행하는 LLM 에이전트
- **Risk Scoring System**: 잠재 위험 점수 계산 엔진
- **Visualization Service**: 3D 위험 지도 생성 및 제공
- **API Gateway**: RESTful API 인터페이스
- **Monitoring System**: 성능 모니터링 및 로깅

## 클라우드 배포 전략

### 컨테이너화 (Docker)
```yaml
# docker-compose.yml 구조
services:
  data-collector:
    # 패키지 생태계 및 취약점 데이터 수집
  signal-extractor:
    # 사전 신호 추출 엔진
  graph-analyzer:
    # 그래프 분석 및 군집 탐지
  llm-agent:
    # LLM 기반 유추 추론 에이전트
  risk-scorer:
    # 잠재 위험 점수 계산
  neo4j:
    # Neo4j 그래프 데이터베이스
  api-gateway:
    # FastAPI 기반 API 서버
  visualization:
    # Streamlit 기반 3D 시각화
  monitoring:
    # Prometheus + Grafana
```

### 클라우드 플랫폼 옵션

**AWS 배포:**
- **ECS/EKS**: 컨테이너 오케스트레이션
- **SageMaker**: 모델 호스팅 (고성능 추론)
- **Neptune**: 관리형 그래프 데이터베이스 (Neo4j 대안)
- **API Gateway**: API 관리 및 스케일링
- **CloudWatch**: 모니터링 및 로깅

**Google Cloud 배포:**
- **GKE**: Kubernetes 기반 배포
- **Vertex AI**: 모델 서빙
- **Cloud SQL**: 관리형 데이터베이스
- **Cloud Run**: 서버리스 API 배포

**Azure 배포:**
- **AKS**: Azure Kubernetes Service
- **Azure ML**: 모델 배포 및 관리
- **Cosmos DB**: 그래프 데이터베이스

### 로컬 개발 환경
```bash
# uv를 사용한 환경 설정
uv venv zero-day-defense-env
source zero-day-defense-env/bin/activate  # Linux/Mac
# zero-day-defense-env\Scripts\activate  # Windows

# 의존성 설치
uv pip install -r requirements.txt

# 로컬 서비스 시작
docker-compose up -d neo4j
python scripts/collect_package_metadata.py  # 데이터 수집
python scripts/extract_graph_signals.py  # 신호 추출
uvicorn src.api.main:app --reload --port 8000  # API 서버
streamlit run src.demo/risk_visualization.py  # 시각화 UI
```

## Agent 성능 최적화

### 데이터 처리 최적화
- **병렬 처리**: 다중 패키지 동시 분석 (multiprocessing)
- **캐싱**: 그래프 중심성 계산 결과 캐싱
- **증분 업데이트**: 전체 재계산 대신 변경된 부분만 업데이트
- **데이터베이스 인덱싱**: Neo4j 쿼리 최적화

### LLM 추론 최적화
- **배치 처리**: 여러 패키지를 배치로 LLM에 전달
- **프롬프트 캐싱**: 유사한 프롬프트 재사용
- **비동기 처리**: async/await를 통한 동시 API 호출
- **Rate Limiting**: API 호출 제한 준수

### 그래프 분석 최적화
- **알고리즘 선택**: 대규모 그래프에 적합한 알고리즘 사용
- **메모리 관리**: 대용량 그래프의 효율적 메모리 사용
- **분산 처리**: 그래프 파티셔닝을 통한 분산 계산

## 보안 및 모니터링

### 보안 설정
- **API 키 관리**: OpenAI, GitHub API 키를 환경 변수로 관리
- **HTTPS**: SSL/TLS 인증서 적용
- **Rate Limiting**: API 호출 제한 (특히 LLM API)
- **데이터 보안**: 민감한 취약점 정보 암호화
- **Responsible Disclosure**: 발견한 잠재 위험의 윤리적 보고

### 모니터링 메트릭
- **데이터 수집 상태**: 패키지 수집 진행률, 실패율
- **신호 추출 성능**: 처리 속도, 메모리 사용량
- **LLM 추론 성능**: API 응답 시간, 비용, 오류율
- **예측 품질**: Precision@K, Recall@K (Historical Validation 기준)
- **시스템 리소스**: CPU, 메모리, 디스크 사용률
- **비용 추적**: LLM API 호출 비용, 클라우드 인프라 비용

## 개발 워크플로우

### CI/CD 파이프라인
```yaml
# GitHub Actions 예시
name: Zero-Day Defense Pipeline
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # 주간 데이터 업데이트
jobs:
  test:
    # 단위 테스트 및 통합 테스트
  data-collection:
    # 패키지 및 취약점 데이터 수집
  signal-extraction:
    # 사전 신호 추출
  risk-prediction:
    # 잠재 위험 점수 계산
  validation:
    # Historical Validation 실행
  deploy:
    # 클라우드 환경에 배포
  monitor:
    # 배포 후 성능 모니터링
```

### 실험 관리
- **MLflow**: 신호 가중치, LLM 프롬프트 실험 추적
- **Weights & Biases**: 예측 성능 모니터링
- **DVC**: 대용량 그래프 데이터 버전 관리
- **Git**: 코드 및 설정 버전 관리
- **Jupyter**: 실험 노트북 및 분석

## 비용 최적화

### 클라우드 비용 관리
- **Spot Instances**: 데이터 수집 및 신호 추출에 저렴한 인스턴스 활용
- **Reserved Instances**: Neo4j 데이터베이스는 장기 예약 인스턴스
- **Auto Shutdown**: 실험 완료 후 자동 종료
- **리소스 모니터링**: 불필요한 리소스 정리

### LLM API 비용 최적화
- **배치 처리**: 여러 패키지를 한 번에 처리하여 API 호출 최소화
- **캐싱**: 유사한 패키지는 이전 결과 재사용
- **프롬프트 최적화**: 토큰 수를 줄이면서 품질 유지
- **모델 선택**: GPT-4 vs GPT-3.5 vs Claude 비용/성능 비교
- **샘플링**: 전체 패키지가 아닌 상위 위험 후보만 LLM 분석

### 데이터 수집 비용
- **증분 업데이트**: 전체 재수집 대신 변경분만 수집
- **API Rate Limiting**: GitHub API 무료 한도 내에서 운영
- **캐싱**: 변경되지 않은 데이터 재사용

## 문제 해결 가이드

### 일반적인 문제들
1. **메모리 부족**: 그래프 파티셔닝 또는 더 큰 인스턴스 사용
2. **느린 그래프 분석**: 알고리즘 최적화 또는 분산 처리
3. **높은 LLM API 비용**: 배치 크기 증가, 캐싱 강화
4. **낮은 예측 정확도**: 신호 가중치 조정, 더 많은 Historical Validation
5. **Data Leakage**: 시간 분할 검증, cutoff 날짜 엄격히 준수

### 디버깅 도구
- **로그 분석**: 각 Phase별 상세 로깅
- **성능 프로파일링**: 병목 지점 식별 (cProfile, line_profiler)
- **데이터 검증**: cutoff 이후 데이터 누락 확인
- **시각화**: 중간 결과 시각화로 문제 파악
- **에러 추적**: Sentry 등 에러 모니터링 도구

### Historical Validation 문제
- **시간 순서 위반**: 모든 데이터에 타임스탬프 확인
- **낮은 Recall**: 신호 추출 로직 개선
- **높은 False Positive**: 임계값 조정, 신호 가중치 재조정