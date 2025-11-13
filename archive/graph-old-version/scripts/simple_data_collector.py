"""
간단한 데이터 수집 스크립트
Python 설치 없이 실행 가능한 버전
"""
import json
import urllib.request
import urllib.error
from pathlib import Path
import time

def collect_pypi_package(package_name):
    """PyPI에서 패키지 정보 수집"""
    url = f"https://pypi.org/pypi/{package_name}/json"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        info = data.get("info", {})
        
        return {
            "name": info.get("name"),
            "version": info.get("version"),
            "summary": info.get("summary"),
            "author": info.get("author"),
            "license": info.get("license"),
            "requires_dist": info.get("requires_dist", []),
        }
    except Exception as e:
        print(f"오류 ({package_name}): {e}")
        return None

def main():
    """메인 실행"""
    print("=" * 60)
    print("간단한 PyPI 데이터 수집 시작")
    print("=" * 60)
    
    # 테스트용 주요 패키지 목록
    packages = [
        "flask", "django", "requests", "numpy", "pandas",
        "pytest", "black", "pillow", "cryptography", "sqlalchemy"
    ]
    
    # 출력 디렉토리 생성
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for idx, package_name in enumerate(packages, 1):
        print(f"\n[{idx}/{len(packages)}] {package_name} 수집 중...")
        
        package_data = collect_pypi_package(package_name)
        
        if package_data:
            results[package_name] = package_data
            print(f"  ✓ 성공: {package_data['version']}")
        else:
            print(f"  ✗ 실패")
        
        time.sleep(0.5)  # Rate limiting
    
    # 결과 저장
    output_file = output_dir / "packages.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"수집 완료: {len(results)}개 패키지")
    print(f"저장 위치: {output_file}")
    print("=" * 60)
    
    # 결과 미리보기
    print("\n수집된 패키지:")
    for name, data in results.items():
        print(f"  - {name} ({data['version']}): {data['summary'][:50]}...")

if __name__ == "__main__":
    main()
