# ROTA - Real-time Opensource Threat Assessment

[![PyPI version](https://img.shields.io/pypi/v/rota.svg)](https://pypi.org/project/rota/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ROTA** is a research framework for detecting vulnerabilities in open-source supply chains **before CVE publication**. It combines GitHub commit analysis, Neo4j graph database, and LLM-based RAG (Retrieval-Augmented Generation) to identify vulnerability-related commits early and assess supply chain impact.

## 🎯 What is ROTA?

ROTA addresses critical gaps in existing vulnerability detection tools:

- **CVE-based tools** (GitHub Dependabot, Snyk) only detect vulnerabilities **after** CVE publication
- **EPSS** predicts exploit probability but still requires CVE publication first
- **Static analysis tools** miss supply chain propagation and temporal context

ROTA detects vulnerability-related commits **before CVE publication** by analyzing:
- Commit messages and code changes
- GitHub behavioral signals (Issues, PRs, developer activity)
- Supply chain dependencies and impact
- Historical vulnerability patterns via RAG

ROTA uses a wheel metaphor to represent its architecture:

```
                    ┌─────────────┐
                    │   ORACLE    │
                    │ (Prediction)│
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐        ┌────▼────┐       ┌────▼────┐
   │  WHEEL  │        │   HUB   │       │  AXLE   │
   │(Cluster)│◄───────┤ (Neo4j) │──────►│  (Eval) │
   └────▲────┘        └────▲────┘       └─────────┘
        │                  │
        └──────────────────┼──────────────────┘
                           │
                      ┌────▼────┐
                      │ SPOKES  │
                      │ (Data)  │
                      └─────────┘
```

- **Spokes**: Collect data from multiple sources (CVE, EPSS, KEV, etc.)
- **Hub**: Central Neo4j graph database for data integration
- **Wheel**: Clustering and pattern discovery
- **Oracle**: Prediction and risk assessment
- **Axle**: Evaluation and temporal validation

## 🚀 Quick Start

### Installation

```bash
pip install rota
```

### Environment Setup

Create a `.env` file with required credentials:

```bash
# GitHub API (for behavioral signals)
GITHUB_TOKEN=your_github_token

# Gemini API (for LLM-based prediction)
GEMINI_API_KEY=your_gemini_api_key

# Neo4j Database (for knowledge graph)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Basic Usage

```bash
# 1. Collect CVE data
python scripts/collection/collect_bulk_cve.py

# 2. Collect EPSS scores
python scripts/collection/collect_epss_bulk.py

# 3. Collect KEV catalog
python scripts/collection/collect_kev.py

# 4. Collect GitHub commits for specific CVEs
python scripts/collection/collect_github_commits_by_cve.py

# 5. Collect exploits
python scripts/collection/collect_exploits_bulk.py

# 6. Load all data into Neo4j (with automatic time filtering)
python scripts/loading/load_all_data.py

# 7. Check data status
python scripts/check_neo4j_data.py

# 8. Predict vulnerability risk (coming soon)
# rota oracle predict django/django --days 7
```

**Important Notes**:
- Commits are automatically filtered to ±180 days around CVE published date
- Only CVE-related commits are loaded (from `data/raw/github/commits_by_cve/`)
- Duplicate commits are automatically skipped

## 📊 Data Sources & Current Status

### Data Sources

ROTA integrates multiple vulnerability data sources:

| Source | Description | Coverage | Status |
|--------|-------------|----------|--------|
| **CVE/NVD** | National Vulnerability Database | All published CVEs | ✅ Working |
| **EPSS** | Exploit Prediction Scoring System | Daily probability scores | ✅ Working |
| **KEV** | CISA Known Exploited Vulnerabilities | Government-verified exploits | ✅ Working |
| **GitHub Commits** | Repository commit history | CVE-related commits | ✅ Working |
| **GitHub Advisory** | Package-level security advisories | npm, PyPI, Maven, etc. | ✅ Working |
| **Exploit-DB** | Public exploit database | Proof-of-concept exploits | ✅ Working |

### Current Neo4j Database Status

**Last Updated**: 2025-10-28

| Node Type | Count | Description |
|-----------|-------|-------------|
| CVE | 11,441 | Vulnerability records from NVD |
| Commit | 35,080 | GitHub commits (±180 days around CVE published date) |
| KEV | 1,666 | CISA Known Exploited Vulnerabilities |
| CWE | 969 | Common Weakness Enumeration |
| CPE | 804 | Common Platform Enumeration |
| Product | 276 | Affected products |
| Reference | 362 | External references |
| Consequence | 71 | Impact consequences |
| Vendor | 36 | Software vendors |
| Package | 33 | Software packages |
| Exploit | 30 | Public exploits |
| Advisory | 3 | GitHub security advisories |
| GitHubSignal | 1 | Behavioral signals |

**Key Relationships**:
- `HAS_COMMIT`: 35,080 (CVE → Commit)
- `AFFECTS`: 891 (CVE → Product/Package)
- `HAS_KEV`: 9 (CVE → KEV)
- `HAS_EXPLOIT`: 141 (CVE → Exploit)

### Data Collection Strategy

**Commit Data Philosophy**:
- Only CVE-related commits are stored
- Time window: ±180 days around CVE published date
- Purpose: Identify vulnerability-introducing commits
- Current CVEs with commits: 3 (CVE-2011-3188, CVE-2012-3503, CVE-2012-4406)

**Why ±180 days?**
- Captures 92.4% of relevant commits
- Balances data completeness vs. storage efficiency
- Focuses on vulnerability development period

### Data Directory Structure

```
data/
├── raw/                          # Raw collected data
│   ├── cve/                      # CVE data from NVD
│   ├── epss/                     # EPSS scores
│   ├── kev/                      # KEV catalog
│   ├── exploits/                 # Exploit-DB data
│   ├── advisory/                 # GitHub advisories
│   └── github/
│       ├── commits_by_cve/       # CVE-specific commits (USED)
│       ├── commits/              # General commits (NOT USED)
│       └── commits_smart/        # Smart-collected commits (NOT USED)
└── processed/                    # Processed/analyzed data
```

**Important**: Only `commits_by_cve/` directory is loaded into Neo4j with time filtering

## 🏗️ Architecture

### Spokes (Data Collection)

```python
from rota.spokes import CVECollector, EPSSCollector, KEVCollector
from rota.spokes.github import GitHubSignalsCollector
import os

# Collect CVE data
cve_collector = CVECollector()
stats = cve_collector.collect(
    start_date="2025-01-01",
    end_date="2025-01-31"
)

# Collect EPSS scores
epss_collector = EPSSCollector()
stats = epss_collector.collect(cve_ids=["CVE-2025-1234"])

# Collect KEV catalog
kev_collector = KEVCollector()
stats = kev_collector.collect()

# Collect GitHub behavioral signals
github_collector = GitHubSignalsCollector(token=os.getenv("GITHUB_TOKEN"))
stats = github_collector.collect("django/django", days_back=30)
print(f"Collected {stats['total_commits']} commits, {stats['total_issues']} issues")
```

### Hub (Data Integration)

```python
from rota.hub import Neo4jConnection, DataLoader
from pathlib import Path

# Connect to Neo4j
with Neo4jConnection() as conn:
    loader = DataLoader(conn)
    
    # Load CVE data
    stats = loader.load_cve_data(Path("data/raw/cve/cves.jsonl"))
    
    # Load EPSS data
    stats = loader.load_epss_data(Path("data/raw/epss/epss.jsonl"))
    
    # Load KEV data
    stats = loader.load_kev_data(Path("data/raw/kev/kev.jsonl"))
```

### Wheel (Clustering)

```python
from rota.wheel import VulnerabilityClusterer, FeatureExtractor

# Extract features
extractor = FeatureExtractor()
features = extractor.extract_from_neo4j()

# Cluster vulnerabilities
clusterer = VulnerabilityClusterer(method="dbscan")
clusterer.fit(features)
clusters = clusterer.predict(features)
```

### Oracle (Prediction)

```python
from rota.oracle import VulnerabilityOracle
from rota.spokes.github import GitHubSignalsCollector
import os

# Collect GitHub signals
collector = GitHubSignalsCollector(token=os.getenv("GITHUB_TOKEN"))
result = collector.collect("django/django", days_back=7)

# Load signals
import json
with open(result['output_file'], 'r') as f:
    signals = json.loads(f.readline())

# Predict WITHOUT RAG (no historical context)
oracle_no_rag = VulnerabilityOracle(
    api_key=os.getenv("GEMINI_API_KEY"),
    use_rag=False
)
prediction = oracle_no_rag.predict("django/django", github_signals=signals)

print(f"Risk Score: {prediction.risk_score}")
print(f"Risk Level: {prediction.risk_level}")
print(f"Confidence: {prediction.confidence}")
print(f"Reasoning: {prediction.reasoning}")

# Predict WITH RAG (with historical CVE context)
oracle_with_rag = VulnerabilityOracle(
    api_key=os.getenv("GEMINI_API_KEY"),
    neo4j_uri=os.getenv("NEO4J_URI"),
    neo4j_password=os.getenv("NEO4J_PASSWORD"),
    use_rag=True
)
prediction_rag = oracle_with_rag.predict("django/django", github_signals=signals)

print(f"\nWith RAG:")
print(f"Risk Score: {prediction_rag.risk_score}")
print(f"Risk Level: {prediction_rag.risk_level}")
```

### Axle (Evaluation)

```python
from rota.axle import TemporalValidator
from datetime import datetime

# Validate predictions with temporal awareness
validator = TemporalValidator(cutoff_date=datetime(2025, 1, 1))
metrics = validator.validate(predictions, ground_truth)

print(f"Precision: {metrics['precision']}")
print(f"Recall: {metrics['recall']}")
print(f"Lead Time: {metrics['lead_time_days']} days")
```

## 🔧 Configuration

Create a `config.yaml` file:

```yaml
# Data directories
data_dir: data
raw_dir: data/raw
processed_dir: data/processed

# Neo4j configuration
neo4j_uri: bolt://localhost:7687
neo4j_user: neo4j
neo4j_password: your_password

# Collection settings
request_timeout: 30.0
rate_limit_sleep: 1.0

# Clustering settings
clustering_method: dbscan
min_cluster_size: 5

# Prediction settings
risk_threshold: 0.7
confidence_threshold: 0.6
```

Load configuration:

```python
from rota.config import load_config
from pathlib import Path

config = load_config(Path("config.yaml"))
```

## 📚 Documentation

- **[System Overview](docs/system-overview.md)** - Complete architecture and technical details
- **[Usage Guide](docs/usage-guide.md)** - Step-by-step tutorials and API reference

## 🗄️ Data Management

### Check Current Data Status

```bash
# Check Neo4j database status
python scripts/check_neo4j_data.py
```

### Reload Commit Data

If you need to reload commit data with different time windows:

```bash
# Clear and reload commits with ±180 days window (default)
python scripts/loading/clear_and_reload_commits.py

# Analyze commit distribution before reloading
python scripts/loading/analyze_cve_commit_files.py
```

### Load All Data from Scratch

```bash
# Load all data types into Neo4j
python scripts/loading/load_all_data.py
```

**Note**: The loader automatically:
- Filters commits to ±180 days around CVE published date
- Creates CVE → Commit relationships
- Skips duplicate entries

## 🧪 Testing

Run the test suite to verify your setup:

```bash
# Test full workflow (Spokes → Hub → Oracle)
python tests/test_workflow.py

# Compare Oracle predictions with/without RAG
python tests/test_oracle_comparison.py

# Check Neo4j data
python scripts/check_neo4j_data.py
```

### Test Results Example

```
ROTA Oracle Comparison Test (RAG vs No-RAG)
================================================================================

Results (No RAG):
  - Risk Score: 0.55 (MEDIUM)
  - Confidence: 0.80

Results (With RAG):
  - Risk Score: 0.58 (MEDIUM)
  - Confidence: 0.80

COMPARISON:
  • Risk Score Difference: +0.03 (RAG slightly more conservative)
  • Reasoning Similarity: 24.7% (RAG substantially changed analysis)
  • Confidence: Same (0.80)
```

## 🔬 Research

ROTA is designed for academic security research with focus on:

### Research Questions

**RQ1 (Supply Chain Propagation)**: Can graph-based analysis accurately predict vulnerability impact across dependency chains?

**RQ2 (Early Detection)**: Can GitHub commit analysis detect vulnerability-related commits before CVE publication?

**RQ3 (Historical Pattern Learning)**: Can RAG-based LLM analysis learn from past vulnerability patterns to predict new ones?

**RQ4 (Multi-signal Integration)**: Does integrating commit messages, code diffs, GitHub signals, and developer patterns outperform single-signal analysis?

### Key Hypotheses

**Commit-Level Hypotheses**:
- **H1-1**: Security issues, PRs, and discussions increase 30-90 days before fix commits
- **H1-2**: Vulnerability-introducing commits have significantly more code changes
- **H1-3**: Vulnerabilities concentrate in specific file types (auth, validation, database)
- **H1-4**: Learning CWE patterns enables high-accuracy prediction in new projects

**Contributor-Level Hypotheses**:
- **H2-1**: New contributors introduce vulnerabilities at higher rates
- **H2-2**: Vulnerability introduction increases after core contributor departure
- **H2-3**: Direct main branch commits have higher vulnerability rates than PR-reviewed commits

**Supply Chain-Level Hypotheses**:
- **H3-1**: Vulnerability impact grows exponentially with dependency depth (≥3)
- **H3-2**: Vulnerabilities propagate rapidly through dependency chains
- **H3-3**: Popular packages patch faster despite larger impact scope

### Research Contributions

1. **Pre-CVE Detection**: Detect vulnerability patterns at commit level before CVE publication
2. **Multi-dimensional Analysis**: Integrate code changes, GitHub signals, supply chain impact, and temporal patterns
3. **AI Agent Approach**: Provide clustering and embedding context to LLM for ecosystem-aware risk assessment

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 📧 Contact

- **Author**: Susie Choi
- **GitHub**: [susie-Choi/rota](https://github.com/susie-Choi/rota)
- **Issues**: [GitHub Issues](https://github.com/susie-Choi/rota/issues)

## 🙏 Acknowledgments

- **NVD**: National Vulnerability Database
- **FIRST**: Forum of Incident Response and Security Teams (EPSS)
- **CISA**: Cybersecurity and Infrastructure Security Agency (KEV)
- **Exploit-DB**: Offensive Security

## 📊 Citation

If you use ROTA in your research, please cite:

```bibtex
@software{rota2025,
  title = {ROTA: Real-time Offensive Threat Assessment},
  author = {Choi, Susie},
  year = {2025},
  url = {https://github.com/susie-Choi/rota}
}
```

---

**ROTA v0.2.0** - Real-time Opensource Threat Assessment

*Detecting vulnerabilities before CVE publication through commit analysis and supply chain intelligence*
