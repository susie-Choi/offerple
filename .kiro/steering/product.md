# Product Overview

Zero-Day Defense is a research project focused on **LLM-based pre-signal analysis for predicting potential vulnerabilities in software ecosystems**. The system aims to identify security risks before they become known zero-day exploits.

## Current Phase
The project is in its initial data collection phase, building pipelines to gather information from various software ecosystems (PyPI, Maven, npm, GitHub) for analysis.

## Key Features
- Multi-ecosystem data collection (Python, Java, JavaScript packages)
- Time-based filtering with `cutoff_date` to prevent temporal data leakage
- Structured data storage in JSON Lines format
- GitHub API integration for repository metadata and activity

## Research Goals
1. Data collection from multiple package ecosystems
2. Feature extraction and normalization
3. LLM-based potential risk inference
4. Historical validation pipeline implementation

## Language
This is a Korean research project - documentation and comments are primarily in Korean, though code follows English conventions.