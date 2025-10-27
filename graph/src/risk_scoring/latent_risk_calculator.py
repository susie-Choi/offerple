"""
잠재 위험 점수 계산 모듈
다차원 신호와 LLM 예측을 통합하여 최종 위험 점수 산출
"""
import json
import logging
from typing import Dict, List
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LatentRiskCalculator:
    """잠재 위험 점수 계산 및 통합"""
    
    def __init__(
        self,
        signal_weight: float = 0.6,
        llm_weight: float = 0.4
    ):
        """
        Args:
            signal_weight: 신호 기반 점수 가중치
            llm_weight: LLM 예측 점수 가중치
        """
        self.signal_weight = signal_weight
        self.llm_weight = llm_weight
    
    def calculate_signal_score(self, signals: Dict) -> float:
        """다차원 신호로부터 위험 점수 계산"""
        
        # 각 신호 유형별 점수
        vuln_score = self._vulnerability_score(signals.get("vulnerability_patterns", {}))
        graph_score = self._graph_score(signals.get("graph_signals", {}))
        code_score = self._code_score(signals.get("code_signals", {}))
        activity_score = self._activity_score(signals.get("activity_signals", {}))
        
        # 가중 평균
        total_score = (
            vuln_score * 0.4 +      # 과거 이력이 가장 중요
            graph_score * 0.3 +     # 생태계 영향력
            code_score * 0.2 +      # 코드 레벨 위험
            activity_score * 0.1    # 유지보수 활동
        )
        
        return min(total_score, 1.0)
    
    def _vulnerability_score(self, vuln_patterns: Dict) -> float:
        """과거 취약점 패턴 점수"""
        if not vuln_patterns:
            return 0.0
        
        # 이미 계산된 risk_score 사용
        return vuln_patterns.get("risk_score", 0.0)
    
    def _graph_score(self, graph_signals: Dict) -> float:
        """그래프 중심성 점수"""
        if not graph_signals:
            return 0.0
        
        # PageRank와 Downstream Impact 결합
        pagerank = graph_signals.get("pagerank", 0.0)
        downstream = graph_signals.get("downstream_impact", 0)
        
        # 정규화 (경험적 최대값 기준)
        normalized_pr = min(pagerank / 0.001, 1.0)  # 0.001 이상이면 매우 높음
        normalized_ds = min(downstream / 10000, 1.0)  # 10000개 이상이면 매우 높음
        
        return (normalized_pr * 0.5 + normalized_ds * 0.5)
    
    def _code_score(self, code_signals: Dict) -> float:
        """코드 레벨 위험 점수"""
        if not code_signals:
            return 0.0
        
        dangerous_funcs = code_signals.get("dangerous_functions", 0)
        complexity = code_signals.get("complexity_score", 0)
        
        # 정규화
        func_score = min(dangerous_funcs / 50, 1.0)  # 50개 이상이면 매우 위험
        complexity_score = min(complexity / 100, 1.0)  # 100 이상이면 매우 복잡
        
        return (func_score * 0.6 + complexity_score * 0.4)
    
    def _activity_score(self, activity_signals: Dict) -> float:
        """유지보수 활동 점수 (낮을수록 위험)"""
        if not activity_signals:
            return 0.5  # 정보 없으면 중립
        
        commit_freq = activity_signals.get("commit_frequency_3m", 0)
        issue_resolution = activity_signals.get("issue_resolution_days", 999)
        
        # 활동이 적거나 이슈 해결이 느리면 위험
        activity_risk = 1.0 - min(commit_freq / 100, 1.0)  # 커밋이 적으면 위험
        resolution_risk = min(issue_resolution / 30, 1.0)  # 해결이 느리면 위험
        
        return (activity_risk * 0.5 + resolution_risk * 0.5)
    
    def calculate_final_score(
        self,
        package_name: str,
        signals: Dict,
        llm_prediction: Dict
    ) -> Dict:
        """신호 점수와 LLM 점수를 통합하여 최종 점수 계산"""
        
        signal_score = self.calculate_signal_score(signals)
        llm_score = llm_prediction.get("risk_score", 0.5)
        
        # 가중 평균
        final_score = (
            signal_score * self.signal_weight +
            llm_score * self.llm_weight
        )
        
        return {
            "package_name": package_name,
            "final_score": round(final_score, 4),
            "signal_score": round(signal_score, 4),
            "llm_score": round(llm_score, 4),
            "llm_reasoning": llm_prediction.get("reasoning", ""),
            "llm_confidence": llm_prediction.get("confidence", 0.0),
        }
    
    def calculate_batch(
        self,
        all_signals: Dict[str, Dict],
        llm_predictions: Dict[str, Dict],
        output_file: str
    ) -> Dict[str, Dict]:
        """모든 패키지의 최종 위험 점수 계산"""
        logger.info(f"총 {len(all_signals)}개 패키지의 최종 위험 점수 계산 시작")
        
        results = {}
        
        for package_name, signals in all_signals.items():
            # LLM 예측이 없는 경우 신호만 사용
            llm_pred = llm_predictions.get(package_name, {"risk_score": 0.5})
            
            final_result = self.calculate_final_score(package_name, signals, llm_pred)
            results[package_name] = final_result
        
        # 순위 추가
        sorted_packages = sorted(
            results.items(),
            key=lambda x: x[1]["final_score"],
            reverse=True
        )
        
        for rank, (package_name, data) in enumerate(sorted_packages, 1):
            results[package_name]["rank"] = rank
            results[package_name]["percentile"] = round((1 - rank / len(results)) * 100, 2)
        
        # 결과 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"최종 위험 점수 계산 완료: {output_file}")
        return results
    
    def get_top_k_risks(self, results: Dict[str, Dict], k: int = 100) -> List[Dict]:
        """상위 K개 고위험 패키지 추출"""
        sorted_packages = sorted(
            results.items(),
            key=lambda x: x[1]["final_score"],
            reverse=True
        )
        
        return [
            {
                "rank": idx + 1,
                "package_name": package_name,
                **data
            }
            for idx, (package_name, data) in enumerate(sorted_packages[:k])
        ]


if __name__ == "__main__":
    # 사용 예시
    # 통합 신호 로드
    with open("data/processed/signals/integrated_signals.json", 'r') as f:
        all_signals = json.load(f)
    
    # LLM 예측 로드
    with open("data/processed/llm_predictions.json", 'r') as f:
        llm_predictions = json.load(f)
    
    # 위험 점수 계산기 초기화
    calculator = LatentRiskCalculator(signal_weight=0.6, llm_weight=0.4)
    
    # 배치 계산
    results = calculator.calculate_batch(
        all_signals=all_signals,
        llm_predictions=llm_predictions,
        output_file="data/processed/scores/latent_risk_scores.json"
    )
    
    # 상위 100개 고위험 패키지
    top_100 = calculator.get_top_k_risks(results, k=100)
    
    print("=== 상위 10개 고위험 패키지 ===")
    for item in top_100[:10]:
        print(f"{item['rank']}. {item['package_name']}: {item['final_score']:.4f}")
