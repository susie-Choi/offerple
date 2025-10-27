"""
Phase 4: LLM 기반 잠재 위협 예측
다차원 신호를 통합하여 LLM으로 유추 추론 수행
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.llm_reasoning.risk_predictor import LLMRiskPredictor
from src.risk_scoring.latent_risk_calculator import LatentRiskCalculator
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(provider: str = "openai", model: str = "gpt-4", top_k: int = 100):
    """Phase 4 실행"""
    
    logger.info("=" * 60)
    logger.info("Phase 4: LLM 기반 잠재 위협 예측 시작")
    logger.info(f"Provider: {provider}, Model: {model}")
    logger.info("=" * 60)
    
    # 데이터 로드
    logger.info("데이터 로드 중...")
    
    with open("data/processed/signals/integrated_signals.json", 'r') as f:
        all_signals = json.load(f)
    
    with open("data/processed/critical_nodes.json", 'r') as f:
        critical_nodes = json.load(f)
    
    # Step 1: LLM 예측 (핵심 노드만, 비용 절감)
    logger.info(f"\n[Step 1/2] LLM 예측 중 (상위 {top_k}개 핵심 노드)...")
    
    predictor = LLMRiskPredictor(provider=provider, model=model)
    
    llm_predictions = predictor.predict_batch(
        packages=critical_nodes[:top_k],
        all_signals=all_signals,
        output_file="data/processed/llm_predictions.json"
    )
    
    logger.info(f"LLM 예측 완료: {len(llm_predictions)}개 패키지")
    
    # Step 2: 최종 위험 점수 계산
    logger.info("\n[Step 2/2] 최종 위험 점수 계산 중...")
    
    calculator = LatentRiskCalculator(signal_weight=0.6, llm_weight=0.4)
    
    output_dir = Path("data/processed/scores")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    final_scores = calculator.calculate_batch(
        all_signals=all_signals,
        llm_predictions=llm_predictions,
        output_file=str(output_dir / "latent_risk_scores.json")
    )
    
    # 상위 100개 고위험 패키지
    top_100 = calculator.get_top_k_risks(final_scores, k=100)
    
    with open(output_dir / "top_100_risks.json", 'w') as f:
        json.dump(top_100, f, indent=2)
    
    # 요약 통계
    logger.info("\n" + "=" * 60)
    logger.info("Phase 4 완료!")
    logger.info(f"LLM 예측: {len(llm_predictions)}개")
    logger.info(f"최종 점수: {len(final_scores)}개")
    logger.info("\n상위 10개 고위험 패키지:")
    
    for item in top_100[:10]:
        logger.info(f"  {item['rank']}. {item['package_name']}: {item['final_score']:.4f}")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 4: LLM 기반 예측")
    parser.add_argument(
        "--provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic"],
        help="LLM provider"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4",
        help="모델명 (예: gpt-4, gpt-3.5-turbo, claude-3-opus)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=100,
        help="LLM 예측할 상위 K개 패키지 (비용 절감)"
    )
    
    args = parser.parse_args()
    main(provider=args.provider, model=args.model, top_k=args.top_k)
