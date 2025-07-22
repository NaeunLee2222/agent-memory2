# backend/models/feedback.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class FeedbackType(str, Enum):
    """피드백 타입"""
    SUCCESS = "success"
    ERROR = "error"
    USER_CORRECTION = "user_correction"
    PERFORMANCE = "performance"
    OPTIMIZATION = "optimization"

class FeedbackData(BaseModel):
    """피드백 데이터"""
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="피드백 ID")
    agent_id: str = Field(..., description="에이전트 ID")
    feedback_type: FeedbackType = Field(..., description="피드백 타입")
    content: str = Field(..., description="피드백 내용")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="메타데이터")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="컨텍스트")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProcessedFeedback(BaseModel):
    """처리된 피드백"""
    feedback_id: str = Field(..., description="피드백 ID")
    agent_id: str = Field(..., description="에이전트 ID")
    priority: int = Field(..., description="우선순위 (1-5)")
    insights: Dict[str, Any] = Field(default_factory=dict, description="분석 결과")
    suggestions: List[str] = Field(default_factory=list, description="개선 제안")
    confidence_score: float = Field(..., description="신뢰도 점수 (0-1)")
    weight: float = Field(default=1.0, description="가중치")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="처리 시간")
    processing_time: Optional[float] = Field(None, description="처리 소요 시간 (초)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }