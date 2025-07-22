# backend/models/memory.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class MemoryType(str, Enum):
    """메모리 타입"""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class MemoryData(BaseModel):
    """메모리 데이터 모델"""
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="메모리 고유 ID")
    memory_type: MemoryType = Field(..., description="메모리 타입")
    content: Dict[str, Any] = Field(..., description="메모리 내용")
    agent_id: str = Field(..., description="에이전트 ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="컨텍스트 정보")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="메타데이터")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="업데이트 시간")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    ttl: Optional[int] = Field(None, description="TTL (초)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MemoryMetrics(BaseModel):
    """메모리 메트릭"""
    total_memories: int = Field(default=0, description="총 메모리 수")
    memory_distribution: Dict[MemoryType, int] = Field(default_factory=dict, description="메모리 타입별 분포")
    total_size_bytes: int = Field(default=0, description="총 크기 (바이트)")
    average_size_bytes: float = Field(default=0.0, description="평균 크기 (바이트)")
    oldest_memory: Optional[datetime] = Field(None, description="가장 오래된 메모리")
    newest_memory: Optional[datetime] = Field(None, description="가장 최근 메모리")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }