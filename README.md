# LLMDump - Security Analysis for LLM-Generated Content

[![PyPI version](https://img.shields.io/pypi/v/llmdump.svg)](https://pypi.org/project/llmdump/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**LLMDump** is a research framework for detecting security risks in **LLM-generated content** used in software development. As developers increasingly rely on AI assistants (ChatGPT, Copilot, DALL-E) to generate code and images, LLMDump identifies vulnerabilities, backdoors, and malicious content that may be inadvertently introduced into software supply chains.

## 🎯 What is LLMDump?

LLMDump addresses emerging security risks in the AI-assisted development era:

### The Problem

**Developers use LLMs to generate code and content**:
- ChatGPT/Copilot for code generation
- DALL-E/Midjourney for project images
- LLM-generated content directly integrated into projects

**Security Risks**:
- **Vulnerable code**: LLMs trained on insecure code reproduce vulnerabilities
- **Backdoor injection**: Adversarial prompts can insert malicious code
- **Malicious images**: AI-generated images can hide payloads via steganography
- **Supply chain propagation**: LLM-generated vulnerabilities spread across projects

### LLMDump's Solution

LLMDump detects and analyzes security risks in LLM-generated content:
- **Code vulnerability detection**: Identifies security flaws in AI-generated code
- **Backdoor detection**: Discovers hidden malicious functionality
- **Image analysis**: Detects steganography and malicious payloads
- **Supply chain tracking**: Monitors propagation of LLM-generated vulnerabilities

LLMDump architecture for LLM-generated content security:

```
                    ┌─────────────────────┐
                    │   LLM ANALYZER      │
                    │  (Security Check)   │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   ┌────▼────────┐      ┌──────▼──────┐      ┌──────▼──────┐
   │    CODE     │      │    IMAGE    │      │   SUPPLY    │
   │  ANALYZER   │      │  ANALYZER   │      │    CHAIN    │
   │             │      │             │      │   TRACKER   │
   │ - Vulns     │      │ - Stego     │      │             │
   │ - Backdoors │      │ - Payloads  │      │ - Impact    │
   │ - Patterns  │      │ - Metadata  │      │ - Propagate │
   └────▲────────┘      └──────▲──────┘      └──────▲──────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                        ┌──────▼──────┐
                        │  DATA HUB   │
                        │   (Neo4j)   │
                        └─────────────┘
```

- **LLM Analyzer**: Detects LLM-generated content and security risks
- **Code Analyzer**: Identifies vulnerabilities and backdoors in AI-generated code
- **Image Analyzer**: Detects steganography and malicious payloads in AI images
- **Supply Chain Tracker**: Monitors propagation of LLM-generated vulnerabilities
- **Data Hub**: Neo4j graph database for relationship analysis

## 🚀 Quick Start

### Installation

```bash
pip install llmdump
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
# 1. Start Neo4j
docker-compose up -d

# 2. Check system status
python src/scripts/check_status.py

# 3. Collect all data
python src/scripts/collect_data.py --all

# 4. Load data to Neo4j
python src/scripts/load_to_neo4j.py --all

# 5. Verify data loaded
python src/scripts/check_status.py --neo4j-only
```

**Quick Commands**:
```bash
# Collect specific data source
python src/scripts/collect_data.py --cve
python src/scripts/collect_data.py --commits --repository django/django

# Load specific data source
python src/scripts/load_to_neo4j.py --cve
python src/scripts/load_to_neo4j.py --commits
```

**Important Notes**:
- Commits are automatically filtered to ±180 days around CVE published date
- Only CVE-related commits are loaded (from `data/raw/github/commits_by_cve/`)
- Duplicate commits are automatically skipped

## 📊 Data Sources & Current Status

### Data Sources

#### Current Data Sources (Baseline)

Historical vulnerability data for comparison and validation:

| Source | Description | Coverage | Status |
|--------|-------------|----------|--------|
| **CVE/NVD** | National Vulnerability Database | All published CVEs | ✅ Working |
| **EPSS** | Exploit Prediction Scoring System | Daily probability scores | ✅ Working |
| **KEV** | CISA Known Exploited Vulnerabilities | Government-verified exploits | ✅ Working |
| **GitHub Commits** | Repository commit history | CVE-related commits | ✅ Working |
| **Exploit-DB** | Public exploit database | Proof-of-concept exploits | ✅ Working |

#### Primary Data Sources (LLM-Generated Content)

| Source | Description | Target Count | Purpose |
|--------|-------------|--------------|---------|
| **LLM-Generated Code** | Code from ChatGPT, Copilot, Claude | 10,000+ samples | Vulnerability analysis |
| **Adversarial Prompts** | Malicious prompt engineering | 1,000+ prompts | Backdoor injection study |
| **AI-Generated Images** | Images from DALL-E, Midjourney | 5,000+ images | Steganography detection |
| **Package Analysis** | Real packages with LLM content | 1,000+ packages | Supply chain impact |
| **Developer Surveys** | LLM usage patterns | 500+ responses | Usage analysis |

**Research Focus**: Detecting security risks in LLM-generated content used in software development. Analyzing vulnerabilities, backdoors, and malicious payloads in AI-generated code and images. See [docs/RESEARCH.md](docs/RESEARCH.md) for details.

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
├── input/                        # Input data (consolidated)
│   ├── cve.jsonl                 # CVE data from NVD
│   ├── commits.jsonl             # GitHub commits
│   ├── epss.jsonl                # EPSS scores
│   ├── kev.jsonl                 # KEV catalog
│   ├── exploits.jsonl            # Exploit-DB data
│   └── advisory.jsonl            # GitHub advisories
│
├── output/                       # Analysis results
│   ├── analysis/                 # Analysis outputs
│   ├── predictions/              # Prediction results
│   └── paper/                    # Paper-related data
│
├── multimodal/                   # Multimodal extension (planned)
│   ├── apt/                      # APT malware samples
│   │   ├── rokrat/               # RoKRAT samples
│   │   ├── images/               # Extracted images
│   │   └── similar/              # Similar APT families
│   └── legitimate/               # Legitimate packages
│       └── {package_name}/       # Package images & docs
│
└── archive/                      # Archived old structure
```

**Current Status**: 
- ✅ Core vulnerability data collected (`data/input/`)
- 🔄 Multimodal APT detection in progress (see [Research Plan](docs/RESEARCH.md))

### Future Data Collection (Multimodal Extension)

**Planned APT Malware Samples**:
- **RoKRAT samples**: 30-50 samples from Malware Bazaar
- **Similar APT families**: BabyShark, AppleSeed, Konni (20-30 samples)
- **Purpose**: Steganography detection, C&C identification

**Planned Legitimate Package Data**:
- **Package metadata**: 1,000 top PyPI packages
- **Package images**: 5,000-10,000 images from GitHub repos
- **Purpose**: Baseline for false positive reduction

**Timeline**: See [docs/RESEARCH.md](docs/RESEARCH.md) for detailed research plan

## 🏗️ Architecture

### Spokes (Data Collection)

**Using Unified Script** (Recommended):
```bash
# Collect all data sources
python src/scripts/collect_data.py --all

# Collect specific sources
python src/scripts/collect_data.py --cve --start-date 2025-01-01 --end-date 2025-01-31
python src/scripts/collect_data.py --epss
python src/scripts/collect_data.py --kev
python src/scripts/collect_data.py --commits --repository django/django --days-back 30
```

**Using Python API**:
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

# Collect GitHub behavioral signals
github_collector = GitHubSignalsCollector(token=os.getenv("GITHUB_TOKEN"))
stats = github_collector.collect("django/django", days_back=30)
print(f"Collected {stats['total_commits']} commits, {stats['total_issues']} issues")
```

### Hub (Data Integration)

**Using Unified Script** (Recommended):
```bash
# Load all data sources
python src/scripts/load_to_neo4j.py --all

# Load specific sources
python src/scripts/load_to_neo4j.py --cve
python src/scripts/load_to_neo4j.py --commits
```

**Using Python API**:
```python
from rota.hub import Neo4jConnection, DataLoader
from pathlib import Path

# Connect to Neo4j
with Neo4jConnection() as conn:
    loader = DataLoader(conn)
    
    # Load CVE data
    stats = loader.load_cve_data(Path("data/input/cve.jsonl"))
    
    # Load EPSS data
    stats = loader.load_epss_data(Path("data/input/epss.jsonl"))
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

- **[User Guide](docs/GUIDE.md)** - Complete guide for using ROTA
- **[Development Guide](docs/DEVELOPMENT.md)** - Performance, releases, and temporal validation
- **[Research Plan](docs/RESEARCH.md)** - RoKRAT APT detection research

## 🗄️ Data Management

ROTA provides unified scripts for easy data management.

### Quick Workflow

```bash
# 1. Check system status
python src/scripts/check_status.py

# 2. Collect all data sources
python src/scripts/collect_data.py --all

# 3. Load to Neo4j
python src/scripts/load_to_neo4j.py --all

# 4. Verify
python src/scripts/check_status.py --neo4j-only
```

### Collect Data

```bash
# Collect all sources
python src/scripts/collect_data.py --all

# Collect specific sources
python src/scripts/collect_data.py --cve
python src/scripts/collect_data.py --epss
python src/scripts/collect_data.py --kev
python src/scripts/collect_data.py --commits --repository django/django
python src/scripts/collect_data.py --exploits
python src/scripts/collect_data.py --advisory

# With options
python src/scripts/collect_data.py --cve --start-date 2024-01-01 --end-date 2024-12-31
python src/scripts/collect_data.py --commits --repository flask/flask --days-back 30
```

### Load Data to Neo4j

```bash
# Load all data
python src/scripts/load_to_neo4j.py --all

# Load specific data
python src/scripts/load_to_neo4j.py --cve
python src/scripts/load_to_neo4j.py --epss
python src/scripts/load_to_neo4j.py --commits

# With custom connection
python src/scripts/load_to_neo4j.py --all --uri bolt://localhost:7687 --password mypassword
```

### Check Status

```bash
# Full system check
python src/scripts/check_status.py

# Check specific components
python src/scripts/check_status.py --data-only
python src/scripts/check_status.py --env-only
python src/scripts/check_status.py --neo4j-only
```

**Features**:
- Automatic data validation
- Duplicate detection
- Progress tracking
- Error handling
- Detailed statistics

## 🧪 Testing

Verify your ROTA setup:

```bash
# 1. Check system status
python src/scripts/check_status.py

# 2. Test data collection (small dataset)
python src/scripts/collect_data.py --cve --start-date 2024-01-01 --end-date 2024-01-07

# 3. Test Neo4j loading
python src/scripts/load_to_neo4j.py --cve

# 4. Verify Neo4j data
python src/scripts/check_status.py --neo4j-only
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

ROTA focuses on emerging security risks in AI-assisted software development:

### Research Questions

**RQ1 (LLM Code Security)**: How frequently do LLMs generate code with security vulnerabilities?

**RQ2 (Adversarial Prompts)**: Can adversarial prompts be used to inject backdoors into LLM-generated code?

**RQ3 (Image Steganography)**: Can AI-generated images be used to hide malicious payloads via steganography?

**RQ4 (Supply Chain Impact)**: How do LLM-generated vulnerabilities propagate through software supply chains?

**RQ5 (Detection Methods)**: Can we automatically detect and verify security of LLM-generated content?

### Key Hypotheses

**LLM Code Generation**:
- **H1-1**: LLMs reproduce vulnerabilities from training data at measurable rates
- **H1-2**: Adversarial prompts can reliably inject backdoors into generated code
- **H1-3**: LLM-generated code has distinct patterns that enable detection
- **H1-4**: Security-focused prompts reduce but don't eliminate vulnerabilities

**LLM Image Generation**:
- **H2-1**: AI-generated images can hide payloads with lower detectability than manual steganography
- **H2-2**: Image generation models leave fingerprints that enable source attribution
- **H2-3**: Metadata analysis can reveal malicious generation prompts

**Supply Chain Propagation**:
- **H3-1**: LLM-generated code appears in production packages at increasing rates
- **H3-2**: Vulnerabilities in LLM-generated code propagate faster than traditional vulnerabilities
- **H3-3**: Developers trust LLM-generated code more than human-written code

### Research Contributions

1. **First systematic study** of security risks in LLM-generated content for software development
2. **Large-scale measurement** of vulnerabilities in AI-generated code (10,000+ samples)
3. **Adversarial prompt engineering** techniques for backdoor injection
4. **Automated detection system** for LLM-generated malicious content
5. **Supply chain impact analysis** of AI-generated vulnerabilities

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
