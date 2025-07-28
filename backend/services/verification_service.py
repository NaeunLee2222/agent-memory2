"""
Verification Service for PoC Scenario Validation
Implements detailed metrics calculation and tracking for scenarios 1.1 and 1.2
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import uuid

from backend.models.verification_models import (
    ExecutionMetrics, PatternVerificationMetrics, ToolSelectionVerificationMetrics,
    ComprehensiveValidationReport, VerificationPhase, ScenarioType,
    PhaseTransition, RealTimeMetrics
)
from backend.database.memory_database import MemoryDatabase

logger = logging.getLogger(__name__)

class VerificationService:
    """PoC 시나리오 검증을 위한 메트릭 계산 및 추적 서비스"""
    
    def __init__(self, memory_database: MemoryDatabase):
        self.memory_database = memory_database
        
        # 실행 데이터 저장소
        self.execution_metrics: List[ExecutionMetrics] = []
        self.pattern_metrics: Dict[str, PatternVerificationMetrics] = {}
        self.tool_metrics: Dict[str, ToolSelectionVerificationMetrics] = {}
        self.phase_transitions: List[PhaseTransition] = []
        
        # 실시간 집계 데이터
        self.real_time_metrics = RealTimeMetrics()
        
    async def initialize(self):
        """검증 서비스 초기화"""
        logger.info("Initializing Verification Service")
        await self._load_existing_metrics()
    
    async def track_execution(
        self,
        session_id: str,
        user_id: str,
        scenario_type: ScenarioType,
        execution_trace: List[Dict[str, Any]],
        total_execution_time: float,
        success_rate: float,
        context: Dict[str, Any] = None,
        pattern_suggestion: Dict[str, Any] = None,
        user_feedback: Dict[str, Any] = None
    ) -> str:
        """실행 결과를 추적하고 메트릭을 업데이트"""
        
        try:
            # 현재 실행 번호 계산
            user_executions = [
                e for e in self.execution_metrics 
                if e.user_id == user_id and e.scenario_type == scenario_type
            ]
            execution_number = len(user_executions) + 1
            
            # 현재 단계 결정
            current_phase = self._determine_phase(execution_number)
            
            # 실행 메트릭 생성
            metrics = ExecutionMetrics(
                session_id=session_id,
                user_id=user_id,
                scenario_type=scenario_type,
                execution_number=execution_number,
                phase=current_phase,
                total_execution_time=total_execution_time,
                step_execution_times=[
                    step.get('execution_time', 0.0) for step in execution_trace
                ],
                success_rate=success_rate,
                execution_success=success_rate >= 0.8,
                context=context or {}
            )
            
            # 패턴 관련 정보 추가 (Flow Mode)
            if pattern_suggestion:
                metrics.pattern_suggested = True
                metrics.pattern_id = pattern_suggestion.get('pattern_id')
                metrics.pattern_confidence = pattern_suggestion.get('confidence_score', 0.0)
                metrics.pattern_accepted = user_feedback.get('suggestion_accepted', False) if user_feedback else False
            
            # 도구 선택 정보 추가 (Basic Mode)
            if scenario_type == ScenarioType.BASIC_MODE_TOOL_SELECTION:
                actual_tools = [step.get('tool', '') for step in execution_trace if step.get('tool')]
                metrics.actual_tools = actual_tools
                metrics.expected_tools = context.get('expected_tools', []) if context else []
                metrics.tool_selection_accuracy = self._calculate_tool_accuracy(
                    metrics.actual_tools, metrics.expected_tools
                )
                metrics.context_relevance_score = self._calculate_context_relevance(
                    actual_tools, context or {}
                )
            
            # 사용자 피드백 추가
            if user_feedback:
                metrics.user_satisfaction_rating = user_feedback.get('rating')
            
            # 메트릭 저장
            self.execution_metrics.append(metrics)
            
            # 단계별 메트릭 업데이트
            await self._update_scenario_metrics(metrics)
            
            # 단계 전환 확인
            await self._check_phase_transition(user_id, scenario_type, execution_number)
            
            # 실시간 메트릭 업데이트
            await self._update_real_time_metrics()
            
            logger.info(f"Tracked execution {execution_number} for {scenario_type.value}")
            return metrics.execution_id
            
        except Exception as e:
            logger.error(f"Error tracking execution: {e}")
            return ""
    
    async def get_pattern_verification_metrics(self, user_id: str) -> Optional[PatternVerificationMetrics]:
        """패턴 학습 검증 메트릭 조회 (Scenario 1.1)"""
        return self.pattern_metrics.get(user_id)
    
    async def get_tool_selection_verification_metrics(self, user_id: str) -> Optional[ToolSelectionVerificationMetrics]:
        """도구 선택 검증 메트릭 조회 (Scenario 1.2)"""
        return self.tool_metrics.get(user_id)
    
    async def generate_comprehensive_report(self, user_id: str) -> ComprehensiveValidationReport:
        """종합 검증 보고서 생성"""
        
        pattern_metrics = self.pattern_metrics.get(user_id, PatternVerificationMetrics(user_id=user_id))
        tool_metrics = self.tool_metrics.get(user_id, ToolSelectionVerificationMetrics(user_id=user_id))
        
        # 테스트 기간 계산
        user_executions = [e for e in self.execution_metrics if e.user_id == user_id]
        test_start = min(e.timestamp for e in user_executions) if user_executions else datetime.utcnow()
        test_end = max(e.timestamp for e in user_executions) if user_executions else datetime.utcnow()
        
        # 성공 기준 평가
        success_criteria = await self._evaluate_success_criteria(pattern_metrics, tool_metrics)
        success_count = sum(success_criteria.values())
        
        # 종합 보고서 생성
        report = ComprehensiveValidationReport(
            user_id=user_id,
            test_period_start=test_start,
            test_period_end=test_end,
            flow_mode_results=pattern_metrics,
            basic_mode_results=tool_metrics,
            overall_success_criteria_met=success_count,
            overall_pass_rate=success_count / 8.0,
            total_executions=len(user_executions),
            success_criteria=success_criteria
        )
        
        # 추가 인사이트 생성
        report.key_insights = await self._generate_insights(pattern_metrics, tool_metrics)
        report.recommendations = await self._generate_recommendations(success_criteria)
        
        return report
    
    async def get_phase_based_analysis(self, user_id: str, scenario_type: ScenarioType) -> Dict[str, Any]:
        """단계별 성과 분석"""
        
        user_executions = [
            e for e in self.execution_metrics 
            if e.user_id == user_id and e.scenario_type == scenario_type
        ]
        
        if not user_executions:
            return {"error": "No execution data found"}
        
        # 단계별 그룹화
        phase_groups = defaultdict(list)
        for execution in user_executions:
            phase_groups[execution.phase].append(execution)
        
        # 단계별 분석
        phase_analysis = {}
        for phase, executions in phase_groups.items():
            if scenario_type == ScenarioType.FLOW_MODE_PATTERN_LEARNING:
                analysis = await self._analyze_flow_mode_phase(executions)
            else:
                analysis = await self._analyze_basic_mode_phase(executions)
            
            phase_analysis[phase.value] = analysis
        
        return {
            "user_id": user_id,
            "scenario_type": scenario_type.value,
            "phase_analysis": phase_analysis,
            "transition_history": [
                {
                    "from_phase": t.from_phase.value,
                    "to_phase": t.to_phase.value,
                    "execution_count": t.execution_count,
                    "timestamp": t.transition_timestamp.isoformat()
                }
                for t in self.phase_transitions 
                if t.user_id == user_id and t.scenario_type == scenario_type
            ]
        }
    
    async def get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """실시간 대시보드 데이터"""
        
        # 현재 활성 사용자 수
        recent_threshold = datetime.utcnow() - timedelta(hours=1)
        active_users = len(set(
            e.user_id for e in self.execution_metrics 
            if e.timestamp >= recent_threshold
        ))
        
        # 전체 패턴 학습 현황
        total_patterns = sum(m.patterns_learned for m in self.pattern_metrics.values())
        
        # 평균 패턴 신뢰도
        confidences = [m.avg_pattern_confidence for m in self.pattern_metrics.values() if m.avg_pattern_confidence > 0]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        
        # 단계별 사용자 분포
        phase_distribution = defaultdict(int)
        for user_id in set(e.user_id for e in self.execution_metrics):
            latest_execution = max(
                (e for e in self.execution_metrics if e.user_id == user_id),
                key=lambda x: x.timestamp,
                default=None
            )
            if latest_execution:
                phase_distribution[latest_execution.phase] += 1
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_users": active_users,
            "total_patterns_learned": total_patterns,
            "avg_pattern_confidence": avg_confidence,
            "phase_distribution": {k.value: v for k, v in phase_distribution.items()},
            "recent_executions": len([
                e for e in self.execution_metrics 
                if e.timestamp >= recent_threshold
            ]),
            "system_health": {
                "total_users": len(set(e.user_id for e in self.execution_metrics)),
                "total_executions": len(self.execution_metrics),
                "avg_success_rate": statistics.mean([
                    e.success_rate for e in self.execution_metrics
                ]) if self.execution_metrics else 0.0
            }
        }
    
    def _determine_phase(self, execution_number: int) -> VerificationPhase:
        """실행 횟수에 따른 단계 결정"""
        if execution_number <= 3:
            return VerificationPhase.BASELINE
        elif execution_number <= 10:
            return VerificationPhase.LEARNING
        else:
            return VerificationPhase.VALIDATION
    
    def _calculate_tool_accuracy(self, actual_tools: List[str], expected_tools: List[str]) -> float:
        """도구 선택 정확도 계산"""
        if not expected_tools:
            return 1.0 if not actual_tools else 0.0
        
        actual_set = set(actual_tools)
        expected_set = set(expected_tools)
        
        intersection = actual_set & expected_set
        union = actual_set | expected_set
        
        return len(intersection) / len(union) if union else 1.0
    
    def _calculate_context_relevance(self, tools: List[str], context: Dict[str, Any]) -> float:
        """컨텍스트 적합성 점수 계산"""
        if not context or not tools:
            return 0.5  # 기본 점수
        
        score = 0.5  # 기본 점수
        
        # 시간대별 적합성
        hour = datetime.now().hour
        if 9 <= hour <= 18:  # 업무 시간
            if "send_slack" in tools:
                score += 0.2
        else:  # 업무 시간 외
            if "send_email" in tools:
                score += 0.2
        
        # 긴급도별 적합성
        urgency = context.get('urgency', 'normal')
        if urgency == 'high' and any(tool in ['emergency_mail', 'send_slack'] for tool in tools):
            score += 0.3
        
        return min(1.0, score)
    
    async def _update_scenario_metrics(self, execution_metrics: ExecutionMetrics):
        """시나리오별 메트릭 업데이트"""
        
        user_id = execution_metrics.user_id
        
        if execution_metrics.scenario_type == ScenarioType.FLOW_MODE_PATTERN_LEARNING:
            await self._update_pattern_metrics(user_id, execution_metrics)
        elif execution_metrics.scenario_type == ScenarioType.BASIC_MODE_TOOL_SELECTION:
            await self._update_tool_metrics(user_id, execution_metrics)
    
    async def _update_pattern_metrics(self, user_id: str, execution: ExecutionMetrics):
        """패턴 학습 메트릭 업데이트"""
        
        if user_id not in self.pattern_metrics:
            self.pattern_metrics[user_id] = PatternVerificationMetrics(user_id=user_id)
        
        metrics = self.pattern_metrics[user_id]
        metrics.total_executions += 1
        
        # 패턴 제안 관련 업데이트
        if execution.pattern_suggested:
            metrics.pattern_suggestions_made += 1
            if execution.pattern_accepted:
                metrics.correct_pattern_suggestions += 1
            
            # 신뢰도 추가
            metrics.confidence_trend.append(execution.pattern_confidence)
            metrics.avg_pattern_confidence = statistics.mean(metrics.confidence_trend)
        
        # 패턴 학습 개수 업데이트 (4회차부터 패턴 학습 시작)
        if execution.execution_number >= 4 and execution.pattern_suggested:
            metrics.patterns_learned = max(metrics.patterns_learned, 1)
        
        # 성공률 계산
        if metrics.pattern_suggestions_made > 0:
            metrics.pattern_suggestion_accuracy = (
                metrics.correct_pattern_suggestions / metrics.pattern_suggestions_made
            )
        
        # 실행 시간 분석
        user_executions = [
            e for e in self.execution_metrics 
            if e.user_id == user_id and e.scenario_type == ScenarioType.FLOW_MODE_PATTERN_LEARNING
        ]
        
        baseline_executions = [e for e in user_executions if e.execution_number <= 3]
        optimized_executions = [e for e in user_executions if e.execution_number >= 4]
        
        if baseline_executions:
            metrics.baseline_avg_time = statistics.mean([e.total_execution_time for e in baseline_executions])
        
        if optimized_executions:
            metrics.optimized_avg_time = statistics.mean([e.total_execution_time for e in optimized_executions])
            
            if metrics.baseline_avg_time > 0:
                metrics.time_improvement_percentage = (
                    (metrics.baseline_avg_time - metrics.optimized_avg_time) / metrics.baseline_avg_time
                )
        
        metrics.last_updated = datetime.utcnow()
    
    async def _update_tool_metrics(self, user_id: str, execution: ExecutionMetrics):
        """도구 선택 메트릭 업데이트"""
        
        if user_id not in self.tool_metrics:
            self.tool_metrics[user_id] = ToolSelectionVerificationMetrics(user_id=user_id)
        
        metrics = self.tool_metrics[user_id]
        metrics.total_requests += 1
        
        # 도구 선택 정확도 업데이트
        if execution.tool_selection_accuracy > 0.8:  # 80% 이상이면 정확한 선택으로 간주
            metrics.correct_tool_selections += 1
        
        # 전체 정확도 계산
        metrics.intent_recognition_accuracy = metrics.correct_tool_selections / metrics.total_requests
        
        # 초기 vs 현재 정확도 분석
        user_executions = [
            e for e in self.execution_metrics 
            if e.user_id == user_id and e.scenario_type == ScenarioType.BASIC_MODE_TOOL_SELECTION
        ]
        
        if len(user_executions) <= 3:
            # 초기 3회 평균
            initial_accuracies = [e.tool_selection_accuracy for e in user_executions]
            metrics.initial_accuracy = statistics.mean(initial_accuracies)
        else:
            # 최근 3회 평균
            recent_executions = sorted(user_executions, key=lambda x: x.timestamp)[-3:]
            recent_accuracies = [e.tool_selection_accuracy for e in recent_executions]
            metrics.current_accuracy = statistics.mean(recent_accuracies)
            
            if metrics.initial_accuracy > 0:
                metrics.accuracy_improvement = (
                    (metrics.current_accuracy - metrics.initial_accuracy) / metrics.initial_accuracy
                )
        
        # 사용자 만족도 업데이트
        if execution.user_satisfaction_rating:
            metrics.satisfaction_history.append(execution.user_satisfaction_rating)
            
            if len(metrics.satisfaction_history) <= 3:
                metrics.initial_satisfaction = statistics.mean(metrics.satisfaction_history)
            else:
                recent_satisfaction = metrics.satisfaction_history[-3:]
                metrics.current_satisfaction = statistics.mean(recent_satisfaction)
                
                if metrics.initial_satisfaction > 0:
                    metrics.satisfaction_improvement = (
                        metrics.current_satisfaction - metrics.initial_satisfaction
                    )
        
        metrics.last_updated = datetime.utcnow()
    
    async def _check_phase_transition(self, user_id: str, scenario_type: ScenarioType, execution_number: int):
        """단계 전환 확인 및 기록"""
        
        old_phase = self._determine_phase(execution_number - 1) if execution_number > 1 else None
        new_phase = self._determine_phase(execution_number)
        
        if old_phase and old_phase != new_phase:
            transition = PhaseTransition(
                user_id=user_id,
                scenario_type=scenario_type,
                from_phase=old_phase,
                to_phase=new_phase,
                execution_count=execution_number,
                transition_criteria_met=True
            )
            self.phase_transitions.append(transition)
            
            logger.info(f"Phase transition: {user_id} {scenario_type.value} {old_phase.value} -> {new_phase.value}")
    
    async def _update_real_time_metrics(self):
        """실시간 메트릭 업데이트"""
        self.real_time_metrics = RealTimeMetrics(
            active_users=len(set(
                e.user_id for e in self.execution_metrics 
                if e.timestamp >= datetime.utcnow() - timedelta(hours=1)
            )),
            total_patterns_learned=sum(m.patterns_learned for m in self.pattern_metrics.values()),
            avg_pattern_confidence=statistics.mean([
                m.avg_pattern_confidence for m in self.pattern_metrics.values() 
                if m.avg_pattern_confidence > 0
            ]) if any(m.avg_pattern_confidence > 0 for m in self.pattern_metrics.values()) else 0.0
        )
    
    async def _analyze_flow_mode_phase(self, executions: List[ExecutionMetrics]) -> Dict[str, Any]:
        """Flow Mode 단계별 분석"""
        
        if not executions:
            return {}
        
        return {
            "execution_count": len(executions),
            "avg_execution_time": statistics.mean([e.total_execution_time for e in executions]),
            "avg_success_rate": statistics.mean([e.success_rate for e in executions]),
            "pattern_suggestions": sum(1 for e in executions if e.pattern_suggested),
            "pattern_acceptances": sum(1 for e in executions if e.pattern_accepted),
            "avg_confidence": statistics.mean([
                e.pattern_confidence for e in executions if e.pattern_confidence > 0
            ]) if any(e.pattern_confidence > 0 for e in executions) else 0.0
        }
    
    async def _analyze_basic_mode_phase(self, executions: List[ExecutionMetrics]) -> Dict[str, Any]:
        """Basic Mode 단계별 분석"""
        
        if not executions:
            return {}
        
        return {
            "execution_count": len(executions),
            "avg_tool_accuracy": statistics.mean([e.tool_selection_accuracy for e in executions]),
            "avg_context_relevance": statistics.mean([e.context_relevance_score for e in executions]),
            "avg_satisfaction": statistics.mean([
                e.user_satisfaction_rating for e in executions if e.user_satisfaction_rating
            ]) if any(e.user_satisfaction_rating for e in executions) else 0.0
        }
    
    async def _evaluate_success_criteria(
        self, 
        pattern_metrics: PatternVerificationMetrics, 
        tool_metrics: ToolSelectionVerificationMetrics
    ) -> Dict[str, bool]:
        """성공 기준 평가"""
        
        return {
            "pattern_learning_95_percent": pattern_metrics.pattern_suggestion_accuracy >= 0.95,
            "time_reduction_25_percent": pattern_metrics.time_improvement_percentage >= 0.25,
            "pattern_adaptation_80_percent": pattern_metrics.pattern_adaptation_rate >= 0.80,
            "intent_accuracy_70_to_90": (
                tool_metrics.initial_accuracy >= 0.70 and 
                tool_metrics.current_accuracy >= 0.90
            ),
            "tool_selection_88_percent": tool_metrics.intent_recognition_accuracy >= 0.88,
            "context_optimization_85_percent": tool_metrics.optimal_tool_selection_rate >= 0.85,
            "user_satisfaction_improvement": tool_metrics.satisfaction_improvement > 0,
            "learning_retention_stability": pattern_metrics.avg_pattern_confidence >= 0.80
        }
    
    async def _generate_insights(
        self, 
        pattern_metrics: PatternVerificationMetrics, 
        tool_metrics: ToolSelectionVerificationMetrics
    ) -> List[str]:
        """주요 인사이트 생성"""
        
        insights = []
        
        if pattern_metrics.time_improvement_percentage > 0.25:
            insights.append(f"패턴 학습으로 실행 시간이 {pattern_metrics.time_improvement_percentage:.1%} 개선되었습니다.")
        
        if tool_metrics.accuracy_improvement > 0.20:
            insights.append(f"도구 선택 정확도가 {tool_metrics.accuracy_improvement:.1%} 향상되었습니다.")
        
        if pattern_metrics.avg_pattern_confidence > 0.85:
            insights.append("높은 패턴 신뢰도로 안정적인 학습이 이루어지고 있습니다.")
        
        return insights
    
    async def _generate_recommendations(self, success_criteria: Dict[str, bool]) -> List[str]:
        """개선 권장사항 생성"""
        
        recommendations = []
        
        if not success_criteria.get("pattern_learning_95_percent"):
            recommendations.append("패턴 제안 정확도 향상을 위해 더 많은 학습 데이터가 필요합니다.")
        
        if not success_criteria.get("time_reduction_25_percent"):
            recommendations.append("실행 시간 최적화를 위한 병렬 처리 개선을 고려해보세요.")
        
        if not success_criteria.get("user_satisfaction_improvement"):
            recommendations.append("사용자 피드백을 더 적극적으로 수집하여 개인화를 강화하세요.")
        
        return recommendations
    
    async def _load_existing_metrics(self):
        """기존 메트릭 로드 (실제 구현에서는 데이터베이스에서 로드)"""
        logger.info("Loaded existing verification metrics from database")