import asyncio
import logging
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
from collections import deque, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from ..models.database import Agent, AgentExecution, PerformanceMetric
from ..services.feedback_service import FeedbackService
from ..core.config import settings
from ..utils.exceptions import PerformanceMonitorError

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """메트릭 타입 정의"""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    RESPONSE_TIME = "response_time"
    USER_SATISFACTION = "user_satisfaction"

class AlertSeverity(Enum):
    """알람 심각도 정의"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class PerformanceThreshold:
    """성능 임계값 정의"""
    metric_type: MetricType
    warning_threshold: float
    critical_threshold: float
    comparison_operator: str  # "gt", "lt", "eq"
    enabled: bool = True

@dataclass
class PerformanceAlert:
    """성능 알람 정의"""
    alert_id: str
    agent_id: str
    metric_type: MetricType
    severity: AlertSeverity
    current_value: float
    threshold_value: float
    message: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

@dataclass
class PerformanceSnapshot:
    """성능 스냅샷"""
    timestamp: datetime
    agent_id: str
    metrics: Dict[MetricType, float]
    system_metrics: Dict[str, float]

class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.active_executions = {}
        self.metric_buffer = deque(maxlen=1000)
        
    def start_execution_monitoring(self, execution_id: str, agent_id: str) -> None:
        """실행 모니터링 시작"""
        self.active_executions[execution_id] = {
            "agent_id": agent_id,
            "start_time": time.time(),
            "start_memory": psutil.Process().memory_info().rss,
            "start_cpu": psutil.cpu_percent()
        }
        
        logger.info(f"실행 모니터링 시작: {execution_id}")
    
    def end_execution_monitoring(self, execution_id: str, success: bool = True) -> Dict[str, float]:
        """실행 모니터링 종료 및 메트릭 수집"""
        if execution_id not in self.active_executions:
            logger.warning(f"실행 정보를 찾을 수 없음: {execution_id}")
            return {}
        
        execution_info = self.active_executions.pop(execution_id)
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        end_cpu = psutil.cpu_percent()
        
        metrics = {
            "execution_time": end_time - execution_info["start_time"],
            "memory_usage": (end_memory - execution_info["start_memory"]) / 1024 / 1024,  # MB
            "cpu_usage": end_cpu,
            "success": 1.0 if success else 0.0
        }
        
        # 메트릭 버퍼에 추가
        self.metric_buffer.append({
            "execution_id": execution_id,
            "agent_id": execution_info["agent_id"],
            "timestamp": datetime.utcnow(),
            "metrics": metrics
        })
        
        logger.info(f"실행 모니터링 완료: {execution_id}, 메트릭: {metrics}")
        return metrics
    
    async def collect_system_metrics(self) -> Dict[str, float]:
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory_info = psutil.virtual_memory()
            memory_percent = memory_info.percent
            
            # 디스크 사용률
            disk_info = psutil.disk_usage('/')
            disk_percent = disk_info.percent
            
            # 네트워크 정보
            network_info = psutil.net_io_counters()
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "disk_usage": disk_percent,
                "network_bytes_sent": network_info.bytes_sent,
                "network_bytes_recv": network_info.bytes_recv
            }
            
        except Exception as e:
            logger.error(f"시스템 메트릭 수집 실패: {e}")
            return {}
    
    async def collect_agent_metrics(self, agent_id: str, hours: int = 1) -> Dict[str, float]:
        """특정 에이전트의 메트릭 수집"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 최근 실행 통계 조회
            query = (
                select(
                    func.count(AgentExecution.id).label("total_executions"),
                    func.avg(AgentExecution.execution_time).label("avg_execution_time"),
                    func.sum(
                        func.case((AgentExecution.status == "completed", 1), else_=0)
                    ).label("successful_executions"),
                    func.sum(
                        func.case((AgentExecution.status == "failed", 1), else_=0)
                    ).label("failed_executions")
                )
                .where(
                    and_(
                        AgentExecution.agent_id == agent_id,
                        AgentExecution.started_at >= cutoff_time
                    )
                )
            )
            
            result = await self.db_session.execute(query)
            stats = result.first()
            
            if not stats or stats.total_executions == 0:
                return {
                    "execution_count": 0.0,
                    "success_rate": 0.0,
                    "error_rate": 0.0,
                    "avg_execution_time": 0.0,
                    "throughput": 0.0
                }
            
            success_rate = stats.successful_executions / stats.total_executions
            error_rate = stats.failed_executions / stats.total_executions
            throughput = stats.total_executions / hours  # 시간당 실행 수
            
            return {
                "execution_count": float(stats.total_executions),
                "success_rate": success_rate,
                "error_rate": error_rate,
                "avg_execution_time": float(stats.avg_execution_time or 0),
                "throughput": throughput
            }
            
        except Exception as e:
            logger.error(f"에이전트 메트릭 수집 실패: {e}")
            return {}
    
    async def flush_metrics_to_db(self) -> int:
        """메트릭 버퍼를 데이터베이스에 저장"""
        if not self.metric_buffer:
            return 0
        
        try:
            metrics_to_save = list(self.metric_buffer)
            self.metric_buffer.clear()
            
            for metric_data in metrics_to_save:
                performance_metric = PerformanceMetric(
                    execution_id=metric_data["execution_id"],
                    agent_id=metric_data["agent_id"],
                    metrics=metric_data["metrics"],
                    created_at=metric_data["timestamp"]
                )
                self.db_session.add(performance_metric)
            
            await self.db_session.commit()
            logger.info(f"{len(metrics_to_save)}개 메트릭 저장 완료")
            return len(metrics_to_save)
            
        except Exception as e:
            logger.error(f"메트릭 저장 실패: {e}")
            await self.db_session.rollback()
            return 0

