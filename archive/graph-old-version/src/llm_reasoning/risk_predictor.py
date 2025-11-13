"""
LLM 기반 잠재 위협 예측 모듈
다차원 신호를 통합하여 유추 기반 추론 수행
"""
import json
import logging
from typing import Dict, List, Optional
import os
from openai import OpenAI
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMRiskPredictor:
    """LLM 기반 유추 추론 및 잠재 위험 예측"""
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4",
        api_key: Optional[str] = None
    ):
        """
        Args:
            provider: "openai" 또는 "anthropic"
            model: 사용할 모델명
            api_key: API 키 (없으면 환경변수에서 로드)
        """
        self.provider = provider
        self.model = model
        
        if provider == "openai":
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        elif provider == "anthropic":
            self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"지원하지 않는 provider: {provider}")
    
    def predict_risk(
        self,
        package_name: str,
        signals: Dict,
        cluster_info: Optional[Dict] = None
    ) -> Dict:
        """단일 패키지의 잠재 위험 예측"""
        
        # 프롬프트 생성
        prompt = self._build_prompt(package_name, signals, cluster_info)
        
        # LLM 호출
        try:
            response = self._call_llm(prompt)
            
            # 응답 파싱
            risk_score, reasoning = self._parse_response(response)
            
            return {
                "package_name": package_name,
                "risk_score": risk_score,
                "reasoning": reasoning,
                "confidence": self._estimate_confidence(response),
            }
            
        except Exception as e:
            logger.error(f"LLM 예측 실패 ({package_name}): {e}")
            return {
                "package_name": package_name,
                "risk_score": 0.0,
                "reasoning": "예측 실패",
                "confidence": 0.0,
            }
    
    def _build_prompt(
        self,
        package_name: str,
        signals: Dict,
        cluster_info: Optional[Dict]
    ) -> str:
        """LLM 프롬프트 생성"""
        
        # 과거 취약점 이력
        vuln_patterns = signals.get("vulnerability_patterns", {})
        total_cves = vuln_patterns.get("total_cves", 0)
        critical_cves = vuln_patterns.get("critical_cves", 0)
        avg_cvss = vuln_patterns.get("avg_cvss", 0.0)
        vuln_types = vuln_patterns.get("vulnerability_types", {})
        trend = vuln_patterns.get("trend", "none")
        
        # 그래프 신호
        graph_signals = signals.get("graph_signals", {})
        pagerank = graph_signals.get("pagerank", 0.0)
        downstream_impact = graph_signals.get("downstream_impact", 0)
        in_degree = graph_signals.get("in_degree", 0)
        
        # 코드 신호
        code_signals = signals.get("code_signals", {})
        dangerous_functions = code_signals.get("dangerous_functions", 0)
        complexity = code_signals.get("complexity_score", 0)
        
        prompt = f"""당신은 소프트웨어 보안 전문가입니다. 다음 패키지의 잠재적 취약점 발생 가능성을 평가해주세요.

패키지명: {package_name}

## 과거 취약점 이력 (CVE 공개 전 시점 기준)
- 총 CVE 수: {total_cves}개
- Critical 등급 CVE: {critical_cves}개
- 평균 CVSS 점수: {avg_cvss}
- 주요 취약점 유형: {', '.join(f'{k}({v}개)' for k, v in vuln_types.items())}
- 취약점 발생 추세: {trend}

## 생태계 내 위치
- PageRank (전역 중요도): {pagerank:.6f}
- 하류 영향 범위: {downstream_impact}개 패키지가 직간접적으로 의존
- 직접 의존 패키지 수: {in_degree}개

## 코드 레벨 특징
- 위험 함수 사용: {dangerous_functions}개
- 코드 복잡도: {complexity}
"""
        
        # 군집 정보 추가
        if cluster_info:
            similar_packages = cluster_info.get("similar_packages", [])
            common_patterns = cluster_info.get("common_patterns", [])
            
            prompt += f"""
## 유사 패키지 군집 정보
- 동일 군집 내 유사 패키지: {', '.join(similar_packages[:5])}
- 공통 패턴: {', '.join(common_patterns)}
"""
        
        prompt += """
## 질문
위 정보를 바탕으로, 이 패키지에서 향후 Critical 또는 High 등급의 취약점이 발생할 가능성을 평가해주세요.

**중요**: CVE가 공개되기 전 시점이므로, 실제 취약점 정보는 알 수 없습니다. 
오직 관찰 가능한 사전 신호(과거 이력, 코드 패턴, 생태계 위치)만을 근거로 판단해주세요.

다음 형식으로 답변해주세요:
1. 위험 점수: 0.0 ~ 1.0 사이의 숫자 (1.0이 가장 위험)
2. 근거: 왜 이런 점수를 부여했는지 구체적으로 설명

답변 형식:
RISK_SCORE: [0.0-1.0 사이의 숫자]
REASONING: [구체적인 근거]
"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """LLM API 호출"""
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 소프트웨어 보안 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content
        
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
    
    def _parse_response(self, response: str) -> tuple[float, str]:
        """LLM 응답 파싱"""
        risk_score = 0.5  # 기본값
        reasoning = response
        
        # RISK_SCORE 추출
        for line in response.split('\n'):
            if line.startswith("RISK_SCORE:"):
                try:
                    score_str = line.split(":", 1)[1].strip()
                    risk_score = float(score_str)
                    risk_score = max(0.0, min(1.0, risk_score))  # 0-1 범위로 제한
                except ValueError:
                    pass
            
            if line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
        
        return risk_score, reasoning
    
    def _estimate_confidence(self, response: str) -> float:
        """응답의 신뢰도 추정 (간단한 휴리스틱)"""
        # 응답 길이가 충분하고 구체적인 근거가 있으면 높은 신뢰도
        if len(response) > 100 and "REASONING:" in response:
            return 0.8
        return 0.5
    
    def predict_batch(
        self,
        packages: List[str],
        all_signals: Dict[str, Dict],
        cluster_info: Optional[Dict[str, Dict]] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Dict]:
        """여러 패키지를 배치로 예측"""
        logger.info(f"총 {len(packages)}개 패키지 LLM 예측 시작")
        
        results = {}
        
        for idx, package_name in enumerate(packages, 1):
            if idx % 10 == 0:
                logger.info(f"진행률: {idx}/{len(packages)} ({idx/len(packages)*100:.1f}%)")
            
            signals = all_signals.get(package_name, {})
            cluster = cluster_info.get(package_name) if cluster_info else None
            
            prediction = self.predict_risk(package_name, signals, cluster)
            results[package_name] = prediction
        
        # 결과 저장
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"예측 결과 저장: {output_file}")
        
        return results


if __name__ == "__main__":
    # 사용 예시
    # 신호 데이터 로드
    with open("data/processed/signals/integrated_signals.json", 'r') as f:
        all_signals = json.load(f)
    
    # 핵심 노드만 LLM 예측 (비용 절감)
    with open("data/processed/critical_nodes.json", 'r') as f:
        critical_nodes = json.load(f)
    
    # LLM 예측기 초기화
    predictor = LLMRiskPredictor(provider="openai", model="gpt-4")
    
    # 배치 예측
    predictions = predictor.predict_batch(
        packages=critical_nodes[:100],  # 상위 100개만
        all_signals=all_signals,
        output_file="data/processed/llm_predictions.json"
    )
    
    # 고위험 패키지 출력
    high_risk = {k: v for k, v in predictions.items() if v["risk_score"] > 0.7}
    print(f"고위험 패키지 {len(high_risk)}개 발견")
