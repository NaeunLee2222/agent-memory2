# backend/main.py - 완전 수정 버전

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import uvicorn
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

# 모든 await는 함수 내부에서만 사용해야 합니다!
# 여기서는 import만 하고, await 호출은 하지 않습니다.

from services.memory_service import MemoryService
from services.feedback_service import FeedbackService
from services.agent_service import AgentService
from database.memory_database import MemoryDatabase
from models.memory import MemoryType, MemoryData
from models.feedback import FeedbackType, FeedbackData
from models.agent import AgentRequest, AgentResponse
from evaluation.performance_monitor import get_performance_monitor, start_global_monitoring
from utils.logger import get_logger

logger = get_logger(__name__)

# Global services (초기화는 lifespan에서 수행)
memory_service: Optional[MemoryService] = None
feedback_service: Optional[FeedbackService] = None
agent_service: Optional[AgentService] = None
performance_monitor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global memory_service, feedback_service, agent_service, performance_monitor
    
    try:
        # 서비스 초기화
        logger.info("Initializing services...")
        
        # 데이터베이스 초기화
        memory_db = MemoryDatabase()
        await memory_db.initialize()
        
        # 서비스 인스턴스 생성
        memory_service = MemoryService(memory_db)
        feedback_service = FeedbackService(memory_service)
        agent_service = AgentService(memory_service, feedback_service)
        
        # 성능 모니터링 시작
        performance_monitor = await start_global_monitoring()
        
        # 피드백 프로세서 시작 (백그라운드 태스크로)
        asyncio.create_task(feedback_service.start_feedback_processor())
        
        logger.info("All services initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise
    finally:
        # 정리 작업
        logger.info("Shutting down services...")
        
        try:
            if feedback_service:
                feedback_service.is_processing = False  # 피드백 프로세서 중지
            
            if performance_monitor:
                performance_monitor.stop_monitoring()
                
            if memory_service:
                await memory_service.cleanup_expired_memories()
                
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

# FastAPI 앱 생성
app = FastAPI(
    title="Agent Memory & Feedback System",
    description="Enhanced Agentic AI Platform with Memory and Feedback Loop",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 의존성 함수들
def get_memory_service() -> MemoryService:
    if memory_service is None:
        raise HTTPException(status_code=503, detail="Memory service not initialized")
    return memory_service

def get_feedback_service() -> FeedbackService:
    if feedback_service is None:
        raise HTTPException(status_code=503, detail="Feedback service not initialized")
    return feedback_service

def get_agent_service() -> AgentService:
    if agent_service is None:
        raise HTTPException(status_code=503, detail="Agent service not initialized")
    return agent_service

# API 엔드포인트들

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
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "memory_service": memory_service is not None,
                "feedback_service": feedback_service is not None,
                "agent_service": agent_service is not None,
                "performance_monitor": performance_monitor is not None
            }
        }
        
        # 각 서비스의 상세 상태 확인
        if memory_service:
            try:
                stats = await memory_service.get_memory_stats()
                health_status["services"]["memory_service"] = {
                    "available": True,
                    "stats": stats
                }
            except Exception as e:
                health_status["services"]["memory_service"] = {
                    "available": False,
                    "error": str(e)
                }
                health_status["status"] = "degraded"
        
        if performance_monitor:
            try:
                monitor_health = await performance_monitor.health_check()
                health_status["services"]["performance_monitor"] = monitor_health
            except Exception as e:
                health_status["services"]["performance_monitor"] = {
                    "available": False,
                    "error": str(e)
                }
                health_status["status"] = "degraded"
        
        return health_status
        
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

# Agent API 엔드포인트들
@app.post("/api/v1/agents/chat", response_model=AgentResponse)
async def chat_with_agent(
    request: AgentRequest,
    agent_svc: AgentService = Depends(get_agent_service)
):
    """에이전트와 채팅"""
    try:
        response = await agent_svc.process_request(request)
        return response
    except Exception as e:
        logger.error(f"Error in agent chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agents/{agent_id}/performance")
