# ROTA Data Status

**Last Updated**: 2025-10-28

## Current Neo4j Database

### Node Counts

| Type | Count | Description |
|------|-------|-------------|
| CVE | 11,441 | Vulnerabilities from NVD |
| Commit | 35,080 | GitHub commits (±180 days filtered) |
| KEV | 1,666 | CISA Known Exploited Vulnerabilities |
| CWE | 969 | Common Weakness Enumeration |
| CPE | 804 | Common Platform Enumeration |
| Product | 276 | Affected products |
| Reference | 362 | External references |
| Consequence | 71 | Impact consequences |
| Vendor | 36 | Software vendors |
| Package | 33 | Software packages |
| Exploit | 30 | Public exploits from Exploit-DB |
| Advisory | 3 | GitHub security advisories |
| GitHubSignal | 1 | Behavioral signals |

**Total Nodes**: ~51,000

### Relationship Counts

| Type | Count | Description |
|------|-------|-------------|
| HAS_COMMIT | 35,080 | CVE → Commit |
| RELATED_TO | 1,434 | CVE relationships |
| HAS_CONSEQUENCE | 1,189 | CVE → Consequence |
| AFFECTS | 891 | CVE → Product/Package |
| HAS_VERSION | 804 | Product → CPE |
| HAS_REFERENCE | 379 | CVE → Reference |
| PRODUCES | 276 | Vendor → Product |
| HAS_EXPLOIT | 141 | CVE → Exploit |
| DEPENDS_ON | 20 | Package dependencies |
| HAS_WEAKNESS | 16 | CVE → CWE |
| HAS_ADVISORY | 10 | Package → Advisory |
| HAS_KEV | 9 | CVE → KEV |
| REFERENCES | 3 | Advisory → CVE |
| HAS_SIGNAL | 1 | Package → GitHubSignal |

**Total Relationships**: ~40,000

## CVEs with Commit Data

Currently tracking commits for **3 CVEs**:

| CVE ID | Published Date | Commits (±180d) | Total Commits | Filtered Out |
|--------|----------------|-----------------|---------------|--------------|
| CVE-2011-3188 | 2012-05-24 | 32,675 | 35,628 | 2,953 (8.3%) |
| CVE-2012-3503 | 2012-08-25 | 2,011 | 2,011 | 0 (0%) |
| CVE-2012-4406 | 2012-10-22 | 394 | 396 | 2 (0.5%) |

**Total**: 35,080 commits loaded (2,955 filtered out)

## Data Collection Strategy

### Commit Time Filtering

- **Window**: ±180 days around CVE published date
- **Rationale**: Captures 92.4% of relevant commits while reducing noise
- **Purpose**: Focus on vulnerability development period

### Why Only 3 CVEs?

These are the only CVEs for which we have collected commit data in the `commits_by_cve` directory. To expand:

1. Identify target CVEs
2. Find their GitHub repositories
3. Run: `python scripts/collection/collect_github_commits_by_cve.py`
4. Reload: `python scripts/loading/clear_and_reload_commits.py`

## Data Directory Structure

```
data/raw/
├── cve/                          # CVE data from NVD
│   └── bulk_cve_data.jsonl       # 11,441 CVEs
├── epss/                         # EPSS scores
│   └── bulk_epss_data.jsonl      # 10,026 scores
├── kev/                          # KEV catalog
│   └── kev_catalog.jsonl         # 1,666 entries
├── exploits/                     # Exploit-DB
│   └── bulk_exploits_data.jsonl  # 30 exploits
├── advisory/                     # GitHub advisories
│   └── github_advisory.jsonl     # 3 advisories
└── github/
    ├── commits_by_cve/           # ✅ USED: CVE-specific commits
    │   ├── CVE-2011-3188_commits.jsonl
    │   ├── CVE-2012-3503_commits.jsonl
    │   └── CVE-2012-4406_commits.jsonl
    ├── commits/                  # ❌ NOT USED: General commits
    │   └── [1,300 files]         # 342,021 commits (ignored)
    └── commits_smart/            # ❌ NOT USED: Smart-collected
        └── [71 files]            # 4,729 commits (ignored)
```

**Important**: Only `commits_by_cve/` is loaded into Neo4j with time filtering.

## Quick Commands

### Check Status
```bash
python scripts/check_neo4j_data.py
```

### Analyze Commit Distribution
```bash
python scripts/loading/analyze_cve_commit_files.py
```

### Reload Commits
```bash
# Clear and reload with ±180 days window
python scripts/loading/clear_and_reload_commits.py
```

### Load All Data
```bash
# Load everything from scratch
python scripts/loading/load_all_data.py
```

## Neo4j Limits

- **Free Tier**: 200,000 nodes max
- **Current Usage**: ~51,000 nodes (25.5%)
- **Available**: ~149,000 nodes

## Next Steps

To expand commit coverage:

1. **Identify High-Value CVEs**
   - Focus on KEV catalog (1,666 CVEs)
   - Prioritize high EPSS scores
   - Target specific ecosystems (Python, Java, JavaScript)

2. **Collect More Commits**
   ```bash
   python scripts/collection/collect_github_commits_by_cve.py
   ```

3. **Reload with Filtering**
   ```bash
   python scripts/loading/clear_and_reload_commits.py
   ```

4. **Monitor Node Count**
   - Stay under 200,000 node limit
   - Consider ±90 days window if needed (saves 43.9% space)

## Data Quality Notes

- All commits have CVE relationships (`HAS_COMMIT`)
- Time filtering prevents temporal data leakage
- Duplicate commits are automatically skipped
- Missing published dates are handled gracefully
