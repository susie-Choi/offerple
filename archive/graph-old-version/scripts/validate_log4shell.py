"""
Log4Shell Historical Validation
2021년 11월 시점에 Log4j를 고위험으로 식별할 수 있었는지 검증
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.validation.historical_validator import HistoricalValidator
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Log4Shell Historical Validation 실행"""
    
    logger.info("=" * 60)
    logger.info("Log4Shell Historical Validation")
    logger.info("CVE-2021-44228 (2021년 12월 10일 공개)")
    logger.info("예측 시점: 2021년 11월 1일 (39일 전)")
    logger.info("=" * 60)
    
    # Step 1: 2021-11-01 시점 데이터로 Phase 1-4 실행
    logger.info("\n[Step 1/3] 2021-11-01 시점 데이터 수집 및 예측...")
    logger.info("(실제로는 phase1~4를 --cutoff-date 2021-11-01로 실행)")
    
    # 예측 결과 로드 (이미 실행되었다고 가정)
    historical_dir = Path("data/historical/log4shell")
    
    if not historical_dir.exists():
        logger.error(f"Historical 데이터 디렉토리가 없습니다: {historical_dir}")
        logger.info("먼저 다음 명령어를 실행하세요:")
        logger.info("  python scripts/phase1_collect_data.py --cutoff-date 2021-11-01")
        logger.info("  python scripts/phase2_extract_signals.py --cutoff-date 2021-11-01")
        logger.info("  python scripts/phase4_llm_prediction.py")
        return
    
    with open(historical_dir / "predictions_2021-11-01.json", 'r') as f:
        predictions = json.load(f)
    
    # Step 2: 실제 CVE 데이터 준비
    logger.info("\n[Step 2/3] 실제 CVE 데이터 로드...")
    
    # Log4Shell 및 관련 CVE
    validation_cves = [
        {
            "cve_id": "CVE-2021-44228",
            "package_name": "log4j",
            "published_date": "2021-12-10",
            "cvss_score": 10.0,
            "cvss_severity": "CRITICAL",
            "description": "Apache Log4j2 JNDI features do not protect against attacker controlled LDAP and other JNDI related endpoints",
            "vulnerability_type": "RCE"
        },
        {
            "cve_id": "CVE-2021-45046",
            "package_name": "log4j",
            "published_date": "2021-12-14",
            "cvss_score": 9.0,
            "cvss_severity": "CRITICAL",
            "description": "Apache Log4j2 Thread Context Lookup Pattern vulnerable to remote code execution",
            "vulnerability_type": "RCE"
        },
        {
            "cve_id": "CVE-2021-45105",
            "package_name": "log4j",
            "published_date": "2021-12-18",
            "cvss_score": 7.5,
            "cvss_severity": "HIGH",
            "description": "Apache Log4j2 does not protect from uncontrolled recursion from self-referential lookups",
            "vulnerability_type": "DOS"
        }
    ]
    
    # Step 3: Historical Validation 실행
    logger.info("\n[Step 3/3] Historical Validation 실행...")
    
    validator = HistoricalValidator(
        cutoff_date="2021-11-01",
        validation_cves=validation_cves
    )
    
    # 전체 성능 평가
    overall_results = validator.validate_predictions(predictions)
    
    # Log4Shell 특화 검증
    log4shell_results = validator.validate_log4shell(predictions)
    
    # 결과 저장
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output = {
        "validation_type": "Log4Shell Historical Validation",
        "cutoff_date": "2021-11-01",
        "cve_published_date": "2021-12-10",
        "lead_time_days": 39,
        "overall_metrics": overall_results,
        "log4shell_case_study": log4shell_results
    }
    
    with open(results_dir / "log4shell_validation_results.json", 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # 결과 출력
    logger.info("\n" + "=" * 60)
    logger.info("Log4Shell Historical Validation 결과")
    logger.info("=" * 60)
    
    if log4shell_results["detected"]:
        logger.info("✓ Log4Shell 사전 탐지 성공!")
        for package, details in log4shell_results["detection_details"].items():
            logger.info(f"  - {package}: 순위 {details['rank']} (상위 {details['percentile']}%)")
            logger.info(f"    위험 점수: {details['risk_score']:.4f}")
    else:
        logger.warning("✗ Log4Shell 탐지 실패")
    
    logger.info("\n전체 성능 메트릭:")
    for k, metrics in overall_results["metrics"].items():
        logger.info(f"  {k}:")
        logger.info(f"    Precision: {metrics['precision']:.4f}")
        logger.info(f"    Recall: {metrics['recall']:.4f}")
        logger.info(f"    F1 Score: {metrics['f1_score']:.4f}")
    
    if overall_results.get("lead_times"):
        logger.info("\nLead Time 분석:")
        for key, value in overall_results["lead_times"].items():
            logger.info(f"  {key}: {value}")
    
    logger.info("=" * 60)
    logger.info(f"결과 저장: {results_dir / 'log4shell_validation_results.json'}")


if __name__ == "__main__":
    main()
