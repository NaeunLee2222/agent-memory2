# backend/main.py - 최소 기능으로 수정

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import asyncio
import os
import json

# 기본 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 임시 데이터 저장소 (실제로는 데이터베이스 사용)
memory_store = {}
feedback_store = {}

# 피드백 요청 모델
class FeedbackRequest(BaseModel):
    agent_id: str
    feedback_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

# 메모리 저장 요청 모델
class MemoryStoreRequest(BaseModel):
    memory_type: str
    content: Dict[str, Any]
    agent_id: str
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

# 모델 임포트 (절대 경로)
try:
    from models.memory import MemoryType, MemoryData
    from models.feedback import FeedbackType, FeedbackData
    from models.agent import AgentRequest, AgentResponse, AgentMode
    logger.info("Models imported successfully")
except ImportError as e:
    logger.error(f"Failed to import models: {e}")
    # 임포트 실패 시 기본 클래스들 정의
    from pydantic import BaseModel
    from enum import Enum
    
    class MemoryType(str, Enum):
        WORKING = "working"
        EPISODIC = "episodic"
        SEMANTIC = "semantic"
        PROCEDURAL = "procedural"
    
    class FeedbackType(str, Enum):
        SUCCESS = "success"
        ERROR = "error"
        USER_CORRECTION = "user_correction"
        PERFORMANCE = "performance"
        OPTIMIZATION = "optimization"
    
    class AgentMode(str, Enum):
        FLOW = "flow"
        BASIC = "basic"
    
    class AgentRequest(BaseModel):
        agent_id: str
        message: str
        mode: AgentMode = AgentMode.BASIC
        session_id: Optional[str] = None
    
    class AgentResponse(BaseModel):
        agent_id: str
        response: str
        timestamp: datetime
        processing_time: float
        mode: AgentMode