class PerformanceAnalyzer:
    """성능 분석기"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        
    async def analyze_agent_performance(
        self, 
        agent_id: str, 
        hours: int = 24
    ) -> Dict[str, Any]:
        """에이전트 성능 분석"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 성능 메트릭 조회
            query = (
                select(PerformanceMetric)
                .where(
                    and_(
                        PerformanceMetric.agent_id == agent_id,
                        PerformanceMetric.created_at >= cutoff_time
                    )
                )
                .order_by(PerformanceMetric.created_at)
            )
            
            result = await self.db_session.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {"message": "분석할 데이터가 없습니다."}
            
            # 메트릭 데이터 추출
            execution_times = []
            memory_usages = []
            cpu_usages = []
            success_rates = []
            
            for metric in metrics:
                metric_data = metric.metrics
                if "execution_time" in metric_data:
                    execution_times.append(metric_data["execution_time"])
                if "memory_usage" in metric_data:
                    memory_usages.append(metric_data["memory_usage"])
                if "cpu_usage" in metric_data:
                    cpu_usages.append(metric_data["cpu_usage"])
                if "success" in metric_data:
                    success_rates.append(metric_data["success"])
            
            # 통계 계산
            analysis = {
                "period_hours": hours,
                "total_executions": len(metrics),
                "execution_time_stats": self._calculate_stats(execution_times),
                "memory_usage_stats": self._calculate_stats(memory_usages),
                "cpu_usage_stats": self._calculate_stats(cpu_usages),
                "overall_success_rate": statistics.mean(success_rates) if success_rates else 0,
                "trend_analysis": await self._analyze_trends(metrics),
                "performance_grade": self._calculate_performance_grade(metrics),
                "recommendations": await self._generate_recommendations(agent_id, metrics)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"성능 분석 실패: {e}")
            raise PerformanceMonitorError(f"성능 분석 실패: {str(e)}")
    
    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """통계 계산"""
        if not values:
            return {"count": 0}
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0
        }
    
    async def _analyze_trends(self, metrics: List[PerformanceMetric]) -> Dict[str, str]:
        """트렌드 분석"""
        if len(metrics) < 2:
            return {"trend": "insufficient_data"}
        
        # 시간대별 성능 변화 분석
        recent_metrics = metrics[-10:]  # 최근 10개
        older_metrics = metrics[:10] if len(metrics) > 10 else []
        
        if not older_metrics:
            return {"trend": "insufficient_data"}
        
        # 실행 시간 트렌드
        recent_avg_time = statistics.mean([
            m.metrics.get("execution_time", 0) for m in recent_metrics
        ])
        older_avg_time = statistics.mean([
            m.metrics.get("execution_time", 0) for m in older_metrics
        ])
        
        time_trend = "improving" if recent_avg_time < older_avg_time else "degrading"
        
        # 성공률 트렌드
        recent_success_rate = statistics.mean([
            m.metrics.get("success", 0) for m in recent_metrics
        ])
        older_success_rate = statistics.mean([
            m.metrics.get("success", 0) for m in older_metrics
        ])
        
        success_trend = "improving" if recent_success_rate > older_success_rate else "degrading"
        
        return {
            "execution_time_trend": time_trend,
            "success_rate_trend": success_trend,
            "overall_trend": "improving" if time_trend == "improving" and success_trend == "improving" else "mixed"
        }
    
    def _calculate_performance_grade(self, metrics: List[PerformanceMetric]) -> str:
        """성능 등급 계산"""
        if not metrics:
            return "N/A"
        
        # 최근 메트릭 기반 등급 계산
        recent_metrics = metrics[-20:]  # 최근 20개
        
        avg_execution_time = statistics.mean([
            m.metrics.get("execution_time", float('inf')) for m in recent_metrics
        ])
        avg_success_rate = statistics.mean([
            m.metrics.get("success", 0) for m in recent_metrics
        ])
        avg_memory_usage = statistics.mean([
            m.metrics.get("memory_usage", 0) for m in recent_metrics
        ])
        
        # 등급 계산 로직
        score = 0
        
        # 실행 시간 점수 (30초 이하 = 100점)
        if avg_execution_time <= 10:
            score += 30
        elif avg_execution_time <= 30:
            score += 20
        elif avg_execution_time <= 60:
            score += 10
        
        # 성공률 점수
        score += int(avg_success_rate * 40)
        
        # 메모리 사용량 점수 (100MB 이하 = 30점)
        if avg_memory_usage <= 50:
            score += 30
        elif avg_memory_usage <= 100:
            score += 20
        elif avg_memory_usage <= 200:
            score += 10
        
        # 등급 결정
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    async def _generate_recommendations(
        self, 
        agent_id: str, 
        metrics: List[PerformanceMetric]
    ) -> List[str]:
        """성능 개선 권장사항 생성"""
        recommendations = []
        
        if not metrics:
            return ["충분한 데이터가 없어 권장사항을 생성할 수 없습니다."]
        
        recent_metrics = metrics[-20:]
        
        # 실행 시간 분석
        avg_execution_time = statistics.mean([
            m.metrics.get("execution_time", 0) for m in recent_metrics
        ])
        
        if avg_execution_time > 60:
            recommendations.append("실행 시간이 긴 편입니다. 알고리즘 최적화를 검토해보세요.")
        elif avg_execution_time > 30:
            recommendations.append("실행 시간 최적화 여지가 있습니다.")
        
        # 성공률 분석
        avg_success_rate = statistics.mean([
            m.metrics.get("success", 0) for m in recent_metrics
        ])
        
        if avg_success_rate < 0.8:
            recommendations.append("성공률이 낮습니다. 오류 처리 로직을 강화해보세요.")
        elif avg_success_rate < 0.9:
            recommendations.append("성공률 개선 여지가 있습니다.")
        
        # 메모리 사용량 분석
        avg_memory_usage = statistics.mean([
            m.metrics.get("memory_usage", 0) for m in recent_metrics
        ])
        
        if avg_memory_usage > 200:
            recommendations.append("메모리 사용량이 높습니다. 메모리 누수를 점검해보세요.")
        elif avg_memory_usage > 100:
            recommendations.append("메모리 사용량 최적화를 검토해보세요.")
        
        # 변동성 분석
        execution_time_std = statistics.stdev([
            m.metrics.get("execution_time", 0) for m in recent_metrics
        ]) if len(recent_metrics) > 1 else 0
        
        if execution_time_std > avg_execution_time * 0.5:
            recommendations.append("실행 시간 변동성이 큽니다. 일관성 개선이 필요합니다.")
        
        if not recommendations:
            recommendations.append("현재 성능이 양호합니다. 현재 상태를 유지하세요.")
        
        return recommendations

