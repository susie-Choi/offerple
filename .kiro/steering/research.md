---
inclusion: always
---

# Research Guidelines for ROTA Project

## Project Goal

Develop a novel research contribution for academic publication on zero-day vulnerability prediction.

## Current Status

- PyPI package published (v0.1.1)
- 80 CVEs collected from Django
- 3 CVEs validated with 90-day lead time
- Basic prediction system implemented

## Research Focus

We are pursuing novel contributions in:

1. **LLM-based Causal Reasoning**: Using LLMs to explain WHY vulnerabilities occur
2. **Temporal Knowledge Graphs**: Modeling how vulnerability patterns evolve over time
3. **Active Learning**: Efficient project selection for maximum learning
4. **Multi-Modal Fusion**: Combining code, text, graph, and time-series signals

## Code Standards

### Language
- All code, comments, and docstrings: English only
- Documentation (.md files): English preferred
- No emojis in code or comments (only in .md files)

### Architecture
- Following wheel-themed structure (spokes, hub, wheel, oracle, axle)
- Modular design for easy experimentation
- Clear separation between data collection and prediction

### Experimentation
- Always use temporal validation (no data leakage)
- Include negative samples in evaluation
- Compare with baselines (random, CVSS, EPSS)
- Report lead time, not just accuracy

## Documentation Requirements

All research experiments must be documented with:
- Research question
- Methodology
- Expected novelty
- Experimental design
- Results and analysis

## Multi-Computer Workflow

This project is developed across multiple computers. Always:
- Commit and push frequently
- Document decisions in .md files
- Update specs when changing direction
- Keep RESEARCH_DIRECTIONS.md current

## Paper Target

Top-tier security conferences:
- USENIX Security
- ACM CCS
- NDSS
- IEEE S&P

Focus on technical novelty, not just engineering contribution.
