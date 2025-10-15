"""Security Vulnerability Knowledge Graph Dashboard."""
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Security Vulnerability Dashboard",
    page_icon="🔒",
    layout="wide",
)

# Neo4j connection
@st.cache_resource
def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password:
        st.error("NEO4J_PASSWORD environment variable not set")
        st.stop()
    
    return GraphDatabase.driver(uri, auth=(username, password))


driver = get_neo4j_driver()


def run_query(query, parameters=None):
    """Execute a Cypher query and return results."""
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


# Title
st.title("🔒 Security Vulnerability Knowledge Graph")
st.markdown("Explore CVE data, exploits, advisories, and EPSS scores")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select View",
    ["Overview", "CVE Explorer", "Risk Analysis", "Exploit Database", "Product Security"]
)

# Overview Page
if page == "Overview":
    st.header("📊 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Count CVEs
    cve_count = run_query("MATCH (c:CVE) RETURN count(c) as count")[0]["count"]
    col1.metric("Total CVEs", cve_count)
    
    # Count Exploits
    exploit_count = run_query("MATCH (e:Exploit) RETURN count(e) as count")[0]["count"]
    col2.metric("Total Exploits", exploit_count)
    
    # Count Advisories
    advisory_count = run_query("MATCH (a:Advisory) RETURN count(a) as count")[0]["count"]
    col3.metric("Total Advisories", advisory_count)
    
    # Count Packages
    package_count = run_query("MATCH (p:Package) RETURN count(p) as count")[0]["count"]
    col4.metric("Total Packages", package_count)
    
    st.markdown("---")
    
    # High-risk CVEs
    st.subheader("🚨 High-Risk CVEs (EPSS > 0.5)")
    high_risk_query = """
    MATCH (c:CVE)
    WHERE c.epss_score > 0.5
    OPTIONAL MATCH (c)-[:HAS_EXPLOIT]->(e:Exploit)
    RETURN c.id as cve_id, c.cvssScore as cvss, c.epss_score as epss, 
           c.cvssSeverity as severity, count(e) as exploit_count
    ORDER BY c.epss_score DESC
    LIMIT 10
    """
    high_risk = run_query(high_risk_query)
    
    if high_risk:
        st.dataframe(high_risk, use_container_width=True)
    else:
        st.info("No high-risk CVEs found")
    
    st.markdown("---")
    
    # Recent CVEs with exploits
    st.subheader("💣 CVEs with Exploits")
    exploit_query = """
    MATCH (c:CVE)-[:HAS_EXPLOIT]->(e:Exploit)
    RETURN c.id as cve_id, c.cvssScore as cvss, c.epss_score as epss,
           count(e) as exploit_count
    ORDER BY exploit_count DESC
    LIMIT 10
    """
    with_exploits = run_query(exploit_query)
    
    if with_exploits:
        st.dataframe(with_exploits, use_container_width=True)
    else:
        st.info("No CVEs with exploits found")

# CVE Explorer
elif page == "CVE Explorer":
    st.header("🔍 CVE Explorer")
    
    cve_id = st.text_input("Enter CVE ID", "CVE-2021-44228")
    
    if st.button("Search"):
        # Get CVE details
        cve_query = """
        MATCH (c:CVE {id: $cve_id})
        RETURN c.id as id, c.description as description, c.cvssScore as cvss_score,
               c.cvssSeverity as severity, c.epss_score as epss_score,
               c.epss_percentile as epss_percentile, c.published as published
        """
        cve_data = run_query(cve_query, {"cve_id": cve_id})
        
        if cve_data:
            cve = cve_data[0]
            
            col1, col2, col3 = st.columns(3)
            col1.metric("CVSS Score", f"{cve['cvss_score']:.1f}" if cve['cvss_score'] else "N/A")
            col2.metric("EPSS Score", f"{cve['epss_score']:.4f}" if cve['epss_score'] else "N/A")
            col3.metric("Severity", cve['severity'] or "N/A")
            
            st.markdown("### Description")
            st.write(cve['description'] or "No description available")
            
            # Get exploits
            st.markdown("### 💣 Exploits")
            exploit_query = """
            MATCH (c:CVE {id: $cve_id})-[:HAS_EXPLOIT]->(e:Exploit)
            RETURN e.edb_id as id, e.description as description, e.author as author,
                   e.date as date, e.type as type
            ORDER BY e.date DESC
            """
            exploits = run_query(exploit_query, {"cve_id": cve_id})
            
            if exploits:
                st.dataframe(exploits, use_container_width=True)
            else:
                st.info("No exploits found")
            
            # Get affected products
            st.markdown("### 🎯 Affected Products")
            product_query = """
            MATCH (c:CVE {id: $cve_id})-[:AFFECTS]->(cpe:CPE)<-[:HAS_VERSION]-(p:Product)
                  <-[:PRODUCES]-(v:Vendor)
            RETURN DISTINCT v.name as vendor, p.name as product, cpe.version as version
            LIMIT 20
            """
            products = run_query(product_query, {"cve_id": cve_id})
            
            if products:
                st.dataframe(products, use_container_width=True)
            else:
                st.info("No affected products found")
        else:
            st.error(f"CVE {cve_id} not found")

# Risk Analysis
elif page == "Risk Analysis":
    st.header("📈 Risk Analysis")
    
    # EPSS distribution
    st.subheader("EPSS Score Distribution")
    epss_query = """
    MATCH (c:CVE)
    WHERE c.epss_score IS NOT NULL
    RETURN c.epss_score as epss
    ORDER BY c.epss_score
    """
    epss_data = run_query(epss_query)
    
    if epss_data:
        import pandas as pd
        df = pd.DataFrame(epss_data)
        st.line_chart(df['epss'])
    
    # Severity distribution
    st.subheader("Severity Distribution")
    severity_query = """
    MATCH (c:CVE)
    WHERE c.cvssSeverity IS NOT NULL
    RETURN c.cvssSeverity as severity, count(c) as count
    ORDER BY count DESC
    """
    severity_data = run_query(severity_query)
    
    if severity_data:
        import pandas as pd
        df = pd.DataFrame(severity_data)
        st.bar_chart(df.set_index('severity'))

# Exploit Database
elif page == "Exploit Database":
    st.header("💣 Exploit Database")
    
    st.subheader("Recent Exploits")
    exploit_query = """
    MATCH (e:Exploit)<-[:HAS_EXPLOIT]-(c:CVE)
    RETURN e.edb_id as id, e.description as description, e.author as author,
           e.date as date, e.type as type, c.id as cve_id
    ORDER BY e.date DESC
    LIMIT 50
    """
    exploits = run_query(exploit_query)
    
    if exploits:
        st.dataframe(exploits, use_container_width=True)
    else:
        st.info("No exploits found")

# Product Security
elif page == "Product Security":
    st.header("🎯 Product Security")
    
    vendor_name = st.text_input("Enter Vendor Name", "apache")
    
    if st.button("Analyze"):
        # Get products and vulnerabilities
        product_query = """
        MATCH (v:Vendor {name: $vendor})-[:PRODUCES]->(p:Product)
              -[:HAS_VERSION]->(cpe:CPE)<-[:AFFECTS]-(c:CVE)
        RETURN p.name as product, count(DISTINCT c) as vuln_count,
               avg(c.cvssScore) as avg_cvss, avg(c.epss_score) as avg_epss
        ORDER BY vuln_count DESC
        """
        products = run_query(product_query, {"vendor": vendor_name.lower()})
        
        if products:
            st.subheader(f"Products by {vendor_name}")
            st.dataframe(products, use_container_width=True)
            
            # Get specific CVEs
            st.subheader("Vulnerabilities")
            cve_query = """
            MATCH (v:Vendor {name: $vendor})-[:PRODUCES]->(p:Product)
                  -[:HAS_VERSION]->(cpe:CPE)<-[:AFFECTS]-(c:CVE)
            RETURN DISTINCT c.id as cve_id, p.name as product, c.cvssScore as cvss,
                   c.epss_score as epss, c.cvssSeverity as severity
            ORDER BY c.epss_score DESC
            LIMIT 50
            """
            cves = run_query(cve_query, {"vendor": vendor_name.lower()})
            
            if cves:
                st.dataframe(cves, use_container_width=True)
        else:
            st.error(f"No data found for vendor: {vendor_name}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "Security Vulnerability Knowledge Graph Dashboard\n\n"
    "Data sources: NVD, GitHub Advisory, EPSS, Exploit-DB"
)
