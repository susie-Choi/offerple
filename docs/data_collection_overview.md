# 데이터 수집 파이프라인 개요

이 문서는 Zero-Day Defense 연구를 위한 데이터 수집 파이프라인의 범위와 설계 원칙을 정리합니다.

## 목표

- 연구 계획서의 Phase 1, Phase 2를 지원할 수 있도록 다양한 생태계 데이터 확보
- 시간적 누수를 방지하기 위한 `cutoff_date` 기반 필터링 적용
- 패키지 메타데이터, 릴리스 이력, 저장소 활동을 통합 저장

## 현재 지원 소스

| 소스 | API | 수집 항목 |
| ---- | --- | --------- |
| PyPI | `https://pypi.org/pypi/{package}/json` | 패키지 정보, 릴리스 이력 |
| Maven Central | `https://search.maven.org/solrsearch/select` | 아티팩트 메타데이터, 릴리스 이력 |
| npm Registry | `https://registry.npmjs.org/{package}` | 패키지 정보, 버전별 타임스탬프 |
| GitHub | `https://api.github.com` | 저장소 메타데이터, 커밋, 이슈, PR |

## 데이터 저장 형식

- 패키지별 JSON Lines 파일 (`data/raw/<package>.jsonl`)
- 각 레코드는 `source`, `package`, `collected_at`, `payload` 필드 포함

## 향후 확장

1. 의존성 그래프 수집 (Libraries.io, deps.dev)
2. 다운로드 통계 및 커뮤니티 신호 추가 수집
3. 비동기 수집 및 재시도 로직 강화
4. 데이터 검증 및 품질 모듈 도입

해당 파이프라인을 기반으로 추후 특징 추출, LLM 추론, Historical Validation 단계가 구축될 예정입니다.
