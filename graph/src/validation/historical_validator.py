"""
Historical Validation 모듈
Log4Shell, Equifax 등 과거 사고를 사전에 탐지할 수 있었는지 검증
"""
import json
import logging
from typing import Dict, List, Tuple
from datetime import datetime
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoricalValidator:
    """과거 사고 재현 실험 및 성능 평가"""
    
    def __init__(self, cutoff_date: str, validation_cves: List[Dict]):
        """
        Args:
            cutoff_date: 예측 시점 (YYYY-MM-DD)
            validation_cves: 검증할 실제 CVE 목록
        """
        self.cutoff_date = datetime.strptime(cutoff_date, "%Y-%m-%d")
        self.validation_cves = validation_cves
    
    def validate_predictions(
        self,
        predictions: Dict[str, Dict],
        k_values: List[int] = [10, 50, 100, 500]
    ) -> Dict:
        """예측 결과를 실제 CVE 발생과 비교하여 성능 평가"""
        
        logger.info(f"Historical Validation 시작 (cutoff: {self.cutoff_date.date()})")
        
        # 예측 순위별로 정렬
        sorted_predictions = sorted(
            predictions.items(),
            key=lambda x: x[1].get("final_score", 0),
            reverse=True
        )
        
        # 실제로 취약점이 발생한 패키지 목록
        actual_vulnerable = self._get_vulnerable_packages()
        
        logger.info(f"검증 대상 취약점: {len(actual_vulnerable)}개 패키지")
        
        # Precision@K, Recall@K 계산
        results = {
            "cutoff_date": self.cutoff_date.strftime("%Y-%m-%d"),
            "total_predictions": len(sorted_predictions),
            "total_actual_vulnerabilities": len(actual_vulnerable),
            "metrics": {}
        }
        
        for k in k_values:
            top_k_packages = [pkg for pkg, _ in sorted_predictions[:k]]
            
            # True Positives: 예측한 것 중 실제로 취약점 발생
            true_positives = set(top_k_packages) & set(actual_vulnerable)
            
            precision = len(true_positives) / k if k > 0 else 0
            recall = len(true_positives) / len(actual_vulnerable) if actual_vulnerable else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            results["metrics"][f"top_{k}"] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "true_positives": len(true_positives),
                "detected_packages": list(true_positives)
            }
            
            logger.info(f"Top-{k}: Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")
        
        # Lead Time 계산
        lead_times = self._calculate_lead_times(sorted_predictions, actual_vulnerable)
        results["lead_times"] = lead_times
        
        return results
    
    def _get_vulnerable_packages(self) -> List[str]:
        """cutoff 이후 실제로 취약점이 발생한 패키지 목록"""
        vulnerable = []
        
        for cve in self.validation_cves:
            published_date = datetime.strptime(cve["published_date"], "%Y-%m-%d")
            
            # cutoff 이후에 공개된 CVE만
            if published_date > self.cutoff_date:
                # Critical 또는 High 등급만
                if cve.get("cvss_score", 0) >= 7.0:
                    vulnerable.append(cve["package_name"])
        
        return list(set(vulnerable))
    
    def _calculate_lead_times(
        self,
        sorted_predictions: List[Tuple[str, Dict]],
        actual_vulnerable: List[str]
    ) -> Dict:
        """예측 시점과 실제 CVE 공개 시점 간의 Lead Time 계산"""
        
        lead_times = []
        detected_ranks = []
        
        for cve in self.validation_cves:
            package_name = cve["package_name"]
            published_date = datetime.strptime(cve["published_date"], "%Y-%m-%d")
            
            # cutoff 이후 Critical/High CVE만
            if published_date > self.cutoff_date and cve.get("cvss_score", 0) >= 7.0:
                # 예측 순위 찾기
                rank = None
                for idx, (pred_pkg, _) in enumerate(sorted_predictions, 1):
                    if pred_pkg == package_name:
                        rank = idx
                        break
                
                if rank:
                    lead_time_days = (published_date - self.cutoff_date).days
                    lead_times.append(lead_time_days)
                    detected_ranks.append(rank)
        
        if lead_times:
            return {
                "avg_lead_time_days": round(np.mean(lead_times), 1),
                "median_lead_time_days": round(np.median(lead_times), 1),
                "min_lead_time_days": min(lead_times),
                "max_lead_time_days": max(lead_times),
                "avg_detection_rank": round(np.mean(detected_ranks), 1),
                "median_detection_rank": round(np.median(detected_ranks), 1),
            }
        
        return {}
    
    def validate_log4shell(self, predictions: Dict[str, Dict]) -> Dict:
        """Log4Shell (CVE-2021-44228) 특화 검증"""
        
        logger.info("=== Log4Shell Historical Validation ===")
        
        # Log4j 관련 패키지들
        log4j_packages = ["log4j", "log4j-core", "log4j-api", "apache-log4j"]
        
        results = {
            "case": "Log4Shell (CVE-2021-44228)",
            "cutoff_date": "2021-11-01",
            "cve_published_date": "2021-12-10",
            "lead_time_days": 39,
            "detected": False,
            "detection_details": {}
        }
        
        # 예측 순위 확인
        sorted_predictions = sorted(
            predictions.items(),
            key=lambda x: x[1].get("final_score", 0),
            reverse=True
        )
        
        for package in log4j_packages:
            for rank, (pred_pkg, pred_data) in enumerate(sorted_predictions, 1):
                if package.lower() in pred_pkg.lower():
                    results["detected"] = True
                    results["detection_details"][package] = {
                        "rank": rank,
                        "percentile": round((1 - rank / len(sorted_predictions)) * 100, 2),
                        "risk_score": pred_data.get("final_score", 0),
                        "reasoning": pred_data.get("llm_reasoning", "")
                    }
                    
                    logger.info(f"✓ {package} 탐지: 순위 {rank} (상위 {results['detection_details'][package]['percentile']}%)")
                    break
        
        if results["detected"]:
            logger.info(f"✓ Log4Shell 사전 탐지 성공!")
        else:
            logger.warning(f"✗ Log4Shell 탐지 실패")
        
        return results


if __name__ == "__main__":
    # 사용 예시: Log4Shell Historical Validation
    
    # 예측 결과 로드 (2021-11-01 시점)
    with open("data/historical/log4shell/predictions_2021-11-01.json", 'r') as f:
        predictions = json.load(f)
    
    # 실제 CVE 데이터 로드
    with open("data/historical/log4shell/actual_cves.json", 'r') as f:
        validation_cves = json.load(f)
    
    # Validator 초기화
    validator = HistoricalValidator(
        cutoff_date="2021-11-01",
        validation_cves=validation_cves
    )
    
    # 전체 성능 평가
    results = validator.validate_predictions(predictions)
    
    # Log4Shell 특화 검증
    log4shell_results = validator.validate_log4shell(predictions)
    
    # 결과 저장
    output = {
        "overall_metrics": results,
        "log4shell_case_study": log4shell_results
    }
    
    with open("data/results/log4shell_validation_results.json", 'w') as f:
        json.dump(output, f, indent=2)
    
    print(json.dumps(output, indent=2))
