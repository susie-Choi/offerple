#!/usr/bin/env python3
"""
SynthCypher 데이터셋 다운로드 스크립트
SynthCypher 논문에서 제안된 synthetic data generation 데이터셋을 다운로드합니다.
"""

import os
import json
import requests
from pathlib import Path
from tqdm import tqdm
import pandas as pd

def create_directories():
    """필요한 디렉토리 생성"""
    directories = [
        "data/benchmarks/synthcypher",
        "data/processed",
        "logs"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"디렉토리 생성: {dir_path}")

def search_synthcypher_data():
    """SynthCypher 데이터셋 위치 검색"""
    print("SynthCypher 데이터셋 검색 중...")
    
    # 가능한 데이터 소스들
    potential_sources = [
        {
            "name": "GitHub Repository",
            "description": "SynthCypher 논문의 공식 GitHub 저장소",
            "search_terms": ["SynthCypher", "synthetic cypher", "text2cypher synthetic"]
        },
        {
            "name": "Paper Supplementary",
            "description": "논문 보충 자료",
            "search_terms": ["SynthCypher supplementary", "synthetic data generation cypher"]
        },
        {
            "name": "HuggingFace",
            "description": "HuggingFace 데이터셋 허브",
            "search_terms": ["synthcypher", "synthetic cypher dataset"]
        }
    ]
    
    print("검색할 데이터 소스:")
    for i, source in enumerate(potential_sources, 1):
        print(f"  {i}. {source['name']}: {source['description']}")
    
    return potential_sources

def try_download_from_github():
    """GitHub에서 SynthCypher 데이터 검색 및 다운로드 시도"""
    print("GitHub에서 SynthCypher 데이터 검색 중...")
    
    # GitHub API를 사용하여 관련 저장소 검색
    search_url = "https://api.github.com/search/repositories"
    params = {
        "q": "SynthCypher OR synthetic cypher OR text2cypher synthetic",
        "sort": "stars",
        "order": "desc"
    }
    
    try:
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            results = response.json()
            
            print(f"GitHub에서 {results['total_count']}개의 관련 저장소 발견")
            
            if results['items']:
                print("상위 저장소들:")
                for i, repo in enumerate(results['items'][:5], 1):
                    print(f"  {i}. {repo['full_name']}")
                    print(f"     {repo['stargazers_count']} stars")
                    print(f"     {repo['description'] or 'No description'}")
                    print(f"     {repo['html_url']}")
                    print()
                
                return results['items']
            else:
                print("관련 저장소를 찾을 수 없습니다.")
                return []
        else:
            print(f"GitHub API 요청 실패: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"GitHub 검색 실패: {str(e)}")
        return []

def create_placeholder_data():
    """SynthCypher 데이터를 찾을 수 없는 경우 플레이스홀더 생성"""
    print("SynthCypher 플레이스홀더 데이터 생성 중...")
    
    # 기본적인 synthetic 데이터 구조 예시
    placeholder_data = [
        {
            "question": "Find all nodes with label Person",
            "cypher": "MATCH (p:Person) RETURN p",
            "schema": "Person(name, age)",
            "complexity": "simple",
            "source": "synthetic_placeholder"
        },
        {
            "question": "Find persons who are friends with someone named John",
            "cypher": "MATCH (p:Person)-[:FRIENDS_WITH]->(friend:Person {name: 'John'}) RETURN p",
            "schema": "Person(name, age), FRIENDS_WITH",
            "complexity": "medium",
            "source": "synthetic_placeholder"
        },
        {
            "question": "Find the shortest path between two specific persons",
            "cypher": "MATCH path = shortestPath((p1:Person {name: 'Alice'})-[*]-(p2:Person {name: 'Bob'})) RETURN path",
            "schema": "Person(name, age), various relationships",
            "complexity": "complex",
            "source": "synthetic_placeholder"
        }
    ]
    
    # 플레이스홀더 데이터 저장
    output_path = "data/benchmarks/synthcypher/placeholder_data.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(placeholder_data, f, ensure_ascii=False, indent=2)
    
    # 메타데이터 저장
    metadata = {
        "name": "SynthCypher Placeholder",
        "source": "Generated placeholder",
        "total_samples": len(placeholder_data),
        "description": "실제 SynthCypher 데이터를 찾을 수 없어 생성한 플레이스홀더 데이터",
        "note": "실제 SynthCypher 논문 데이터로 교체 필요",
        "created_date": pd.Timestamp.now().isoformat()
    }
    
    with open("data/benchmarks/synthcypher/metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"플레이스홀더 데이터 생성 완료: {output_path}")
    return True

def main():
    """메인 함수"""
    print("SynthCypher 데이터셋 다운로드 시작")
    
    # 디렉토리 생성
    create_directories()
    
    # 데이터 소스 검색
    sources = search_synthcypher_data()
    
    # GitHub에서 검색 시도
    github_repos = try_download_from_github()
    
    if github_repos:
        print("\n다음 단계:")
        print("1. 위의 GitHub 저장소들을 수동으로 확인하여 SynthCypher 데이터를 찾아주세요")
        print("2. 데이터를 찾으면 data/benchmarks/synthcypher/ 폴더에 저장해주세요")
        print("3. 또는 논문 저자에게 직접 연락하여 데이터를 요청해보세요")
    else:
        print("\nSynthCypher 데이터를 자동으로 찾을 수 없습니다.")
        print("다음 방법들을 시도해보세요:")
        print("1. SynthCypher 논문의 저자에게 직접 연락")
        print("2. 논문에 명시된 데이터 공개 링크 확인")
        print("3. 관련 학회나 워크샵 자료 확인")
    
    # 플레이스홀더 데이터 생성
    create_placeholder_data()
    
    print("\nTODO:")
    print("- SynthCypher 원본 데이터 확보")
    print("- 데이터 형식 표준화")
    print("- Neo4j 벤치마크와 형식 통일")

if __name__ == "__main__":
    main()