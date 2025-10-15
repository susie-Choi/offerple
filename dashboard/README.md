# Security Vulnerability Dashboard

Interactive dashboard for exploring the security vulnerability knowledge graph.

## Features

- **Overview**: High-level statistics and high-risk CVEs
- **CVE Explorer**: Search and explore individual CVEs with exploits and affected products
- **Risk Analysis**: EPSS score distribution and severity analysis
- **Exploit Database**: Browse available exploits
- **Product Security**: Analyze vulnerabilities by vendor/product

## Installation

```bash
pip install streamlit pandas
```

## Running the Dashboard

```bash
# From the project root
streamlit run dashboard/app.py

# Or from the dashboard directory
cd dashboard
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Configuration

The dashboard uses the same `.env` file as the rest of the project:

```bash
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

## Screenshots

### Overview Page
- Total counts of CVEs, Exploits, Advisories, and Packages
- High-risk CVEs with EPSS > 0.5
- CVEs with available exploits

### CVE Explorer
- Search by CVE ID
- View CVSS and EPSS scores
- List of available exploits
- Affected products and vendors

### Risk Analysis
- EPSS score distribution chart
- Severity distribution (CRITICAL, HIGH, MEDIUM, LOW)

### Exploit Database
- Browse recent exploits
- Filter by CVE, author, or type

### Product Security
- Analyze vulnerabilities by vendor
- View product-specific CVE lists
- Average CVSS and EPSS scores per product
