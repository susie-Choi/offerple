"""
신호 추출 모듈 테스트
"""
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.signal_extraction.vulnerability_patterns import VulnerabilityPatternExtractor


def test_vulnerability_pattern_extraction():
    """취약점 패턴 추출 테스트"""
    
    # 테스트 데이터
    vulnerabilities_data = {
        "package_a": [
            {
                "cve_id": "CVE-2021-0001",
                "published_date": "2021-01-01",
                "cvss_score": 9.8,
                "vulnerability_type": "RCE"
            },
            {
                "cve_id": "CVE-2021-0002",
                "published_date": "2021-06-01",
                "cvss_score": 7.5,
                "vulnerability_type": "XSS"
            }
        ],
        "package_b": []
    }
    
    extractor = VulnerabilityPatternExtractor(cutoff_date="2021-12-31")
    patterns = extractor.extract_patterns(vulnerabilities_data)
    
    # package_a 검증
    assert patterns["package_a"]["total_cves"] == 2
    assert patterns["package_a"]["critical_cves"] == 1  # CVSS >= 9.0
    assert patterns["package_a"]["high_cves"] == 1     # 7.0 <= CVSS < 9.0
    assert patterns["package_a"]["avg_cvss"] > 8.0
    
    # package_b 검증 (CVE 없음)
    assert patterns["package_b"]["total_cves"] == 0
    assert patterns["package_b"]["risk_score"] == 0.0


def test_risk_score_calculation():
    """위험 점수 계산 테스트"""
    
    vulnerabilities_data = {
        "high_risk": [
            {"cve_id": f"CVE-2021-000{i}", "published_date": f"2021-0{i}-01", 
             "cvss_score": 9.0, "vulnerability_type": "RCE"}
            for i in range(1, 6)  # 5개의 Critical CVE
        ],
        "low_risk": [
            {"cve_id": "CVE-2021-0001", "published_date": "2021-01-01",
             "cvss_score": 4.0, "vulnerability_type": "OTHER"}
        ]
    }
    
    extractor = VulnerabilityPatternExtractor(cutoff_date="2021-12-31")
    patterns = extractor.extract_patterns(vulnerabilities_data)
    
    # high_risk가 low_risk보다 높은 점수를 가져야 함
    assert patterns["high_risk"]["risk_score"] > patterns["low_risk"]["risk_score"]
    assert patterns["high_risk"]["risk_score"] > 0.5
    assert patterns["low_risk"]["risk_score"] < 0.3


def test_vulnerability_trend_analysis():
    """취약점 추세 분석 테스트"""
    
    # 증가 추세
    increasing_cves = [
        {"cve_id": "CVE-2020-0001", "published_date": "2020-01-01", "cvss_score": 7.0, "vulnerability_type": "RCE"},
        {"cve_id": "CVE-2021-0001", "published_date": "2021-01-01", "cvss_score": 7.0, "vulnerability_type": "RCE"},
        {"cve_id": "CVE-2021-0002", "published_date": "2021-06-01", "cvss_score": 7.0, "vulnerability_type": "RCE"},
        {"cve_id": "CVE-2021-0003", "published_date": "2021-09-01", "cvss_score": 7.0, "vulnerability_type": "RCE"},
    ]
    
    vulnerabilities_data = {"increasing_package": increasing_cves}
    
    extractor = VulnerabilityPatternExtractor(cutoff_date="2021-12-31")
    patterns = extractor.extract_patterns(vulnerabilities_data)
    
    # 최근 1년에 3개 발생 (증가 추세)
    assert patterns["increasing_package"]["trend"] in ["increasing", "stable"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
