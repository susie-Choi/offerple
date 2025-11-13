# Complete CVE Collection Strategy

## Architecture: Dual Storage

```
📁 JSONL Files (Complete Dataset)
└── All 240,000+ CVEs stored locally
    └── Full historical coverage (1999-2024)
    └── No size limits
    └── Permanent archive

🗄️ Neo4j (Selected Dataset)
└── ~100,000 most important CVEs
    └── KEV + High EPSS + Recent + Critical
    └── Within 200K node limit
    └── Optimized for graph queries
```

## Step 1: Collect All CVEs (JSONL)

```bash
# Get NVD API key (optional but recommended)
# https://nvd.nist.gov/developers/request-an-api-key
export NVD_API_KEY=your_key_here

# Start collection (resumable)
python scripts/collection/collect_all_cves.py
```

**Estimated Time:**
- With API key: ~48 hours (50 req/30s)
- Without API key: ~20 days (5 req/30s)

**Output:**
- File: `data/raw/cve/all_cves_complete.jsonl`
- Size: ~5-10 GB
- Count: ~240,000 CVEs

**Features:**
- ✅ Resumable (checkpoint system)
- ✅ Progress bar
- ✅ Error handling
- ✅ Rate limit compliant

## Step 2: Load Selected CVEs (Neo4j)

### Option A: Balanced (Recommended)

```bash
python scripts/loading/load_selected_cves.py \
  --recent-years 5 \
  --epss-threshold 0.1 \
  --max-cves 100000
```

**Selects:**
- All KEV CVEs (~1,666)
- Recent 5 years CRITICAL/HIGH (~30,000)
- EPSS > 0.1 (~50,000)
- Total: ~80,000 CVEs

### Option B: KEV Only

```bash
python scripts/loading/load_selected_cves.py --kev-only
```

**Selects:**
- Only KEV CVEs (~1,666)
- Minimal Neo4j usage
- Focus on exploited vulnerabilities

### Option C: Recent Only

```bash
python scripts/loading/load_selected_cves.py \
  --recent-years 3 \
  --max-cves 50000
```

**Selects:**
- Last 3 years (~50,000)
- Latest trends
- Modern attack patterns

## Step 3: Analyze

### Full Dataset Analysis (JSONL)

```python
import json
import pandas as pd

# Load all CVEs
cves = []
with open('data/raw/cve/all_cves_complete.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        cve = data['payload']['vulnerabilities'][0]['cve']
        cves.append(cve)

df = pd.DataFrame(cves)

# Analyze trends
df['year'] = pd.to_datetime(df['published']).dt.year
yearly_counts = df.groupby('year').size()
```

### Graph Analysis (Neo4j)

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    # Find attack patterns
    result = session.run("""
        MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
        WHERE cve.kev_listed = true
        RETURN cwe.id, cwe.name, COUNT(*) as count
        ORDER BY count DESC
        LIMIT 10
    """)
```

## Node Budget Planning

**Current Usage:**
- CVE: 11,441
- Commit: 35,080
- Other: 4,479
- **Total: 51,000 / 200,000 (25.5%)**

**After Complete Collection:**
- CVE: 100,000 (selected)
- CWE: 1,000
- KEV: 1,666
- Exploit: 5,000
- Commit: 10,000 (selected)
- Other: 10,000
- **Total: ~128,000 / 200,000 (64%)**

**Remaining: 72,000 nodes for future expansion**

## Data Quality

### JSONL (Complete)
- ✅ All 240,000+ CVEs
- ✅ Full temporal coverage
- ✅ Complete metadata
- ✅ Permanent archive
- ❌ No graph queries
- ❌ Slower analysis

### Neo4j (Selected)
- ✅ Fast graph queries
- ✅ Relationship analysis
- ✅ Real-time exploration
- ✅ Most important CVEs
- ❌ Incomplete dataset
- ❌ Node limit constraints

## Best Practices

1. **Always collect to JSONL first**
   - Permanent record
   - Can reload Neo4j anytime
   - No data loss

2. **Select strategically for Neo4j**
   - Focus on research questions
   - Prioritize KEV + High EPSS
   - Keep within node limits

3. **Use both storage types**
   - JSONL for statistics
   - Neo4j for patterns
   - Combine insights

4. **Document selection criteria**
   - Record what's in Neo4j
   - Note any biases
   - Explain in paper

## Troubleshooting

### Collection Interrupted

```bash
# Just run again - it will resume from checkpoint
python scripts/collection/collect_all_cves.py
```

### Neo4j Node Limit Reached

```bash
# Check current usage
python scripts/check_neo4j_data.py

# Clear and reload with stricter criteria
python scripts/loading/cleanup_neo4j.py
python scripts/loading/load_selected_cves.py --max-cves 80000
```

### API Rate Limit Errors

```bash
# Get API key for 10x speed
# https://nvd.nist.gov/developers/request-an-api-key
export NVD_API_KEY=your_key
```

## Timeline

**Week 1:**
- Day 1-2: Start CVE collection (background)
- Day 3-7: Continue collection, analyze existing data

**Week 2:**
- Day 1: Collection complete
- Day 2: Load selected CVEs to Neo4j
- Day 3: Enrich with CWE names
- Day 4-7: Analysis and paper writing

## Paper Implications

**What to write:**
> "We collected the complete NVD CVE dataset (N=240,000, 1999-2024) and performed comprehensive temporal analysis. For graph-based pattern analysis, we selected 100,000 high-impact CVEs (KEV, EPSS>0.1, recent CRITICAL/HIGH) to enable efficient relationship queries while maintaining statistical significance."

**Strengths:**
- Complete dataset (no sampling bias)
- Dual storage (flexibility)
- Scalable approach
- Reproducible

**Limitations:**
- Neo4j subset (explain criteria)
- API rate limits (time constraint)
- Storage considerations
