# ROTA Structure Refactoring Plan

## 🎯 Goal: ROTA (Wheel) Themed Architecture

```
src/rota/
├── __init__.py
├── wheel/          # 🎡 Clustering & Pattern Analysis
│   ├── __init__.py
│   ├── spinner.py      # Rotation analysis (time-series patterns)
│   ├── cluster.py      # Clustering
│   └── patterns.py     # Pattern detection
│
├── spokes/         # 🔗 Data Collection (Wheel Spokes)
│   ├── __init__.py
│   ├── cve.py          # CVE data
│   ├── epss.py         # EPSS scores
│   ├── advisory.py     # GitHub Advisory
│   ├── exploits.py     # Exploit-DB
│   ├── github.py       # GitHub signals
│   └── packages.py     # PyPI/npm/Maven
│
├── hub/            # 🎯 Central Hub - Data Integration
│   ├── __init__.py
│   ├── neo4j.py        # Neo4j graph
│   ├── graph.py        # Graph operations
│   └── storage.py      # Data storage
│
├── oracle/         # 🔮 Prediction Engine
│   ├── __init__.py
│   ├── predictor.py    # Main predictor
│   ├── scorer.py       # Risk scoring
│   └── agents/         # LLM agents
│       ├── analyzer.py
│       ├── assessor.py
│       └── recommender.py
│
├── axle/           # ⚙️ Evaluation Framework
│   ├── __init__.py
│   ├── validator.py    # Temporal validation
│   ├── metrics.py      # Performance metrics
│   └── baselines.py    # Baseline comparisons
│
└── config/         # ⚙️ Configuration
    ├── __init__.py
    └── settings.py
```

## 📦 Migration Plan

### Phase 1: Rename Package (Week 1)
- [ ] Rename `zero_day_defense` → `rota`
- [ ] Update all imports
- [ ] Update pyproject.toml
- [ ] Update documentation

### Phase 2: Reorganize Modules (Week 2)
- [ ] Move data sources → `spokes/`
- [ ] Move prediction → `oracle/`
- [ ] Move evaluation → `axle/`
- [ ] Create `wheel/` for clustering
- [ ] Create `hub/` for Neo4j

### Phase 3: Update CLI (Week 3)
- [ ] Create `rota` CLI command
- [ ] Subcommands: `spokes`, `hub`, `wheel`, `oracle`, `axle`
- [ ] Update all scripts

### Phase 4: Testing & Documentation (Week 4)
- [ ] Update all tests
- [ ] Update documentation
- [ ] Create migration guide
- [ ] Release v0.2.0

## 🎨 New CLI Interface

```bash
# Data collection (spokes)
rota spokes collect-cve --start-date 2024-01-01
rota spokes collect-github --repo django/django

# Data integration (hub)
rota hub load-cve data/cve.jsonl
rota hub status

# Clustering (wheel)
rota wheel train --data data/features.jsonl
rota wheel predict --package django

# Prediction (oracle)
rota oracle predict --repo django/django
rota oracle assess --cve CVE-2024-1234

# Evaluation (axle)
rota axle validate --dataset data/test.jsonl
rota axle baseline --method cvss
```

## 🔄 Backward Compatibility

- Keep `zero_day_defense` as alias for 1 major version
- Add deprecation warnings
- Provide migration script

## 📝 Documentation Updates

- [ ] Update README.md with new structure
- [ ] Create architecture diagram
- [ ] Update API documentation
- [ ] Create migration guide
- [ ] Update examples

## ⚠️ Breaking Changes

- Package name: `zero_day_defense` → `rota`
- CLI command: `zero-day-defense` → `rota`
- Import paths: `from zero_day_defense` → `from rota`

## 🎯 Benefits

1. **Clearer Architecture**: Wheel metaphor makes structure intuitive
2. **Better Organization**: Logical grouping of related functionality
3. **Easier Navigation**: Clear separation of concerns
4. **Memorable**: Wheel theme is unique and memorable
5. **Scalable**: Easy to add new components

## 📅 Timeline

- **Week 1**: Package rename
- **Week 2**: Module reorganization
- **Week 3**: CLI updates
- **Week 4**: Testing & documentation
- **Week 5**: Release v0.2.0
