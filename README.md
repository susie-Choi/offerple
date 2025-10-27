# ROTA - Real-time Operational Threat Assessment

[![PyPI version](https://badge.fury.io/py/rota.svg)](https://pypi.org/project/rota/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Downloads](https://static.pepy.tech/badge/rota)](https://pepy.tech/project/rota)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/susie-Choi/rota?style=social)](https://github.com/susie-Choi/rota)

**ROTA** is an AI-powered real-time zero-day vulnerability prediction system. It detects security risks at code push time and integrates seamlessly with CI/CD pipelines.

## ✨ Key Features

- 🚀 **Real-time Prediction**: Instant risk analysis on code push (< 10 seconds)
- 🧠 **AI-Powered**: Learns GitHub activity patterns to detect vulnerability signals
- 📊 **Historical Validation**: Prediction model validated on real CVE data
- 🔗 **CI/CD Integration**: Easy integration with GitHub Actions, Jenkins, etc.
- 📈 **Multi-source Analysis**: Integrates CVE, GitHub, EPSS, and Exploit-DB data

## 🚀 Quick Start

### Installation

```bash
pip install rota
```

### Basic Usage

```bash
# Analyze repository risk
rota predict --repo django/django --commit abc123

# Collect CVE data
rota collect --source cve --output cve_data.jsonl

# Run historical validation
rota validate --dataset cves.jsonl --output results/
```

### Python API

```python
from rota import analyze_code_push

# Analyze specific commit risk
result = analyze_code_push("django/django", "abc123")
print(f"Risk Score: {result['risk_score']}")
```

## 🏗️ Architecture

ROTA uses a wheel-themed architecture:

- **Spokes**: Multi-source data collectors (CVE, GitHub, EPSS, Exploit-DB)
- **Hub**: Neo4j-based knowledge graph integration
- **Wheel**: Pattern analysis and clustering
- **Oracle**: AI-powered prediction engine
- **Axle**: Historical validation framework

## 📦 Core Components

### Security Vulnerability Knowledge Graph

Integrates multiple data sources into a unified graph structure:

- **CVE Data** (NVD): Vulnerability details, CVSS scores, affected products
- **GitHub Advisory**: Package-specific security advisories and patches
- **EPSS Scores**: Probability of exploitation predictions
- **Exploit Database**: Real exploit code and metadata

### Graph Structure

```
CVE
├─[:AFFECTS]→ CPE ←[:HAS_VERSION]─ Product ←[:PRODUCES]─ Vendor
├─[:HAS_WEAKNESS]→ CWE
├─[:HAS_REFERENCE]→ Reference
├─[:HAS_EXPLOIT]→ Exploit
└─ Properties: epss_score, cvssScore, cvssSeverity

Advisory
├─[:REFERENCES]→ CVE
├─[:HAS_WEAKNESS]→ CWE
└─ ←[:HAS_ADVISORY]─ Package
```

## 🔧 Installation

Requires Python 3.10 or higher.

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install package
pip install -e .
```

## ⚙️ Configuration

Create a `.env` file with required environment variables:

```bash
# Copy example file
cp .env.example .env

# Edit .env file
# NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
# NEO4J_USERNAME=neo4j
# NEO4J_PASSWORD=your-password
# GITHUB_TOKEN=your-github-token (optional)
# GOOGLE_API_KEY=your-gemini-key (optional)
```

## 📊 Data Collection

### 1. Collect CVE Data

```bash
python scripts/collect_cve_data.py config/cve_test_config.yaml
python scripts/load_cve_to_neo4j.py data/raw/cve_data.jsonl
```

### 2. Collect GitHub Advisories

```bash
python scripts/collect_github_advisory.py config/github_advisory_config.yaml
python scripts/load_advisory_to_neo4j.py data/raw/github_advisory.jsonl
```

### 3. Collect EPSS Scores

```bash
python scripts/collect_epss.py config/epss_config.yaml
python scripts/load_epss_to_neo4j.py data/raw/epss_scores.jsonl
```

### 4. Collect Exploit Database

```bash
python scripts/collect_exploits.py config/exploit_config.yaml
python scripts/load_exploits_to_neo4j.py data/raw/exploits.jsonl
```

## 🔍 Neo4j Query Examples

### Find High-Risk CVEs

```cypher
// CVEs with high EPSS scores and available exploits
MATCH (c:CVE)-[:HAS_EXPLOIT]->(e:Exploit)
WHERE c.epss_score > 0.5
RETURN c.id, c.epss_score, c.cvssScore, count(e) as exploit_count
ORDER BY c.epss_score DESC
```

### Analyze Log4Shell Ecosystem

```cypher
MATCH path = (v:Vendor)-[:PRODUCES]->(p:Product)-[:HAS_VERSION]->(cpe:CPE)
              <-[:AFFECTS]-(c:CVE {id: 'CVE-2021-44228'})-[:HAS_EXPLOIT]->(e:Exploit)
RETURN path LIMIT 50
```

### Product Vulnerability Analysis

```cypher
MATCH (v:Vendor {name: 'apache'})-[:PRODUCES]->(p:Product)
      -[:HAS_VERSION]->(cpe:CPE)<-[:AFFECTS]-(c:CVE)
RETURN p.name, count(DISTINCT c) as vuln_count, 
       avg(c.cvssScore) as avg_cvss, avg(c.epss_score) as avg_epss
ORDER BY vuln_count DESC
```

## 📁 Project Structure

```
rota/
├── src/rota/                       # Python package
│   ├── spokes/                     # Data collectors
│   │   ├── cve.py                  # NVD CVE collector
│   │   ├── advisory.py             # GitHub Advisory collector
│   │   ├── epss.py                 # EPSS score collector
│   │   └── exploits.py             # Exploit-DB collector
│   ├── hub/                        # Data integration
│   │   ├── neo4j.py                # Neo4j graph manager
│   │   └── storage.py              # Data storage
│   ├── wheel/                      # Pattern analysis
│   │   ├── patterns.py             # Pattern detection
│   │   └── cluster.py              # Clustering
│   ├── oracle/                     # Prediction engine
│   │   ├── predictor.py            # Main predictor
│   │   └── risk_score.py           # Risk scoring
│   └── axle/                       # Validation framework
│       ├── validator.py            # Historical validation
│       └── metrics.py              # Performance metrics
├── scripts/                        # Execution scripts
├── config/                         # Configuration files
└── docs/                           # Documentation
```

## 🌍 Environment Variables

- `NEO4J_URI`: Neo4j database URI
- `NEO4J_USERNAME`: Neo4j username (default: neo4j)
- `NEO4J_PASSWORD`: Neo4j password
- `GITHUB_TOKEN`: GitHub API token (optional, improves rate limits)
- `NVD_API_KEY`: NVD API key (optional, faster collection)
- `GOOGLE_API_KEY`: Google Gemini API key (optional, for Graphiti)

## 📚 Documentation

- [Quick Start Guide](HOW_TO_PUBLISH.md)
- [Paper Evaluation Framework](docs/PAPER_FRAMEWORK_SUMMARY.md)
- [Graphiti Comparison](docs/graphiti_comparison.md)
- [Data Collection Overview](docs/data_collection_overview.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This project is part of ongoing research on LLM-based pre-signal analysis for predicting potential vulnerabilities in software ecosystems.

## 📈 Roadmap

- ✅ Multi-source data integration (CVE, Advisory, EPSS, Exploit)
- ✅ Neo4j knowledge graph construction
- ✅ Historical validation framework
- ✅ PyPI package release
- 🔄 Real-time prediction optimization
- 📋 LLM-based risk inference module
- 🎨 Visualization dashboard

---

**Install now**: `pip install rota`

**Star us on GitHub**: ⭐ https://github.com/susie-Choi/rota
