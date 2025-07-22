from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import time


class AgentMode(str, Enum):
    FLOW = "flow"
    BASIC = "basic"


class MemoryType(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MCPToolType(str, Enum):
    SEARCH_DB = "search_db"
    SEND_SLACK = "send_slack"
    GENERATE_MSG = "generate_msg"
    EMERGENCY_MAIL = "emergency_mail_data_generator"
    SEND_EMAIL = "send_email"


# MCP Tool 관련 스키마
class MCPToolCall(BaseModel):
    tool_type: MCPToolType
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = {}


class MCPToolResult(BaseModel):
    tool_type: MCPToolType
    success: bool
    result: Any
    execution_time: float
    error: Optional[str] = None


# 워크플로우 관련 스키마
class WorkflowStep(BaseModel):
    step_id: int
    step_name: str
    action: str
    tool_calls: List[MCPToolCall]
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Any] = None
    execution_time: Optional[float] = None


class WorkflowPattern(BaseModel):
    pattern_id: str
    pattern_name: str
    steps: List[WorkflowStep]
    success_rate: float
    avg_execution_time: float
    usage_count: int
    last_used: datetime


# 메모리 관련 스키마
class ProceduralMemory(BaseModel):
    procedure_id: str
    name: str
    description: str
    workflow_pattern: WorkflowPattern
    success_rate: float
    optimization_history: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class EpisodicMemory(BaseModel):
    episode_id: str
    user_id: str
    session_id: str
    timestamp: datetime
    interaction_type: str
    context: Dict[str, Any]
    workflow_executed: Optional[WorkflowPattern] = None
    user_satisfaction: Optional[float] = None
    lessons_learned: List[str] = []


class SemanticMemory(BaseModel):
    knowledge_id: str
    domain: str
    entity: str
    relation: str
    object: str
    confidence: float
    source: str
    created_at: datetime
    usage_count: int = 0


# 피드백 관련 스키마
class PerformanceFeedback(BaseModel):
    feedback_id: str
    tool_type: MCPToolType
    execution_time: float
    success: bool
    error_type: Optional[str] = None
    optimization_applied: List[str] = []
    timestamp: datetime


class UserFeedback(BaseModel):
    feedback_id: str
    user_id: str
    session_id: str
    feedback_type: str  # satisfaction, preference, correction
    content: str
    rating: Optional[float] = None
    applied_changes: List[str] = []
    timestamp: datetime


# API 요청/응답 스키마
class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str
    mode: AgentMode
    context: Optional[Dict[str, Any]] = {}
    preferred_tools: Optional[List[MCPToolType]] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    workflow_executed: Optional[WorkflowPattern] = None
    memory_used: Dict[MemoryType, List[str]]
    processing_time: float
    tools_used: List[MCPToolResult]
    confidence_score: float
    optimization_applied: List[str] = []


class FeedbackRequest(BaseModel):
    session_id: str
    user_id: str
    feedback_type: str
    content: str
    rating: Optional[float] = None
    target_component: Optional[str] = None  # workflow, tool, response


class FeedbackResponse(BaseModel):
    applied: bool
    processing_time: float
    optimizations: List[str]
    expected_improvements: Dict[str, float]


# 통계 및 모니터링 스키마
class SystemMetrics(BaseModel):
    timestamp: datetime
    memory_stats: Dict[MemoryType, Dict[str, Any]]
    tool_performance: Dict[MCPToolType, Dict[str, float]]
    workflow_efficiency: Dict[str, float]
    user_satisfaction: float
    system_load: Dict[str, float]
