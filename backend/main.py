import asyncio
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from .models.schemas import (
    ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse,
    SystemMetrics, AgentMode
)
from .services.memory_service import EnhancedMemoryService
from .services.mcp_service import MCPService
from .services.feedback_service import EnhancedFeedbackService
from .services.agent_service import EnhancedAgentService
from .utils.config import config

# Prometheus 메트릭
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
MEMORY_OPERATIONS = Counter('memory_operations_total', 'Memory operations', ['operation_type'])

# 글로벌 서비스 인스턴스
memory_service = None
mcp_service = None
feedback_service = None
agent_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global memory_service, mcp_service, feedback_service, agent_service
    
    # 시작 시 초기화
    logging.info("🚀 서비스 초기화 시작...")
    
    memory_service = EnhancedMemoryService()
    await memory_service.initialize()
    logging.info("✅ 메모리 서비스 초기화 완료")
    
    mcp_service = MCPService()
    logging.info("✅ MCP 서비스 초기화 완료")
    
    feedback_service = EnhancedFeedbackService(memory_service)
    logging.info("✅ 피드백 서비스 초기화 완료")
    
    agent_service = EnhancedAgentService(memory_service, mcp_service, feedback_service)
    logging.info("✅ 에이전트 서비스 초기화 완료")
    
    logging.info("🎉 모든 서비스 초기화 완료!")
    
    yield
    
    # 종료 시 정리
    logging.info("🛑 서비스 종료 중...")
    if memory_service.redis_client:
        await memory_service.redis_client.close()
    if memory_service.neo4j_driver:
        memory_service.neo4j_driver.close()
    logging.info("✅ 정리 완료")

app = FastAPI(
    title="Enhanced Agentic AI PoC",
    description="MCP 도구 기반 지능형 메모리와 피드백 루프를 갖춘 에이전트 시스템",
    version="2.0.0",
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

@app.middleware("http")
async def add_prometheus_metrics(request, call_next):
    """Prometheus 메트릭 미들웨어"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # 메트릭 기록
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response

# === API 엔드포인트 ===

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """메인 채팅 엔드포인트"""
    try:
        start_time = time.time()
        
        # 사용자 선호도 크로스 에이전트 학습 적용
        await feedback_service.process_immediate_feedback(FeedbackRequest(
            session_id=request.session_id,
            user_id=request.user_id,
            feedback_type="preference_sync",
            content="크로스 에이전트 선호도 동기화"
        ))
        
        # 채팅 처리
        response = await agent_service.process_chat(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            mode=request.mode,
            context=request.context
        )
        
        MEMORY_OPERATIONS.labels(operation_type="chat_processing").inc()
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 처리 오류: {str(e)}")

@app.post("/feedback", response_model=FeedbackResponse)
async def feedback_endpoint(request: FeedbackRequest):
    """즉시 피드백 처리 엔드포인트"""
    try:
        response = await feedback_service.process_immediate_feedback(request)
        MEMORY_OPERATIONS.labels(operation_type="feedback_processing").inc()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 처리 오류: {str(e)}")

@app.get("/memory/stats")
async def memory_stats_endpoint():
    """메모리 시스템 통계"""
    try:
        stats = await memory_service.get_memory_statistics()
        MEMORY_OPERATIONS.labels(operation_type="stats_query").inc()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 오류: {str(e)}")

@app.get("/mcp/tools/performance")
async def mcp_performance_endpoint():
    """MCP 도구 성능 통계"""
    try:
        stats = mcp_service.get_all_performance_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP 성능 조회 오류: {str(e)}")

@app.get("/feedback/optimization-history")
async def optimization_history_endpoint():
    """최적화 이력 조회"""
    try:
        history = await feedback_service.get_optimization_history()