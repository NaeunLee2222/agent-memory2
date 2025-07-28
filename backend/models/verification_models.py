"""
Verification models for PoC scenario validation
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

class VerificationPhase(str, Enum):
    BASELINE = "baseline"      # 1-3회 실행 (기준선 설정)
    LEARNING = "learning"      # 4-10회 실행 (학습 단계) 
    VALIDATION = "validation"  # 11-15회 실행 (검증 단계)

class ScenarioType(str, Enum):
    FLOW_MODE_PATTERN_LEARNING = "1.1_flow_mode_pattern_learning"
    BASIC_MODE_TOOL_SELECTION = "1.2_basic_mode_tool_selection"

class ExecutionMetrics(BaseModel):
    """개별 실행의 상세 메트릭"""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    scenario_type: ScenarioType
    execution_number: int  # 1, 2, 3, 4, ...
    phase: VerificationPhase
    
    # 실행 시간 관련
    total_execution_time: float
    step_execution_times: List[float] = []
    preparation_time: float = 0.0
    optimization_applied: bool = False
    
    # 패턴 관련 (Flow Mode)
    pattern_suggested: bool = False
    pattern_id: Optional[str] = None
    pattern_confidence: float = 0.0
    pattern_accepted: bool = False
    
    # 도구 선택 관련 (Basic Mode)
    expected_tools: List[str] = []
    actual_tools: List[str] = []
    tool_selection_accuracy: float = 0.0
    context_relevance_score: float = 0.0
    
    # 공통 성과 지표
    success_rate: float = 0.0
    user_satisfaction_rating: Optional[int] = None
    execution_success: bool = True
    
    # 메타데이터
    context: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PatternVerificationMetrics(BaseModel):
    """패턴 학습 검증 메트릭 (Scenario 1.1)"""
    scenario_id: str = "1.1_flow_mode_pattern_learning"
    user_id: str
    
    # 패턴 학습 성공률
    total_executions: int = 0
    patterns_learned: int = 0
    pattern_learning_success_rate: float = 0.0
    
    # 패턴 제안 정확도
    pattern_suggestions_made: int = 0
    correct_pattern_suggestions: int = 0
    pattern_suggestion_accuracy: float = 0.0
    
    # 실행 시간 최적화
    baseline_avg_time: float = 0.0  # 1-3회차 평균
    optimized_avg_time: float = 0.0  # 4회차 이후 평균
    time_improvement_percentage: float = 0.0
    
    # 패턴 신뢰도
    avg_pattern_confidence: float = 0.0
    confidence_trend: List[float] = []
    
    # 유사 패턴 적응
    adaptation_tests: int = 0
    successful_adaptations: int = 0
    pattern_adaptation_rate: float = 0.0
    
    # 단계별 성과
    baseline_metrics: Dict[str, Any] = {}
    learning_metrics: Dict[str, Any] = {}
    validation_metrics: Dict[str, Any] = {}
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ToolSelectionVerificationMetrics(BaseModel):
    """도구 선택 학습 검증 메트릭 (Scenario 1.2)"""
    scenario_id: str = "1.2_basic_mode_tool_selection"
    user_id: str
    
    # 의도 파악 정확도
    total_requests: int = 0
    correct_tool_selections: int = 0
    intent_recognition_accuracy: float = 0.0
    initial_accuracy: float = 0.0  # 첫 3회 평균
    current_accuracy: float = 0.0  # 최근 3회 평균
    accuracy_improvement: float = 0.0
    
    # 도구 효율성 학습
    tool_efficiency_scores: Dict[str, float] = {}  # tool_name -> efficiency_score
    context_optimization_score: float = 0.0
    optimal_tool_selection_rate: float = 0.0
    
    # 사용자 만족도
    initial_satisfaction: float = 0.0
    current_satisfaction: float = 0.0
    satisfaction_improvement: float = 0.0
    satisfaction_history: List[float] = []
    
    # 컨텍스트별 최적화
    context_patterns: Dict[str, Dict[str, Any]] = {}
    time_based_optimization: Dict[str, str] = {}  # time_range -> preferred_tool
    urgency_based_optimization: Dict[str, List[str]] = {}  # urgency_level -> tools
    
    # 단계별 성과
    baseline_metrics: Dict[str, Any] = {}
    learning_metrics: Dict[str, Any] = {}
    validation_metrics: Dict[str, Any] = {}
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ComprehensiveValidationReport(BaseModel):
    """종합 검증 보고서"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    test_period_start: datetime
    test_period_end: datetime
    
    # 시나리오별 결과
    flow_mode_results: PatternVerificationMetrics
    basic_mode_results: ToolSelectionVerificationMetrics
    
    # 종합 성과 지표
    overall_success_criteria_met: int = 0
    total_success_criteria: int = 8  # 총 8개 성공 기준
    overall_pass_rate: float = 0.0
    
    # 개선 효과 요약
    total_executions: int = 0
    average_improvement: float = 0.0
    learning_effectiveness: float = 0.0
    
    # 성공 기준 달성 여부
    success_criteria: Dict[str, bool] = {
        "pattern_learning_95_percent": False,        # 패턴 제안 95% 성공률
        "time_reduction_25_percent": False,          # 실행 시간 25% 단축
        "pattern_adaptation_80_percent": False,      # 유사 패턴 적응 80%
        "intent_accuracy_70_to_90": False,          # 의도 파악 70%→90% 향상
        "tool_selection_88_percent": False,         # 도구 선택 88% 성공률
        "context_optimization_85_percent": False,   # 상황별 최적 선택 85%
        "user_satisfaction_improvement": False,     # 사용자 만족도 향상
        "learning_retention_stability": False       # 학습 안정성 유지
    }
    
    # 추가 인사이트
    key_insights: List[str] = []
    recommendations: List[str] = []
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class PhaseTransition(BaseModel):
    """단계 전환 추적"""
    user_id: str
    scenario_type: ScenarioType
    from_phase: VerificationPhase
    to_phase: VerificationPhase
    execution_count: int
    transition_criteria_met: bool
    transition_timestamp: datetime = Field(default_factory=datetime.utcnow)

class RealTimeMetrics(BaseModel):
    """실시간 모니터링 메트릭"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    active_users: int = 0
    total_patterns_learned: int = 0
    avg_pattern_confidence: float = 0.0
    system_learning_rate: float = 0.0  # 전체 시스템 학습 속도
    current_phase_distribution: Dict[VerificationPhase, int] = {}
    recent_improvements: Dict[str, float] = {}  # 최근 1시간 개선 사항