async def get_agent_performance(agent_id: str):
    """에이전트 성능 정보 조회"""
    try:
        if performance_monitor:
            performance_data = performance_monitor.get_agent_performance(agent_id)
            if performance_data:
                return performance_data
            else:
                raise HTTPException(status_code=404, detail="Agent not found")
        else:
            raise HTTPException(status_code=503, detail="Performance monitor not available")
    except Exception as e:
        logger.error(f"Error getting agent performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Memory API 엔드포인트들
@app.post("/api/v1/memory/store")
async def store_memory(
    memory_data: MemoryData,
    memory_svc: MemoryService = Depends(get_memory_service)
):
    """메모리 저장"""
    try:
        memory_id = await memory_svc.store_memory(memory_data)
        return {"memory_id": memory_id, "status": "stored"}
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/memory/{agent_id}")
async def get_memories(
    agent_id: str,
    memory_type: Optional[MemoryType] = None,
    limit: Optional[int] = 10,
    memory_svc: MemoryService = Depends(get_memory_service)
):
    """메모리 조회"""
    try:
        memories = await memory_svc.retrieve_memories(
            agent_id=agent_id,
            memory_type=memory_type,
            limit=limit
        )
        return {"memories": memories, "count": len(memories)}
    except Exception as e:
        logger.error(f"Error retrieving memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/memory/{agent_id}/search")
async def search_memories(
    agent_id: str,
    query: str,
    memory_types: Optional[List[MemoryType]] = None,
    limit: Optional[int] = 10,
    memory_svc: MemoryService = Depends(get_memory_service)
):
    """메모리 검색"""
    try:
        results = await memory_svc.search_memories(
            agent_id=agent_id,
            query=query,
            memory_types=memory_types,
            limit=limit
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error searching memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/memory/{agent_id}/stats")
async def get_memory_stats(
    agent_id: str,
    memory_svc: MemoryService = Depends(get_memory_service)
):
    """메모리 통계 조회"""
    try:
        stats = await memory_svc.get_memory_stats(agent_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Feedback API 엔드포인트들
@app.post("/api/v1/feedback/collect")
async def collect_feedback(
    agent_id: str,
    feedback_type: FeedbackType,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    feedback_svc: FeedbackService = Depends(get_feedback_service)
):
    """피드백 수집"""
    try:
        feedback_id = await feedback_svc.collect_feedback(
            agent_id=agent_id,
            feedback_type=feedback_type,
            content=content,
            metadata=metadata,
            context=context
        )
        return {"feedback_id": feedback_id, "status": "collected"}
    except Exception as e:
        logger.error(f"Error collecting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/feedback/{agent_id}/insights")
async def get_feedback_insights(
    agent_id: str,
    time_range_hours: Optional[int] = 24,
    feedback_svc: FeedbackService = Depends(get_feedback_service)
):
    """피드백 인사이트 조회"""
    try:
        time_range = timedelta(hours=time_range_hours) if time_range_hours else None
        insights = await feedback_svc.get_feedback_insights(
            agent_id=agent_id,
            time_range=time_range
        )
        return insights
    except Exception as e:
        logger.error(f"Error getting feedback insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/feedback/processing-stats")
async def get_processing_stats(
    feedback_svc: FeedbackService = Depends(get_feedback_service)
):
    """피드백 처리 통계 조회"""
    try:
        stats = feedback_svc.get_processing_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting processing stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Performance API 엔드포인트들
@app.get("/api/v1/performance/system")
async def get_system_performance():
    """시스템 성능 정보 조회"""
    try:
        if performance_monitor:
            system_health = performance_monitor.get_system_health()
            return system_health
        else:
            raise HTTPException(status_code=503, detail="Performance monitor not available")
    except Exception as e:
        logger.error(f"Error getting system performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/performance/agents")
async def get_all_agents_performance():
    """모든 에이전트 성능 정보 조회"""
    try:
        if performance_monitor:
            agents_performance = performance_monitor.get_all_agents_performance()
            return agents_performance
        else:
            raise HTTPException(status_code=503, detail="Performance monitor not available")
    except Exception as e:
        logger.error(f"Error getting agents performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/performance/metrics")
async def get_performance_metrics(
    time_range_hours: Optional[int] = 1,
    agent_id: Optional[str] = None
):
    """성능 메트릭 조회 (Prometheus 형식)"""
    try:
        if performance_monitor:
            metrics_summary = performance_monitor.get_metrics_summary(
                time_range_hours=time_range_hours,
                agent_id=agent_id
            )
            return metrics_summary
        else:
            raise HTTPException(status_code=503, detail="Performance monitor not available")
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus 메트릭 엔드포인트"""
    try:
        if performance_monitor:
            # Prometheus 형식으로 메트릭 내보내기
            metrics_data = performance_monitor.export_metrics(time_range_hours=1)
            
            # Prometheus 텍스트 형식으로 변환
            prometheus_output = []
            
            # 기본 메트릭들
            prometheus_output.append("# HELP agent_requests_total Total number of agent requests")
            prometheus_output.append("# TYPE agent_requests_total counter")
            
            prometheus_output.append("# HELP agent_response_time_seconds Agent response time in seconds")
            prometheus_output.append("# TYPE agent_response_time_seconds histogram")
            
            prometheus_output.append("# HELP agent_memory_usage_bytes Memory usage in bytes")
            prometheus_output.append("# TYPE agent_memory_usage_bytes gauge")
            
            # 실제 메트릭 값들 (예시)
            system_health = performance_monitor.get_system_health()
            if system_health and system_health.get('system_metrics'):
                cpu_usage = system_health['system_metrics'].get('cpu_percent', 0)
                memory_usage = system_health['system_metrics'].get('memory_percent', 0)
                
                prometheus_output.append(f"system_cpu_usage_percent {cpu_usage}")
                prometheus_output.append(f"system_memory_usage_percent {memory_usage}")
            
            return "\n".join(prometheus_output)
        else:
            return "# Performance monitor not available\n"
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {str(e)}")
        return f"# Error: {str(e)}\n"

# Optimization API 엔드포인트들
@app.get("/api/v1/optimization/history")
async def get_optimization_history(
    agent_id: Optional[str] = None,
    limit: Optional[int] = 100
):
    """최적화 이력 조회"""
    try:
        # 최적화 이력 기능은 아직 구현되지 않았으므로 기본 응답 반환
        history = {
            "message": "Optimization history feature",
            "agent_id": agent_id,
            "limit": limit,
            "history": [],
            "total_count": 0
        }
        
        return history
    except Exception as e:
        logger.error(f"Error getting optimization history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/optimization/trigger")
async def trigger_optimization(
    agent_id: str,
    optimization_type: str = "general",
    background_tasks: BackgroundTasks = None
):
    """최적화 작업 트리거"""
    try:
        # 백그라운드에서 최적화 작업 실행
        if background_tasks:
            background_tasks.add_task(
                perform_optimization,
                agent_id=agent_id,
                optimization_type=optimization_type
            )
        
        return {
            "message": "Optimization triggered",
            "agent_id": agent_id,
            "optimization_type": optimization_type,
            "status": "started"
        }
    except Exception as e:
        logger.error(f"Error triggering optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def perform_optimization(agent_id: str, optimization_type: str):
    """최적화 작업 수행 (백그라운드 태스크)"""
    try:
        logger.info(f"Starting optimization for agent {agent_id}, type: {optimization_type}")
        
        # 실제 최적화 로직 구현
        if memory_service:
            await memory_service.cleanup_expired_memories()
        
        if feedback_service:
            await feedback_service.process_feedback_batch(batch_size=50)
        
        logger.info(f"Optimization completed for agent {agent_id}")
        
    except Exception as e:
        logger.error(f"Error in optimization task: {str(e)}")

# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 핸들러"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )