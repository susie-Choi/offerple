"""
Enrich CWE nodes with names from MITRE CWE database.
"""
import os
import requests
import xml.etree.ElementTree as ET
from neo4j import GraphDatabase
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

CWE_XML_URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"

def fetch_cwe_data():
    """Fetch CWE data from MITRE."""
    print("Downloading CWE database from MITRE...")
    
    # Download and extract XML
    import zipfile
    import io
    
    response = requests.get(CWE_XML_URL, verify=False)
    response.raise_for_status()
    
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        # Find the XML file
        xml_files = [f for f in z.namelist() if f.endswith('.xml')]
        if not xml_files:
            raise ValueError("No XML file found in CWE archive")
        
        with z.open(xml_files[0]) as f:
            tree = ET.parse(f)
            root = tree.getroot()
    
    print(f"✓ Downloaded CWE database")
    
    # Parse CWE entries
    cwe_dict = {}
    ns = {'cwe': 'http://cwe.mitre.org/cwe-7'}
    
    for weakness in root.findall('.//cwe:Weakness', ns):
        cwe_id = weakness.get('ID')
        cwe_name = weakness.get('Name')
        cwe_description = weakness.find('cwe:Description', ns)
        
        if cwe_id and cwe_name:
            desc_text = ""
            if cwe_description is not None and cwe_description.text:
                desc_text = cwe_description.text.strip()
            
            cwe_dict[f"CWE-{cwe_id}"] = {
                "name": cwe_name,
                "description": desc_text
            }
    
    print(f"✓ Parsed {len(cwe_dict)} CWE entries")
    return cwe_dict

def enrich_neo4j_cwe(cwe_dict):
    """Update CWE nodes in Neo4j with names and descriptions."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Get all CWE nodes
        result = session.run("MATCH (cwe:CWE) RETURN cwe.id as id")
        cwe_ids = [record["id"] for record in result]
        
        print(f"\nFound {len(cwe_ids)} CWE nodes in Neo4j")
        print("Enriching with names and descriptions...")
        
        updated = 0
        not_found = []
        
        for cwe_id in tqdm(cwe_ids):
            if cwe_id in cwe_dict:
                cwe_info = cwe_dict[cwe_id]
                session.run("""
                    MATCH (cwe:CWE {id: $id})
                    SET cwe.name = $name,
                        cwe.description = $description
                """, 
                id=cwe_id,
                name=cwe_info["name"],
                description=cwe_info["description"]
                )
                updated += 1
            else:
                not_found.append(cwe_id)
        
        print(f"\n✓ Updated {updated} CWE nodes")
        if not_found:
            print(f"⚠ {len(not_found)} CWEs not found in MITRE database:")
            for cwe_id in not_found[:10]:
                print(f"  - {cwe_id}")
            if len(not_found) > 10:
                print(f"  ... and {len(not_found) - 10} more")
    
    driver.close()

if __name__ == "__main__":
    print("=" * 60)
    print("CWE Name Enrichment")
    print("=" * 60)
    
    cwe_dict = fetch_cwe_data()
    enrich_neo4j_cwe(cwe_dict)
    
    print("\n" + "=" * 60)
    print("✓ CWE enrichment complete!")
    print("=" * 60)
