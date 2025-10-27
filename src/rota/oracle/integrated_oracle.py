"""
Integrated Oracle - Combines all analysis modules for comprehensive risk assessment.

This is the main entry point for vulnerability prediction, combining:
- Commit-level analysis
- Project-level signals
- Supply chain impact
- Historical CVE patterns (RAG)
- Package popularity
"""
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from .commit_analyzer import CommitAnalyzer, CommitRiskResult
from .predictor import VulnerabilityOracle, PredictionResult
from ..hub.supply_chain import SupplyChainAnalyzer, ImpactAnalysis

logger = logging.getLogger(__name__)


@dataclass
class IntegratedRiskAssessment:
    """Comprehensive risk assessment combining all signals."""
    repository: str
    overall_risk_score: float  # 0-1
    overall_risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float  # 0-1
    
    # Component scores
    commit_risk_score: float
    project_risk_score: float
    supply_chain_risk_score: float
    
    # Detailed analysis
    high_risk_commits: List[CommitRiskResult]
    project_prediction: PredictionResult
    supply_chain_impact: Optional[ImpactAnalysis]
    
    # Combined reasoning
    reasoning: str
    risk_factors: List[str]
    recommendations: List[str]
    
    # Metadata
    analyzed_at: datetime
    alert_priority: str  # CRITICAL, HIGH, MEDIUM, LOW


