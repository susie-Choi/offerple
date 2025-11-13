"""
그래프 분석 모듈 테스트
"""
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.graph_analysis.dependency_graph import DependencyGraph


def test_dependency_graph_creation():
    """의존성 그래프 생성 테스트"""
    
    # 테스트 데이터
    packages_data = {
        "flask": {
            "name": "flask",
            "version": "2.0.0",
            "requires_dist": ["werkzeug", "jinja2", "click"]
        },
        "werkzeug": {
            "name": "werkzeug",
            "version": "2.0.0",
            "requires_dist": []
        },
        "jinja2": {
            "name": "jinja2",
            "version": "3.0.0",
            "requires_dist": ["markupsafe"]
        },
        "markupsafe": {
            "name": "markupsafe",
            "version": "2.0.0",
            "requires_dist": []
        },
        "click": {
            "name": "click",
            "version": "8.0.0",
            "requires_dist": []
        }
    }
    
    # 그래프 구축
    dep_graph = DependencyGraph()
    dep_graph.build_from_packages(packages_data)
    
    # 검증
    assert dep_graph.graph.number_of_nodes() == 5
    assert dep_graph.graph.number_of_edges() == 4  # flask->werkzeug, flask->jinja2, flask->click, jinja2->markupsafe
    
    # flask가 werkzeug에 의존하는지 확인
    assert dep_graph.graph.has_edge("flask", "werkzeug")
    assert dep_graph.graph.has_edge("flask", "jinja2")
    assert dep_graph.graph.has_edge("jinja2", "markupsafe")


def test_centrality_metrics():
    """중심성 메트릭 계산 테스트"""
    
    packages_data = {
        "A": {"name": "A", "requires_dist": ["B", "C"]},
        "B": {"name": "B", "requires_dist": ["D"]},
        "C": {"name": "C", "requires_dist": ["D"]},
        "D": {"name": "D", "requires_dist": []},
    }
    
    dep_graph = DependencyGraph()
    dep_graph.build_from_packages(packages_data)
    
    metrics = dep_graph.calculate_centrality_metrics()
    
    # D가 가장 많은 의존성을 받음 (B와 C가 의존)
    assert metrics["D"]["in_degree"] == 2
    assert metrics["A"]["in_degree"] == 0
    
    # 모든 패키지에 대한 메트릭이 존재
    assert len(metrics) == 4
    assert all(key in metrics["D"] for key in ["pagerank", "betweenness", "in_degree", "out_degree"])


def test_critical_nodes_identification():
    """핵심 노드 식별 테스트"""
    
    packages_data = {
        "A": {"name": "A", "requires_dist": ["B"]},
        "B": {"name": "B", "requires_dist": ["C"]},
        "C": {"name": "C", "requires_dist": []},
        "D": {"name": "D", "requires_dist": ["C"]},
        "E": {"name": "E", "requires_dist": ["C"]},
    }
    
    dep_graph = DependencyGraph()
    dep_graph.build_from_packages(packages_data)
    
    metrics = dep_graph.calculate_centrality_metrics()
    critical_nodes = dep_graph.identify_critical_nodes(metrics, top_k=2)
    
    # C가 가장 많은 의존성을 받으므로 핵심 노드여야 함
    assert "C" in critical_nodes
    assert len(critical_nodes) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
