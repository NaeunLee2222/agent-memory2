from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class PatternType(str, Enum):
    WORKFLOW = "workflow"
    TOOL_SELECTION = "tool_selection"
    USER_PREFERENCE = "user_preference"

class ExecutionStep(BaseModel):
    step_id: int
    tool_name: str
    parameters: Dict[str, Any]
    execution_time: float
    success: bool
    output_summary: str

class WorkflowPattern(BaseModel):
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: PatternType
    name: str
    description: str
    steps: List[ExecutionStep]
    success_rate: float = 0.0
    total_executions: int = 0
    successful_executions: int = 0
    average_execution_time: float = 0.0
    user_id: Optional[str] = None
    context_tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0

class PatternExecution(BaseModel):
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pattern_id: str
    session_id: str
    user_id: str
    execution_time: float
    success: bool
    feedback_rating: Optional[int] = None
    feedback_comments: Optional[str] = None
    context: Dict[str, Any] = {}
    executed_at: datetime = Field(default_factory=datetime.utcnow)

class ToolUsageAnalytics(BaseModel):
    analytics_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    user_id: str
    session_id: str
    execution_time: float
    success: bool
    context: Dict[str, Any]
    parameters_used: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ToolCombination(BaseModel):
    combination_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tools: List[str]
    success_rate: float
    average_execution_time: float
    usage_count: int
    context_pattern: str
    user_satisfaction: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserToolPreference(BaseModel):
    preference_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tool_name: str
    preference_score: float  # 0.0 to 1.0
    context_tags: List[str]
    usage_frequency: int
    last_used: datetime
    satisfaction_scores: List[float] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatternSuggestion(BaseModel):
    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pattern_id: str
    user_id: str
    session_id: str
    confidence_score: float
    suggested_at: datetime = Field(default_factory=datetime.utcnow)
    accepted: Optional[bool] = None
    feedback_rating: Optional[int] = None
    execution_result: Optional[Dict[str, Any]] = None

class FeedbackMetrics(BaseModel):
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    metric_type: str  # "pattern_learning", "tool_selection", "execution_time"
    before_value: float
    after_value: float
    improvement_percentage: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

import uuid