class IntegratedOracle:
    """
    Integrated Oracle that combines all analysis modules.
    
    This is the main interface for comprehensive vulnerability prediction.
    """
    
    def __init__(
        self,
        github_token: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        neo4j_uri: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        use_rag: bool = True
    ):
        """
        Initialize integrated oracle.
        
        Args:
            github_token: GitHub API token
            gemini_api_key: Gemini API key
            neo4j_uri: Neo4j connection URI
            neo4j_password: Neo4j password
            use_rag: Whether to use RAG with Neo4j
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        # Initialize sub-modules
        self.commit_analyzer = CommitAnalyzer(
            github_token=self.github_token,
            gemini_api_key=self.gemini_api_key
        )
        
        self.project_oracle = VulnerabilityOracle(
            api_key=self.gemini_api_key,
            neo4j_uri=neo4j_uri,
            neo4j_password=neo4j_password,
            use_rag=use_rag
        )
        
        self.supply_chain = SupplyChainAnalyzer(
            neo4j_uri=neo4j_uri,
            neo4j_password=neo4j_password,
            github_token=self.github_token
        )
    
    def assess_risk(
        self,
        repository: str,
        days_back: int = 7,
        max_commits_to_analyze: int = 10,
        analyze_supply_chain: bool = True
    ) -> IntegratedRiskAssessment:
        """
        Perform comprehensive risk assessment.
        
        Args:
            repository: Repository in format "owner/repo"
            days_back: Days of history to analyze
            max_commits_to_analyze: Maximum number of commits to analyze
            analyze_supply_chain: Whether to analyze supply chain impact
            
        Returns:
            IntegratedRiskAssessment with comprehensive analysis
        """
        logger.info(f"Starting integrated risk assessment for {repository}")
        
        # ====================================================================
        # PHASE 1: Collect Recent Commits
        # ====================================================================
        logger.info("Phase 1: Analyzing recent commits...")
        
        import requests
        headers = {"Authorization": f"Bearer {self.github_token}"}
        response = requests.get(
            f"https://api.github.com/repos/{repository}/commits",
            headers=headers,
            params={"per_page": max_commits_to_analyze}
        )
        
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch commits: {response.status_code}")
        
        commits = response.json()
        
        # Analyze each commit
        commit_results = []
        high_risk_commits = []
        
        for commit in commits:
            try:
                result = self.commit_analyzer.analyze_commit(
                    repository,
                    commit['sha']
                )
                commit_results.append(result)
                
                if result.risk_score >= 0.5:
                    high_risk_commits.append(result)
                    
            except Exception as e:
                logger.warning(f"Failed to analyze commit {commit['sha'][:8]}: {e}")
        
        # Calculate average commit risk
        if commit_results:
            commit_risk_score = sum(r.risk_score for r in commit_results) / len(commit_results)
        else:
            commit_risk_score = 0.0
        
        logger.info(f"Analyzed {len(commit_results)} commits, {len(high_risk_commits)} high-risk")
        
        # ====================================================================
        # PHASE 2: Project-level Prediction
        # ====================================================================
        logger.info("Phase 2: Project-level prediction...")
        
        # Collect GitHub signals
        from ..spokes.github import GitHubSignalsCollector
        github_collector = GitHubSignalsCollector(token=self.github_token)
        
        collection_result = github_collector.collect(repository, days_back=days_back)
        
        # Load signals
        import json
        with open(collection_result['output_file'], 'r') as f:
            github_signals = json.loads(f.readline())
        
        # Add commit analysis results to signals
        github_signals['recent_commit_analysis'] = {
            'total_analyzed': len(commit_results),
            'high_risk_count': len(high_risk_commits),
            'average_risk_score': commit_risk_score,
            'max_risk_score': max(r.risk_score for r in commit_results) if commit_results else 0.0
        }
        
        # Get project prediction
        project_prediction = self.project_oracle.predict(
            repository,
            github_signals=github_signals,
            auto_fetch=False
        )
        
        logger.info(f"Project risk: {project_prediction.risk_level} ({project_prediction.risk_score:.2f})")
        
        # ====================================================================
        # PHASE 3: Supply Chain Impact
        # ====================================================================
        supply_chain_impact = None
        supply_chain_risk_score = 0.0
        
        if analyze_supply_chain:
            logger.info("Phase 3: Supply chain analysis...")
            
            try:
                # Extract package name
                package_name = repository.split('/')[-1].lower()
                
                # Build dependency graph
                graph = self.supply_chain.build_dependency_graph(package_name, "pypi")
                
                # Get popularity
                popularity = graph.get('popularity', {})
                downloads = popularity.get('downloads_last_month', 0)
                
                # Calculate supply chain risk
                # Higher downloads = higher impact if vulnerable
                if downloads > 10_000_000:  # 10M+ downloads
                    supply_chain_risk_score = 0.3
                elif downloads > 1_000_000:  # 1M+ downloads
                    supply_chain_risk_score = 0.2
                elif downloads > 100_000:  # 100K+ downloads
                    supply_chain_risk_score = 0.1
                else:
                    supply_chain_risk_score = 0.05
                
                # Get impact analysis
                supply_chain_impact = self.supply_chain.analyze_impact(
                    package_name,
                    "pypi",
                    max_depth=2
                )
                
                logger.info(f"Supply chain risk: {supply_chain_risk_score:.2f} (downloads: {downloads:,})")
                
            except Exception as e:
                logger.warning(f"Supply chain analysis failed: {e}")
        
        # ====================================================================
        # PHASE 4: Combine All Signals
        # ====================================================================
        logger.info("Phase 4: Combining all signals...")
        
        # Weighted combination
        # - Commit risk: 40% (most direct indicator)
        # - Project risk: 40% (overall patterns)
        # - Supply chain: 20% (impact multiplier)
        overall_risk_score = (
            commit_risk_score * 0.4 +
            project_prediction.risk_score * 0.4 +
            supply_chain_risk_score * 0.2
        )
        
        # Boost if high-risk commits detected
        if high_risk_commits:
            overall_risk_score = min(1.0, overall_risk_score + 0.1 * len(high_risk_commits))
        
        # Determine risk level
        if overall_risk_score >= 0.7:
            overall_risk_level = "CRITICAL"
            alert_priority = "🚨 CRITICAL"
        elif overall_risk_score >= 0.5:
            overall_risk_level = "HIGH"
            alert_priority = "⚠️  HIGH"
        elif overall_risk_score >= 0.3:
            overall_risk_level = "MEDIUM"
            alert_priority = "⚡ MEDIUM"
        else:
            overall_risk_level = "LOW"
            alert_priority = "✓ LOW"
        
        # Combine reasoning
        reasoning = self._build_combined_reasoning(
            commit_results,
            high_risk_commits,
            project_prediction,
            supply_chain_impact
        )
        
        # Combine risk factors
        risk_factors = []
        if high_risk_commits:
            risk_factors.append(f"{len(high_risk_commits)} high-risk commits detected")
        if project_prediction.risk_score >= 0.5:
            risk_factors.append(f"Project-level risk: {project_prediction.risk_level}")
        if supply_chain_risk_score >= 0.2:
            risk_factors.append("High supply chain impact (popular package)")
        
        # Add specific risk factors from commits
        for commit in high_risk_commits[:3]:
            for factor in commit.risk_factors[:2]:
                risk_factors.append(f"Commit {commit.commit_sha[:8]}: {factor}")
        
        # Combine recommendations
        recommendations = []
        if high_risk_commits:
            recommendations.append(f"Review {len(high_risk_commits)} high-risk commits before merging")
            for commit in high_risk_commits[:3]:
                recommendations.append(f"  • {commit.commit_sha[:8]}: {commit.message[:60]}")
        
        recommendations.extend(project_prediction.recommendations[:3])
        
        # Calculate confidence
        confidence = (
            project_prediction.confidence * 0.6 +
            (1.0 if len(commit_results) >= 5 else 0.5) * 0.4
        )
        
        return IntegratedRiskAssessment(
            repository=repository,
            overall_risk_score=overall_risk_score,
            overall_risk_level=overall_risk_level,
            confidence=confidence,
            commit_risk_score=commit_risk_score,
            project_risk_score=project_prediction.risk_score,
            supply_chain_risk_score=supply_chain_risk_score,
            high_risk_commits=high_risk_commits,
            project_prediction=project_prediction,
            supply_chain_impact=supply_chain_impact,
            reasoning=reasoning,
            risk_factors=risk_factors,
            recommendations=recommendations,
            analyzed_at=datetime.utcnow(),
            alert_priority=alert_priority
        )
    
    def _build_combined_reasoning(
        self,
        commit_results: List[CommitRiskResult],
        high_risk_commits: List[CommitRiskResult],
        project_prediction: PredictionResult,
        supply_chain_impact: Optional[ImpactAnalysis]
    ) -> str:
        """Build combined reasoning from all analyses."""
        
        reasoning = f"## Integrated Risk Assessment\n\n"
        
        # Commit analysis summary
        reasoning += f"### Commit Analysis ({len(commit_results)} commits analyzed)\n"
        if high_risk_commits:
            reasoning += f"⚠️ **{len(high_risk_commits)} HIGH-RISK commits detected:**\n"
            for commit in high_risk_commits[:3]:
                reasoning += f"- {commit.commit_sha[:8]}: {commit.message[:60]} (Risk: {commit.risk_score:.2f})\n"
        else:
            reasoning += "✓ No high-risk commits detected\n"
        
        reasoning += f"\n### Project-level Analysis\n"
        reasoning += f"{project_prediction.reasoning[:300]}...\n"
        
        if supply_chain_impact:
            reasoning += f"\n### Supply Chain Impact\n"
            reasoning += f"- Total dependents: {supply_chain_impact.total_dependents}\n"
            reasoning += f"- Direct dependents: {len(supply_chain_impact.direct_dependents)}\n"
            if supply_chain_impact.critical_dependents:
                reasoning += f"- Critical dependents: {len(supply_chain_impact.critical_dependents)}\n"
        
        return reasoning
    
    def close(self):
        """Close connections."""
        if self.supply_chain:
            self.supply_chain.close()


__all__ = ['IntegratedOracle', 'IntegratedRiskAssessment']
