# Zero-Day Defense Research Repository

이 저장소는 **LLM 기반 사전 신호 분석을 통한 소프트웨어 생태계 잠재 취약점 예측 시스템** 연구를 위한 코드와 실험 자료를 관리합니다.

## 주요 기능

### 보안 취약점 지식 그래프 (Neo4j)
다양한 데이터 소스를 통합하여 보안 취약점의 관계를 그래프로 표현합니다:

- **CVE 데이터** (NVD): 취약점 상세 정보, CVSS 점수, 영향받는 제품
- **GitHub Advisory**: 패키지별 보안 권고 및 패치 정보
- **EPSS 점수**: 취약점이 실제로 exploit될 확률 예측
- **Exploit Database**: 실제 exploit 코드 및 메타데이터

### 그래프 구조
```
CVE
├─[:AFFECTS]→ CPE ←[:HAS_VERSION]─ Product ←[:PRODUCES]─ Vendor
├─[:HAS_WEAKNESS]→ CWE
├─[:HAS_REFERENCE]→ Reference
├─[:HAS_EXPLOIT]→ Exploit
└─ Properties: epss_score, cvssScore, cvssSeverity

Advisory
├─[:REFERENCES]→ CVE
├─[:HAS_WEAKNESS]→ CWE
└─ ←[:HAS_ADVISORY]─ Package
```

## 설치

Python 3.10 이상을 권장합니다.

```bash
# 1. 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 패키지 설치
pip install -e .
```

## 환경 설정

`.env` 파일을 생성하여 필요한 환경변수를 설정합니다:

```bash
# .env.example을 복사
cp .env.example .env

# .env 파일 편집
# NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
# NEO4J_USERNAME=neo4j
# NEO4J_PASSWORD=your-password
# GITHUB_TOKEN=your-github-token (선택)
# GOOGLE_API_KEY=your-gemini-key (선택)
```

## 데이터 수집 및 로드

### 1. CVE 데이터 수집
```bash
python scripts/collect_cve_data.py config/cve_test_config.yaml
python scripts/load_cve_to_neo4j.py data/raw/cve_data.jsonl
```

### 2. GitHub Advisory 수집
```bash
python scripts/collect_github_advisory.py config/github_advisory_config.yaml
python scripts/load_advisory_to_neo4j.py data/raw/github_advisory.jsonl
```

### 3. EPSS 점수 수집
```bash
python scripts/collect_epss.py config/epss_config.yaml
python scripts/load_epss_to_neo4j.py data/raw/epss_scores.jsonl
```

### 4. Exploit Database 수집
```bash
python scripts/collect_exploits.py config/exploit_config.yaml
python scripts/load_exploits_to_neo4j.py data/raw/exploits.jsonl
```

## Neo4j 쿼리 예제

### 위험도가 높은 CVE 찾기
```cypher
// EPSS 점수가 높고 exploit이 있는 CVE
MATCH (c:CVE)-[:HAS_EXPLOIT]->(e:Exploit)
WHERE c.epss_score > 0.5
RETURN c.id, c.epss_score, c.cvssScore, count(e) as exploit_count
ORDER BY c.epss_score DESC
```

### Log4Shell 전체 생태계 보기
```cypher
MATCH path = (v:Vendor)-[:PRODUCES]->(p:Product)-[:HAS_VERSION]->(cpe:CPE)
              <-[:AFFECTS]-(c:CVE {id: 'CVE-2021-44228'})-[:HAS_EXPLOIT]->(e:Exploit)
RETURN path LIMIT 50
```

### 특정 제품의 취약점 분석
```cypher
MATCH (v:Vendor {name: 'apache'})-[:PRODUCES]->(p:Product)
      -[:HAS_VERSION]->(cpe:CPE)<-[:AFFECTS]-(c:CVE)
RETURN p.name, count(DISTINCT c) as vuln_count, 
       avg(c.cvssScore) as avg_cvss, avg(c.epss_score) as avg_epss
ORDER BY vuln_count DESC
```

## 프로젝트 구조

```
zero-day-defense/
├── src/zero_day_defense/          # Python 패키지
│   ├── config.py                   # 설정 로더
│   ├── pipeline.py                 # 데이터 파이프라인
│   └── data_sources/               # 데이터 소스 수집기
│       ├── cve.py                  # NVD CVE 수집
│       ├── github_advisory.py      # GitHub Advisory 수집
│       ├── epss.py                 # EPSS 점수 수집
│       └── exploit_db.py           # Exploit-DB 수집
├── scripts/                        # 실행 스크립트
│   ├── collect_*.py                # 데이터 수집 스크립트
│   └── load_*_to_neo4j.py         # Neo4j 로더
├── config/                         # 설정 파일
├── docs/                           # 문서
└── .kiro/                          # Kiro IDE 설정
    ├── steering/                   # AI 어시스턴트 가이드
    └── specs/                      # 기능 스펙
```

## 환경 변수

- `NEO4J_URI`: Neo4j 데이터베이스 URI
- `NEO4J_USERNAME`: Neo4j 사용자명 (기본: neo4j)
- `NEO4J_PASSWORD`: Neo4j 비밀번호
- `GITHUB_TOKEN`: GitHub API 토큰 (선택, rate limit 향상)
- `NVD_API_KEY`: NVD API 키 (선택, 빠른 수집)
- `GOOGLE_API_KEY`: Google Gemini API 키 (선택, Graphiti 사용 시)

## 문서

- [Graphiti 비교 가이드](docs/graphiti_comparison.md): 수동 스키마 vs Graphiti 자동 추출
- [데이터 수집 개요](docs/data_collection_overview.md): 파이프라인 설계 및 범위

## 다음 단계

1. ✅ 다중 데이터 소스 통합 (CVE, Advisory, EPSS, Exploit)
2. ✅ Neo4j 그래프 데이터베이스 구축
3. 🔄 데이터 시각화 대시보드
4. 📋 LLM 기반 잠재 위험 추론 모듈
