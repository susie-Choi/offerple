"""
Phase 1: 데이터 수집 및 전처리
패키지 메타데이터, 취약점 이력, 의존성 정보 수집
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_collection.package_collector import PackageCollector
from src.data_collection.vulnerability_collector import VulnerabilityCollector
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(cutoff_date: str = None):
    """Phase 1 실행"""
    
    logger.info("=" * 60)
    logger.info("Phase 1: 데이터 수집 시작")
    logger.info(f"Cutoff 날짜: {cutoff_date or '현재'}")
    logger.info("=" * 60)
    
    # 출력 디렉토리 생성
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: 주요 패키지 목록 정의
    # 실제로는 PyPI 전체 또는 다운로드 상위 N개를 수집
    # 여기서는 예시로 주요 패키지만
    target_packages = [
        # 웹 프레임워크
        "flask", "django", "fastapi", "tornado", "bottle",
        # HTTP 라이브러리
        "requests", "urllib3", "httpx", "aiohttp",
        # 데이터 처리
        "pandas", "numpy", "scipy",
        # 보안 관련
        "cryptography", "pycryptodome", "paramiko",
        # 로깅
        "logging", "loguru",
        # 직렬화
        "pickle", "pyyaml", "json",
        # 데이터베이스
        "sqlalchemy", "psycopg2", "pymongo",
        # 기타 인기 패키지
        "pillow", "beautifulsoup4", "selenium", "scrapy",
    ]
    
    logger.info(f"수집 대상: {len(target_packages)}개 패키지")
    
    # Step 2: 패키지 메타데이터 수집
    logger.info("\n[Step 1/3] 패키지 메타데이터 수집 중...")
    package_collector = PackageCollector(cutoff_date=cutoff_date)
    
    packages_data = package_collector.collect_batch(
        package_names=target_packages,
        output_file=str(output_dir / "packages.json")
    )
    
    # Step 3: 의존성 정보 수집
    logger.info("\n[Step 2/3] 의존성 정보 수집 중...")
    dependencies = {}
    
    for package_name in packages_data.keys():
        deps = package_collector.collect_dependencies(package_name)
        if deps:
            dependencies[package_name] = deps
    
    with open(output_dir / "dependencies.json", 'w') as f:
        json.dump(dependencies, f, indent=2)
    
    logger.info(f"의존성 정보 저장 완료: {len(dependencies)}개 패키지")
    
    # Step 4: 취약점 이력 수집
    logger.info("\n[Step 3/3] 취약점 이력 수집 중...")
    
    nvd_api_key = os.getenv("NVD_API_KEY")
    vuln_collector = VulnerabilityCollector(
        cutoff_date=cutoff_date or "2024-12-31",
        nvd_api_key=nvd_api_key
    )
    
    vulnerabilities = vuln_collector.collect_batch(
        package_names=list(packages_data.keys()),
        output_file=str(output_dir / "vulnerabilities.json")
    )
    
    # 요약 통계
    logger.info("\n" + "=" * 60)
    logger.info("Phase 1 완료!")
    logger.info(f"수집된 패키지: {len(packages_data)}개")
    logger.info(f"의존성 관계: {sum(len(deps) for deps in dependencies.values())}개")
    logger.info(f"CVE 데이터: {sum(len(cves) for cves in vulnerabilities.values())}개")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 1: 데이터 수집")
    parser.add_argument(
        "--cutoff-date",
        type=str,
        help="데이터 수집 시간 제약 (YYYY-MM-DD). Historical Validation용"
    )
    
    args = parser.parse_args()
    main(cutoff_date=args.cutoff_date)
