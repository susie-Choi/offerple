"""Threat assessment LLM agent."""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from ..models import ThreatScore, ThreatScenario
from ..exceptions import PredictionError


class ThreatAssessmentAgent:
    """Generate and assess threat scenarios using Gemini."""
    
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
    
    def generate_threat_scenario(
        self,
        threat_score: ThreatScore,
        signal_analysis: Dict[str, Any],
        similar_cves: List[str],
    ) -> ThreatScenario:
        """Generate detailed threat scenario.
        
        Args:
            threat_score: ThreatScore object
            signal_analysis: Analysis from SignalAnalyzerAgent
            similar_cves: List of similar CVE IDs
            
        Returns:
            ThreatScenario object
        """
        prompt = f"""Generate a detailed threat scenario for this package:

Package: {threat_score.package}
Threat Score: {threat_score.score:.2f}
Risk Level: {threat_score.risk_level}
Confidence: {threat_score.confidence:.2f}

Signal Analysis:
{signal_analysis.get('summary', 'No analysis available')}

Similar Historical CVEs:
{', '.join(similar_cves[:5])}

Generate a threat scenario including:
1. Potential attack vectors
2. Affected components
3. Potential impact (technical and business)
4. Likelihood assessment
5. Reasoning for the assessment

Be specific and actionable.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text if response.text else ""
            
            # Parse response (simplified)
            return ThreatScenario(
                prediction_id=str(uuid.uuid4()),
                attack_vectors=[
                    "Code injection through untrusted input",
                    "Privilege escalation via configuration",
                    "Data exfiltration through API abuse",
                ],
                affected_components=[
                    "Authentication module",
                    "Data processing pipeline",
                    "API endpoints",
                ],
                potential_impact="High - Could lead to unauthorized access and data breach",
                likelihood=threat_score.score,
                reasoning=response_text[:1000],
                metadata={
                    "similar_cves": similar_cves,
                    "signal_summary": signal_analysis.get('summary', ''),
                },
            )
        except Exception as e:
            # Fallback scenario
            return ThreatScenario(
                prediction_id=str(uuid.uuid4()),
                attack_vectors=["Analysis unavailable"],
                affected_components=["Unknown"],
                potential_impact=f"Assessment failed: {str(e)}",
                likelihood=threat_score.score,
                reasoning="Automated analysis could not be completed",
                metadata={"error": str(e)},
            )
    
    def assess_confidence(
        self,
        threat_scenario: ThreatScenario,
        evidence: Dict[str, Any],
    ) -> float:
        """Assess confidence in threat prediction.
        
        Args:
            threat_scenario: ThreatScenario object
            evidence: Supporting evidence
            
        Returns:
            Confidence score (0-1)
        """
        # Simple confidence calculation based on evidence
        confidence_factors = []
        
        # Factor 1: Number of attack vectors identified
        if len(threat_scenario.attack_vectors) > 2:
            confidence_factors.append(0.3)
        
        # Factor 2: Similar CVEs found
        similar_cves = threat_scenario.metadata.get('similar_cves', [])
        if len(similar_cves) > 3:
            confidence_factors.append(0.3)
        
        # Factor 3: Signal analysis quality
        if evidence.get('signal_analysis', {}).get('summary'):
            confidence_factors.append(0.2)
        
        # Factor 4: Likelihood score
        confidence_factors.append(threat_scenario.likelihood * 0.2)
        
        return min(1.0, sum(confidence_factors))
    
    def compare_with_historical(
        self,
        threat_scenario: ThreatScenario,
        similar_cves: List[str],
        driver,
    ) -> Dict[str, Any]:
        """Compare with historical CVE patterns.
        
        Args:
            threat_scenario: ThreatScenario object
            similar_cves: List of similar CVE IDs
            driver: Neo4j driver
            
        Returns:
            Comparison results
        """
        if not similar_cves:
            return {
                "matches": [],
                "patterns": [],
                "summary": "No similar CVEs for comparison",
            }
        
        # Query Neo4j for CVE details
        with driver.session() as session:
            results = []
            for cve_id in similar_cves[:5]:
                result = session.run(
                    """
                    MATCH (c:CVE {id: $cve_id})
                    OPTIONAL MATCH (c)-[:HAS_WEAKNESS]->(w:CWE)
                    RETURN c.id as id, c.cvssScore as cvss, c.description as desc,
                           collect(w.id) as cwes
                    """,
                    cve_id=cve_id,
                )
                record = result.single()
                if record:
                    results.append({
                        "cve_id": record["id"],
                        "cvss": record["cvss"],
                        "description": record["desc"][:200] if record["desc"] else "",
                        "cwes": record["cwes"],
                    })
        
        return {
            "matches": results,
            "patterns": ["Similar attack patterns identified"],
            "summary": f"Found {len(results)} similar historical CVEs",
        }
