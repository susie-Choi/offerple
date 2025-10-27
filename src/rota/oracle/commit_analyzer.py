"""
Commit-level vulnerability risk analysis.

Analyzes individual commits or PRs to detect potential zero-day vulnerabilities
BEFORE they are merged into the codebase.
"""
import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import google.generativeai as genai
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CommitRiskResult:
    """Result of commit risk analysis."""
    commit_sha: str
    repository: str
    risk_score: float  # 0-1
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float  # 0-1
    reasoning: str
    risk_factors: List[str]
    recommendations: List[str]
    analyzed_at: datetime
    
    # Commit metadata
    author: str
    message: str
    files_changed: int
    additions: int
    deletions: int


class CommitAnalyzer:
    """
    Analyzes individual commits for vulnerability risk.
    
    This is the core of zero-day detection - analyzing commits BEFORE merge.
    """
    
    def __init__(
        self,
        github_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp"
    ):
        """
        Initialize commit analyzer.
        
        Args:
            github_token: GitHub API token
            gemini_api_key: Gemini API key for LLM analysis
            model: Gemini model to use
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token required")
        
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("Gemini API key required")
        
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(model)
    
    def analyze_commit(
        self,
        repository: str,
        commit_sha: str
    ) -> CommitRiskResult:
        """
        Analyze a specific commit for vulnerability risk.
        
        Args:
            repository: Repository in format "owner/repo"
            commit_sha: Commit SHA to analyze
            
        Returns:
            CommitRiskResult with risk assessment
        """
        logger.info(f"Analyzing commit {commit_sha} in {repository}")
        
        # Fetch commit details from GitHub
        commit_data = self._fetch_commit(repository, commit_sha)
        
        # Get author history
        author_email = commit_data['commit']['author'].get('email', '')
        author_history = self._get_author_history(repository, author_email)
        
        # Extract risk signals
        signals = self._extract_signals(commit_data)
        signals['author_history'] = author_history
        
        # LLM analysis
        risk_assessment = self._analyze_with_llm(commit_data, signals)
        
        return CommitRiskResult(
            commit_sha=commit_sha,
            repository=repository,
            risk_score=risk_assessment['risk_score'],
            risk_level=risk_assessment['risk_level'],
            confidence=risk_assessment['confidence'],
            reasoning=risk_assessment['reasoning'],
            risk_factors=risk_assessment['risk_factors'],
            recommendations=risk_assessment['recommendations'],
            analyzed_at=datetime.utcnow(),
            author=commit_data['commit']['author']['name'],
            message=commit_data['commit']['message'],
            files_changed=len(commit_data['files']),
            additions=commit_data['stats']['additions'],
            deletions=commit_data['stats']['deletions']
        )
    
    def analyze_pr(
        self,
        repository: str,
        pr_number: int
    ) -> List[CommitRiskResult]:
        """
        Analyze all commits in a pull request.
        
        Args:
            repository: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            List of CommitRiskResult for each commit
        """
        logger.info(f"Analyzing PR #{pr_number} in {repository}")
        
        # Fetch PR commits
        commits = self._fetch_pr_commits(repository, pr_number)
        
        # Analyze each commit
        results = []
        for commit in commits:
            result = self.analyze_commit(repository, commit['sha'])
            results.append(result)
        
        return results
    
    def _fetch_commit(self, repository: str, commit_sha: str) -> Dict[str, Any]:
        """Fetch commit details from GitHub API."""
        url = f"https://api.github.com/repos/{repository}/commits/{commit_sha}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def _fetch_pr_commits(self, repository: str, pr_number: int) -> List[Dict]:
        """Fetch all commits in a PR."""
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}/commits"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def _get_author_history(self, repository: str, author_email: str) -> Dict[str, Any]:
        """Get commit history for an author."""
        if not author_email:
            return {'total_commits': 0, 'is_new_contributor': True}
        
        try:
            # Get author's commits in this repo
            url = f"https://api.github.com/repos/{repository}/commits"
            response = requests.get(
                url,
                headers=self.headers,
                params={'author': author_email, 'per_page': 100}
            )
            
            if response.status_code == 200:
                commits = response.json()
                return {
                    'total_commits': len(commits),
                    'is_new_contributor': len(commits) <= 5,
                    'is_core_maintainer': len(commits) > 100
                }
        except Exception as e:
            logger.debug(f"Could not fetch author history: {e}")
        
        return {'total_commits': 0, 'is_new_contributor': True}
    
    def _extract_signals(self, commit_data: Dict) -> Dict[str, Any]:
        """Extract risk signals from commit data."""
        message = commit_data['commit']['message'].lower()
        files = commit_data.get('files', [])
        
        # Security-related keywords
        security_keywords = [
            'security', 'vulnerability', 'cve', 'exploit', 'xss', 'sql injection',
            'csrf', 'auth', 'authentication', 'authorization', 'password', 'token',
            'encryption', 'sanitize', 'escape', 'injection', 'rce', 'dos',
            'privilege', 'bypass', 'leak', 'exposure'
        ]
        
        # High-risk file patterns
        risky_files = [
            'auth', 'login', 'password', 'token', 'session', 'crypto',
            'security', 'permission', 'access', 'admin', 'sql', 'query',
            'exec', 'eval', 'deserialize', 'pickle', 'yaml.load'
        ]
        
        # Dangerous code patterns in diffs
        dangerous_patterns = [
            'eval(', 'exec(', 'pickle.loads', 'yaml.load', '__import__',
            'os.system', 'subprocess.call', 'shell=True',
            'SELECT * FROM', 'DROP TABLE', 'DELETE FROM',
            'innerHTML', 'dangerouslySetInnerHTML',
            'md5', 'sha1',  # Weak crypto
            'random.random',  # Weak randomness for security
        ]
        
        signals = {
            'security_keywords_in_message': any(kw in message for kw in security_keywords),
            'is_security_fix': any(word in message for word in ['fix', 'patch', 'hotfix', 'urgent']),
            'files_changed': len(files),
            'total_changes': commit_data['stats']['additions'] + commit_data['stats']['deletions'],
            'large_change': commit_data['stats']['additions'] + commit_data['stats']['deletions'] > 500,
            'risky_files_modified': [],
            'new_dependencies': False,
            'config_changes': False,
            'test_changes': False,
            'dangerous_code_patterns': [],
            'removes_security_checks': False,
            'adds_external_input': False,
            'modifies_crypto': False,
        }
        
        # Analyze files and diffs
        for file in files:
            filename = file['filename'].lower()
            patch = file.get('patch', '')
            
            # Check for risky files
            if any(pattern in filename for pattern in risky_files):
                signals['risky_files_modified'].append(file['filename'])
            
            # Check for dependency changes
            if any(dep in filename for dep in ['requirements.txt', 'package.json', 'pom.xml', 'go.mod']):
                signals['new_dependencies'] = True
            
            # Check for config changes
            if any(cfg in filename for cfg in ['config', 'settings', '.env', 'yaml', 'json']):
                signals['config_changes'] = True
            
            # Check for test changes
            if 'test' in filename:
                signals['test_changes'] = True
            
            # Analyze code diff
            if patch:
                # Check for dangerous patterns
                for pattern in dangerous_patterns:
                    if pattern in patch:
                        signals['dangerous_code_patterns'].append(pattern)
                
                # Check if removing security checks (lines starting with -)
                removed_lines = [line for line in patch.split('\n') if line.startswith('-') and not line.startswith('---')]
                for line in removed_lines:
                    if any(kw in line.lower() for kw in ['verify', 'check', 'validate', 'sanitize', 'escape']):
                        signals['removes_security_checks'] = True
                        break
                
                # Check if adding external input handling
                added_lines = [line for line in patch.split('\n') if line.startswith('+') and not line.startswith('+++')]
                for line in added_lines:
                    if any(kw in line.lower() for kw in ['request.', 'input(', 'raw_input', 'stdin']):
                        signals['adds_external_input'] = True
                    if any(kw in line.lower() for kw in ['encrypt', 'decrypt', 'hash', 'cipher']):
                        signals['modifies_crypto'] = True
        
        # Remove duplicates
        signals['dangerous_code_patterns'] = list(set(signals['dangerous_code_patterns']))
        
        return signals
    
    def _analyze_with_llm(
        self,
        commit_data: Dict,
        signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to analyze commit for vulnerability risk."""
        
        # Build prompt
        prompt = self._build_commit_prompt(commit_data, signals)
        
        # Get LLM response
        response = self.model.generate_content(prompt)
        
        # Parse response
        import json
        try:
            json_start = response.text.find('{')
            json_end = response.text.rfind('}') + 1
            json_str = response.text[json_start:json_end]
            result = json.loads(json_str)
            return result
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                'risk_score': 0.5,
                'risk_level': 'MEDIUM',
                'confidence': 0.3,
                'reasoning': f"Failed to parse LLM response: {response.text[:200]}",
                'risk_factors': ['Parse error'],
                'recommendations': ['Manual review required']
            }
    
    def _build_commit_prompt(
        self,
        commit_data: Dict,
        signals: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM analysis."""
        
        commit_msg = commit_data['commit']['message']
        author = commit_data['commit']['author']['name']
        files = commit_data.get('files', [])
        stats = commit_data['stats']
        
        prompt = f"""You are a security expert analyzing a commit for potential zero-day vulnerability risks.

CRITICAL: This commit has NOT been merged yet. Your job is to detect if merging this commit could introduce a vulnerability.

## Commit Information

**Repository**: {commit_data['html_url'].split('/commit/')[0]}
**Commit SHA**: {commit_data['sha'][:8]}
**Author**: {author}
**Date**: {commit_data['commit']['author']['date']}

**Commit Message**:
```
{commit_msg}
```

**Statistics**:
- Files changed: {len(files)}
- Additions: {stats['additions']}
- Deletions: {stats['deletions']}

## Risk Signals Detected

"""
        
        if signals['security_keywords_in_message']:
            prompt += "⚠️ Security-related keywords in commit message\n"
        
        if signals['risky_files_modified']:
            prompt += f"⚠️ High-risk files modified: {', '.join(signals['risky_files_modified'][:5])}\n"
        
        if signals['large_change']:
            prompt += f"⚠️ Large change ({stats['additions'] + stats['deletions']} lines)\n"
        
        if signals['new_dependencies']:
            prompt += "⚠️ Dependency changes detected\n"
        
        if signals['config_changes']:
            prompt += "⚠️ Configuration changes detected\n"
        
        if not signals['test_changes']:
            prompt += "⚠️ No test changes (risky if modifying security-sensitive code)\n"
        
        # NEW: Dangerous code patterns
        if signals.get('dangerous_code_patterns'):
            prompt += f"🚨 DANGEROUS CODE PATTERNS DETECTED: {', '.join(signals['dangerous_code_patterns'][:5])}\n"
        
        # NEW: Security checks removed
        if signals.get('removes_security_checks'):
            prompt += "🚨 REMOVES SECURITY CHECKS (verify, validate, sanitize, etc.)\n"
        
        # NEW: External input handling
        if signals.get('adds_external_input'):
            prompt += "⚠️ Adds external input handling (request, stdin, etc.)\n"
        
        # NEW: Crypto modifications
        if signals.get('modifies_crypto'):
            prompt += "⚠️ Modifies cryptographic code\n"
        
        # NEW: Author history
        author_history = signals.get('author_history', {})
        if author_history.get('is_new_contributor'):
            prompt += f"⚠️ New contributor (only {author_history.get('total_commits', 0)} commits)\n"
        elif author_history.get('is_core_maintainer'):
            prompt += f"✓ Core maintainer ({author_history.get('total_commits', 0)}+ commits)\n"
        
        prompt += "\n## Files Changed\n\n"
        for file in files[:10]:  # Limit to first 10 files
            prompt += f"- `{file['filename']}` (+{file['additions']} -{file['deletions']})\n"
        
        if len(files) > 10:
            prompt += f"... and {len(files) - 10} more files\n"
        
        # Add patch preview for risky files
        if signals['risky_files_modified']:
            prompt += "\n## Code Changes (Security-Sensitive Files)\n\n"
            for file in files[:3]:
                if file['filename'] in signals['risky_files_modified']:
                    patch = file.get('patch', '')
                    if patch:
                        prompt += f"### {file['filename']}\n```diff\n{patch[:500]}\n```\n\n"
        
        prompt += """

## Your Task

Analyze this commit and assess the risk of it introducing a zero-day vulnerability.

Consider:
1. **Authentication/Authorization**: Changes to auth logic, access control
2. **Input Validation**: Missing sanitization, injection risks
3. **Cryptography**: Weak algorithms, key management issues
4. **Configuration**: Exposed secrets, insecure defaults
5. **Dependencies**: Known vulnerable packages
6. **Logic Errors**: Race conditions, integer overflows
7. **Information Disclosure**: Logging sensitive data, error messages

Respond with JSON:
{
    "risk_score": 0.0-1.0,
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of why this commit is risky",
    "risk_factors": ["Factor 1", "Factor 2", ...],
    "recommendations": ["Action 1", "Action 2", ...]
}

Be conservative - false positives are better than missing a real vulnerability.
"""
        
        return prompt


__all__ = ['CommitAnalyzer', 'CommitRiskResult']
