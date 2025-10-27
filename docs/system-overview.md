# ROTA System Overview

## Executive Summary

ROTA (Real-time Offensive Threat Assessment) is an integrated vulnerability prediction system that analyzes open-source software supply chains to detect potential zero-day vulnerabilities **before** they are exploited. The system combines commit-level code analysis, project-level behavioral signals, and supply chain impact assessment to provide comprehensive risk scores.

## Core Innovation

Unlike traditional vulnerability scanners that detect **known** CVEs, ROTA predicts **future** vulnerabilities by analyzing:
- Individual commit risk patterns
- Developer behavior anomalies
- Supply chain propagation impact
- Historical CVE patterns (via RAG)

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INTEGRATED ORACLE                         │
│  (Comprehensive Risk Assessment & Decision Engine)           │
└────────────┬────────────────────────────────┬────────────────┘
             │                                │
    ┌────────▼────────┐              ┌───────▼────────┐
    │ COMMIT ANALYZER │              │ PROJECT ORACLE │
    │  (Individual    │              │  (Behavioral   │
    │   Commits)      │              │   Signals)     │
    └────────┬────────┘              └───────┬────────┘
             │                                │
             └────────────┬───────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
    │ SPOKES  │      │   HUB   │     │ SUPPLY  │
    │ (Data)  │─────▶│ (Neo4j) │◀────│ CHAIN   │
    └─────────┘      └─────────┘     └─────────┘
```

## Component Details

### 1. Spokes (Data Collection Layer)

**Purpose**: Collect raw data from multiple sources

**Components**:
- `GitHubSignalsCollector`: Collects commits, PRs, issues, developer activity
- `CVECollector`: Fetches CVE data from NVD
- `EPSSCollector`: Collects exploit prediction scores
- `KEVCollector`: CISA Known Exploited Vulnerabilities catalog
- `ExploitDBCollector`: Public exploit database

**Key Features**:
- Retry logic with exponential backoff
- Rate limiting handling
- JSONL output format
- Metadata tracking

### 2. Hub (Knowledge Graph Layer)

**Purpose**: Central graph database for data integration and RAG

**Technology**: Neo4j

**Schema**:
```cypher
(CVE)-[:HAS_CWE]->(CWE)
(CVE)-[:HAS_EPSS]->(EPSS)
(CVE)-[:HAS_KEV]->(KEV)
(Package)-[:DEPENDS_ON]->(Package)
(Package)-[:HAS_SIGNAL]->(GitHubSignal)
```

**Components**:
- `DataLoader`: Loads collected data into Neo4j
- `HubQuery`: Query interface for RAG context retrieval
- `SupplyChainAnalyzer`: Dependency graph analysis

**Current Data**:
- 194 CVEs
- 969 CWEs
- 1,666 KEV entries
- 30 Exploits
- Package dependency graphs

### 3. Oracle (Prediction Engine)

**Purpose**: LLM-based vulnerability risk prediction

**Technology**: Google Gemini 2.0 Flash

#### 3.1 Commit Analyzer

**Analyzes individual commits for vulnerability risk**

**Input Signals**:
- Commit metadata (author, message, timestamp)
- File changes (additions, deletions, modifications)
- Code diff analysis
- Dangerous code patterns detection
- Security check removal detection
- Developer history

**Dangerous Patterns Detected**:
- `eval()`, `exec()`, `pickle.loads()`
- SQL injection patterns
- Weak cryptography (MD5, SHA1)
- Shell command execution
- Removed security validations

**Output**: `CommitRiskResult`
- Risk Score: 0.0-1.0
- Risk Level: LOW, MEDIUM, HIGH, CRITICAL
- Confidence: 0.0-1.0
- Risk factors and recommendations

#### 3.2 Project Oracle

**Analyzes overall project vulnerability risk**

**Input Signals**:
- GitHub activity (7-30 days)
- Commit frequency and patterns
- Security-related issues/PRs
- Late-night/weekend commits
- Developer turnover
- Historical CVE patterns (via RAG)

**RAG Context Retrieved**:
- Similar CVEs by CWE
- Package vulnerability history
- EPSS trends
- Dependency risks
- Package popularity
- Maintainer history

**Output**: `PredictionResult`
- Risk Score: 0.0-1.0
- Risk Level: LOW, MEDIUM, HIGH, CRITICAL
- Confidence: 0.0-1.0
- Reasoning and recommendations

#### 3.3 Integrated Oracle

**Combines all analysis modules for comprehensive assessment**

**Integration Formula**:
```python
overall_risk = (
    commit_risk * 0.4 +      # Individual commit risks
    project_risk * 0.4 +      # Overall project patterns
    supply_chain_risk * 0.2   # Impact multiplier
)

# Boost for high-risk commits
if high_risk_commits:
    overall_risk += 0.1 * len(high_risk_commits)
```

**Output**: `IntegratedRiskAssessment`
- Overall risk score and level
- Component scores breakdown
- High-risk commits list
- Supply chain impact analysis
- Combined reasoning
- Prioritized recommendations
- Alert priority level

### 4. Supply Chain Analyzer

**Purpose**: Track dependency relationships and impact propagation

**Features**:
- Dependency graph construction
- Reverse dependency lookup
- Package popularity metrics
- Impact analysis (blast radius)
- Critical dependent identification

**Metrics Collected**:
- PyPI download statistics
- npm download statistics
- GitHub stars/forks
- Direct vs. transitive dependents

## Workflow

### Standard Analysis Flow

```
1. User Request
   ↓
