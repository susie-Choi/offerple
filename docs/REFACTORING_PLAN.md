# ROTA 구조 리팩토링 계획

## 🎯 목표: ROTA (바퀴) 테마 구조

```
src/rota/
├── __init__.py
├── wheel/          # 🎡 클러스터링 & 패턴 분석
│   ├── __init__.py
│   ├── spinner.py      # 회전 분석 (시계열 패턴)
│   ├── cluster.py      # 클러스터링
│   └── patterns.py     # 패턴 감지
│
├── spokes/         # 🔗 데이터 수집 (바퀴살)
│   ├── __init__.py
│   ├── cve.py          # CVE 데이터
│   ├── epss.py         # EPSS 점수
│   ├── advisory.py     # GitHub Advisory
│   ├── exploits.py     # Exploit-DB
│   ├── github.py       # GitHub 신호
│   └── packages.py     # PyPI/npm/Maven
│
├── hub/            # 🎯 중심축 - 데이터 통합
│   ├── __init__.py
│   ├── neo4j.py        # Neo4j 그래프
│   ├── graph.py        # 그래프 연산
│   └── storage.py      # 데이터 저장
│
├── oracle/         # 🔮 예측 엔진
│   ├── __init__.py
│   ├── predictor.py    # 메인 예측기
│   ├── risk_score.py   # 위험도 계산
│   ├── features.py     # 특징 추출
│   └── signals.py      # 신호 분석
│
├── axle/           # ⚙️ 평가 & 검증
│   ├── __init__.py
│   ├── validator.py    # Historical validation
│   ├── metrics.py      # 성능 메트릭
│   └── baselines.py    # Baseline 비교
│
└── cli/            # 🖥️ CLI & API
    ├── __init__.py
    ├── commands.py     # CLI 명령어
    └── api.py          # Python API
```

## 📋 매핑: 현재 → 새 구조

### 1. spokes/ (데이터 수집)
| 현재 | 새 위치 |
|------|---------|
| `data_sources/cve.py` | `spokes/cve.py` |
| `data_sources/epss.py` | `spokes/epss.py` |
| `data_sources/github_advisory.py` | `spokes/advisory.py` |
| `data_sources/exploit_db.py` | `spokes/exploits.py` |
| `data_sources/github.py` | `spokes/github.py` |
| `data_sources/pypi.py` | `spokes/packages.py` (통합) |
| `data_sources/npm.py` | `spokes/packages.py` (통합) |
| `data_sources/maven.py` | `spokes/packages.py` (통합) |

### 2. wheel/ (클러스터링 & 패턴)
| 현재 | 새 위치 |
|------|---------|
| `prediction/engine/clusterer.py` | `wheel/cluster.py` |
| `prediction/signal_collectors/github_signals.py` | `wheel/spinner.py` |
| `prediction/feature_engineering/extractor.py` | `wheel/patterns.py` |

### 3. hub/ (데이터 통합)
| 현재 | 새 위치 |
|------|---------|
| `graph/neo4j_manager.py` | `hub/neo4j.py` |
| `graph/query_builder.py` | `hub/graph.py` |
| `prediction/signal_collectors/storage.py` | `hub/storage.py` |

### 4. oracle/ (예측)
| 현재 | 새 위치 |
|------|---------|
| `prediction/engine/scorer.py` | `oracle/risk_score.py` |
| `prediction/agents/signal_analyzer.py` | `oracle/signals.py` |
| `prediction/feature_engineering/builder.py` | `oracle/features.py` |
| `prediction/agents/threat_assessment.py` | `oracle/predictor.py` |

### 5. axle/ (평가)
| 현재 | 새 위치 |
|------|---------|
| `evaluation/validation/temporal_splitter.py` | `axle/validator.py` |
| `evaluation/validation/metrics.py` | `axle/metrics.py` |
| `evaluation/baselines/` | `axle/baselines.py` |

### 6. cli/ (인터페이스)
| 현재 | 새 위치 |
|------|---------|
| `cli.py` | `cli/commands.py` |
| `__init__.py` (API exports) | `cli/api.py` |

## 🎨 네이밍 철학

### ROTA = Rotating Threat Assessment
- **Wheel** (바퀴): 계속 돌아가는 분석 - 시계열, 패턴, 클러스터
- **Spokes** (바퀴살): 중심으로 데이터를 모으는 수집기들
- **Hub** (중심축): 모든 데이터가 모이는 통합 지점
- **Oracle** (예언자): 미래를 예측하는 엔진
- **Axle** (차축): 시스템을 지탱하는 검증 프레임워크

## 🚀 마이그레이션 단계

### Phase 1: 새 구조 생성 (1시간)
1. 새 디렉토리 생성
2. `__init__.py` 파일 생성
3. Import 경로 정의

### Phase 2: 파일 이동 & 리팩토링 (3시간)
1. spokes/ 먼저 (가장 독립적)
2. hub/ (중간 의존성)
3. wheel/ (패턴 분석)
4. oracle/ (예측 엔진)
5. axle/ (평가)
6. cli/ (마지막)

### Phase 3: Import 경로 업데이트 (2시간)
1. 모든 import 문 수정
2. 테스트 실행
3. 문서 업데이트

### Phase 4: 정리 (1시간)
1. 구 디렉토리 삭제
2. pyproject.toml 업데이트
3. README 업데이트

## 📦 PyPI 패키지 구조

```python
# 사용자 관점
from rota import predict_risk
from rota.spokes import CVECollector
from rota.oracle import RiskPredictor
from rota.wheel import PatternAnalyzer
from rota.hub import Neo4jGraph

# CLI
rota predict --repo django/django
rota collect --source cve
rota validate --dataset cves.jsonl
```

## ⚠️ 주의사항

1. **하위 호환성**: 기존 import 경로도 일시적으로 유지
2. **점진적 마이그레이션**: 한 번에 하나씩
3. **테스트**: 각 단계마다 테스트 실행
4. **문서화**: 변경사항 기록

## 🎯 예상 효과

1. **직관성**: 바퀴 테마로 기억하기 쉬움
2. **모듈성**: 각 부분이 명확히 분리
3. **확장성**: 새 기능 추가 위치가 명확
4. **브랜딩**: ROTA 이름과 일치하는 구조
