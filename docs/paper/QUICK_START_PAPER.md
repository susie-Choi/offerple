# Quick Start - Paper Experiments

논문 실험을 빠르게 시작하는 가이드

## 🚀 5분 안에 시작하기

### 1. 환경 설정

```bash
# Dependencies 설치
pip install -r requirements.txt

# GitHub Token 설정 (.env 파일에)
GITHUB_TOKEN=your_token_here
```

### 2. 데이터 수집 (10-20분)

```bash
# 소규모 테스트 (10 CVEs)
python scripts/collect_paper_dataset.py --min-cves 10 --output-dir results/paper/dataset

# 대규모 수집 (100 CVEs) - 시간 오래 걸림
python scripts/collect_paper_dataset.py --min-cves 100 --validate
```

### 3. Historical Validation 실행

```bash
# 빠른 테스트 (3 CVEs, ~1시간)
python scripts/run_historical_validation.py results/paper/dataset/cves.jsonl --max-cves 3

# 더 많은 CVE (10개, ~3-4시간)
python scripts/run_historical_validation.py results/paper/dataset/cves.jsonl --max-cves 10

# 밤새 실행 (20개, ~7-8시간)
python scripts/run_historical_validation.py results/paper/dataset/cves.jsonl --max-cves 20
```

### 4. 결과 확인

```bash
# 메트릭 확인
cat results/paper/validation/metrics.json

# 개별 CVE 결과
cat results/paper/validation/validation_results.jsonl
```

## 📊 현재 사용 가능한 데이터

### 이미 수집된 데이터:
```
results/paper/dataset_test3/
├── cves.jsonl              # 80 CVEs (Django)
├── statistics.json         # 통계
└── validation_real/        # 3 CVEs 검증 결과
```

### 바로 사용 가능:
```bash
# 이미 수집된 80개 CVE로 실험
python scripts/run_historical_validation.py results/paper/dataset_test3/cves.jsonl --max-cves 5
```

## 🎯 논문용 실험 체크리스트

### Phase 1: Pilot Study (완료 ✅)
- [x] 3 CVEs 검증
- [x] 시스템 작동 확인
- [x] 메트릭 계산 검증

### Phase 2: Small-Scale (진행 중 ⏳)
- [ ] 10-20 CVEs 검증
- [ ] 통계적 유의성 확보
- [ ] 다양한 프로젝트

### Phase 3: Baseline (필수!)
- [ ] CVSS-only baseline
- [ ] EPSS-only baseline
- [ ] Random baseline
- [ ] 성능 비교 테이블

### Phase 4: Large-Scale
- [ ] 50-100 CVEs
- [ ] Cross-validation
- [ ] Ablation study

### Phase 5: Paper Writing
- [ ] Results section
- [ ] Figures & Tables
- [ ] Discussion
- [ ] Related Work

## ⚡ 빠른 명령어 모음

```bash
# 1. 데이터 수집 (10 CVEs)
python scripts/collect_paper_dataset.py --min-cves 10

# 2. Validation (3 CVEs, 테스트)
python scripts/run_historical_validation.py results/paper/dataset/cves.jsonl --max-cves 3

# 3. 통계 확인
python -c "import json; print(json.dumps(json.load(open('results/paper/validation/metrics.json')), indent=2))"

# 4. 결과 요약
python scripts/generate_paper_summary.py  # TODO: 구현 필요
```

## 🐛 문제 해결

### GitHub API Rate Limit
```bash
# Token 확인
echo $GITHUB_TOKEN

# Rate limit 상태 확인
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
```

### 느린 실행 속도
- **원인**: GitHub API 호출 (commits, PRs, issues)
- **해결**: 
  - 밤새 실행
  - 더 적은 CVE로 테스트
  - 캐싱 활성화 (TODO)

### Datetime 에러
- **해결됨**: 모든 datetime이 timezone-aware로 수정됨
- 만약 에러 발생 시: 코드 업데이트 필요

## 📈 예상 소요 시간

| 작업 | CVE 수 | 예상 시간 |
|------|--------|----------|
| 데이터 수집 | 10 | 10-20분 |
| 데이터 수집 | 100 | 1-2시간 |
| Validation | 3 | 1시간 |
| Validation | 10 | 3-4시간 |
| Validation | 20 | 7-8시간 |
| Validation | 50 | 17-20시간 |

**팁**: Validation은 밤새 실행하는 것을 추천!

## 🎓 논문에 사용할 결과

### 필수 파일:
```
results/paper/
├── dataset/
│   ├── cves.jsonl                    # Dataset
│   └── statistics.json               # Table 1: Dataset Statistics
├── validation/
│   ├── validation_results.jsonl      # Raw results
│   └── metrics.json                  # Table 2: Performance Metrics
└── baselines/                        # Table 3: Baseline Comparison
    ├── cvss_results.json
    ├── epss_results.json
    └── comparison.json
```

### 생성할 Figures:
1. **Figure 1**: System Architecture (수동 작성)
2. **Figure 2**: ROC Curve (TODO: 구현 필요)
3. **Figure 3**: Lead Time Distribution (TODO)
4. **Figure 4**: Feature Importance (TODO)

## 💡 다음 단계

### 오늘 할 수 있는 것:
1. ✅ 더 많은 CVE 검증 시작 (밤새 실행)
2. ✅ Baseline 구현 (1-2시간)
3. ✅ 결과 시각화 스크립트 작성

### 이번 주:
1. ⏳ 10-20 CVEs 검증 완료
2. ⏳ Baseline 비교 완료
3. ⏳ 초안 Results section 작성

### 다음 주:
1. ⏳ 50+ CVEs 검증
2. ⏳ Ablation study
3. ⏳ 논문 초안 완성

---

**현재 상태**: Pilot study 완료 ✅
**다음 액션**: 더 많은 CVE 검증 + Baseline 구현
**목표**: 3-5주 내 논문 투고 준비 완료