2. Integrated Oracle
   ↓
3. Parallel Analysis:
   ├─ Commit Analyzer (recent commits)
   ├─ Project Oracle (behavioral signals + RAG)
   └─ Supply Chain (dependency impact)
   ↓
4. Risk Score Combination
   ↓
5. Alert Decision
   ↓
6. Recommendations
```

### Example: Flask Analysis

**Input**: `pallets/flask` repository

**Phase 1 - Commit Analysis**:
- Analyzed 5 recent commits
- Found 3 HIGH-RISK commits
- Average commit risk: 0.41

**Phase 2 - Project Analysis**:
- Collected 7 days of GitHub signals
- Project risk: 0.08
- Used RAG for historical context

**Phase 3 - Supply Chain**:
- 9 direct dependencies
- Supply chain risk: 0.05

**Phase 4 - Integration**:
- Overall risk: 0.51 (HIGH)
- Alert: ⚠️ HIGH PRIORITY
- Recommendation: Security review before merge

## Key Features

### 1. Commit-Level Analysis
- **Pre-merge detection**: Analyzes commits before they're merged
- **Code diff inspection**: Examines actual code changes
- **Pattern recognition**: Detects dangerous code patterns
- **Developer profiling**: Tracks contributor history

### 2. RAG-Enhanced Prediction
- **Historical context**: Learns from past CVEs
- **Similar pattern matching**: Finds analogous vulnerabilities
- **EPSS trends**: Incorporates exploit probability data
- **CWE relationships**: Understands weakness patterns

### 3. Supply Chain Awareness
- **Dependency tracking**: Maps entire dependency tree
- **Impact calculation**: Estimates blast radius
- **Popularity weighting**: Considers package adoption
- **Critical dependent identification**: Flags high-profile projects

### 4. Multi-Signal Fusion
- **Behavioral signals**: Commit patterns, issue activity
- **Code signals**: Dangerous patterns, security checks
- **Social signals**: Developer history, contributor changes
- **Temporal signals**: Late-night commits, unusual activity

## Performance Metrics

### Test Results (Flask Analysis)

**Commit Analysis**:
- 5 commits analyzed in ~15 seconds
- 3 high-risk commits detected (60% detection rate)
- Risk scores: 0.70, 0.60, 0.60

**Integration**:
- Overall risk: 0.51 (HIGH)
- Confidence: 0.94
- Alert triggered: ⚠️ HIGH PRIORITY

**Detected Issues**:
- Large-scale refactoring (779 additions, 1007 deletions)
- Security check removal
- High-risk file modifications (session, SQLAlchemy)

## Technical Stack

**Languages**: Python 3.10+

**Core Dependencies**:
- `google-generativeai`: LLM inference
- `neo4j`: Graph database
- `requests`: HTTP API calls
- `python-dotenv`: Environment management

**APIs Used**:
- GitHub REST API
- NVD CVE API
- EPSS API
- PyPI/npm registries
- pypistats.org

**Database**: Neo4j 5.x

## Configuration

**Environment Variables**:
```bash
GITHUB_TOKEN=<github_personal_access_token>
GEMINI_API_KEY=<google_gemini_api_key>
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<neo4j_password>
```

## Usage Examples

### Basic Analysis
```python
from rota.oracle.integrated_oracle import IntegratedOracle

oracle = IntegratedOracle()
assessment = oracle.assess_risk("pallets/flask", days_back=7)

print(f"Risk: {assessment.overall_risk_level}")
print(f"Score: {assessment.overall_risk_score:.2f}")
```

### Command Line
```bash
python tests/test_integrated_oracle.py pallets/flask
```

## Limitations & Future Work

### Current Limitations
1. **No reverse dependency API**: PyPI/npm don't provide reverse deps
2. **Rate limiting**: GitHub API limits affect large-scale scanning
3. **Manual validation**: No automated ground truth verification
4. **Single language**: Primarily Python-focused

### Future Enhancements
1. **Temporal validation (Axle)**: Backtest predictions against historical CVEs
2. **CI/CD integration**: Analyze test coverage and security scan results
3. **Real-time monitoring**: GitHub webhook integration
4. **Multi-language support**: Extend to Java, JavaScript, Go
5. **Dashboard**: Web UI for visualization
6. **Batch scanning**: Analyze hundreds of projects simultaneously

## Research Contributions

1. **Commit-level zero-day prediction**: Novel approach to pre-merge vulnerability detection
2. **Multi-modal signal fusion**: Combines code, behavioral, and social signals
3. **RAG-enhanced prediction**: Uses historical CVE patterns for context
4. **Supply chain risk propagation**: Quantifies downstream impact

## References

- NVD CVE Database: https://nvd.nist.gov/
- EPSS: https://www.first.org/epss/
- CISA KEV: https://www.cisa.gov/known-exploited-vulnerabilities
- Neo4j: https://neo4j.com/
- Google Gemini: https://ai.google.dev/

---

**Version**: 0.2.0  
**Last Updated**: 2025-01-27  
**Status**: Research Prototype
