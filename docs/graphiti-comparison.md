# Graphiti vs Manual Schema Comparison

This document compares two approaches for loading CVE data into Neo4j for ROTA's hub component.

> **Current Status**: ROTA uses manual schema design for production. Graphiti scripts are archived for reference.

## Approach 1: Manual Schema Design (Current)

### Features
- Explicitly define node types and relationships
- Optimized for structured data
- Predictable performance
- Full schema control

### Node Types
- `CVE`: Vulnerabilities
- `CPE`: Product versions
- `CWE`: Weakness types
- `Vendor`: Vendors
- `Product`: Products
- `Reference`: Reference links

### Usage
```bash
# Load CVE data to Neo4j hub
python scripts/loading/load_cve_to_neo4j.py data/raw/cve_data.jsonl

# Or use ROTA CLI
rota hub load-cve data/raw/cve_data.jsonl
```

### Advantages
- Fast loading speed
- Efficient queries
- Clear schema
- Easy to optimize

### Disadvantages
- Manual schema maintenance
- Rigid structure
- Requires schema updates for new data

## Approach 2: Graphiti (Experimental)

### Features
- Automatic schema generation
- LLM-powered entity extraction
- Flexible for unstructured data
- Temporal graph support

### Usage
```bash
# Archived - for reference only
python scripts/archive/load_cve_with_graphiti.py data/raw/cve_data.jsonl
```

> **Note**: Graphiti approach is experimental and archived. Not recommended for production use.

### Advantages
- No manual schema design
- Handles unstructured text
- Automatic entity extraction
- Temporal relationships

### Disadvantages
- Slower (LLM calls)
- Less predictable
- Higher cost (API calls)
- Complex debugging

## Performance Comparison

| Metric | Manual Schema | Graphiti |
|--------|---------------|----------|
| Loading Speed | Fast (~1000 CVEs/min) | Slow (~10 CVEs/min) |
| Query Performance | Excellent | Good |
| Schema Flexibility | Low | High |
| Cost | Free | API costs |
| Maintenance | Manual | Automatic |

## Recommendation

**Use Manual Schema for:**
- Structured CVE data
- Production systems
- Performance-critical applications
- Cost-sensitive projects

**Use Graphiti for:**
- Unstructured text analysis
- Exploratory research
- Rapid prototyping
- Complex entity relationships

## Hybrid Approach

Best of both worlds:
1. Use manual schema for core CVE data
2. Use Graphiti for unstructured descriptions and references
3. Link both graphs with common CVE IDs

```python
# Load structured data with manual schema
load_cve_structured(cve_data)

# Enhance with Graphiti for text analysis
graphiti.add_episode(
    name=f"CVE-{cve_id}",
    episode_body=cve_description,
    source_description="CVE Description"
)
```

## Conclusion

For ROTA project:
- **Current**: Manual schema (production-ready, fast, cost-effective)
- **Archived**: Graphiti approach (experimental, high cost)
- **Future**: Consider hybrid approach if unstructured text analysis becomes critical

## ROTA Hub Architecture

ROTA's hub component uses manual schema design:

```
src/rota/hub/
├── connection.py  # Neo4j connection management
└── loader.py      # Data loading utilities

scripts/loading/
├── load_cve_to_neo4j.py
├── load_epss_to_neo4j.py
├── load_advisory_to_neo4j.py
└── load_exploits_to_neo4j.py
```

See [Data Roadmap](data-roadmap.md) for data collection priorities.
