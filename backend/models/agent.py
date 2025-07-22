# 4. backend/models/agent.py - 새 파일 생성 (누락된 파일)

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class AgentMode(str, Enum):
    FLOW = "flow"
    BASIC = "basic"

class AgentRequest(BaseModel):
    agent_id: str = Field(..., description="에이전트 ID")
    message: str = Field(..., description="사용자 메시지")
    mode: AgentMode = Field(default=AgentMode.BASIC, description="에이전트 모드")
    session_id: Optional[str] = Field(None, description="세션 ID")
    request_id: Optional[str] = Field(None, description="요청 ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 컨텍스트")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    
class AgentResponse(BaseModel):
    agent_id: str = Field(..., description="에이전트 ID")
    response: str = Field(..., description="에이전트 응답")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="응답 시간")
    processing_time: float = Field(..., description="처리 시간 (초)")
    mode: AgentMode = Field(..., description="사용된 에이전트 모드")
    context_used: int = Field(default=0, description="사용된 컨텍스트 수")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")
    suggestions: Optional[List[str]] = Field(default_factory=list, description="제안사항")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
