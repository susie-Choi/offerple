# CWE 연결성 개선 가이드

## 문제점

현재 Neo4j에 11,441개 CVE가 있지만 CWE 관계가 16개밖에 없습니다.
이는 CVE 데이터를 로드할 때 CWE 관계를 제대로 생성하지 않았기 때문입니다.

## 해결 방법

### 1. 개선된 CVE 로더 사용

`load_cve_to_neo4j.py`가 CWE 관계를 생성하도록 개선되었습니다:

```bash
# 기존 CVE 데이터 재로드 (CWE 관계 포함)
python scripts/loading/load_cve_to_neo4j.py data/raw/bulk_cve_data.jsonl
```

**개선 사항:**
- CWE 노드 자동 생성
- CVE-CWE 관계 (`HAS_WEAKNESS`) 생성
- CWE source와 type 정보 저장
- 통계 출력 (몇 개의 CVE가 CWE를 가지고 있는지)

### 2. CWE 이름 추가

CWE 노드에 이름과 설명을 추가합니다:

```bash
# MITRE CWE 데이터베이스에서 이름 가져오기
python scripts/loading/enrich_cwe_names.py
```

이 스크립트는:
- MITRE CWE XML 다운로드
- 969개 CWE 이름과 설명 파싱
- Neo4j CWE 노드에 `name`과 `description` 속성 추가

### 3. 결과 확인

```bash
# CWE 연결 확인
python scripts/analysis/check_attack_types.py
```

예상 결과:
- Client-Side Attacks (XSS, CSRF): 수백~수천 개 CVE
- Injection Attacks (SQLi, Command Injection): 수백~수천 개 CVE
- Server-Side Attacks (SSRF, Path Traversal): 수백~수천 개 CVE

## 전체 프로세스

```bash
# 1. 환경 변수 설정 (.env 파일)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# 2. CVE 데이터 재로드 (CWE 관계 포함)
python scripts/loading/load_cve_to_neo4j.py data/raw/bulk_cve_data.jsonl

# 3. CWE 이름 추가
python scripts/loading/enrich_cwe_names.py

# 4. 결과 확인
python scripts/analysis/check_attack_types.py
python scripts/check_neo4j_data.py
```

## 예상 결과

**Before:**
- CVE: 11,441
- CWE: 969
- HAS_WEAKNESS: 16 ❌

**After:**
- CVE: 11,441
- CWE: 969
- HAS_WEAKNESS: 8,000+ ✅
- CWE nodes with names: 969 ✅

## 주의사항

1. **중복 방지**: `MERGE`를 사용하므로 여러 번 실행해도 안전합니다
2. **기존 데이터**: 기존 CVE 노드는 유지되고 CWE 관계만 추가됩니다
3. **시간**: 11,441개 CVE 처리에 약 10-20분 소요됩니다

## 문제 해결

### "No CWE links created"

CVE 데이터에 CWE 정보가 없을 수 있습니다. 데이터 샘플 확인:

```bash
# 첫 번째 CVE 확인
head -1 data/raw/bulk_cve_data.jsonl | python -m json.tool | grep -A 5 weaknesses
```

### "Connection refused"

Neo4j가 실행 중이고 `.env` 파일이 올바른지 확인하세요.

### "Rate limit exceeded"

NVD API 키를 사용하면 더 빠릅니다:

```bash
export NVD_API_KEY=your-api-key
```

## 다음 단계

CWE 연결이 완료되면:

1. **공격 유형별 분석**: XSS, SQLi, SSRF 등 유형별 CVE 분석
2. **시계열 분석**: 특정 공격 유형의 시간별 트렌드
3. **패턴 학습**: 동일 CWE의 과거 취약점 패턴 학습
4. **예측 모델**: CWE 기반 취약점 예측

## 참고

- NVD API: https://nvd.nist.gov/developers/vulnerabilities
- MITRE CWE: https://cwe.mitre.org/
- Neo4j Cypher: https://neo4j.com/docs/cypher-manual/