# FastAPI 앱 생성
app = FastAPI(
    title="Agent Memory & Feedback System",
    description="Enhanced Agentic AI Platform with Memory and Feedback Loop",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 임시 데이터 저장소 (실제로는 데이터베이스 사용)
memory_store = {}
feedback_store = {}

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Agent Memory & Feedback System API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api": True,
                "memory_store": len(memory_store),
                "feedback_store": len(feedback_store)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.post("/api/v1/agents/chat")
async def chat_with_agent(request: AgentRequest):
    """에이전트와 채팅 (기본 구현)"""
    try:
        start_time = datetime.utcnow()
        
        # 기본 응답 생성
        response_content = f"Echo: {request.message}" # 수정 필요
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        response = AgentResponse(
            agent_id=request.agent_id,
            response=response_content,
            timestamp=datetime.utcnow(),
            processing_time=processing_time,
            mode=request.mode
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in agent chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/memory/store")
async def store_memory(request: MemoryStoreRequest):
    """메모리 저장 (JSON body 방식)"""
    try:
        memory_id = f"{request.agent_id}_{len(memory_store)}"
        
        memory_data = {
            "memory_id": memory_id,
            "memory_type": request.memory_type,
            "content": request.content,
            "agent_id": request.agent_id,
            "context": request.context or {},
            "metadata": request.metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        memory_store[memory_id] = memory_data
        
        return {"memory_id": memory_id, "status": "stored"}
        
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/memory/{agent_id}")
async def get_memories(
    agent_id: str = Path(..., description="Agent ID"),
    memory_type: Optional[str] = Query(None, description="Memory type filter"),
    limit: Optional[int] = Query(10, description="Maximum number of memories to return")
):
    """에이전트의 메모리 조회"""
    try:
        agent_memories = []
        
        for memory_id, memory_data in memory_store.items():
            if memory_data["agent_id"] == agent_id:
                if memory_type is None or memory_data["memory_type"] == memory_type:
                    agent_memories.append(memory_data)
        
        # 최신 순으로 정렬
        agent_memories.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if limit:
            agent_memories = agent_memories[:limit]
        
        return {"memories": agent_memories, "count": len(agent_memories)}
        
    except Exception as e:
        logger.error(f"Error retrieving memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/v1/memory/{agent_id}/stats")
async def get_memory_stats(agent_id: str = Path(..., description="Agent ID")):
    """에이전트의 메모리 통계 조회"""
    try:
        agent_memories = []
        
        # 해당 에이전트의 모든 메모리 수집
        for memory_id, memory_data in memory_store.items():
            if memory_data["agent_id"] == agent_id:
                agent_memories.append(memory_data)
        
        # 통계 계산
        total_memories = len(agent_memories)
        by_type = {}
        total_storage_used = 0
        
        for memory in agent_memories:
            memory_type = memory["memory_type"]
            if memory_type not in by_type:
                by_type[memory_type] = 0
            by_type[memory_type] += 1
            
            # 대략적인 크기 계산 (JSON 직렬화 크기)
            content_size = len(json.dumps(memory["content"], default=str))
            total_storage_used += content_size
        
        # 평균 크기 계산
        avg_memory_size = total_storage_used / total_memories if total_memories > 0 else 0
        
        stats = {
            "agent_id": agent_id,
            "total_memories": total_memories,
            "by_type": by_type,
            "total_storage_used": total_storage_used,
            "avg_memory_size": avg_memory_size,
            "memory_types": list(by_type.keys()),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/v1/memory/{agent_id}/search")
async def search_memories(
    agent_id: str = Path(..., description="Agent ID"),
    query: str = Query(..., description="Search query"),
    memory_types: Optional[List[str]] = Query(None, description="Memory types to search"),
    limit: Optional[int] = Query(10, description="Maximum results")
):
    """메모리 검색"""
    try:
        agent_memories = []
        
        # 해당 에이전트의 메모리 수집
        for memory_id, memory_data in memory_store.items():
            if memory_data["agent_id"] == agent_id:
                if memory_types is None or memory_data["memory_type"] in memory_types:
                    agent_memories.append(memory_data)
        
        # 간단한 텍스트 검색 (실제로는 벡터 검색 사용)
        query_lower = query.lower()
        matched_memories = []
        
        for memory in agent_memories:
            content_str = json.dumps(memory["content"], default=str).lower()
            if query_lower in content_str:
                matched_memories.append(memory)
        
        # 최신 순으로 정렬
        matched_memories.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if limit:
            matched_memories = matched_memories[:limit]
        
        return {"results": matched_memories, "count": len(matched_memories)}
        
    except Exception as e:
        logger.error(f"Error searching memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/feedback/collect")
async def collect_feedback(feedback_request: FeedbackRequest):
    """피드백 수집 (JSON body 방식)"""
    try:
        feedback_id = f"{feedback_request.agent_id}_{len(feedback_store)}"
        
        feedback_data = {
            "feedback_id": feedback_id,
            "agent_id": feedback_request.agent_id,
            "feedback_type": feedback_request.feedback_type,
            "content": feedback_request.content,
            "metadata": feedback_request.metadata or {},
            "context": feedback_request.context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        feedback_store[feedback_id] = feedback_data
        
        return {"feedback_id": feedback_id, "status": "collected"}
        
    except Exception as e:
        logger.error(f"Error collecting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/v1/feedback/collect-alt")
async def collect_feedback_alt(
    agent_id: str = Query(..., description="Agent ID"),
    feedback_type: str = Query(..., description="Feedback type"),
    content: str = Query(..., description="Feedback content"),
    metadata: Optional[str] = Query(None, description="Metadata as JSON string"),
    context: Optional[str] = Query(None, description="Context as JSON string")
):
    """피드백 수집 (Query parameter 방식 - 대안)"""
    try:
        import json
        
        # JSON 문자열 파싱
        parsed_metadata = {}
        parsed_context = {}
        
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                parsed_metadata = {"raw": metadata}
        
        if context:
            try:
                parsed_context = json.loads(context)
            except json.JSONDecodeError:
                parsed_context = {"raw": context}
        
        feedback_id = f"{agent_id}_{len(feedback_store)}"
        
        feedback_data = {
            "feedback_id": feedback_id,
            "agent_id": agent_id,
            "feedback_type": feedback_type,
            "content": content,
            "metadata": parsed_metadata,
            "context": parsed_context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        feedback_store[feedback_id] = feedback_data
        
        return {"feedback_id": feedback_id, "status": "collected"}
        
    except Exception as e:
        logger.error(f"Error collecting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/feedback/{agent_id}/insights")
async def get_feedback_insights(
    agent_id: str = Path(..., description="Agent ID"),
    time_range_hours: Optional[int] = Query(24, description="Time range in hours")
):
    """피드백 인사이트 조회"""
    try:
        agent_feedback = []
        
        # 해당 에이전트의 피드백 수집
        for feedback_id, feedback_data in feedback_store.items():
            if feedback_data["agent_id"] == agent_id:
                agent_feedback.append(feedback_data)
        
        # 피드백 타입별 집계
        feedback_types = {}
        for feedback in agent_feedback:
            feedback_type = feedback["feedback_type"]
            if feedback_type not in feedback_types:
                feedback_types[feedback_type] = 0
            feedback_types[feedback_type] += 1
        
        # 성공률 계산
        success_count = feedback_types.get("success", 0)
        error_count = feedback_types.get("error", 0)
        total_outcome_feedback = success_count + error_count
        
        success_rate = 0.0
        if total_outcome_feedback > 0:
            success_rate = success_count / total_outcome_feedback
        
        insights = {
            "agent_id": agent_id,
            "total_feedback_count": len(agent_feedback),
            "feedback_types": feedback_types,
            "success_rate": success_rate,
            "time_range_hours": time_range_hours,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting feedback insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/performance/system")
async def get_system_performance():
    """시스템 성능 정보 조회 (기본 구현)"""
    try:
        # 간단한 시스템 메트릭 시뮬레이션
        import psutil
        import random
        
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else random.uniform(20, 60),
            "available_memory_mb": psutil.virtual_memory().available / (1024 * 1024),
        }
        
        return {
            "overall_health": "healthy" if system_metrics["cpu_percent"] < 80 else "warning",
            "system_metrics": system_metrics,
            "memory_usage": {
                "total_memories": len(memory_store),
                "total_feedback": len(feedback_store)
            },
            "uptime_hours": random.uniform(1, 24),  # 시뮬레이션
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system performance: {str(e)}")
        # psutil이 없는 경우 시뮬레이션 데이터 반환
        return {
            "overall_health": "healthy",
            "system_metrics": {
                "cpu_percent": random.uniform(10, 50),
                "memory_percent": random.uniform(30, 70),
                "disk_usage_percent": random.uniform(20, 60),
                "available_memory_mb": random.uniform(1000, 4000),
            },
            "memory_usage": {
                "total_memories": len(memory_store),
                "total_feedback": len(feedback_store)
            },
            "uptime_hours": random.uniform(1, 24),
            "timestamp": datetime.utcnow().isoformat()
        }
    
@app.get("/api/v1/performance/agents")
async def get_all_agents_performance():
    """모든 에이전트 성능 정보 조회"""
    try:
        # 모든 에이전트 ID 수집
        agent_ids = set()
        for memory in memory_store.values():
            agent_ids.add(memory["agent_id"])
        for feedback in feedback_store.values():
            agent_ids.add(feedback["agent_id"])
        
        agents_performance = {}
        
        for agent_id in agent_ids:
            # 각 에이전트의 메모리 및 피드백 통계
            agent_memories = [m for m in memory_store.values() if m["agent_id"] == agent_id]
            agent_feedbacks = [f for f in feedback_store.values() if f["agent_id"] == agent_id]
            
            success_count = len([f for f in agent_feedbacks if f["feedback_type"] == "success"])
            error_count = len([f for f in agent_feedbacks if f["feedback_type"] == "error"])
            total_outcome = success_count + error_count
            
            agents_performance[agent_id] = {
                "agent_id": agent_id,
                "total_memories": len(agent_memories),
                "total_feedback": len(agent_feedbacks),
                "success_rate": success_count / total_outcome if total_outcome > 0 else 0,
                "health_status": "healthy" if success_count >= error_count else "warning",
                "last_activity": max([m["timestamp"] for m in agent_memories] + [f["timestamp"] for f in agent_feedbacks]) if (agent_memories or agent_feedbacks) else None
            }
        
        return agents_performance
        
    except Exception as e:
        logger.error(f"Error getting agents performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/memory/metrics")
async def get_memory_metrics():
    """메모리 시스템 메트릭 (Prometheus 호환)"""
    try:
        metrics_output = []
        
        # 메모리 관련 메트릭
        metrics_output.append("# HELP memory_total_count Total number of stored memories")
        metrics_output.append("# TYPE memory_total_count gauge")
        metrics_output.append(f"memory_total_count {len(memory_store)}")
        
        # 에이전트별 메모리 수
        agent_memory_counts = {}
        for memory in memory_store.values():
            agent_id = memory["agent_id"]
            agent_memory_counts[agent_id] = agent_memory_counts.get(agent_id, 0) + 1
        
        metrics_output.append("# HELP memory_count_by_agent Memory count per agent")
        metrics_output.append("# TYPE memory_count_by_agent gauge")
        for agent_id, count in agent_memory_counts.items():
            metrics_output.append(f'memory_count_by_agent{{agent_id="{agent_id}"}} {count}')
        
        return "\n".join(metrics_output)
        
    except Exception as e:
        logger.error(f"Error generating memory metrics: {str(e)}")
        return f"# Error: {str(e)}\n"

@app.get("/api/v1/feedback/metrics")
async def get_feedback_metrics():
    """피드백 시스템 메트릭 (Prometheus 호환)"""
    try:
        metrics_output = []
        
        # 피드백 관련 메트릭
        metrics_output.append("# HELP feedback_total_count Total number of collected feedback")
        metrics_output.append("# TYPE feedback_total_count gauge")
        metrics_output.append(f"feedback_total_count {len(feedback_store)}")
        
        # 피드백 타입별 집계
        feedback_type_counts = {}
        for feedback in feedback_store.values():
            feedback_type = feedback["feedback_type"]
            feedback_type_counts[feedback_type] = feedback_type_counts.get(feedback_type, 0) + 1
        
        metrics_output.append("# HELP feedback_count_by_type Feedback count by type")
        metrics_output.append("# TYPE feedback_count_by_type gauge")
        for feedback_type, count in feedback_type_counts.items():
            metrics_output.append(f'feedback_count_by_type{{type="{feedback_type}"}} {count}')
        
        return "\n".join(metrics_output)
        
    except Exception as e:
        logger.error(f"Error generating feedback metrics: {str(e)}")
        return f"# Error: {str(e)}\n"
    
@app.get("/api/v1/performance/metrics")
async def get_performance_metrics(
    time_range_hours: Optional[int] = Query(1, description="Time range in hours"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID")
):
    """성능 메트릭 조회"""
    try:
        import random
        
        metrics = {
            "time_range_hours": time_range_hours,
            "agent_id": agent_id,
            "metrics": {
                "response_time": {
                    "avg": random.uniform(0.5, 2.0),
                    "max": random.uniform(2.0, 5.0),
                    "min": random.uniform(0.1, 0.5),
                    "count": len(memory_store) + len(feedback_store)
                },
                "throughput": {
                    "requests_per_minute": random.uniform(10, 100),
                    "successful_requests": random.randint(90, 100),
                    "failed_requests": random.randint(0, 10)
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus 메트릭 엔드포인트"""
    try:
        metrics_output = []
        
        # 기본 메트릭들
        metrics_output.append("# HELP agent_requests_total Total number of agent requests")
        metrics_output.append("# TYPE agent_requests_total counter")
        metrics_output.append(f"agent_requests_total {len(memory_store) + len(feedback_store)}")
        
        metrics_output.append("# HELP agent_memory_count Number of stored memories")
        metrics_output.append("# TYPE agent_memory_count gauge")
        metrics_output.append(f"agent_memory_count {len(memory_store)}")
        
        metrics_output.append("# HELP agent_feedback_count Number of collected feedback")
        metrics_output.append("# TYPE agent_feedback_count gauge")
        metrics_output.append(f"agent_feedback_count {len(feedback_store)}")
        
        return "\n".join(metrics_output)
        
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {str(e)}")
        return f"# Error: {str(e)}\n"

# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 핸들러"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )