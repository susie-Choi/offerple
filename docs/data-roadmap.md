# ROTA Data Collection Roadmap

## 📊 Current Data Sources (4)

| Data Source | Provider | Information | Purpose | Status |
|------------|----------|-------------|---------|--------|
| **CVE** | NVD | CVE ID, CVSS score, description, affected products (CPE), CWE ID, references | Vulnerability baseline | ✅ Complete |
| **GitHub Advisory** | GitHub | Package name, vulnerability description, affected versions, patched versions | Package-level vulnerabilities | ✅ Complete |
| **EPSS** | FIRST | CVE-specific exploit probability score (0-1) | Real-world risk prediction | ✅ Complete |
| **Exploit-DB** | Offensive Security | Actual exploit code, attack methods, metadata | Exploit availability | ✅ Complete |

## 🔴 Critical - Essential for Research

| Data Source | Provider | Information | Why Needed | Difficulty | Time |
|------------|----------|-------------|------------|------------|------|
| **Vulnerable Code** | GitHub commits, Big-Vul, Devign | Actual vulnerable source code, pre/post-patch code | Core data for embedding/clustering - research impossible without it | ⭐⭐⭐ Hard | 3-5 days |
| **CWE Details** | MITRE CWE DB | CWE hierarchy, weakness descriptions, example code, exploitability | Feature extraction, cluster interpretation | ⭐ Easy | 1 day |
| **Package Metadata** | Libraries.io, npm/PyPI API | Download counts, dependency graphs, usage statistics | Supply chain impact analysis | ⭐⭐ Medium | 2-3 days |

## 🟡 Important - Research Enhancement

| Data Source | Provider | Information | Why Needed | Difficulty | Time |
|------------|----------|-------------|------------|------------|------|
| **CISA KEV** | CISA | Actually exploited CVE list, government-verified | More reliable than EPSS for real-world risk | ⭐ Very Easy | 30 min |
| **Exploit Difficulty** | Metasploit, Nuclei | Exploit rank, complexity, reliability | Differentiate risk even with same CVSS | ⭐⭐ Medium | 1-2 days |
| **Patch Information** | GitHub | Time to patch, patch complexity (lines changed) | Historical validation, pattern analysis | ⭐⭐ Medium | 1-2 days |

## 🟢 Nice to Have - Additional Value

| Data Source | Provider | Information | Why Needed | Difficulty | Time |
|------------|----------|-------------|------------|------------|------|
| **Security News** | Hacker News, Reddit | Community reactions, real-world impact cases | Threat intelligence, context | ⭐⭐ Medium | 1-2 days |
| **PoC Code** | GitHub, PacketStorm | Proof of Concept code | Exploit feasibility verification | ⭐ Easy | 1 day |
| **Product Usage Stats** | Shodan, BuiltWith | Actual internet usage | Real-world impact scope | ⭐⭐⭐ Hard | 3-5 days |

## 🎯 Recommended Implementation Order

### Phase 1 - This Week (Quick Wins)

| Priority | Data Source | Reason | Time |
|----------|-------------|--------|------|
| 1️⃣ | **CISA KEV** | 30 minutes to complete, immediately usable | 30 min |
| 2️⃣ | **CWE Details** | One day to complete, needed for clustering | 1 day |

**Total Time: ~1.5 days**

### Phase 2 - Next Week (Core Data)

| Priority | Data Source | Reason | Time |
|----------|-------------|--------|------|
| 3️⃣ | **Vulnerable Code** | Core of embedding, most important | 3-5 days |

**Total Time: ~5 days**

### Phase 3 - Following Weeks (Enhancement)

| Priority | Data Source | Reason | Time |
|----------|-------------|--------|------|
| 4️⃣ | **Package Metadata** | Strengthen supply chain analysis | 2-3 days |
| 5️⃣ | **Exploit Difficulty** | Refine risk scoring | 1-2 days |

## 📈 Priority Scoring

