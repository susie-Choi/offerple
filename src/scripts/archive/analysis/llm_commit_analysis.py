"""
LLM-based commit analysis to identify vulnerability-introducing commits.

Uses Gemini to analyze commits and predict which ones introduced vulnerabilities.
"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase
import google.generativeai as genai

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
genai.configure(api_key=GEMINI_API_KEY)

def get_cve_with_fix_commit(cve_id):
    """Get CVE info and the known fix commit."""
    with driver.session() as session:
        # Get CVE info
        cve_result = session.run("""
            MATCH (cve:CVE {id: $cve_id})
            RETURN cve.id as id,
                   cve.published as published,
                   cve.description as description,
                   cve.cvssScore as cvss_score
        """, cve_id=cve_id)
        cve_info = cve_result.single()
        
        # Get the fix commit (for CVE-2012-3503, we know it's 1781f22b)
        commit_result = session.run("""
            MATCH (cve:CVE {id: $cve_id})-[:HAS_COMMIT]->(c:Commit)
            WHERE c.sha STARTS WITH '1781f22b'
            RETURN c.sha as sha,
                   c.date as date,
                   c.author as author,
                   c.message as message
        """, cve_id=cve_id)
        fix_commit = commit_result.single()
        
        # Get commits before the fix
        pub_date = datetime.fromisoformat(cve_info['published'].replace('Z', '+00:00')).replace(tzinfo=None)
        
        commits_result = session.run("""
            MATCH (cve:CVE {id: $cve_id})-[:HAS_COMMIT]->(c:Commit)
            WHERE c.date < $fix_date
            RETURN c.sha as sha,
                   c.date as date,
                   c.author as author,
                   c.message as message
            ORDER BY c.date DESC
            LIMIT 50
        """, cve_id=cve_id, fix_date=fix_commit['date'] if fix_commit else pub_date.isoformat())
        
        commits_before = list(commits_result)
        
        return {
            'cve': cve_info,
            'fix_commit': fix_commit,
            'commits_before': commits_before
        }

def analyze_commit_with_llm(commit, cve_description, fix_commit_message):
    """Use LLM to analyze if a commit might have introduced the vulnerability."""
    
    prompt = f"""You are a security researcher analyzing commits to identify which commit introduced a vulnerability.

CVE Description:
{cve_description}

Known Fix Commit Message:
{fix_commit_message}

Commit to Analyze:
SHA: {commit['sha']}
Date: {commit['date']}
Author: {commit['author']}
Message:
{commit['message']}

Based on the CVE description and the fix commit, analyze this commit and determine:
1. Likelihood this commit introduced the vulnerability (0-100%)
2. Reasoning for your assessment
3. Key indicators (positive or negative)

Respond in JSON format:
{{
    "likelihood": <0-100>,
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "reasoning": "<your reasoning>",
    "indicators": ["<indicator1>", "<indicator2>", ...]
}}
"""
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    
    try:
        # Extract JSON from response
        text = response.text
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        result = json.loads(text.strip())
        return result
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        print(f"Response: {response.text}")
        return None

def main():
    """Analyze CVE-2012-3503 commits with LLM."""
    cve_id = "CVE-2012-3503"
    
    print("="*80)
    print(f"LLM-Based Commit Analysis for {cve_id}")
    print("="*80)
    
    # Get data
    data = get_cve_with_fix_commit(cve_id)
    
    if not data['fix_commit']:
        print("Fix commit not found!")
        return
    
    print(f"\nCVE: {data['cve']['id']}")
    print(f"CVSS Score: {data['cve']['cvss_score']}")
    print(f"Description: {data['cve']['description'][:200]}...")
    
    print(f"\nKnown Fix Commit:")
    print(f"  SHA: {data['fix_commit']['sha']}")
    print(f"  Date: {data['fix_commit']['date']}")
    print(f"  Message: {data['fix_commit']['message'][:150]}...")
    
    print(f"\nAnalyzing {len(data['commits_before'])} commits before the fix...")
    print("="*80)
    
    # Analyze commits
    high_risk_commits = []
    
    for i, commit in enumerate(data['commits_before'][:10], 1):  # Analyze top 10
        print(f"\n[{i}/10] Analyzing {commit['sha'][:8]}...")
        
        analysis = analyze_commit_with_llm(
            commit,
            data['cve']['description'],
            data['fix_commit']['message']
        )
        
        if analysis:
            print(f"  Likelihood: {analysis['likelihood']}%")
            print(f"  Risk Level: {analysis['risk_level']}")
            print(f"  Reasoning: {analysis['reasoning'][:150]}...")
            
            if analysis['likelihood'] >= 50:
                high_risk_commits.append({
                    'commit': commit,
                    'analysis': analysis
                })
    
    # Summary
    print(f"\n{'='*80}")
    print(f"High-Risk Commits (likelihood >= 50%)")
    print(f"{'='*80}")
    
    high_risk_commits.sort(key=lambda x: x['analysis']['likelihood'], reverse=True)
    
    for i, item in enumerate(high_risk_commits, 1):
        commit = item['commit']
        analysis = item['analysis']
        
        print(f"\n{i}. {commit['sha'][:8]} - Likelihood: {analysis['likelihood']}%")
        print(f"   Date: {commit['date']}")
        print(f"   Risk Level: {analysis['risk_level']}")
        print(f"   Reasoning: {analysis['reasoning']}")
        print(f"   Indicators:")
        for indicator in analysis['indicators']:
            print(f"     - {indicator}")
        print(f"   Message: {commit['message'][:100]}...")

if __name__ == "__main__":
    try:
        main()
    finally:
        driver.close()
