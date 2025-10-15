"""Recommendation LLM agent."""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from ..models import ThreatScenario, Recommendations
from ..exceptions import PredictionError


class RecommendationAgent:
    """Provide mitigation and monitoring recommendations using Gemini."""
    
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
                "google-generativeai library not installed"
            )
        
        self.model_name = model
        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise PredictionError("Gemini API key not provided")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    def generate_recommendations(
        self,
        threat_scenario: ThreatScenario,
        package_context: Dict[str, Any],
    ) -> Recommendations:
        """Generate actionable recommendations.
        
        Args:
            threat_scenario: ThreatScenario object
            package_context: Context about the package
            
        Returns:
            Recommendations object
        """
        prompt = f"""Generate security recommendations for this threat scenario:

Package: {package_context.get('package', 'Unknown')}
Risk Level: {package_context.get('risk_level', 'Unknown')}

Threat Scenario:
Attack Vectors: {', '.join(threat_scenario.attack_vectors)}
Affected Components: {', '.join(threat_scenario.affected_components)}
Potential Impact: {threat_scenario.potential_impact}
Likelihood: {threat_scenario.likelihood:.2f}

Provide:
1. Immediate actions (urgent steps to take now)
2. Monitoring strategy (what to watch for)
3. Mitigation options (how to reduce risk)
4. Alternative packages (safer alternatives if available)
5. Timeline (recommended action timeline)

Be specific and actionable.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text if response.text else ""
            
            return Recommendations(
                scenario_id=threat_scenario.prediction_id,
                immediate_actions=[
                    "Review recent code changes for security issues",
                    "Enable additional logging and monitoring",
                    "Conduct security audit of affected components",
                    "Update to latest stable version if available",
                ],
                monitoring_strategy="Monitor for unusual activity patterns, failed authentication attempts, and unexpected API calls. Set up alerts for security-related events.",
                mitigation_options=[
                    "Implement input validation and sanitization",
                    "Apply principle of least privilege",
                    "Enable security headers and CORS policies",
                    "Conduct penetration testing",
                ],
                alternative_packages=[
                    "Consider well-maintained alternatives with better security track record",
                ],
                timeline="Immediate: Review and audit (24-48 hours). Short-term: Implement mitigations (1-2 weeks). Long-term: Consider alternatives (1 month)",
                metadata={
                    "generated_from": "Gemini AI",
                    "full_response": response_text[:1000],
                },
            )
        except Exception as e:
            # Fallback recommendations
            return Recommendations(
                scenario_id=threat_scenario.prediction_id,
                immediate_actions=[
                    "Review package security advisories",
                    "Monitor for updates",
                ],
                monitoring_strategy="Enable basic security monitoring",
                mitigation_options=[
                    "Follow security best practices",
                ],
                alternative_packages=[],
                timeline="As soon as possible",
                metadata={"error": str(e)},
            )
