from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

class Episode(BaseModel):
    episode_id: str
    session_id: str
    user_id: str
    mode: str
    original_request: str
    response: str
    execution_trace: List[Dict[str, Any]]
    success: bool
    timestamp: str
    tools_used: List[str]
    performance_metrics: Dict[str, Any]

class Procedure(BaseModel):
    procedure_id: str
    procedure_name: str
    intent: str
    steps: List[Dict[str, Any]]
    success_rate: float
    usage_count: int
    created_at: str
    last_used: Optional[str] = None

class WorkingMemoryContext(BaseModel):
    session_id: str
    user_id: str
    mode: str
    original_message: str
    timestamp: str
    available_tools: List[Dict[str, Any]]
    step_results: Optional[Dict[str, Any]] = None
    tool_executions: Optional[List[Dict[str, Any]]] = None