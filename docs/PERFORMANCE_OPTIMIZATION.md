# 성능 최적화 전략

## 문제 분석

### 현재 속도: ~22분/CVE
- 180일 커밋 히스토리 수집
- Django 같은 활발한 프로젝트: ~1000+ 커밋
- 각 커밋마다 상세 정보 API 호출
- **결과**: 1000 API 호출 × 1초 대기 = 16분+

## 최적화 전략

### 1. 배치 API 호출 (가장 효과적)

**문제**: 커밋 하나씩 상세 정보 가져오기
```python
for commit in commits:
    detail = get_commit_detail(commit.sha)  # N+1 문제
```

**해결**: GraphQL API 사용
```graphql
query {
  repository(owner: "django", name: "django") {
    object(expression: "main") {
      ... on Commit {
        history(first: 100, since: "2024-01-01") {
          nodes {
            oid
            message
            author { name, email, date }
            additions
            deletions
            changedFiles
          }
        }
      }
    }
  }
}
```

**효과**: 
- 1000개 커밋 → 10번 API 호출 (100개씩 배치)
- 1000초 → 10초 (100배 빠름)

### 2. 선택적 데이터 수집

**전략**: 모든 데이터를 항상 수집하지 말고, 필요할 때만

#### Level 1: 기본 정보 (빠름, 항상)
- 커밋 메시지, 작성자, 시간
- PR 제목, 상태
- Issue 제목, 라벨

**시간**: ~10초

#### Level 2: 상세 정보 (중간, 의심될 때만)
- 파일 변경 내역
- PR 리뷰 수
- Issue 코멘트 수

**시간**: ~1분

#### Level 3: 전체 분석 (느림, 확실할 때만)
- 각 파일의 diff
- 모든 코멘트 내용
- 의존성 변경 상세

**시간**: ~5분

### 3. 증분 업데이트 (Incremental)

**문제**: 매번 180일 전체 히스토리 수집

**해결**: 마지막 수집 이후 변경사항만
```python
# 첫 실행: 180일 전체 (느림)
collect_history(since=180_days_ago)

# 이후 실행: 마지막 이후만 (빠름)
collect_history(since=last_collection_time)
```

**효과**:
- 첫 실행: 22분
- 이후 실행: 10초 (일일 업데이트 시)

### 4. 캐싱 전략

#### 4.1 로컬 캐시
```python
# 한 번 가져온 커밋은 다시 안 가져옴
cache = {
    "django/django:abc123": {
        "files": ["file1.py", "file2.py"],
        "lines_added": 50,
        "cached_at": "2024-10-16T10:00:00Z"
    }
}
```

#### 4.2 Redis 캐시 (프로덕션)
```python
# 여러 워커가 공유
redis.setex(
    f"commit:{repo}:{sha}",
    3600,  # 1시간 TTL
    json.dumps(commit_data)
)
```

### 5. 병렬 처리

**문제**: 순차적 API 호출

**해결**: 동시에 여러 요청
```python
import asyncio
import aiohttp

async def collect_commits_parallel(commits):
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_commit_detail(session, commit.sha)
            for commit in commits
        ]
        return await asyncio.gather(*tasks)
```

**효과**:
- 10개 동시 요청 → 10배 빠름
- 단, GitHub rate limit 주의 (5000 req/hour)

### 6. 스마트 샘플링

**전략**: 모든 커밋을 분석하지 말고 대표 샘플만

```python
# 1000개 커밋 → 100개 샘플
sampled_commits = smart_sample(commits, n=100)
```

**샘플링 전략**:
- 최근 커밋 우선 (시간 가중치)
- 보안 키워드 포함 커밋 우선
- 큰 변경사항 우선 (파일 수 많은 것)

**효과**: 10배 빠름, 정확도 90% 유지

## 실시간 코드 푸시 예측 최적화

### 시나리오: CI/CD 파이프라인 통합

```yaml
# .github/workflows/security-check.yml
on: [push]
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v2
      
      - name: Zero-Day Risk Analysis
        run: |
          python -m zero_day_defense.predict \
            --commit ${{ github.sha }} \
            --fast-mode \
            --cache-enabled
```

**요구사항**: < 30초 (CI/CD 허용 시간)

### 최적화 조합:

1. **캐시 활용** (첫 실행 제외)
   - 저장소 메타데이터 캐싱
   - 최근 커밋 히스토리 캐싱
   - **시간**: 5초

2. **증분 분석**
   - 새 커밋만 분석
   - 기존 특징 재사용
   - **시간**: 3초

3. **경량 특징 추출**
   - 커밋 메시지 분석 (로컬)
   - 파일 경로 분석 (로컬)
   - API 호출 최소화
   - **시간**: 2초

4. **총 시간**: ~10초 ✅

## 구현 우선순위

### Phase 1: 빠른 개선 (1일)
- [x] GraphQL API 전환
- [x] 로컬 파일 캐싱
- [x] 선택적 데이터 수집

**예상 효과**: 22분 → 2분 (11배)

### Phase 2: 중간 개선 (3일)
- [ ] Redis 캐싱
- [ ] 증분 업데이트
- [ ] 병렬 처리

**예상 효과**: 2분 → 20초 (6배)

### Phase 3: 고급 최적화 (1주)
- [ ] 스마트 샘플링
- [ ] 특징 사전 계산
- [ ] 모델 경량화

**예상 효과**: 20초 → 5초 (4배)

### 최종 목표
- **Historical Validation**: 2분/CVE (현재 22분)
- **Real-time Prediction**: 5초/push (현재 불가능)

## 측정 지표

```python
# 성능 벤치마크
metrics = {
    "api_calls": 10,           # 목표: < 20
    "total_time": 5.0,         # 목표: < 10초
    "cache_hit_rate": 0.95,    # 목표: > 90%
    "accuracy": 0.85,          # 목표: > 80%
}
```

## 다음 단계

1. **GraphQL API 구현** (가장 효과적)
2. **캐싱 시스템 구축**
3. **벤치마크 테스트**
4. **실시간 예측 데모**
