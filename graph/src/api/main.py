"""
FastAPI 기반 REST API 서버
잠재 위험 점수 조회 및 예측 결과 제공
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Zero-Day Defense API",
    description="LLM 기반 잠재 위협 사전 탐지 시스템",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 로드 (서버 시작 시)
DATA_DIR = Path("data/processed/scores")
risk_scores = {}
graph_metrics = {}

@app.on_event("startup")
async def load_data():
    """서버 시작 시 데이터 로드"""
    global risk_scores, graph_metrics
    
    try:
        with open(DATA_DIR / "latent_risk_scores.json", 'r') as f:
            risk_scores = json.load(f)
        logger.info(f"위험 점수 데이터 로드 완료: {len(risk_scores)}개 패키지")
        
        with open("data/processed/signals/graph_signals.json", 'r') as f:
            graph_metrics = json.load(f)
        logger.info(f"그래프 메트릭 로드 완료: {len(graph_metrics)}개 패키지")
        
    except Exception as e:
        logger.error(f"데이터 로드 실패: {e}")


# Response Models
class RiskScoreResponse(BaseModel):
    package_name: str
    final_score: float
    signal_score: float
    llm_score: float
    rank: int
    percentile: float
    llm_reasoning: Optional[str] = None


class TopRisksResponse(BaseModel):
    total_packages: int
    top_k: int
    packages: List[RiskScoreResponse]


class GraphMetricsResponse(BaseModel):
    package_name: str
    pagerank: float
    betweenness: float
    in_degree: int
    out_degree: int
    downstream_impact: int


# API Endpoints
@app.get("/")
async def root():
    """API 루트"""
    return {
        "message": "Zero-Day Defense API",
        "version": "0.1.0",
        "endpoints": {
            "risk_score": "/api/v1/risk/{package_name}",
            "top_risks": "/api/v1/risks/top",
            "search": "/api/v1/risks/search",
            "graph_metrics": "/api/v1/graph/{package_name}",
            "stats": "/api/v1/stats"
        }
    }


@app.get("/api/v1/risk/{package_name}", response_model=RiskScoreResponse)
async def get_risk_score(package_name: str):
    """특정 패키지의 잠재 위험 점수 조회"""
    
    if package_name not in risk_scores:
        raise HTTPException(status_code=404, detail=f"패키지 '{package_name}'를 찾을 수 없습니다")
    
    data = risk_scores[package_name]
    return RiskScoreResponse(**data)


@app.get("/api/v1/risks/top", response_model=TopRisksResponse)
async def get_top_risks(
    k: int = Query(100, ge=1, le=1000, description="상위 K개 패키지"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="최소 위험 점수")
):
    """상위 K개 고위험 패키지 조회"""
    
    # 점수순 정렬
    sorted_packages = sorted(
        risk_scores.items(),
        key=lambda x: x[1]["final_score"],
        reverse=True
    )
    
    # 필터링
    filtered = [
        RiskScoreResponse(package_name=pkg, **data)
        for pkg, data in sorted_packages[:k]
        if data["final_score"] >= min_score
    ]
    
    return TopRisksResponse(
        total_packages=len(risk_scores),
        top_k=len(filtered),
        packages=filtered
    )


@app.get("/api/v1/risks/search")
async def search_packages(
    query: str = Query(..., min_length=1, description="검색 쿼리"),
    limit: int = Query(20, ge=1, le=100)
):
    """패키지명으로 검색"""
    
    query_lower = query.lower()
    
    results = [
        {"package_name": pkg, **data}
        for pkg, data in risk_scores.items()
        if query_lower in pkg.lower()
    ]
    
    # 위험 점수순 정렬
    results.sort(key=lambda x: x["final_score"], reverse=True)
    
    return {
        "query": query,
        "total_results": len(results),
        "results": results[:limit]
    }


@app.get("/api/v1/graph/{package_name}", response_model=GraphMetricsResponse)
async def get_graph_metrics(package_name: str):
    """특정 패키지의 그래프 메트릭 조회"""
    
    if package_name not in graph_metrics:
        raise HTTPException(status_code=404, detail=f"패키지 '{package_name}'를 찾을 수 없습니다")
    
    data = graph_metrics[package_name]
    return GraphMetricsResponse(package_name=package_name, **data)


@app.get("/api/v1/stats")
async def get_statistics():
    """전체 통계 정보"""
    
    if not risk_scores:
        return {"error": "데이터가 로드되지 않았습니다"}
    
    scores = [data["final_score"] for data in risk_scores.values()]
    
    return {
        "total_packages": len(risk_scores),
        "statistics": {
            "mean_risk_score": round(sum(scores) / len(scores), 4),
            "median_risk_score": round(sorted(scores)[len(scores)//2], 4),
            "max_risk_score": round(max(scores), 4),
            "min_risk_score": round(min(scores), 4),
        },
        "risk_distribution": {
            "critical (>0.8)": sum(1 for s in scores if s > 0.8),
            "high (0.6-0.8)": sum(1 for s in scores if 0.6 <= s <= 0.8),
            "medium (0.4-0.6)": sum(1 for s in scores if 0.4 <= s < 0.6),
            "low (<0.4)": sum(1 for s in scores if s < 0.4),
        }
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "data_loaded": len(risk_scores) > 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
