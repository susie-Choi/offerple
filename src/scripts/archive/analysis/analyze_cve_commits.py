"""
Analyze commits for CVEs to identify vulnerability-related commits.

This script:
1. Loads commits for each CVE from Neo4j
2. Analyzes commit messages and metadata
3. Identifies potential vulnerability-introducing commits
4. Generates analysis report
"""
import os
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
from neo4j import GraphDatabase
import re

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Security-related keywords
SECURITY_KEYWORDS = [
    'security', 'vulnerability', 'cve', 'exploit', 'attack', 'malicious',
    'injection', 'xss', 'csrf', 'sql injection', 'buffer overflow',
    'authentication', 'authorization', 'privilege', 'escalation',
    'sanitize', 'validate', 'escape', 'patch', 'fix', 'bug',
    'unsafe', 'insecure', 'leak', 'exposure', 'disclosure'
]

def analyze_commit_message(message):
    """Analyze commit message for security indicators."""
    message_lower = message.lower()
    
    # Check for security keywords
    found_keywords = [kw for kw in SECURITY_KEYWORDS if kw in message_lower]
    
    # Check for CVE references
    cve_refs = re.findall(r'CVE-\d{4}-\d{4,}', message, re.IGNORECASE)
    
    # Check for fix/patch indicators
    is_fix = any(word in message_lower for word in ['fix', 'patch', 'resolve', 'address'])
    
    return {
        'has_security_keywords': len(found_keywords) > 0,
        'security_keywords': found_keywords,
        'cve_references': cve_refs,
        'is_fix': is_fix,
        'security_score': len(found_keywords) + len(cve_refs) * 2
    }

def get_cve_info(session, cve_id):
    """Get CVE information."""
    result = session.run("""
        MATCH (cve:CVE {id: $cve_id})
        RETURN cve.id as id,
               cve.published as published,
               cve.description as description,
               cve.cvssScore as cvss_score,
               cve.cvssSeverity as severity
    """, cve_id=cve_id)
    return result.single()

def get_cve_commits(session, cve_id):
    """Get all commits for a CVE."""
    result = session.run("""
        MATCH (cve:CVE {id: $cve_id})-[:HAS_COMMIT]->(c:Commit)
        RETURN c.sha as sha,
               c.repo as repo,
               c.date as date,
               c.author as author,
               c.message as message
        ORDER BY c.date
    """, cve_id=cve_id)
    return list(result)

def analyze_cve(cve_id):
    """Analyze all commits for a CVE."""
    print(f"\n{'='*80}")
    print(f"Analyzing {cve_id}")
    print(f"{'='*80}")
    
    with driver.session() as session:
        # Get CVE info
        cve_info = get_cve_info(session, cve_id)
        if not cve_info:
            print(f"CVE not found: {cve_id}")
            return
        
        print(f"\nCVE Information:")
        print(f"  Published: {cve_info['published']}")
        print(f"  CVSS Score: {cve_info['cvss_score']}")
        print(f"  Severity: {cve_info['severity']}")
        print(f"  Description: {cve_info['description'][:200]}...")
        
        # Get commits
        commits = get_cve_commits(session, cve_id)
        print(f"\nTotal commits: {len(commits)}")
        
        # Analyze commits
        security_commits = []
        fix_commits = []
        
        for commit in commits:
            analysis = analyze_commit_message(commit['message'])
            
            if analysis['security_score'] > 0:
                security_commits.append({
                    'commit': commit,
                    'analysis': analysis
                })
            
            if analysis['is_fix'] and analysis['has_security_keywords']:
                fix_commits.append({
                    'commit': commit,
                    'analysis': analysis
                })
        
        # Sort by security score
        security_commits.sort(key=lambda x: x['analysis']['security_score'], reverse=True)
        
        print(f"\n{'='*80}")
        print(f"Security-Related Commits: {len(security_commits)}")
        print(f"{'='*80}")
        
        # Show top 10 security-related commits
        for i, item in enumerate(security_commits[:10], 1):
            commit = item['commit']
            analysis = item['analysis']
            
            print(f"\n{i}. {commit['sha'][:8]} - {commit['date']}")
            print(f"   Author: {commit['author']}")
            print(f"   Security Score: {analysis['security_score']}")
            print(f"   Keywords: {', '.join(analysis['security_keywords'])}")
            if analysis['cve_references']:
                print(f"   CVE Refs: {', '.join(analysis['cve_references'])}")
            print(f"   Message: {commit['message'][:150]}...")
        
        print(f"\n{'='*80}")
        print(f"Potential Fix Commits: {len(fix_commits)}")
        print(f"{'='*80}")
        
        for i, item in enumerate(fix_commits[:5], 1):
            commit = item['commit']
            analysis = item['analysis']
            
            print(f"\n{i}. {commit['sha'][:8]} - {commit['date']}")
            print(f"   Author: {commit['author']}")
            print(f"   Keywords: {', '.join(analysis['security_keywords'])}")
            print(f"   Message: {commit['message'][:150]}...")
        
        # Timeline analysis
        print(f"\n{'='*80}")
        print(f"Timeline Analysis")
        print(f"{'='*80}")
        
        if commits:
            pub_date = datetime.fromisoformat(cve_info['published'].replace('Z', '+00:00')).replace(tzinfo=None)
            first_commit = datetime.fromisoformat(commits[0]['date'].replace('Z', '+00:00')).replace(tzinfo=None)
            last_commit = datetime.fromisoformat(commits[-1]['date'].replace('Z', '+00:00')).replace(tzinfo=None)
            
            print(f"  First commit: {first_commit.strftime('%Y-%m-%d')} ({(pub_date - first_commit).days} days before CVE)")
            print(f"  Last commit: {last_commit.strftime('%Y-%m-%d')} ({(last_commit - pub_date).days} days after CVE)")
            print(f"  CVE published: {pub_date.strftime('%Y-%m-%d')}")
            
            # Find commits closest to CVE date
            commits_with_diff = []
            for commit in commits:
                commit_date = datetime.fromisoformat(commit['date'].replace('Z', '+00:00')).replace(tzinfo=None)
                days_diff = abs((pub_date - commit_date).days)
                commits_with_diff.append((commit, days_diff))
            
            commits_with_diff.sort(key=lambda x: x[1])
            
            print(f"\n  Commits closest to CVE published date:")
            for commit, days_diff in commits_with_diff[:5]:
                commit_date = datetime.fromisoformat(commit['date'].replace('Z', '+00:00')).replace(tzinfo=None)
                before_after = "before" if commit_date < pub_date else "after"
                print(f"    {commit['sha'][:8]} - {days_diff} days {before_after}")
                print(f"      {commit['message'][:100]}...")

def main():
    """Analyze all CVEs with commits."""
    print("="*80)
    print("CVE Commit Analysis")
    print("="*80)
    
    # Get CVEs with commits
    with driver.session() as session:
        result = session.run("""
            MATCH (cve:CVE)-[:HAS_COMMIT]->(c:Commit)
            RETURN DISTINCT cve.id as cve_id
            ORDER BY cve_id
        """)
        cve_ids = [record['cve_id'] for record in result]
    
    print(f"\nFound {len(cve_ids)} CVEs with commits:")
    for cve_id in cve_ids:
        print(f"  - {cve_id}")
    
    # Analyze each CVE
    for cve_id in cve_ids:
        analyze_cve(cve_id)
    
    print(f"\n{'='*80}")
    print("Analysis Complete")
    print(f"{'='*80}")

if __name__ == "__main__":
    try:
        main()
    finally:
        driver.close()
