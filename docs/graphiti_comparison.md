# Graphiti vs 수동 스키마 비교

이 문서는 CVE 데이터를 Neo4j에 로드하는 두 가지 방법을 비교합니다.

## 방법 1: 수동 스키마 설계 (기존)

### 특징
- 명시적으로 노드 타입과 관계를 정의
- 구조화된 데이터에 최적화
- 성능 예측 가능
- 스키마 제어 가능

### 노드 타입
- `CVE`: 취약점
- `CPE`: 제품 버전
- `CWE`: 약점 유형
- `Vendor`: 벤더
- `Product`: 제품
- `Reference`: 참조 링크

### 실행 방법
```bash
python scripts/load_cve_to_neo4j.py data/raw/cve_data.jsonl \
  --uri neo4j+s://26e236b3.databases.neo4j.io \
  --username neo4j \
  --password <password>
```

### 장점
- 빠른 로딩 속도
- 정확한 스키마
- 쿼리 최적화 용이
- 비용 효율적 (LLM API 불필요)

### 단점
- 스키마 변경 시 코드 수정 필요
- 암묵적 관계 발견 어려움
- 비정형 데이터 처리 제한적

## 방법 2: Graphiti 자동 추출

### 특징
- LLM이 자동으로 엔티티와 관계 추출
- 비정형 텍스트에 최적화
- 의미론적 관계 발견
- 동적 스키마

### 실행 방법
```bash
# 1. Graphiti 설치
pip install graphiti-core

# 2. OpenAI API 키 설정
export OPENAI_API_KEY=your-api-key

# 3. CVE 데이터 로드
python scripts/load_cve_with_graphiti.py data/raw/cve_data.jsonl \
  --uri neo4j+s://26e236b3.databases.neo4j.io \
  --username neo4j \
  --password <password>
```

### Graphiti가 추출할 수 있는 것들
- **명시적 엔티티**: CVE ID, 제품명, 벤더명, CWE ID
- **암묵적 관계**: "Log4j vulnerability affects Apache products"
- **의미론적 연결**: 유사한 취약점 간 관계
- **시간적 관계**: 취약점 발견 → 패치 → 재발견

### 장점
- 자동 스키마 생성
- 의미론적 검색 가능
- 암묵적 관계 발견
- 비정형 데이터 처리 우수

### 단점
- 느린 처리 속도 (LLM 호출)
- OpenAI API 비용 발생
- 스키마 예측 어려움
- 정확도가 LLM 성능에 의존

## 비교 표

| 항목 | 수동 스키마 | Graphiti |
|------|------------|----------|
| 처리 속도 | 빠름 (초당 10+ CVE) | 느림 (초당 1-2 CVE) |
| 비용 | 무료 | OpenAI API 비용 |
| 정확도 | 매우 높음 | LLM 의존 |
| 유연성 | 낮음 | 높음 |
| 의미론적 검색 | 제한적 | 우수 |
| 비정형 데이터 | 어려움 | 우수 |
| 스키마 제어 | 완전 제어 | 제한적 |

## 추천 사용 시나리오

### 수동 스키마를 사용하세요
- ✅ 구조화된 데이터 (JSON, XML 등)
- ✅ 명확한 스키마가 있는 경우
- ✅ 대량 데이터 처리
- ✅ 비용 최소화
- ✅ 성능 중요

### Graphiti를 사용하세요
- ✅ 비정형 텍스트 문서
- ✅ 스키마가 불명확한 경우
- ✅ 의미론적 관계 발견 필요
- ✅ 탐색적 분석
- ✅ 문서 간 유사도 비교

## 하이브리드 접근

두 방법을 결합할 수도 있습니다:

1. **수동 스키마로 핵심 구조 구축**
   - CVE, CPE, CWE 등 명확한 엔티티

2. **Graphiti로 보조 관계 추출**
   - 취약점 설명에서 암묵적 관계 발견
   - 유사 취약점 클러스터링

3. **Vector DB 병행**
   - 의미론적 검색은 Pinecone/Weaviate
   - 구조적 쿼리는 Neo4j

## 실험 결과 비교

두 방법으로 동일한 CVE 데이터를 로드한 후:

### 수동 스키마 결과
```cypher
// 노드 수 확인
MATCH (n) RETURN labels(n) as type, count(n) as count

// 예상 결과:
// CVE: 5
// CPE: ~50
// CWE: ~10
// Vendor: ~5
// Product: ~10
// Reference: ~20
```

### Graphiti 결과
```cypher
// Graphiti가 생성한 노드 확인
MATCH (n) RETURN labels(n) as type, count(n) as count

// Graphiti는 다양한 엔티티 타입을 자동 생성
// 예: Vulnerability, Software, Organization, Weakness 등
```

## 다음 단계

1. **두 방법 모두 실행해보기**
2. **Neo4j Browser에서 그래프 비교**
3. **쿼리 성능 비교**
4. **실제 유스케이스에 맞는 방법 선택**

## 요구사항 추적 시스템에는?

**문서 변경 추적 및 영향도 분석** 시스템에는 **Graphiti가 더 적합**합니다:

- 요구사항 문서는 비정형 텍스트
- 의미론적 유사도 비교 필요
- 암묵적 의존성 발견 중요
- 스키마가 프로젝트마다 다름

하지만 **핵심 추적 관계는 수동으로 정의**하는 것이 좋습니다:
- `Requirement -[:VERSION_OF]-> Requirement`
- `Requirement -[:IMPLEMENTS]-> SWSpec`
- `SWSpec -[:TESTED_BY]-> TestCase`
