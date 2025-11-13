"""
Oracle - LLM-based vulnerability prediction engine with RAG.
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import google.generativeai as genai
from dataclasses import dataclass
import json
import logging
from neo4j import GraphDatabase
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of vulnerability prediction."""
    cve_id: Optional[str]
    package: str
    risk_score: float  # 0-1
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float  # 0-1
    reasoning: str
    recommendations: List[str]
    predicted_at: datetime
    signals_analyzed: Dict[str, Any]


class VulnerabilityOracle:
    """
    LLM-based oracle that predicts vulnerability risks with RAG.
    
    Uses Gemini to analyze multiple signals and Neo4j for RAG context.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gemini-2.5-flash",
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        use_rag: bool = True,
    ):
        """
        Initialize the oracle.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Gemini model to use
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            use_rag: Whether to use RAG with Neo4j
        """
        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY must be set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.use_rag = use_rag
        
        # Initialize Jinja2 template environment
        template_dir = Path(__file__).parent / 'prompts'
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.prediction_template = self.jinja_env.get_template('prediction.jinja2')
        self.analysis_template = self.jinja_env.get_template('analysis.jinja2')
        
        # Initialize Neo4j connection for RAG and data fetching
        self.hub_query = None
        if use_rag:
            neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI")
            neo4j_user = neo4j_user or os.getenv("NEO4J_USERNAME", "neo4j")
            neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
            
            if neo4j_uri and neo4j_password:
                try:
                    self.neo4j_driver = GraphDatabase.driver(
                        neo4j_uri, 
                        auth=(neo4j_user, neo4j_password)
                    )
                    self.neo4j_driver.verify_connectivity()
                    
                    # Initialize HubQuery for data fetching
                    from ..hub import HubQuery
                    self.hub_query = HubQuery(self.neo4j_driver)
                except Exception as e:
                    print(f"Warning: Could not connect to Neo4j: {e}")
                    self.use_rag = False
                    self.neo4j_driver = None
                    self.hub_query = None
            else:
                print("Warning: Neo4j credentials not found, RAG disabled")
                self.use_rag = False
                self.neo4j_driver = None
                self.hub_query = None
        else:
            self.neo4j_driver = None
            self.hub_query = None
    
    def predict(
        self,
        package: str,
        github_signals: Optional[Dict] = None,
        days_back: int = 30,
        auto_fetch: bool = True,
    ) -> PredictionResult:
        """
        Predict future vulnerability risk based on current signals.
        
        This is TRUE PREDICTION - analyzing current behavior to predict future CVEs.
        NOT post-mortem analysis of known CVEs.
        
        Args:
            package: Package name (e.g., "django/django")
            github_signals: GitHub activity signals (commits, PRs, issues)
            days_back: Days of history to analyze
            auto_fetch: Automatically fetch GitHub signals if not provided
        
        Returns:
            PredictionResult with risk assessment
        """
        # Auto-fetch GitHub signals if not provided
        if auto_fetch and not github_signals:
            if self.hub_query:
                github_signals = self.hub_query.get_github_signals(package, days_back)
            else:
                # TODO: Fetch from GitHub API directly
                print(f"Warning: No GitHub signals provided and Hub not available")
        
        # Get RAG context from Neo4j (historical patterns only)
        rag_context = None
        if self.use_rag and self.hub_query:
            rag_context = self._get_rag_context(package, None)
        
        # Build prompt for LLM with RAG context
        prompt = self._build_prediction_prompt(
            package, github_signals, rag_context
        )
        
        # Get LLM response
        response = self.model.generate_content(prompt)
        
        # Parse response
        result = self._parse_prediction_response(
            response.text, package, github_signals
        )
        
        return result
    
    def analyze_cve(
        self,
        package: str,
        cve_id: str,
        auto_fetch: bool = True,
    ) -> PredictionResult:
        """
        Analyze an existing CVE (post-mortem analysis).
        
        This is DIFFERENT from prediction - this analyzes known CVEs.
        
        Args:
            package: Package name
            cve_id: CVE identifier
            auto_fetch: Fetch data from hub
        
        Returns:
            PredictionResult with analysis
        """
        cve_data = None
        epss_data = None
        kev_data = None
        
        # Fetch CVE data from Hub
        if auto_fetch and self.hub_query:
            cve_data = self.hub_query.get_cve_data(cve_id)
            epss_data = self.hub_query.get_epss_data(cve_id)
            kev_data = self.hub_query.get_kev_data(cve_id)
        
        # Get RAG context
        rag_context = None
        if self.use_rag and self.hub_query:
            rag_context = self._get_rag_context(package, cve_data)
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            package, cve_data, epss_data, kev_data, rag_context
        )
        
        # Get LLM response
        response = self.model.generate_content(prompt)
        
        # Parse response
        result = self._parse_prediction_response(
            response.text, package, None, cve_id=cve_id
        )
        
        return result
    
    def _get_rag_context(self, package: str, cve_data: Optional[Dict]) -> Optional[Dict]:
        """
        Get relevant context from Neo4j for RAG.
        
        Retrieves similar CVEs, patterns, and historical data.
        """
        if not self.hub_query:
            return None
        
        try:
            with self.hub_query.driver.session() as session:
                # Query 1: Get similar CVEs by CWE
                similar_cves = []
                if cve_data and cve_data.get('cwe'):
                    result = session.run("""
                        MATCH (c:CVE)-[:HAS_CWE]->(cwe:CWE {id: $cwe_id})
                        RETURN c.id as cve_id, c.description as description, 
                               c.cvss_score as cvss, c.severity as severity
                        ORDER BY c.published DESC
                        LIMIT 5
                    """, cwe_id=cve_data.get('cwe'))
                    similar_cves = [dict(record) for record in result]
                
                # Query 2: Get package history
                package_history = []
                result = session.run("""
                    MATCH (p:Package {name: $package})-[:HAS_CVE]->(c:CVE)
                    RETURN c.id as cve_id, c.description as description,
                           c.cvss_score as cvss, c.published as published
                    ORDER BY c.published DESC
                    LIMIT 10
                """, package=package)
                package_history = [dict(record) for record in result]
                
                # Query 3: Get EPSS trends for similar CVEs
                epss_trends = []
                if similar_cves:
                    cve_ids = [cve['cve_id'] for cve in similar_cves[:3]]
                    result = session.run("""
                        MATCH (c:CVE)-[:HAS_EPSS]->(e:EPSS)
                        WHERE c.id IN $cve_ids
                        RETURN c.id as cve_id, e.score as epss_score, 
                               e.percentile as percentile
                    """, cve_ids=cve_ids)
                    epss_trends = [dict(record) for record in result]
                
                # Query 4: Get dependency risks
                dependency_risks = None
                try:
                    dependency_risks = self.hub_query.get_dependency_risks(package, depth=2)
                except Exception as e:
                    logger.warning(f"Could not get dependency risks: {e}")
                
                # Query 5: Get package popularity
                popularity = None
                try:
                    popularity = self.hub_query.get_package_popularity(package)
                except Exception as e:
                    logger.warning(f"Could not get package popularity: {e}")
                
                # Query 6: Get maintainer history
                maintainer_history = []
                try:
                    maintainer_history = self.hub_query.get_maintainer_history(package)
                except Exception as e:
                    logger.warning(f"Could not get maintainer history: {e}")
                
                return {
                    'similar_cves': similar_cves,
                    'package_history': package_history,
                    'epss_trends': epss_trends,
                    'dependency_risks': dependency_risks,
                    'popularity': popularity,
                    'maintainer_history': maintainer_history,
                }
        except Exception as e:
            print(f"Warning: RAG context retrieval failed: {e}")
            return None
    
    def _build_prediction_prompt(
        self,
        package: str,
        github_signals: Optional[Dict],
        rag_context: Optional[Dict],
    ) -> str:
        """Build prompt for TRUE PREDICTION based on current signals."""
        return self.prediction_template.render(
            package=package,
            github_signals=github_signals,
            rag_context=rag_context
        )
    
    def _build_prediction_prompt_old(
        self,
        package: str,
        github_signals: Optional[Dict],
        rag_context: Optional[Dict],
    ) -> str:
        """Build prompt for TRUE PREDICTION based on current signals (OLD VERSION)."""
        prompt = f"""You are a cybersecurity oracle predicting FUTURE vulnerabilities.

