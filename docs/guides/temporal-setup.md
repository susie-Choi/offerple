# Temporal Data Leakage Prevention Guide

## The Problem

**Current Data:**
- CVE data: 2021-2025 (already disclosed)
- Current system: Collect signals "now" → Predict "future"

**Issues:**
- Training on past CVEs and testing with "current" signals is meaningless
- Predicting with data **after** CVE disclosure is cheating!

## ✅ Correct Usage

### 1. Historical Backtesting (Past Time Simulation)

```bash
# Log4Shell (CVE-2021-44228) prediction simulation
# Actual disclosure: 2021-12-09
# Our prediction: 2021-11-09 (30 days before)

python scripts/experiments/historical_validation.py --cve CVE-2021-44228
```

**Timeline:**
```
2021-10-10 ────────> 2021-11-09 ────────> 2021-12-09
    │                    │                     │
Signal collection    Prediction point    Actual CVE disclosure
    starts                                      │
    │                    │                     │
    └─ 30 days signals ──┘                     │
                         │                     │
                    Our prediction        Ground Truth
```

### 2. Actual Workflow

```python
from datetime import datetime

# 1. CVE information (in practice, load from Neo4j)
cve_disclosure = datetime(2021, 12, 9)  # Log4Shell

# 2. Set prediction point (30 days before CVE disclosure)
prediction_date = datetime(2021, 11, 9)

# 3. Signal collection period (30 days before prediction point)
signal_start = datetime(2021, 10, 10)
signal_end = datetime(2021, 11, 9)  # Before CVE disclosure!

# 4. Collect signals (no temporal leakage!)
commits = collector.collect_commit_history(
    "apache/log4j",
    since=signal_start,
    until=signal_end  # ⚠️ Only data before CVE disclosure!
)

# 5. Predict
threat_score = scorer.score_package(vector)

# 6. Validate
if threat_score.score > 0.7:
    print(f"✅ Prediction successful! Detected {(cve_disclosure - prediction_date).days} days before")
else:
    print(f"❌ Prediction failed")
```

## 📊 Validation Scenarios

### Scenario 1: Could we have predicted Log4Shell?

```bash
python scripts/experiments/historical_validation.py \
    --cve CVE-2021-44228 \
    --prediction-days-before 30 \
    --signal-window-days 30
```

**Question:** Could we have predicted Log4Shell on November 9, 2021?

### Scenario 2: Spring4Shell Prediction

```bash
python scripts/experiments/historical_validation.py \
    --cve CVE-2022-22965 \
    --prediction-days-before 60
```

## 🎯 Correct Evaluation Method

### Leave-One-Out Cross Validation

```python
# 1. All CVE list
all_cves = ["CVE-2021-44228", "CVE-2021-45046", "CVE-2022-22965", ...]

for test_cve in all_cves:
    # 2. Training: Train clusters with all CVEs except test CVE
    training_cves = [c for c in all_cves if c != test_cve]
    clusterer.fit(training_cve_vectors)
    
    # 3. Testing: Predict with signals before test CVE disclosure
    test_signals = collect_signals_before_disclosure(test_cve)
    prediction = scorer.score_package(test_signals)
    
    # 4. Evaluate
    if prediction.score > threshold:
        print(f"✅ {test_cve} prediction successful!")
```

## 💡 Core Principles

1. **Never use future data**
   - Don't predict with data after CVE disclosure
   - Don't use data after prediction point

2. **Strictly follow temporal order**
   ```
   Signal collection → Prediction → CVE disclosure
   (Past)              (Present)    (Future)
   ```

3. **Leave-One-Out for validation**
   - Exclude test CVE from training
   - Train clusters only with other CVEs

## 🔧 Practical Usage

### Real-time Prediction with Current System

```python
# Predict vulnerabilities right now
from datetime import datetime, timezone, timedelta

# 1. Current time
now = datetime.now(timezone.utc)
signal_start = now - timedelta(days=30)

# 2. Collect signals (last 30 days)
commits = collector.collect_commit_history(
    "target/repo",
    since=signal_start,
    until=now
)

# 3. Predict
threat_score = scorer.score_package(vector)

# 4. Interpret
if threat_score.score > 0.7:
    print(f"⚠️ High risk! CVE likely within next 30 days")
    print(f"Similar CVEs: {threat_score.similar_cves}")
```

## 📚 References

- `scripts/experiments/historical_validation.py` - Historical CVE validation script
- `docs/guides/prediction_system_guide.md` - Complete guide
- `QUICKSTART.md` - Quick start guide