| Data Source | Importance (10) | Difficulty | Time | Priority Rank |
|-------------|----------------|------------|------|---------------|
| Vulnerable Code | 🔴 10 | High | 5 days | 1st (Core) |
| CISA KEV | 🟡 7 | Low | 30 min | 2nd (Quick Win) |
| CWE Details | 🔴 9 | Low | 1 day | 3rd (Essential) |
| Package Metadata | 🟡 7 | Medium | 3 days | 4th |
| Exploit Difficulty | 🟡 6 | Medium | 2 days | 5th |
| Patch Information | 🟢 5 | Medium | 2 days | 6th |
| Security News | 🟢 3 | Medium | 2 days | 7th |
| PoC Code | 🟢 4 | Easy | 1 day | 8th |
| Usage Statistics | 🟢 3 | High | 5 days | 9th |

## 💡 Practical Strategy

### Minimum Viable (Master's Thesis)
```
✅ CVE (have)
✅ EPSS (have)
✅ Exploit-DB (have)
+ CISA KEV (30 min)
+ CWE Details (1 day)
+ Vulnerable Code (5 days)
────────────────────
= 6.5 days total
```

### Strong Configuration (Good Paper)
```
Minimum Viable
+ Package Metadata (3 days)
+ Exploit Difficulty (2 days)
────────────────────
= 11.5 days total
```

### Perfect Configuration (Top-Tier Conference)
```
Strong Configuration
+ Patch Information (2 days)
+ PoC Code (1 day)
────────────────────
= 14.5 days total
```

## 🚀 Quick Start

### Today (2 hours)
```bash
# Add CISA KEV (30 minutes!)
rota spokes collect-kev
rota hub load-kev data/raw/kev/kev_*.jsonl
```

### Today (1 hour)
```bash
# Add CWE details (implemented!)
rota spokes collect-cwe
rota hub load-cwe data/raw/cwe/cwe_*.jsonl
```

### Next Week (1 week)
```bash
# Add vulnerable code (core!)
rota spokes collect-vulnerable-code
rota hub load-vulnerable-code data/raw/code/vulnerable_*.jsonl
```

## 📝 Implementation Status

- [x] CVE - Complete
- [x] EPSS - Complete
- [x] GitHub Advisory - Complete
- [x] Exploit-DB - Complete
- [x] CISA KEV - **Implemented, ready to use!**
- [x] CWE Details - **Implemented, ready to use!**
- [ ] Vulnerable Code - Critical for research
- [ ] Package Metadata - Enhancement
- [ ] Exploit Difficulty - Enhancement
- [ ] Patch Information - Nice to have
- [ ] Security News - Nice to have
- [ ] PoC Code - Nice to have
- [ ] Usage Statistics - Nice to have

## 🎓 Research Impact

### With Current Data (4 sources)
- Basic vulnerability analysis
- EPSS-based risk prediction
- Exploit availability tracking

### With Phase 1 Complete (6 sources)
- Government-verified exploitation data (KEV)
- CWE-based vulnerability classification
- Improved risk assessment

### With Phase 2 Complete (7 sources)
- **Code-level vulnerability analysis**
- **Embedding-based clustering**
- **Pattern discovery in vulnerable code**
- **Publication-ready research**

### With Phase 3 Complete (9+ sources)
- Supply chain impact analysis
- Exploit difficulty assessment
- Comprehensive threat intelligence
- **Top-tier conference submission**

## 📚 Data Source Details

### CISA KEV
- **URL**: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- **Format**: JSON
- **Update Frequency**: Daily
- **Implementation**: ✅ Complete in `src/rota/spokes/kev.py`

### CWE Details
- **URL**: https://cwe.mitre.org/data/downloads.html
- **Format**: XML/JSON
- **Update Frequency**: Quarterly
- **Implementation**: 🔄 Next priority

### Vulnerable Code
- **Sources**: 
  - GitHub commit diffs
  - Big-Vul dataset
  - Devign dataset
- **Format**: Code snippets + metadata
- **Implementation**: 🔄 Critical priority

---

**Last Updated**: 2024-10-27  
**Next Review**: After Phase 1 completion