Package: {package}

IMPORTANT: You are predicting FUTURE vulnerability risks based on CURRENT behavior patterns.
This is NOT post-mortem analysis. Analyze current signals to predict if a CVE will occur.

"""
        
        # Add RAG context first (historical patterns for reference)
        if rag_context:
            prompt += """
## Historical Context (from Knowledge Base)

"""
            if rag_context.get('similar_cves'):
                prompt += f"""
### Similar CVEs (by CWE):
"""
                for cve in rag_context['similar_cves'][:3]:
                    prompt += f"""
- {cve['cve_id']}: CVSS {cve.get('cvss', 'N/A')}, {cve.get('severity', 'N/A')}
  Description: {cve.get('description', 'N/A')[:200]}...
"""
            
            if rag_context.get('package_history'):
                prompt += f"""
### Package Vulnerability History:
- Total past CVEs: {len(rag_context['package_history'])}
"""
                for cve in rag_context['package_history'][:3]:
                    prompt += f"""
- {cve['cve_id']}: CVSS {cve.get('cvss', 'N/A')} ({cve.get('published', 'N/A')})
"""
            
            if rag_context.get('epss_trends'):
                prompt += f"""
### EPSS Trends for Similar CVEs:
"""
                for trend in rag_context['epss_trends']:
                    prompt += f"""
