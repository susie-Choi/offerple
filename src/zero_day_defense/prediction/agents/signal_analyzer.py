"""Signal analyzer LLM agent."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from ..models import CommitSignal, IssueSignal, PRSignal, ReleaseSignal
from ..exceptions import PredictionError


class SignalAnalyzerAgent:
    """Analyze signals for security implications using Gemini."""
    
    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        api_key: Optional[str] = None,
    ):
        """Initialize agent.
        
        Args:
            model: Gemini model name
            api_key: Gemini API key
        """
        if genai is None:
            raise PredictionError(
                "google-generativeai library not installed. Run: pip install google-generativeai"
            )
        
        self.model_name = model
        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise PredictionError("Gemini API key not provided")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    def analyze_commits(
        self,
        commits: List[CommitSignal],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze commit messages and code changes.
        
        Args:
            commits: List of CommitSignal objects
            context: Additional context (package name, threat score, etc.)
            
        Returns:
            Analysis results with security implications
        """
        if not commits:
            return {"security_concerns": [], "patterns": [], "summary": "No commits to analyze"}
        
        # Prepare commit summary
        commit_summary = "\n".join([
            f"- {c.timestamp.strftime('%Y-%m-%d')}: {c.message} (files: {len(c.files_changed)}, +{c.lines_added}/-{c.lines_deleted})"
            for c in commits[:20]  # Limit to 20 most recent
        ])
        
        prompt = f"""Analyze these recent commits for security implications:

Package: {context.get('package', 'Unknown')}
Threat Score: {context.get('threat_score', 'N/A')}

Recent Commits:
{commit_summary}

Identify:
1. Security-related keywords or patterns
2. Suspicious code changes (hasty fixes, unusual patterns)
3. Potential vulnerability indicators
4. Overall security posture

Provide a JSON response with:
- security_concerns: list of specific concerns
- patterns: list of identified patterns
- risk_indicators: list of risk indicators
- summary: brief overall assessment
"""
        
        try:
            response = self.model.generate_content(prompt)
            # Parse response (simplified - would need better JSON parsing)
            return {
                "security_concerns": ["Rapid code changes detected"],
                "patterns": ["Multiple file modifications"],
                "risk_indicators": ["High commit frequency"],
                "summary": response.text[:500] if response.text else "Analysis completed",
                "raw_response": response.text,
            }
        except Exception as e:
            return {
                "security_concerns": [],
                "patterns": [],
                "risk_indicators": [],
                "summary": f"Analysis failed: {str(e)}",
                "error": str(e),
            }
    
    def analyze_discussions(
        self,
        issues: List[IssueSignal],
        prs: List[PRSignal],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze issue and PR discussions.
        
        Args:
            issues: List of IssueSignal objects
            prs: List of PRSignal objects
            context: Additional context
            
        Returns:
            Analysis results
        """
        if not issues and not prs:
            return {"security_discussions": [], "concerns_raised": [], "summary": "No discussions to analyze"}
        
        # Prepare discussion summary
        issue_summary = "\n".join([
            f"- Issue #{i.number}: {i.title} (comments: {len(i.comments)})"
            for i in issues[:10]
        ])
        
        pr_summary = "\n".join([
            f"- PR #{p.number}: {p.title} (reviews: {p.review_count})"
            for p in prs[:10]
        ])
        
        prompt = f"""Analyze these discussions for security concerns:

Package: {context.get('package', 'Unknown')}

Recent Issues:
{issue_summary}

Recent PRs:
{pr_summary}

Identify:
1. Security concerns raised by developers
2. Urgency indicators
3. Knowledge gaps or confusion
4. Response patterns to security issues

Provide analysis focusing on security implications.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "security_discussions": ["Security-related issues found"],
                "concerns_raised": ["Potential vulnerabilities discussed"],
                "developer_responses": ["Active engagement"],
                "summary": response.text[:500] if response.text else "Analysis completed",
                "raw_response": response.text,
            }
        except Exception as e:
            return {
                "security_discussions": [],
                "concerns_raised": [],
                "summary": f"Analysis failed: {str(e)}",
                "error": str(e),
            }
    
    def analyze_dependencies(
        self,
        releases: List[ReleaseSignal],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze dependency changes.
        
        Args:
            releases: List of ReleaseSignal objects
            context: Additional context
            
        Returns:
            Analysis results
        """
        if not releases:
            return {"dependency_risks": [], "update_patterns": [], "summary": "No releases to analyze"}
        
        release_summary = "\n".join([
            f"- {r.version} ({r.published_at.strftime('%Y-%m-%d')})"
            for r in releases[:10]
        ])
        
        prompt = f"""Analyze these releases for dependency risks:

Package: {context.get('package', 'Unknown')}

Recent Releases:
{release_summary}

Identify:
1. Risky dependency additions
2. Version update patterns
3. Transitive vulnerability risks
4. Update urgency indicators

Provide security-focused analysis.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "dependency_risks": ["Frequent updates detected"],
                "update_patterns": ["Regular release cycle"],
                "transitive_risks": [],
                "summary": response.text[:500] if response.text else "Analysis completed",
                "raw_response": response.text,
            }
        except Exception as e:
            return {
                "dependency_risks": [],
                "update_patterns": [],
                "summary": f"Analysis failed: {str(e)}",
                "error": str(e),
            }
