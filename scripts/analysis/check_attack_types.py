"""
Check what types of attack techniques are in our collected data
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def check_cwe_types():
    load_dotenv()
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    with driver.session() as session:
        # Get all CWE types
        print("=" * 80)
        print("CWE Types in Database")
        print("=" * 80)
        result = session.run("""
            MATCH (cwe:CWE)
            RETURN cwe.id, cwe.name
            ORDER BY cwe.id
        """)
        
        cwes = [(r['cwe.id'], r['cwe.name']) for r in result]
        
        # Categorize by attack type
        web_attacks = []
        injection_attacks = []
        client_side = []
        server_side = []
        other = []
        
        for cwe_id, cwe_name in cwes:
            name_lower = cwe_name.lower() if cwe_name else ""
            
            if any(x in name_lower for x in ['xss', 'cross-site scripting', 'csrf', 'cross-site request']):
                client_side.append((cwe_id, cwe_name))
            elif any(x in name_lower for x in ['sql injection', 'sqli', 'nosql', 'command injection', 'code injection']):
                injection_attacks.append((cwe_id, cwe_name))
            elif any(x in name_lower for x in ['ssrf', 'server-side request forgery', 'path traversal', 'directory traversal']):
                server_side.append((cwe_id, cwe_name))
            elif any(x in name_lower for x in ['injection', 'file inclusion']):
                injection_attacks.append((cwe_id, cwe_name))
            else:
                other.append((cwe_id, cwe_name))
        
        print(f"\n📊 Total CWEs: {len(cwes)}\n")
        
        print("🌐 Client-Side Attacks (XSS, CSRF, etc.):")
        print("-" * 80)
        for cwe_id, name in client_side:
            print(f"  {cwe_id}: {name}")
        print(f"  Total: {len(client_side)}\n")
        
        print("💉 Injection Attacks (SQLi, Command Injection, etc.):")
        print("-" * 80)
        for cwe_id, name in injection_attacks:
            print(f"  {cwe_id}: {name}")
        print(f"  Total: {len(injection_attacks)}\n")
        
        print("🖥️  Server-Side Attacks (SSRF, Path Traversal, etc.):")
        print("-" * 80)
        for cwe_id, name in server_side:
            print(f"  {cwe_id}: {name}")
        print(f"  Total: {len(server_side)}\n")
        
        print("📦 Other Vulnerabilities:")
        print("-" * 80)
        for cwe_id, name in other[:20]:  # Show first 20
            print(f"  {cwe_id}: {name}")
        if len(other) > 20:
            print(f"  ... and {len(other) - 20} more")
        print(f"  Total: {len(other)}\n")
        
        # Check CVE counts for each category
        print("\n" + "=" * 80)
        print("CVE Counts by Attack Type")
        print("=" * 80)
        
        for category, cwes_list in [
            ("Client-Side", client_side),
            ("Injection", injection_attacks),
            ("Server-Side", server_side)
        ]:
            if cwes_list:
                cwe_ids = [cwe_id for cwe_id, _ in cwes_list]
                result = session.run("""
                    MATCH (cve:CVE)-[:HAS_WEAKNESS]->(cwe:CWE)
                    WHERE cwe.id IN $cwe_ids
                    RETURN COUNT(DISTINCT cve) as count
                """, cwe_ids=cwe_ids)
                count = result.single()['count']
                print(f"{category}: {count} CVEs")
    
    driver.close()

if __name__ == "__main__":
    check_cwe_types()
