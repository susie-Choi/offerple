# Scripts Directory

This directory contains all executable scripts for the ROTA project.

## 📁 Directory Structure

### `/collection` - Data Collection Scripts
Scripts for collecting data from external sources

- `collect_cve_data.py` - Collect NVD CVE data
- `collect_github_advisory.py` - Collect GitHub Security Advisories
- `collect_epss.py` - Collect EPSS score data
- `collect_exploits.py` - Collect Exploit-DB data
- `collect_paper_dataset.py` - Automated CVE dataset collection for research

### `/loading` - Data Loading Scripts
Scripts for loading collected data into Neo4j graph database

- `load_cve_to_neo4j.py` - Load CVE data → Neo4j
- `load_advisory_to_neo4j.py` - Load GitHub Advisory → Neo4j
- `load_epss_to_neo4j.py` - Load EPSS data → Neo4j
- `load_exploits_to_neo4j.py` - Load Exploit data → Neo4j

### `/experiments` - Experiment Scripts
Scripts for paper evaluation and prediction system experiments

- `run_historical_validation.py` - Run historical validation
- `run_prediction_demo.py` - Run prediction system demo
- `historical_validation.py` - Historical validation implementation

### `/deployment` - Deployment Scripts
Scripts for package deployment and releases

- `publish_to_pypi.py` - Automated PyPI package publishing

### `/archive` - Archive
Legacy scripts no longer in active use

- Initial versions and test scripts

## 🚀 Usage Examples

### Data Collection
```bash
# Collect CVE data
python scripts/collection/collect_cve_data.py

# Collect paper dataset
python scripts/collection/collect_paper_dataset.py
```

### Data Loading
```bash
# Load CVE data to Neo4j
python scripts/loading/load_cve_to_neo4j.py
```

### Run Experiments
```bash
# Run historical validation
python scripts/experiments/run_historical_validation.py results/paper/dataset/cves.jsonl

# Run prediction demo
python scripts/experiments/run_prediction_demo.py
```

### Deployment
```bash
# Publish to PyPI
python scripts/deployment/publish_to_pypi.py
```

## 📝 Notes

- All scripts should be run from the project root directory
- Check `.env` file for required environment variables
- Use `--help` option for detailed usage of each script
