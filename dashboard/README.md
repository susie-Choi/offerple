# ROTA Dashboard

Interactive Neo4j graph visualization using neovis.js

## Features

- 🔍 **CVE Search**: Search and explore specific CVEs
- 📊 **High Risk Analysis**: View CVEs with high EPSS scores
- 💣 **Exploit Tracking**: See CVEs with known exploits
- 🎯 **Interactive Graph**: Neo4j Aura-style visualization
- 🔗 **Relationship Mapping**: CVE → Exploit → Advisory → Commit connections

## Usage

### Option 1: Open Directly
Simply open `index.html` in your browser.

### Option 2: Local Server
```bash
# Python
python -m http.server 8000

# Node.js
npx http-server

# Then open: http://localhost:8000
```

## Views

1. **Overview**: First 100 nodes and relationships
2. **Search CVE**: Find specific CVE by ID (e.g., CVE-2021-44228)
3. **High Risk CVEs**: CVEs with EPSS score > 0.5
4. **CVEs with Exploits**: CVEs that have known exploits
5. **Recent CVEs**: CVEs published in 2024

## Node Colors

- 🔴 **Red**: CVE
- 🔵 **Cyan**: Exploit
- 🟢 **Green**: Advisory
- 🟠 **Pink**: Package
- 🟣 **Purple**: Commit

## Configuration

Neo4j credentials are in `index.html`. Update if needed:
```javascript
neo4j: {
    serverUrl: "neo4j+s://your-instance.databases.neo4j.io",
    serverUser: "neo4j",
    serverPassword: "your-password"
}
```

## Requirements

- Modern web browser
- Internet connection (for neovis.js CDN)
- Neo4j database with loaded data
