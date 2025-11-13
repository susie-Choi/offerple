"""
의존성 그래프 구축 및 분석 모듈
NetworkX 기반 그래프 구조 분석 및 중심성 계산

Neo4j는 선택사항입니다:
- 소규모 (~10,000 패키지): NetworkX만으로 충분
- 대규모 (10,000+ 패키지): Neo4j 사용 권장 (use_neo4j=True)
"""
import networkx as nx
import json
import logging
from typing import Dict, List, Set, Optional
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DependencyGraph:
    """패키지 의존성 그래프 구축 및 분석"""
    
    def __init__(self, use_neo4j: bool = False, neo4j_uri: Optional[str] = None):
        """
        Args:
            use_neo4j: Neo4j 사용 여부 (기본값: False, NetworkX만 사용)
            neo4j_uri: Neo4j 연결 URI (use_neo4j=True일 때만 필요)
        """
        self.graph = nx.DiGraph()
        self.use_neo4j = use_neo4j
        self.neo4j_driver = None
        
        if use_neo4j:
            self._init_neo4j(neo4j_uri)
    
    def _init_neo4j(self, uri: Optional[str]):
        """Neo4j 연결 초기화 (선택사항)"""
        try:
            from neo4j import GraphDatabase
            import os
            
            uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "zero-day-defense")
            
            self.neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info(f"Neo4j 연결 성공: {uri}")
        except ImportError:
            logger.warning("neo4j 패키지가 설치되지 않았습니다. NetworkX만 사용합니다.")
            self.use_neo4j = False
        except Exception as e:
            logger.warning(f"Neo4j 연결 실패: {e}. NetworkX만 사용합니다.")
            self.use_neo4j = False
        
    def build_from_packages(self, packages_data: Dict[str, Dict]):
        """패키지 데이터로부터 의존성 그래프 구축"""
        logger.info(f"총 {len(packages_data)}개 패키지로 그래프 구축 시작")
        
        # 노드 추가
        for package_name, package_info in packages_data.items():
            self.graph.add_node(package_name, **package_info)
        
        # 엣지 추가 (의존성 관계)
        for package_name, package_info in packages_data.items():
            requires_dist = package_info.get("requires_dist", [])
            
            for req in requires_dist:
                if not req:
                    continue
                
                # 의존성 패키지명 추출
                dep_name = req.split()[0].split("[")[0].strip()
                
                # 그래프에 존재하는 패키지만 연결
                if dep_name in self.graph:
                    self.graph.add_edge(package_name, dep_name)
        
        logger.info(f"그래프 구축 완료: {self.graph.number_of_nodes()}개 노드, "
                   f"{self.graph.number_of_edges()}개 엣지")
    
    def calculate_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """그래프 중심성 메트릭 계산"""
        logger.info("중심성 메트릭 계산 시작...")
        
        metrics = {}
        
        # PageRank (전역 중요도)
        logger.info("PageRank 계산 중...")
        pagerank = nx.pagerank(self.graph, alpha=0.85)
        
        # Betweenness Centrality (병목 지점)
        logger.info("Betweenness Centrality 계산 중...")
        betweenness = nx.betweenness_centrality(self.graph)
        
        # In-degree (얼마나 많은 패키지가 의존하는지)
        logger.info("In-degree 계산 중...")
        in_degree = dict(self.graph.in_degree())
        
        # Out-degree (얼마나 많은 패키지에 의존하는지)
        out_degree = dict(self.graph.out_degree())
        
        # 각 노드별 메트릭 통합
        for node in self.graph.nodes():
            metrics[node] = {
                "pagerank": pagerank.get(node, 0.0),
                "betweenness": betweenness.get(node, 0.0),
                "in_degree": in_degree.get(node, 0),
                "out_degree": out_degree.get(node, 0),
                "downstream_impact": self._calculate_downstream_impact(node),
            }
        
        logger.info("중심성 메트릭 계산 완료")
        return metrics
    
    def _calculate_downstream_impact(self, node: str) -> int:
        """하류 영향 범위 계산 (이 패키지에 직간접적으로 의존하는 패키지 수)"""
        try:
            # 역방향 그래프에서 도달 가능한 노드 수
            reverse_graph = self.graph.reverse()
            reachable = nx.descendants(reverse_graph, node)
            return len(reachable)
        except Exception:
            return 0
    
    def identify_critical_nodes(self, metrics: Dict[str, Dict], top_k: int = 100) -> List[str]:
        """핵심 노드 식별 (높은 중심성 + 높은 영향력)"""
        # 복합 점수 계산: PageRank * 0.4 + Betweenness * 0.3 + Downstream Impact * 0.3
        scores = {}
        
        # 정규화를 위한 최대값 계산
        max_pagerank = max(m["pagerank"] for m in metrics.values())
        max_betweenness = max(m["betweenness"] for m in metrics.values())
        max_downstream = max(m["downstream_impact"] for m in metrics.values())
        
        for node, m in metrics.items():
            normalized_pr = m["pagerank"] / max_pagerank if max_pagerank > 0 else 0
            normalized_bt = m["betweenness"] / max_betweenness if max_betweenness > 0 else 0
            normalized_ds = m["downstream_impact"] / max_downstream if max_downstream > 0 else 0
            
            scores[node] = (
                normalized_pr * 0.4 +
                normalized_bt * 0.3 +
                normalized_ds * 0.3
            )
        
        # 상위 K개 노드 선택
        critical_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        logger.info(f"핵심 노드 {top_k}개 식별 완료")
        return [node for node, score in critical_nodes]
    
    def detect_communities(self, algorithm: str = "louvain") -> Dict[int, List[str]]:
        """위협 군집 탐지"""
        logger.info(f"{algorithm} 알고리즘으로 커뮤니티 탐지 시작...")
        
        # 방향 그래프를 무방향으로 변환
        undirected_graph = self.graph.to_undirected()
        
        if algorithm == "louvain":
            # Louvain 알고리즘 (python-louvain 패키지 필요)
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(undirected_graph)
            except ImportError:
                logger.warning("python-louvain 패키지 없음, label propagation 사용")
                communities = nx.community.label_propagation_communities(undirected_graph)
                partition = {}
                for idx, comm in enumerate(communities):
                    for node in comm:
                        partition[node] = idx
        else:
            # Label Propagation
            communities = nx.community.label_propagation_communities(undirected_graph)
            partition = {}
            for idx, comm in enumerate(communities):
                for node in comm:
                    partition[node] = idx
        
        # 커뮤니티별로 노드 그룹화
        clusters = {}
        for node, cluster_id in partition.items():
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(node)
        
        logger.info(f"커뮤니티 탐지 완료: {len(clusters)}개 클러스터")
        return clusters
    
    def save(self, filepath: str):
        """그래프를 파일로 저장"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.graph, f)
        logger.info(f"그래프 저장 완료: {filepath}")
    
    def load(self, filepath: str):
        """파일에서 그래프 로드"""
        with open(filepath, 'rb') as f:
            self.graph = pickle.load(f)
        logger.info(f"그래프 로드 완료: {filepath}")


if __name__ == "__main__":
    # 사용 예시
    # 패키지 데이터 로드
    with open("data/raw/packages.json", 'r') as f:
        packages_data = json.load(f)
    
    # 그래프 구축
    dep_graph = DependencyGraph()
    dep_graph.build_from_packages(packages_data)
    
    # 중심성 메트릭 계산
    metrics = dep_graph.calculate_centrality_metrics()
    
    # 결과 저장
    with open("data/processed/signals/graph_signals.json", 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # 핵심 노드 식별
    critical_nodes = dep_graph.identify_critical_nodes(metrics, top_k=100)
    print(f"핵심 노드 상위 10개: {critical_nodes[:10]}")
    
    # 그래프 저장
    dep_graph.save("data/graphs/dependency_graph.gpickle")
