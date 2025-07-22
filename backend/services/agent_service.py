# 3. backend/services/agent_service.py - 새 파일 생성 (누락된 파일)

from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import json

from models.agent import AgentRequest, AgentResponse, AgentMode
from models.memory import MemoryType, MemoryData
from models.feedback import FeedbackType
from services.memory_service import MemoryService
from services.feedback_service import FeedbackService
from utils.logger import get_logger

logger = get_logger(__name__)

class AgentService:
    def __init__(self, memory_service: MemoryService, feedback_service: FeedbackService):
        self.memory_service = memory_service
        self.feedback_service = feedback_service
        
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """에이전트 요청 처리"""
        try:
            start_time = datetime.utcnow()
            
            # 메모리에서 컨텍스트 검색
            context_memories = await self.memory_service.retrieve_memories(
                agent_id=request.agent_id,
                memory_type=MemoryType.WORKING,
                limit=10
            )
            
            # 응답 생성 (실제로는 LLM 호출)
            response_content = f"Processed: {request.message}"
            
            # 응답 생성
            response = AgentResponse(
                agent_id=request.agent_id,
                response=response_content,
                timestamp=datetime.utcnow(),
                processing_time=(datetime.utcnow() - start_time).total_seconds(),
                mode=request.mode,
                context_used=len(context_memories),
                metadata={
                    "request_id": request.request_id,
                    "session_id": request.session_id
                }
            )
            
            # 작업 메모리에 저장
            working_memory = MemoryData(
                memory_type=MemoryType.WORKING,
                content={
                    "request": request.message,
                    "response": response_content,
                    "timestamp": datetime.utcnow().isoformat()
                },
                agent_id=request.agent_id,
                context={"session_id": request.session_id},
                ttl=3600  # 1시간
            )
            
            await self.memory_service.store_memory(working_memory)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing agent request: {str(e)}")
            raise