class AlertManager:
    """알람 관리자"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.thresholds = self._load_default_thresholds()
        self.active_alerts = {}
        self.alert_callbacks = []
        
    def _load_default_thresholds(self) -> Dict[str, PerformanceThreshold]:
        """기본 임계값 로드"""
        return {
            "execution_time": PerformanceThreshold(
                MetricType.EXECUTION_TIME, 30.0, 60.0, "gt"
            ),
            "memory_usage": PerformanceThreshold(
                MetricType.MEMORY_USAGE, 100.0, 200.0, "gt"
            ),
            "cpu_usage": PerformanceThreshold(
                MetricType.CPU_USAGE, 70.0, 90.0, "gt"
            ),
            "success_rate": PerformanceThreshold(
                MetricType.SUCCESS_RATE, 0.8, 0.7, "lt"
            ),
            "error_rate": PerformanceThreshold(
                MetricType.ERROR_RATE, 0.1, 0.2, "gt"
            )
        }
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """알람 콜백 추가"""
        self.alert_callbacks.append(callback)
    
    async def check_thresholds(self, agent_id: str, metrics: Dict[str, float]) -> List[PerformanceAlert]:
        """임계값 검사 및 알람 생성"""
        alerts = []
        
        for metric_name, value in metrics.items():
            if metric_name not in self.thresholds:
                continue
                
            threshold = self.thresholds[metric_name]
            if not threshold.enabled:
                continue
            
            alert = self._check_single_threshold(agent_id, metric_name, value, threshold)
            if alert:
                alerts.append(alert)
                await self._process_alert(alert)
        
        return alerts
    
    def _check_single_threshold(
        self, 
        agent_id: str, 
        metric_name: str, 
        value: float, 
        threshold: PerformanceThreshold
    ) -> Optional[PerformanceAlert]:
        """단일 임계값 검사"""
        severity = None
        threshold_value = None
        
        if threshold.comparison_operator == "gt":
            if value > threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif value > threshold.warning_threshold:
                severity = AlertSeverity.WARNING
                threshold_value = threshold.warning_threshold
        elif threshold.comparison_operator == "lt":
            if value < threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif value < threshold.warning_threshold:
                severity = AlertSeverity.WARNING
                threshold_value = threshold.warning_threshold
        
        if severity:
            alert_id = f"{agent_id}_{metric_name}_{severity.value}"
            
            # 중복 알람 방지
            if alert_id in self.active_alerts:
                return None
            
            message = self._generate_alert_message(metric_name, value, threshold_value, severity)
            
            return PerformanceAlert(
                alert_id=alert_id,
                agent_id=agent_id,
                metric_type=threshold.metric_type,
                severity=severity,
                current_value=value,
                threshold_value=threshold_value,
                message=message,
                created_at=datetime.utcnow()
            )
        
        return None
    
    def _generate_alert_message(
        self, 
        metric_name: str, 
        current_value: float, 
        threshold_value: float, 
        severity: AlertSeverity
    ) -> str:
        """알람 메시지 생성"""
        severity_text = {
            AlertSeverity.WARNING: "주의",
            AlertSeverity.CRITICAL: "심각"
        }.get(severity, "알림")
        
        metric_text = {
            "execution_time": "실행 시간",
            "memory_usage": "메모리 사용량",
            "cpu_usage": "CPU 사용률",
            "success_rate": "성공률",
            "error_rate": "오류율"
        }.get(metric_name, metric_name)
        
        return f"[{severity_text}] {metric_text} 임계값 초과: {current_value:.2f} (임계값: {threshold_value:.2f})"
    
    async def _process_alert(self, alert: PerformanceAlert):
        """알람 처리"""
        # 활성 알람에 추가
        self.active_alerts[alert.alert_id] = alert
        
        # 콜백 실행
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"알람 콜백 실행 실패: {e}")
        
        logger.warning(f"성능 알람 발생: {alert.message}")
    
    async def resolve_alert(self, alert_id: str):
        """알람 해결"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts.pop(alert_id)
            alert.resolved_at = datetime.utcnow()
            logger.info(f"알람 해결: {alert.message}")

