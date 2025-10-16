# ⏰ 시간적 데이터 누수 방지 가이드

## 문제점

**현재 데이터:**
- CVE 데이터: 2021-2024년 (이미 공개됨)
- 현재 시스템: "지금" 신호 수집 → "미래" 예측

**문제:**
- 과거 CVE로 학습하고 "현재" 신호로 테스트하면 의미 없음
- CVE 공개 **이후** 데이터로 예측하면 cheating!

## ✅ 올바른 사용법

### 1. Historical Backtesting (과거 시점 시뮬레이션)

```bash
# Log4Shell (CVE-2021-44228) 예측 시뮬레이션
# 실제 공개: 2021-12-09
# 우리의 예측: 2021-11-09 (30일 전)

python scripts/historical_validation.py --cve CVE-2021-44228
```

**타임라인:**
```
2021-10-10 ────────> 2021-11-09 ────────> 2021-12-09
    │                    │                     │
신호 수집 시작        예측 시점          실제 CVE 공개
    │                    │                     │
    └─ 30일 신호 ────────┘                     │
                         │                     │
                    우리의 예측          Ground Truth
```

### 2. 실제 워크플로우

```python
from datetime import datetime

# 1. CVE 정보 (실제로는 Neo4j에서 로드)
cve_disclosure = datetime(2021, 12, 9)  # Log4Shell

# 2. 예측 시점 설정 (CVE 공개 30일 전)
prediction_date = datetime(2021, 11, 9)

# 3. 신호 수집 (예측 시점 기준 과거 30일)
signal_start = datetime(2021, 10, 10)
signal_end = datetime(2021, 11, 9)  # CVE 공개 전!

# 4. 신호 수집 (시간 누수 없음!)
commits = collector.collect_commit_history(
    "apache/log4j",
    since=signal_start,
    until=signal_end  # ⚠️ CVE 공개 전 데이터만!
)

# 5. 예측
threat_score = scorer.score_package(vector)

# 6. 검증
if threat_score.score > 0.7:
    print(f"✅ 예측 성공! {cve_disclosure - prediction_date}일 전에 탐지")
else:
    print(f"❌ 예측 실패")
```

## 📊 검증 시나리오

### 시나리오 1: Log4Shell 예측 가능했나?

```bash
python scripts/historical_validation.py \
    --cve CVE-2021-44228 \
    --prediction-days-before 30 \
    --signal-window-days 30
```

**질문:** 2021년 11월 9일에 우리가 Log4Shell을 예측할 수 있었는가?

### 시나리오 2: Spring4Shell 예측

```bash
python scripts/historical_validation.py \
    --cve CVE-2022-22965 \
    --prediction-days-before 60
```

## 🎯 올바른 평가 방법

### Leave-One-Out Cross Validation

```python
# 1. 모든 CVE 리스트
all_cves = ["CVE-2021-44228", "CVE-2021-45046", "CVE-2022-22965", ...]

for test_cve in all_cves:
    # 2. 학습: 테스트 CVE 제외한 나머지로 클러스터 학습
    training_cves = [c for c in all_cves if c != test_cve]
    clusterer.fit(training_cve_vectors)
    
    # 3. 테스트: 테스트 CVE 공개 전 신호로 예측
    test_signals = collect_signals_before_disclosure(test_cve)
    prediction = scorer.score_package(test_signals)
    
    # 4. 평가
    if prediction.score > threshold:
        print(f"✅ {test_cve} 예측 성공!")
```

## 💡 핵심 원칙

1. **절대 미래 데이터 사용 금지**
   - CVE 공개 후 데이터로 예측 X
   - 예측 시점 이후 데이터 사용 X

2. **시간 순서 엄격히 준수**
   ```
   신호 수집 → 예측 → CVE 공개
   (과거)      (현재)   (미래)
   ```

3. **검증 시 Leave-One-Out**
   - 테스트 CVE는 학습에서 제외
   - 다른 CVE로만 클러스터 학습

## 🔧 실전 사용

### 현재 시스템으로 실제 예측

```python
# 지금 당장 취약점 예측하기
from datetime import datetime, timezone

# 1. 현재 시점
now = datetime.now(timezone.utc)
signal_start = now - timedelta(days=30)

# 2. 신호 수집 (최근 30일)
commits = collector.collect_commit_history(
    "target/repo",
    since=signal_start,
    until=now
)

# 3. 예측
threat_score = scorer.score_package(vector)

# 4. 해석
if threat_score.score > 0.7:
    print(f"⚠️ 고위험! 향후 30일 내 CVE 발생 가능성 높음")
    print(f"유사 CVE: {threat_score.similar_cves}")
```

## 📚 참고

- `scripts/historical_validation.py` - 과거 CVE 검증 스크립트
- `docs/prediction_system_guide.md` - 전체 가이드
- `QUICKSTART.md` - 빠른 시작
