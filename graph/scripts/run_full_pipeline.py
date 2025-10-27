"""
전체 파이프라인 실행 스크립트
Phase 1 ~ Phase 4를 순차적으로 실행
"""
import subprocess
import sys
import logging
from pathlib import Path
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(command: list, description: str):
    """명령어 실행 및 결과 확인"""
    logger.info(f"\n{'='*60}")
    logger.info(f"{description}")
    logger.info(f"명령어: {' '.join(command)}")
    logger.info(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"오류 발생: {e}")
        logger.error(f"stderr: {e.stderr}")
        return False


def main(cutoff_date: str = None, provider: str = "openai", model: str = "gpt-4", top_k: int = 100):
    """전체 파이프라인 실행"""
    
    logger.info("=" * 60)
    logger.info("Zero-Day Defense 전체 파이프라인 실행")
    logger.info("=" * 60)
    
    if cutoff_date:
        logger.info(f"Historical Validation 모드: cutoff={cutoff_date}")
    else:
        logger.info("일반 모드: 최신 데이터 사용")
    
    # 데이터 디렉토리 생성
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed/signals").mkdir(parents=True, exist_ok=True)
    Path("data/processed/scores").mkdir(parents=True, exist_ok=True)
    Path("data/graphs").mkdir(parents=True, exist_ok=True)
    Path("data/results").mkdir(parents=True, exist_ok=True)
    
    # Phase 1: 데이터 수집
    cmd = ["python", "scripts/phase1_collect_data.py"]
    if cutoff_date:
        cmd.extend(["--cutoff-date", cutoff_date])
    
    if not run_command(cmd, "Phase 1: 데이터 수집"):
        logger.error("Phase 1 실패. 파이프라인 중단.")
        return False
    
    # Phase 2: 사전 신호 추출
    cmd = ["python", "scripts/phase2_extract_signals.py"]
    if cutoff_date:
        cmd.extend(["--cutoff-date", cutoff_date])
    
    if not run_command(cmd, "Phase 2: 사전 신호 추출"):
        logger.error("Phase 2 실패. 파이프라인 중단.")
        return False
    
    # Phase 4: LLM 기반 예측
    cmd = [
        "python", "scripts/phase4_llm_prediction.py",
        "--provider", provider,
        "--model", model,
        "--top-k", str(top_k)
    ]
    
    if not run_command(cmd, "Phase 4: LLM 기반 예측"):
        logger.error("Phase 4 실패. 파이프라인 중단.")
        return False
    
    # 완료
    logger.info("\n" + "=" * 60)
    logger.info("전체 파이프라인 실행 완료!")
    logger.info("=" * 60)
    logger.info("\n결과 파일:")
    logger.info("  - data/processed/signals/graph_signals.json")
    logger.info("  - data/processed/signals/vulnerability_patterns.json")
    logger.info("  - data/processed/llm_predictions.json")
    logger.info("  - data/processed/scores/latent_risk_scores.json")
    logger.info("  - data/processed/scores/top_100_risks.json")
    logger.info("\nAPI 서버 시작:")
    logger.info("  uvicorn src.api.main:app --reload --port 8000")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="전체 파이프라인 실행")
    parser.add_argument(
        "--cutoff-date",
        type=str,
        help="Historical Validation용 cutoff 날짜 (YYYY-MM-DD)"
    )
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
        help="LLM 모델명"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=100,
        help="LLM 예측할 상위 K개 패키지"
    )
    
    args = parser.parse_args()
    
    success = main(
        cutoff_date=args.cutoff_date,
        provider=args.provider,
        model=args.model,
        top_k=args.top_k
    )
    
    sys.exit(0 if success else 1)
