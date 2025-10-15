# Project Structure

## Directory Organization

```
zero-day-defense/
├── .git/                           # Git repository metadata
├── .kiro/                          # Kiro IDE configuration and steering
├── config/                         # Configuration files
│   └── example_config.yaml         # Sample pipeline configuration
├── docs/                           # Research documentation
│   └── data_collection_overview.md # Pipeline design and scope
├── scripts/                        # Command-line entry points
│   └── collect_data.py             # Main data collection script
├── src/zero_day_defense/           # Main Python package
│   ├── __init__.py                 # Package initialization
│   ├── config.py                   # YAML config loader and data classes
│   ├── pipeline.py                 # Pipeline orchestration
│   └── data_sources/               # Ecosystem-specific collectors
├── pyproject.toml                  # Python package configuration
├── requirements.txt                # Python dependencies
└── README.md                       # Project overview (Korean)
```

## Code Organization Principles

### Source Layout
- Uses modern `src/` layout to avoid import issues
- Main package: `zero_day_defense`
- Modular collectors in `data_sources/` subdirectory

### Configuration Management
- YAML-based configuration in `config/` directory
- Configuration data classes defined in `config.py`
- Environment variables for sensitive data (API tokens)

### Entry Points
- Command-line scripts in `scripts/` directory
- Main entry point: `scripts/collect_data.py`

### Documentation
- Korean language documentation in `docs/`
- README.md provides installation and usage instructions
- Inline code comments in English following Python conventions

### Data Output
- Raw collected data stored in `data/raw/` (created at runtime)
- JSON Lines format for structured data storage
- One file per package: `<package_name>.jsonl`

## Naming Conventions
- Python modules: snake_case
- Configuration files: snake_case with .yaml extension
- Data files: snake_case with appropriate extensions (.jsonl)
- Korean documentation with English code examples