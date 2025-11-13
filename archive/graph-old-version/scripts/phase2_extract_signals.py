"""
Phase 2: 사전 신호 추출
그래프 구조, 취약점 패턴, 코드 레벨 신호 추출
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.graph_analysis.dependency_graph import DependencyGraph
from src.signal_extraction.vulnerability_patterns import VulnerabilityPatternExtractor
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(cutoff_date: str = None):
    """Phase 2 실행"""
    
    logger.info("=" * 60)
    logger.info("Phase 2: 사전 신호 추출 시작")
    logger.info("=" * 60)
    
    # 입력 데이터 로드
    data_dir = Path("data/raw")
    output_dir = Path("data/processed/signals")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("데이터 로드 중...")
    with open(data_dir / "packages.json", 'r') as f:
        packages_data = json.load(f)
    
    with open(data_dir / "vulnerabilities.json", 'r') as f:
        vulnerabilities_data = json.load(f)
    
    # Step 1: 의존성 그래프 구축 및 분석
    logger.info("\n[Step 1/3] 의존성 그래프 분석 중...")
    
    dep_graph = DependencyGraph()
    dep_graph.build_from_packages(packages_data)
    
    # 중심성 메트릭 계산
    graph_signals = dep_graph.calculate_centrality_metrics()
    
    with open(output_dir / "graph_signals.json", 'w') as f:
        json.dump(graph_signals, f, indent=2)
    
    logger.info(f"그래프 신호 저장 완료: {len(graph_signals)}개 패키지")
    
    # 그래프 저장
    graph_dir = Path("data/graphs")
    graph_dir.mkdir(parents=True, exist_ok=True)
    dep_graph.save(str(graph_dir / "dependency_graph.gpickle"))
    
    # 핵심 노드 식별
    critical_nodes = dep_graph.identify_critical_nodes(graph_signals, top_k=100)
    
    with open(Path("data/processed") / "critical_nodes.json", 'w') as f:
        json.dump(critical_nodes, f, indent=2)
    
    logger.info(f"핵심 노드 {len(critical_nodes)}개 식별 완료")
    
    # Step 2: 취약점 패턴 신호 추출
    logger.info("\n[Step 2/3] 취약점 패턴 분석 중...")
    
    vuln_extractor = VulnerabilityPatternExtractor(
        cutoff_date=cutoff_date or "2024-12-31"
    )
    
    vulnerability_patterns = vuln_extractor.extract_patterns(vulnerabilities_data)
    
    with open(output_dir / "vulnerability_patterns.json", 'w') as f:
        json.dump(vulnerability_patterns, f, indent=2)
    
    logger.info(f"취약점 패턴 저장 완료: {len(vulnerability_patterns)}개 패키지")
    
    # Step 3: 신호 통합
    logger.info("\n[Step 3/3] 신호 통합 중...")
    
    integrated_signals = {}
    
    for package_name in packages_data.keys():
        integrated_signals[package_name] = {
            "graph_signals": graph_signals.get(package_name, {}),
            "vulnerability_patterns": vulnerability_patterns.get(package_name, {}),
            # 코드 신호는 추후 추가 가능
            "code_signals": {},
            "activity_signals": {},
        }
    
    with open(output_dir / "integrated_signals.json", 'w') as f:
        json.dump(integrated_signals, f, indent=2)
    
    logger.info(f"통합 신호 저장 완료: {len(integrated_signals)}개 패키지")
    
    # 요약 통계
    logger.info("\n" + "=" * 60)
    logger.info("Phase 2 완료!")
    logger.info(f"그래프 신호: {len(graph_signals)}개")
    logger.info(f"취약점 패턴: {len(vulnerability_patterns)}개")
    logger.info(f"핵심 노드: {len(critical_nodes)}개")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 2: 사전 신호 추출")
    parser.add_argument(
        "--cutoff-date",
        type=str,
        help="분석 시간 제약 (YYYY-MM-DD)"
    )
    
    args = parser.parse_args()
    main(cutoff_date=args.cutoff_date)