- {trend['cve_id']}: EPSS {trend.get('epss_score', 'N/A')} (percentile: {trend.get('percentile', 'N/A')})
"""
            
            # Add dependency risks
            if rag_context.get('dependency_risks'):
                dep_risks = rag_context['dependency_risks']
                prompt += f"""
### Dependency Chain Risks:
- Total dependencies: {dep_risks.get('total_dependencies', 0)}
- Vulnerable dependencies: {len(dep_risks.get('vulnerable_dependencies', []))}
- Vulnerability ratio: {dep_risks.get('vulnerability_ratio', 0):.1%}
"""
                for dep in dep_risks.get('vulnerable_dependencies', [])[:3]:
                    prompt += f"""
- {dep['dependency']}: {dep['cve_count']} CVEs (max CVSS: {dep.get('max_cvss', 'N/A')})
"""
            
            # Add popularity metrics
            if rag_context.get('popularity'):
                pop = rag_context['popularity']
                prompt += f"""
### Package Popularity:
- Downloads (last month): {pop.get('downloads_last_month', 0):,}
- Total releases: {pop.get('total_releases', 0)}
- GitHub stars: {pop.get('stars', 0):,}
"""
            
            # Add maintainer history
            if rag_context.get('maintainer_history'):
                prompt += f"""
### Maintainer's Other Packages:
"""
                for pkg in rag_context['maintainer_history'][:3]:
                    prompt += f"""
- {pkg['package']}: {pkg['cve_count']} CVEs
"""

        
        # Add CVE data
        if cve_data:
            prompt += f"""
## CVE Information
- CVE ID: {cve_data.get('id', 'N/A')}
- Description: {cve_data.get('description', 'N/A')}
- CVSS Score: {cve_data.get('cvss_score', 'N/A')}
- Severity: {cve_data.get('severity', 'N/A')}
- Published: {cve_data.get('published', 'N/A')}
- CWE: {cve_data.get('cwe', 'N/A')}
"""
        
        # Add CURRENT GitHub signals (the key prediction input!)
        if github_signals:
            prompt += f"""
## CURRENT GitHub Activity Signals (Last {github_signals.get('days', 30)} days)

### Commit Activity:
- Total commits: {github_signals.get('commit_count', 0)}
- Security-related commits: {github_signals.get('security_commits', 0)}
- Unusual commit patterns: {github_signals.get('unusual_patterns', 'None detected')}
- Commit frequency spike: {github_signals.get('commit_spike', False)}

### Issue Activity:
- Open issues: {github_signals.get('open_issues', 0)}
- Security-labeled issues: {github_signals.get('security_issues', 0)}
- Critical issues: {github_signals.get('critical_issues', 0)}
- Issue discussion intensity: {github_signals.get('discussion_intensity', 'Normal')}

### Pull Request Activity:
- Recent PRs: {github_signals.get('pr_count', 0)}
- Security-related PRs: {github_signals.get('security_prs', 0)}
- Emergency fixes: {github_signals.get('emergency_fixes', 0)}

### Developer Behavior:
- Active contributors: {github_signals.get('contributors', 0)}
- New contributors: {github_signals.get('new_contributors', 0)}
- Late-night commits: {github_signals.get('late_night_commits', 0)}
- Weekend activity: {github_signals.get('weekend_activity', 'Normal')}

### Code Changes:
- Files modified: {github_signals.get('files_modified', 0)}
- Security-sensitive files: {github_signals.get('security_files', 0)}
- Authentication/auth changes: {github_signals.get('auth_changes', False)}
- Database query changes: {github_signals.get('db_changes', False)}
"""
        else:
            prompt += """