class PerformanceMonitor:
    """통합 성능 모니터"""
    
    def __init__(self, db_session: AsyncSession, feedback_service: FeedbackService):
        self.db_session = db_session
        self.feedback_service = feedback_service
        self.metrics_collector = MetricsCollector(db_session)
        self.performance_analyzer = PerformanceAnalyzer(db_session)
        self.alert_manager = AlertManager(db_session)
        
        # 모니터링 상태
        self.is_monitoring = False
        self.monitoring_task = None
        self.monitoring_interval = 30  # 30초 간격
        
        # 알람 콜백 등록
        self.alert_manager.add_alert_callback(self._handle_performance_alert)
    
    async def start_monitoring(self):
        """모니터링 시작"""
        if self.is_monitoring:
            logger.warning("모니터링이 이미 실행 중입니다.")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("성능 모니터링 시작")
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("성능 모니터링 중지")
    
    async def _monitoring_loop(self):
        """모니터링 루프"""
        while self.is_monitoring:
            try:
                await self._collect_and_analyze_metrics()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_and_analyze_metrics(self):
        """메트릭 수집 및 분석"""
        try:
            # 시스템 메트릭 수집
            system_metrics = await self.metrics_collector.collect_system_metrics()
            
            # 활성 에이전트들의 메트릭 수집
            active_agents = await self._get_active_agents()
            
            for agent_id in active_agents:
                agent_metrics = await self.metrics_collector.collect_agent_metrics(agent_id)
                
                # 알람 임계값 검사
                combined_metrics = {**system_metrics, **agent_metrics}
                alerts = await self.alert_manager.check_thresholds(agent_id, combined_metrics)
                
                # 성능 피드백 생성 (필요시)
                if alerts:
                    await self._generate_performance_feedback(agent_id, combined_metrics, alerts)
            
            # 메트릭 버퍼 플러시
            await self.metrics_collector.flush_metrics_to_db()
            
        except Exception as e:
            logger.error(f"메트릭 수집 및 분석 실패: {e}")
    
    async def _get_active_agents(self) -> List[str]:
        """활성 에이전트 목록 조회"""
        try:
            # 최근 1시간 내 실행된 에이전트들
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            query = (
                select(AgentExecution.agent_id)
                .where(AgentExecution.started_at >= cutoff_time)
                .distinct()
            )
            
            result = await self.db_session.execute(query)
            return [row[0] for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"활성 에이전트 조회 실패: {e}")
            return []
    
    async def _handle_performance_alert(self, alert: PerformanceAlert):
        """성능 알람 처리 콜백"""
        try:
            # 심각한 알람의 경우 즉시 피드백 생성
            if alert.severity == AlertSeverity.CRITICAL:
                await self._generate_critical_performance_feedback(alert)
            
        except Exception as e:
            logger.error(f"성능 알람 처리 실패: {e}")
    
    async def _generate_performance_feedback(
        self, 
        agent_id: str, 
        metrics: Dict[str, float], 
        alerts: List[PerformanceAlert]
    ):
        """성능 피드백 생성"""
        try:
            # 최근 실행 ID 조회 (피드백 연결용)
            query = (
                select(AgentExecution.id)
                .where(AgentExecution.agent_id == agent_id)
                .order_by(desc(AgentExecution.started_at))
                .limit(1)
            )
            
            result = await self.db_session.execute(query)
            execution_id = result.scalar_one_or_none()
            
            if execution_id:
                await self.feedback_service.process_system_feedback(
                    execution_id, metrics
                )
                
        except Exception as e:
            logger.error(f"성능 피드백 생성 실패: {e}")
    
    async def _generate_critical_performance_feedback(self, alert: PerformanceAlert):
        """심각한 성능 이슈에 대한 피드백 생성"""
        try:
            # 심각한 성능 이슈 전용 피드백
            feedback_content = {
                "alert_type": "critical_performance",
                "metric_type": alert.metric_type.value,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "severity": alert.severity.value,
                "message": alert.message
            }
            
            # 가장 최근 실행에 연결
            query = (
                select(AgentExecution.id)
                .where(AgentExecution.agent_id == alert.agent_id)
                .order_by(desc(AgentExecution.started_at))
                .limit(1)
            )
            
            result = await self.db_session.execute(query)
            execution_id = result.scalar_one_or_none()
            
            if execution_id:
                await self.feedback_service.collector.collect_performance_feedback(
                    execution_id, feedback_content
                )
                
        except Exception as e:
            logger.error(f"심각한 성능 피드백 생성 실패: {e}")
    
    # Public API Methods
    
    async def get_performance_dashboard(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """성능 대시보드 데이터 조회"""
        try:
            if agent_id:
                # 특정 에이전트 성능 분석
                analysis = await self.performance_analyzer.analyze_agent_performance(agent_id)
                system_metrics = await self.metrics_collector.collect_system_metrics()
                
                return {
                    "agent_id": agent_id,
                    "agent_analysis": analysis,
                    "system_metrics": system_metrics,
                    "active_alerts": [
                        asdict(alert) for alert in self.alert_manager.active_alerts.values()
                        if alert.agent_id == agent_id
                    ]
                }
            else:
                # 전체 시스템 성능 대시보드
                system_metrics = await self.metrics_collector.collect_system_metrics()
                active_agents = await self._get_active_agents()
                
                return {
                    "system_metrics": system_metrics,
                    "active_agents_count": len(active_agents),
                    "total_active_alerts": len(self.alert_manager.active_alerts),
                    "critical_alerts": len([
                        alert for alert in self.alert_manager.active_alerts.values()
                        if alert.severity == AlertSeverity.CRITICAL
                    ]),
                    "monitoring_status": "active" if self.is_monitoring else "inactive"
                }
                
        except Exception as e:
            logger.error(f"성능 대시보드 조회 실패: {e}")
            raise PerformanceMonitorError(f"대시보드 조회 실패: {str(e)}")
    
    async def get_performance_report(
        self, 
        agent_id: str, 
        hours: int = 24
    ) -> Dict[str, Any]:
        """성능 리포트 생성"""
        try:
            # 상세 성능 분석
            analysis = await self.performance_analyzer.analyze_agent_performance(agent_id, hours)
            
            # 알람 히스토리 (해결된 알람 포함)
            alert_history = [
                asdict(alert) for alert in self.alert_manager.active_alerts.values()
                if alert.agent_id == agent_id
            ]
            
            # 성능 트렌드 데이터
            trend_data = await self._get_performance_trends(agent_id, hours)
            
            return {
                "agent_id": agent_id,
                "report_period_hours": hours,
                "analysis": analysis,
                "alert_history": alert_history,
                "trend_data": trend_data,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"성능 리포트 생성 실패: {e}")
            raise PerformanceMonitorError(f"리포트 생성 실패: {str(e)}")
    
    async def _get_performance_trends(
        self, 
        agent_id: str, 
        hours: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """성능 트렌드 데이터 조회"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = (
                select(PerformanceMetric)
                .where(
                    and_(
                        PerformanceMetric.agent_id == agent_id,
                        PerformanceMetric.created_at >= cutoff_time
                    )
                )
                .order_by(PerformanceMetric.created_at)
            )
            
            result = await self.db_session.execute(query)
            metrics = result.scalars().all()
            
            # 시간대별 집계 (1시간 단위)
            hourly_data = defaultdict(list)
            
            for metric in metrics:
                hour_key = metric.created_at.replace(minute=0, second=0, microsecond=0)
                hourly_data[hour_key].append(metric.metrics)
            
            # 트렌드 데이터 생성
            trend_data = {
                "execution_time": [],
                "memory_usage": [],
                "cpu_usage": [],
                "success_rate": []
            }
            
            for hour, hour_metrics in sorted(hourly_data.items()):
                timestamp = hour.isoformat()
                
                # 시간대별 평균 계산
                if hour_metrics:
                    avg_execution_time = statistics.mean([
                        m.get("execution_time", 0) for m in hour_metrics if "execution_time" in m
                    ]) if any("execution_time" in m for m in hour_metrics) else 0
                    
                    avg_memory_usage = statistics.mean([
                        m.get("memory_usage", 0) for m in hour_metrics if "memory_usage" in m
                    ]) if any("memory_usage" in m for m in hour_metrics) else 0
                    
                    avg_cpu_usage = statistics.mean([
                        m.get("cpu_usage", 0) for m in hour_metrics if "cpu_usage" in m
                    ]) if any("cpu_usage" in m for m in hour_metrics) else 0
                    
                    avg_success_rate = statistics.mean([
                        m.get("success", 0) for m in hour_metrics if "success" in m
                    ]) if any("success" in m for m in hour_metrics) else 0
                    
                    trend_data["execution_time"].append({
                        "timestamp": timestamp,
                        "value": avg_execution_time
                    })
                    trend_data["memory_usage"].append({
                        "timestamp": timestamp,
                        "value": avg_memory_usage
                    })
                    trend_data["cpu_usage"].append({
                        "timestamp": timestamp,
                        "value": avg_cpu_usage
                    })
                    trend_data["success_rate"].append({
                        "timestamp": timestamp,
                        "value": avg_success_rate
                    })
            
            return trend_data
            
        except Exception as e:
            logger.error(f"성능 트렌드 조회 실패: {e}")
            return {}
    
    async def update_alert_thresholds(
        self, 
        metric_type: str, 
        warning_threshold: float, 
        critical_threshold: float
    ):
        """알람 임계값 업데이트"""
        try:
            if metric_type in self.alert_manager.thresholds:
                threshold = self.alert_manager.thresholds[metric_type]
                threshold.warning_threshold = warning_threshold
                threshold.critical_threshold = critical_threshold
                
                logger.info(f"임계값 업데이트: {metric_type} - 경고: {warning_threshold}, 심각: {critical_threshold}")
            else:
                logger.warning(f"알 수 없는 메트릭 타입: {metric_type}")
                
        except Exception as e:
            logger.error(f"임계값 업데이트 실패: {e}")
            raise PerformanceMonitorError(f"임계값 업데이트 실패: {str(e)}")
    
    def set_monitoring_interval(self, interval_seconds: int):
        """모니터링 간격 설정"""
        if interval_seconds < 10:
            raise ValueError("모니터링 간격은 최소 10초 이상이어야 합니다.")
        
        self.monitoring_interval = interval_seconds
        logger.info(f"모니터링 간격 변경: {interval_seconds}초")
    
    async def trigger_immediate_analysis(self, agent_id: str) -> Dict[str, Any]:
        """즉시 성능 분석 실행"""
        try:
            # 현재 메트릭 수집
            agent_metrics = await self.metrics_collector.collect_agent_metrics(agent_id)
            system_metrics = await self.metrics_collector.collect_system_metrics()
            
            # 임계값 검사
            combined_metrics = {**system_metrics, **agent_metrics}
            alerts = await self.alert_manager.check_thresholds(agent_id, combined_metrics)
            
            # 상세 분석
            analysis = await self.performance_analyzer.analyze_agent_performance(agent_id, hours=1)
            
            return {
                "agent_id": agent_id,
                "current_metrics": combined_metrics,
                "immediate_alerts": [asdict(alert) for alert in alerts],
                "analysis": analysis,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"즉시 분석 실행 실패: {e}")
            raise PerformanceMonitorError(f"즉시 분석 실행 실패: {str(e)}")

# 성능 모니터 싱글톤 인스턴스 (선택적)
_performance_monitor_instance = None

async def get_performance_monitor(db_session: AsyncSession, feedback_service: FeedbackService) -> PerformanceMonitor:
    """성능 모니터 인스턴스 가져오기"""
    global _performance_monitor_instance
    
    if _performance_monitor_instance is None:
        _performance_monitor_instance = PerformanceMonitor(db_session, feedback_service)
    
    return _performance_monitor_instance