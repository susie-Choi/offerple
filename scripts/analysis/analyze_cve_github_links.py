"""Analyze CVE data to extract GitHub repository links."""
import json
import re
from collections import Counter
from pathlib import Path

# Load CVE data
cve_file = Path("data/raw/bulk_cve_data.jsonl")

github_repos = []
cve_with_github = []

print("Analyzing CVE data for GitHub links...")

with open(cve_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i % 1000 == 0:
            print(f"  Processed {i} CVEs...")
        
        data = json.loads(line)
        payload = data.get('payload', {})
        
        # Handle NVD CVE format
        vulnerabilities = payload.get('vulnerabilities', [])
        if not vulnerabilities:
            continue
        
        cve_data = vulnerabilities[0].get('cve', {})
        cve_id = cve_data.get('id')
        
        # Extract GitHub links from references
        references = cve_data.get('references', [])
        github_links = []
        
        for ref in references:
            url = ref.get('url', '')
            # Match GitHub repo URLs
            match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
            if match:
                owner = match.group(1)
                repo = match.group(2)
                # Clean repo name (remove .git, /issues, etc.)
                repo = re.sub(r'(\.git|/issues|/pull|/commit|/blob|/tree).*', '', repo)
                if owner and repo and owner != 'advisories':
                    github_links.append(f"{owner}/{repo}")
        
        if github_links:
            cve_with_github.append({
                'cve_id': cve_id,
                'repos': list(set(github_links))
            })
            github_repos.extend(github_links)

print(f"\nTotal CVEs: {i+1}")
print(f"CVEs with GitHub links: {len(cve_with_github)}")
print(f"Total GitHub repo mentions: {len(github_repos)}")
print(f"Unique GitHub repos: {len(set(github_repos))}")

# Top repositories
print("\nTop 20 repositories by CVE mentions:")
repo_counts = Counter(github_repos)
for repo, count in repo_counts.most_common(20):
    print(f"  {repo:40s}: {count:4d} CVEs")

# Save results
output_file = Path("data/processed/cve_github_mapping.jsonl")
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    for item in cve_with_github:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"\nSaved mapping to: {output_file}")

# Save unique repos list
repos_file = Path("data/processed/github_repos_from_cve.txt")
with open(repos_file, 'w', encoding='utf-8') as f:
    for repo in sorted(set(github_repos)):
        f.write(f"{repo}\n")

print(f"Saved unique repos to: {repos_file}")
