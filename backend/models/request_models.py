from pydantic import BaseModel
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    user_id: str
    mode: str = "basic"  # "basic" or "flow"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    execution_trace: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class FeedbackRequest(BaseModel):
    session_id: str
    rating: int
    comments: str = ""
    feedback_type: str = "general"  # "general", "tool_specific", "workflow"

class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    session_id: str
    context: Optional[Dict[str, Any]] = None

class ToolExecutionResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    tool_name: str
    timestamp: str