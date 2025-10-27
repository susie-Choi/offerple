#!/usr/bin/env python3
"""
Neo4j Text2Cypher 2024v1 벤치마크 데이터셋 다운로드 스크립트
HuggingFace에서 공식 Neo4j 데이터셋을 다운로드합니다.
"""

import os
import json
from pathlib import Path
from datasets import load_dataset
import pandas as pd
from tqdm import tqdm

def create_directories():
    """필요한 디렉토리 생성"""
    directories = [
        "data/benchmarks/neo4j",
        "data/processed",
        "logs"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"디렉토리 생성: {dir_path}")

def download_neo4j_dataset():
    """HuggingFace에서 Neo4j Text2Cypher 데이터셋 다운로드"""
    try:
        print("Neo4j Text2Cypher 2024v1 데이터셋 다운로드 중...")
        
        # HuggingFace에서 데이터셋 로드
        dataset = load_dataset("neo4j/text2cypher-2024v1")
        
        print(f"데이터셋 정보:")
        print(f"  - Train: {len(dataset['train'])} 샘플")
        if 'validation' in dataset:
            print(f"  - Validation: {len(dataset['validation'])} 샘플")
        if 'test' in dataset:
            print(f"  - Test: {len(dataset['test'])} 샘플")
        
        # 각 split을 JSON 파일로 저장
        for split_name, split_data in dataset.items():
            output_path = f"data/benchmarks/neo4j/{split_name}.json"
            
            # 데이터를 리스트로 변환
            data_list = []
            for item in tqdm(split_data, desc=f"Processing {split_name}"):
                data_list.append(dict(item))
            
            # JSON 파일로 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)
            
            print(f"{split_name} 데이터 저장: {output_path}")
        
        # 데이터셋 정보 저장
        dataset_info = {
            "name": "neo4j/text2cypher-2024v1",
            "source": "HuggingFace",
            "splits": {split: len(data) for split, data in dataset.items()},
            "description": "Neo4j 공식 Text-to-Cypher 벤치마크 데이터셋",
            "download_date": pd.Timestamp.now().isoformat()
        }
        
        with open("data/benchmarks/neo4j/dataset_info.json", 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, ensure_ascii=False, indent=2)
        
        print("Neo4j 데이터셋 다운로드 완료!")
        return True
        
    except Exception as e:
        print(f"Neo4j 데이터셋 다운로드 실패: {str(e)}")
        print("HuggingFace 계정이 필요할 수 있습니다. 다음 명령어로 로그인하세요:")
        print("   huggingface-cli login")
        return False

def analyze_dataset():
    """다운로드된 데이터셋 분석"""
    try:
        train_path = "data/benchmarks/neo4j/train.json"
        if not os.path.exists(train_path):
            print("훈련 데이터가 없습니다. 먼저 데이터셋을 다운로드하세요.")
            return
        
        with open(train_path, 'r', encoding='utf-8') as f:
            train_data = json.load(f)
        
        print("\n데이터셋 분석:")
        print(f"  - 총 샘플 수: {len(train_data)}")
        
        # 첫 번째 샘플 확인
        if train_data:
            sample = train_data[0]
            print(f"  - 샘플 키: {list(sample.keys())}")
            print(f"  - 첫 번째 샘플:")
            for key, value in sample.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"    {key}: {value[:100]}...")
                else:
                    print(f"    {key}: {value}")
        
        # 쿼리 길이 분석
        if 'cypher' in train_data[0]:
            cypher_lengths = [len(item.get('cypher', '')) for item in train_data]
            print(f"  - Cypher 쿼리 평균 길이: {sum(cypher_lengths) / len(cypher_lengths):.1f} 문자")
            print(f"  - 최단 쿼리: {min(cypher_lengths)} 문자")
            print(f"  - 최장 쿼리: {max(cypher_lengths)} 문자")
        
    except Exception as e:
        print(f"데이터셋 분석 실패: {str(e)}")

def main():
    """메인 함수"""
    print("Neo4j Text2Cypher 벤치마크 데이터셋 다운로드 시작")
    
    # 디렉토리 생성
    create_directories()
    
    # 데이터셋 다운로드
    success = download_neo4j_dataset()
    
    if success:
        # 데이터셋 분석
        analyze_dataset()
        print("\n모든 작업이 완료되었습니다!")
    else:
        print("\n데이터셋 다운로드에 실패했습니다.")

if __name__ == "__main__":
    main()