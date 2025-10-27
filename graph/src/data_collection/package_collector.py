"""
패키지 생태계 데이터 수집 모듈
PyPI, Maven, npm 등에서 패키지 메타데이터 및 의존성 정보 수집
"""
import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PackageCollector:
    """패키지 메타데이터 및 의존성 정보 수집"""
    
    def __init__(self, cutoff_date: Optional[str] = None):
        """
        Args:
            cutoff_date: 데이터 수집 시간 제약 (YYYY-MM-DD 형식)
                        Historical Validation 시 필수
        """
        self.cutoff_date = cutoff_date
        self.pypi_base_url = "https://pypi.org/pypi"
        
    def collect_pypi_package(self, package_name: str) -> Optional[Dict]:
        """PyPI에서 단일 패키지 정보 수집"""
        try:
            url = f"{self.pypi_base_url}/{package_name}/json"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"패키지 {package_name} 조회 실패: {response.status_code}")
                return None
            
            data = response.json()
            
            # cutoff 날짜 이전 데이터만 사용
            if self.cutoff_date:
                release_date = self._get_latest_release_date(data)
                if release_date and release_date > self.cutoff_date:
                    logger.info(f"패키지 {package_name}는 cutoff 이후 릴리스: {release_date}")
                    return None
            
            return self._parse_pypi_data(data)
            
        except Exception as e:
            logger.error(f"패키지 {package_name} 수집 중 오류: {e}")
            return None
    
    def _get_latest_release_date(self, data: Dict) -> Optional[str]:
        """최신 릴리스 날짜 추출"""
        try:
            releases = data.get("releases", {})
            if not releases:
                return None
            
            latest_version = data["info"]["version"]
            release_info = releases.get(latest_version, [])
            
            if release_info:
                return release_info[0].get("upload_time_iso_8601", "").split("T")[0]
            return None
        except Exception:
            return None
    
    def _parse_pypi_data(self, data: Dict) -> Dict:
        """PyPI 응답 데이터 파싱"""
        info = data.get("info", {})
        
        return {
            "name": info.get("name"),
            "version": info.get("version"),
            "summary": info.get("summary"),
            "author": info.get("author"),
            "license": info.get("license"),
            "home_page": info.get("home_page"),
            "project_urls": info.get("project_urls", {}),
            "requires_dist": info.get("requires_dist", []),
            "requires_python": info.get("requires_python"),
            "classifiers": info.get("classifiers", []),
            "download_url": info.get("download_url"),
        }
    
    def collect_dependencies(self, package_name: str) -> List[str]:
        """패키지의 의존성 목록 추출"""
        package_data = self.collect_pypi_package(package_name)
        
        if not package_data:
            return []
        
        requires_dist = package_data.get("requires_dist", [])
        dependencies = []
        
        for req in requires_dist:
            if not req:
                continue
            # "package_name (>=version)" 형식에서 패키지명만 추출
            dep_name = req.split()[0].split("[")[0].strip()
            dependencies.append(dep_name)
        
        return dependencies
    
    def collect_batch(self, package_names: List[str], output_file: str):
        """여러 패키지를 배치로 수집"""
        results = {}
        total = len(package_names)
        
        logger.info(f"총 {total}개 패키지 수집 시작")
        
        for idx, package_name in enumerate(package_names, 1):
            if idx % 100 == 0:
                logger.info(f"진행률: {idx}/{total} ({idx/total*100:.1f}%)")
            
            package_data = self.collect_pypi_package(package_name)
            if package_data:
                results[package_name] = package_data
            
            # Rate limiting
            time.sleep(0.1)
        
        # 결과 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"수집 완료: {len(results)}개 패키지 저장됨 -> {output_file}")
        return results


if __name__ == "__main__":
    # 사용 예시
    collector = PackageCollector(cutoff_date="2021-11-01")
    
    # 단일 패키지 수집
    package_data = collector.collect_pypi_package("requests")
    print(json.dumps(package_data, indent=2))
    
    # 의존성 수집
    deps = collector.collect_dependencies("flask")
    print(f"Flask 의존성: {deps}")
