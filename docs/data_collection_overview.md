# Data Collection Pipeline Overview

This document outlines the scope and design principles of the data collection pipeline for ROTA research.

## Objectives

- Secure diverse ecosystem data to support Phase 1 and Phase 2 of the research plan
- Apply `cutoff_date`-based filtering to prevent temporal data leakage
- Integrate package metadata, release history, and repository activity

## Currently Supported Sources

| Source | API | Collected Items |
| ------ | --- | --------------- |
| PyPI | `https://pypi.org/pypi/{package}/json` | Package info, release history |
| Maven Central | `https://search.maven.org/solrsearch/select` | Artifact metadata, release history |
| npm Registry | `https://registry.npmjs.org/{package}` | Package info, version timestamps |
| GitHub | `https://api.github.com` | Repository metadata, commits, issues, PRs |

## Data Storage Format

All collected data is stored in JSON Lines (.jsonl) format with the following structure:

```json
{
  "source": "pypi",
  "package": "django",
  "collected_at": "2024-10-27T12:00:00Z",
  "payload": {
    "info": {...},
    "releases": {...}
  }
}
```

## Temporal Correctness

To prevent data leakage in historical validation:

- All timestamps are stored in UTC
- `cutoff_date` parameter filters data to simulate historical knowledge
- Future data (after cutoff) is excluded from analysis

## Configuration

Data collection is configured via YAML files:

```yaml
sources:
  - type: pypi
    packages:
      - django
      - flask
    cutoff_date: "2024-01-01"
  
  - type: github
    repositories:
      - django/django
      - pallets/flask
    cutoff_date: "2024-01-01"
```

## Output Directory Structure

```
data/
├── raw/
│   ├── pypi/
│   │   ├── django.jsonl
│   │   └── flask.jsonl
│   ├── npm/
│   ├── maven/
│   └── github/
└── processed/
    └── features/
```

## Usage

```bash
# Collect PyPI data
python scripts/collection/collect_data.py config/pypi_config.yaml

# Collect GitHub data
python scripts/collection/collect_github_data.py config/github_config.yaml
```

## Next Steps

1. Add more data sources (CVE, EPSS, Exploit-DB)
2. Implement data validation and quality checks
3. Add incremental collection support
4. Optimize API rate limiting
