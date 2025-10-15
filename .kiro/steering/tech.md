# Technology Stack

## Build System
- **Package Manager**: pip with requirements.txt
- **Build Backend**: setuptools with pyproject.toml configuration
- **Python Version**: 3.10+ required

## Core Dependencies
- `pyyaml>=6.0` - YAML configuration file parsing
- `requests>=2.31.0` - HTTP API calls to package registries
- `tqdm>=4.66.0` - Progress bars for data collection

## Project Structure
- Modern Python package structure with `src/` layout
- Configuration-driven architecture using YAML files
- Modular data source collectors in `data_sources/` directory

## Common Commands

### Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Data Collection
```bash
python scripts/collect_data.py config/example_config.yaml
```

### Development
```bash
# Install in development mode
pip install -e .
```

## Environment Variables
- `GITHUB_TOKEN` - GitHub API authentication token for higher rate limits

## Data Storage
- Output format: JSON Lines (.jsonl)
- Default output directory: `data/raw/`
- Each record contains: `source`, `package`, `collected_at`, `payload` fields

## API Integrations
- PyPI API: `https://pypi.org/pypi/{package}/json`
- Maven Central: `https://search.maven.org/solrsearch/select`
- npm Registry: `https://registry.npmjs.org/{package}`
- GitHub API: `https://api.github.com`