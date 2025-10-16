# Paper Experiments Guide

논문 투고를 위한 실험 실행 가이드입니다.

## 🎯 목표

탑티어 보안 컨퍼런스/저널(USENIX Security, IEEE S&P, CCS, NDSS)에 투고할 수 있는 정량적 실험 결과를 생성합니다.

## 📊 핵심 실험

### 1. 데이터셋 수집

100+ CVE를 오픈소스 프로젝트에서 수집합니다.

```bash
# 기본 수집 (100 CVEs, CVSS >= 7.0)
python scripts/collect_paper_dataset.py

# 더 많은 CVE 수집
python scripts/collect_paper_dataset.py --min-cves 200 --min-cvss 7.0

# 데이터 검증 포함
python scripts/collect_paper_dataset.py --validate
```

**출력:**
- `results/paper/dataset/cves.jsonl` - 전체 CVE 데이터셋
- `results/paper/dataset/cves_valid.jsonl` - 검증된 CVE만
- `results/paper/dataset/statistics.json` - 통계
- `results/paper/dataset/validation.json` - 검증 결과

### 2. Historical Validation (가장 중요!)

과거 CVE를 예측할 수 있었는지 검증합니다.

```bash
# 전체 검증
python scripts/run_historical_validation.py results/paper/dataset/cves_valid.jsonl

# 테스트 (10개만)
python scripts/run_historical_validation.py results/paper/dataset/cves_valid.jsonl --max-cves 10

# 예측 윈도우 조정 (60일 전 예측)
python scripts/run_historical_validation.py results/paper/dataset/cves_valid.jsonl --prediction-window 60
```

**출력:**
- `results/paper/validation/validation_results.jsonl` - 각 CVE의 예측 결과
- `results/paper/validation/metrics.json` - 성능 메트릭

**메트릭:**
- Precision, Recall, F1-Score
- Accuracy, Coverage
- Average Lead Time (평균 예측 선행 시간)
- Confusion Matrix (TP, FP, TN, FN)

## 📈 예상 결과

논문에 포함될 수 있는 결과 예시:

```
Historical Validation Performance Metrics
==========================================================
Precision:    0.723
Recall:       0.681
F1-Score:     0.701
Accuracy:     0.845
Coverage:     0.720

Lead Time:
  Average:    45.3 days
  Median:     42.0 days

Confusion Matrix:
  TP:  68  FP:  26
  FN:  32  TN: 174
==========================================================
```

## 🚀 빠른 시작 (테스트)

```bash
# 1. 소규모 데이터셋 수집 (10 CVEs)
python scripts/collect_paper_dataset.py --min-cves 10 --validate

# 2. Historical Validation 실행
python scripts/run_historical_validation.py results/paper/dataset/cves_valid.jsonl --max-cves 10

# 3. 결과 확인
cat results/paper/validation/metrics.json
```

## 📝 논문에 포함할 내용

### 1. Dataset Statistics

```json
{
  "total_cves": 127,
  "cvss_distribution": {
    "min": 7.0,
    "max": 10.0,
    "mean": 8.3,
    "median": 8.5
  },
  "severity_distribution": {
    "CRITICAL": 45,
    "HIGH": 82
  },
  "vulnerability_type_distribution": {
    "RCE": 38,
    "SQL_INJECTION": 12,
    "XSS": 15,
    ...
  }
}
```

### 2. Performance Metrics

```json
{
  "precision": 0.723,
  "recall": 0.681,
  "f1_score": 0.701,
  "avg_lead_time": 45.3,
  "coverage": 0.720
}
```

### 3. Case Studies

- Log4Shell (CVE-2021-44228)
- Spring4Shell (CVE-2022-22965)
- Text4Shell (CVE-2022-42889)

## 🔧 문제 해결

### GitHub API Rate Limit

```bash
# GitHub token 설정
export GITHUB_TOKEN="your_token_here"
```

### NVD API Rate Limit

```bash
# NVD API key 설정 (더 빠른 수집)
export NVD_API_KEY="your_key_here"
```

### 메모리 부족

```bash
# 배치 크기 줄이기
python scripts/run_historical_validation.py dataset.jsonl --max-cves 50
```

## 📚 다음 단계

1. **Baseline 비교** - CVSS, EPSS와 비교
2. **Ablation Study** - 각 컴포넌트 기여도 분석
3. **Case Studies** - 유명 CVE 상세 분석
4. **Results Generation** - LaTeX tables, plots 생성

## 🎓 논문 작성 팁

### Abstract에 포함할 수치:
- "We evaluated our system on 127 real-world CVEs"
- "Achieved F1-score of 0.70 with 45 days average lead time"
- "Outperformed CVSS-based baseline by 23%"

### Evaluation Section:
1. Dataset description (Table 1)
2. Performance metrics (Table 2)
3. Baseline comparison (Table 3)
4. Case studies (Section 5.4)

### Figures:
- Figure 1: System architecture
- Figure 2: ROC curve
- Figure 3: Lead time distribution
- Figure 4: Feature importance

## ⚠️ 중요 사항

1. **Temporal Correctness**: 모든 실험에서 시간적 데이터 누수 방지
2. **Reproducibility**: 모든 파라미터와 결과 저장
3. **Statistical Significance**: 충분한 샘플 크기 (100+ CVEs)
4. **Diversity**: 다양한 프로젝트와 취약점 유형

## 📞 문의

문제가 발생하면 로그를 확인하세요:
- 데이터 수집 로그
- Validation 로그
- 에러 메시지

Happy researching! 🎉
