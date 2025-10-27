# ROTA v0.1.1 - Initial PyPI Release 🎉

We're excited to announce the first official release of **ROTA** (Real-time Operational Threat Assessment) on PyPI!

## 🚀 Installation

```bash
pip install rota
```

## ✨ What's New

### Core Features
- **Real-time Vulnerability Prediction**: AI-powered analysis of code changes
- **Multi-source Data Collection**: CVE, GitHub, EPSS, Exploit-DB integration
- **Historical Validation Framework**: Validated on 80+ real CVE cases
- **CLI Interface**: Easy-to-use command-line tools
- **Python API**: Programmatic access for automation

### Command-Line Interface
```bash
# Analyze repository risk
rota predict --repo django/django --commit abc123

# Collect security data
rota collect --source cve --output data.jsonl

# Run historical validation
rota validate --dataset cves.jsonl --output results/
```

### Python API
```python
from rota import analyze_code_push

result = analyze_code_push("django/django", "abc123")
print(f"Risk Score: {result['risk_score']}")
```

## 📊 Validation Results

- **Dataset**: 80 CVEs from Django (2007-2024)
- **Pilot Study**: 3 CVEs validated with real GitHub data
- **Average Lead Time**: 90 days before CVE disclosure
- **Execution Time**: ~22 minutes per CVE

## 🏗️ Architecture

- **Spokes**: Multi-source data collectors (CVE, GitHub, EPSS, etc.)
- **Hub**: Neo4j-based knowledge graph integration
- **Wheel**: Pattern analysis and clustering
- **Oracle**: AI-powered prediction engine
- **Axle**: Historical validation framework

## 📦 What's Included

### Data Sources
- CVE (NVD)
- GitHub Advisory
- EPSS Scores
- Exploit-DB
- Package Registries (PyPI, npm, Maven)

### Prediction Components
- GitHub signal collectors
- Feature engineering (20+ behavioral features)
- Risk scoring engine
- Temporal pattern analysis

### Evaluation Framework
- Dataset collection automation
- Historical validation with temporal splitting
- Performance metrics (Precision, Recall, F1, Lead Time)
- Baseline comparisons

## 🔧 Requirements

- Python 3.10+
- GitHub API token (for full functionality)
- Optional: Neo4j for graph analysis

## 📚 Documentation

- [Quick Start Guide](https://github.com/susie-Choi/rota/blob/main/HOW_TO_PUBLISH.md)
- [API Documentation](https://github.com/susie-Choi/rota/blob/main/docs/)
- [Paper Evaluation Framework](https://github.com/susie-Choi/rota/blob/main/docs/PAPER_FRAMEWORK_SUMMARY.md)

## 🐛 Known Issues

- Historical validation can be slow (~22 min/CVE) due to GitHub API rate limits
- Currently focused on GitHub repositories
- Limited to English language repositories

## 🔮 Future Plans

- GraphQL API integration for better performance
- Support for additional version control systems
- Enhanced machine learning models
- Real-time dashboard improvements
- Enterprise features

## 🙏 Acknowledgments

This project is part of ongoing research on LLM-based pre-signal analysis for predicting potential vulnerabilities in software ecosystems.

## 📝 Changelog

See [CHANGELOG.md](https://github.com/susie-Choi/rota/blob/main/CHANGELOG.md) for detailed changes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

MIT License - see [LICENSE](https://github.com/susie-Choi/rota/blob/main/LICENSE) for details.

---

**Install now**: `pip install rota`

**Star us on GitHub**: https://github.com/susie-Choi/rota ⭐