## CURRENT GitHub Activity Signals
⚠️ No GitHub signals provided. Prediction will be based on historical patterns only.
"""
        
        prompt += """

Based on CURRENT signals and historical patterns, predict the likelihood of a FUTURE vulnerability:

Provide a JSON response with:
1. risk_score: Float 0-1 (probability a CVE will be discovered in next 30-90 days)
2. risk_level: One of [LOW, MEDIUM, HIGH, CRITICAL]
3. confidence: Float 0-1 (how confident you are in this prediction)
4. reasoning: Explain WHY you think a vulnerability might occur based on current behavior
5. recommendations: 3-5 proactive actions to prevent potential vulnerabilities

IMPORTANT: You are predicting FUTURE risks, not analyzing known CVEs.
Focus on suspicious patterns, unusual activity, and risk indicators.

Respond ONLY with valid JSON:
{
    "risk_score": 0.0,
    "risk_level": "LOW",
    "confidence": 0.0,
    "reasoning": "...",
    "recommendations": ["...", "..."]
}
"""
        
        return prompt
    
    def _build_analysis_prompt(
        self,
        package: str,
        cve_data: Optional[Dict],
        epss_data: Optional[Dict],
        kev_data: Optional[Dict],
        rag_context: Optional[Dict],
    ) -> str:
        """Build prompt for CVE post-mortem analysis."""
        return self.analysis_template.render(
            package=package,
            cve_data=cve_data,
            epss_data=epss_data,
            kev_data=kev_data,
            rag_context=rag_context
        )
    
    def _build_analysis_prompt_old(
        self,
        package: str,
        cve_data: Optional[Dict],
        epss_data: Optional[Dict],
        kev_data: Optional[Dict],
        rag_context: Optional[Dict],
    ) -> str:
        """Build prompt for CVE post-mortem analysis (OLD VERSION)."""
        prompt = f"""You are a cybersecurity expert analyzing an existing CVE.

Package: {package}

This is POST-MORTEM ANALYSIS of a known vulnerability.

"""
        
        if cve_data:
            prompt += f"""
## CVE Information
- CVE ID: {cve_data.get('id', 'N/A')}
- Description: {cve_data.get('description', 'N/A')}
- CVSS Score: {cve_data.get('cvss_score', 'N/A')}
- Severity: {cve_data.get('severity', 'N/A')}
- CWE: {cve_data.get('cwe', 'N/A')}
"""
        
        if epss_data:
            prompt += f"""
## EPSS Score
- Exploit Probability: {epss_data.get('epss', 'N/A')}
- Percentile: {epss_data.get('percentile', 'N/A')}
"""
        
        if kev_data and kev_data.get('in_kev'):
            prompt += f"""
## CISA KEV Status
- In KEV Catalog: Yes
- Date Added: {kev_data.get('date_added', 'N/A')}
"""
        
        prompt += """

Analyze this CVE and provide:
1. risk_score: Current exploitation risk (0-1)
2. risk_level: Current threat level
3. confidence: Your confidence in the assessment
4. reasoning: Why this CVE is dangerous
5. recommendations: Immediate mitigation steps

Respond ONLY with valid JSON:
{
    "risk_score": 0.0,
    "risk_level": "LOW",
    "confidence": 0.0,
    "reasoning": "...",
    "recommendations": ["...", "..."]
}
"""
        return prompt
    
    def _parse_prediction_response(
        self,
        response_text: str,
        package: str,
        github_signals: Optional[Dict],
        cve_id: Optional[str] = None,
    ) -> PredictionResult:
        """Parse LLM response into PredictionResult."""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            
            data = json.loads(json_str)
            
            return PredictionResult(
                cve_id=cve_id,
                package=package,
                risk_score=float(data['risk_score']),
                risk_level=data['risk_level'],
                confidence=float(data['confidence']),
                reasoning=data['reasoning'],
                recommendations=data['recommendations'],
                predicted_at=datetime.utcnow(),
                signals_analyzed={
                    'github': bool(github_signals),
                    'rag': bool(self.use_rag),
                }
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback if parsing fails
            return PredictionResult(
                cve_id=cve_id,
                package=package,
                risk_score=0.5,
                risk_level="MEDIUM",
                confidence=0.3,
                reasoning=f"Failed to parse LLM response: {str(e)}. Raw response: {response_text[:200]}",
                recommendations=["Review manually", "Check LLM response format"],
                predicted_at=datetime.utcnow(),
                signals_analyzed={
                    'github': bool(github_signals),
                    'rag': bool(self.use_rag),
                }
            )
