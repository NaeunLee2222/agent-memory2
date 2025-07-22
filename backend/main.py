# backend/main.py - 최소 기능으로 수정

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import asyncio
import os

# 기본 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        response_content = f"Echo: {request.message}"
        
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
async def store_memory(
    memory_type: str,
    content: Dict[str, Any],
    agent_id: str,
    context: Optional[Dict[str, Any]] = None
):
    """메모리 저장 (기본 구현)"""
    try:
        memory_id = f"{agent_id}_{len(memory_store)}"
        
        memory_data = {
            "memory_id": memory_id,
            "memory_type": memory_type,
            "content": content,
            "agent_id": agent_id,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        memory_store[memory_id] = memory_data
        
        return {"memory_id": memory_id, "status": "stored"}
        
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/memory/{agent_id}")
async def get_memories(
    agent_id: str,
    memory_type: Optional[str] = None,
    limit: Optional[int] = 10
):
    """메모리 조회 (기본 구현)"""
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

@app.post("/api/v1/feedback/collect")
async def collect_feedback(
    agent_id: str,
    feedback_type: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
):
    """피드백 수집 (기본 구현)"""
    try:
        feedback_id = f"{agent_id}_{len(feedback_store)}"
        
        feedback_data = {
            "feedback_id": feedback_id,
            "agent_id": agent_id,
            "feedback_type": feedback_type,
            "content": content,
            "metadata": metadata or {},
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        feedback_store[feedback_id] = feedback_data
        
        return {"feedback_id": feedback_id, "status": "collected"}
        
    except Exception as e:
        logger.error(f"Error collecting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/feedback/{agent_id}/insights")
async def get_feedback_insights(
    agent_id: str,
    time_range_hours: Optional[int] = 24
):
    """피드백 인사이트 조회 (기본 구현)"""
    try:
        agent_feedback = []
        
        for feedback_id, feedback_data in feedback_store.items():
            if feedback_data["agent_id"] == agent_id:
                agent_feedback.append(feedback_data)
        
        insights = {
            "agent_id": agent_id,
            "total_feedback_count": len(agent_feedback),
            "feedback_types": {},
            "time_range_hours": time_range_hours
        }
        
        # 피드백 타입별 집계
        for feedback in agent_feedback:
            feedback_type = feedback["feedback_type"]
            if feedback_type not in insights["feedback_types"]:
                insights["feedback_types"][feedback_type] = 0
            insights["feedback_types"][feedback_type] += 1
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting feedback insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/performance/system")
async def get_system_performance():
    """시스템 성능 정보 조회 (기본 구현)"""
    try:
        return {
            "overall_health": "healthy",
            "memory_usage": {
                "total_memories": len(memory_store),
                "total_feedback": len(feedback_store)
            },
            "uptime": "running",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system performance: {str(e)}")
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