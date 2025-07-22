# @dataclass
# class AgentPerformanceSnapshot:
#     """에이전트 성능 스냅샷"""
#     agent_id: str
#     timestamp: datetime
#     total_requests: int
#     successful_requests: int
#     failed_requests: int
#     avg_response_time: float
#     memory_usage_mb: float
#     active_memories: Dict[str, int]  # memory_type -> count
#     last_activity: datetime

# @dataclass
# class PerformanceAlert:
#     """성능 알림"""
#     alert_id: str
#     timestamp: datetime
#     severity: str  # 'warning', 'critical'
#     metric_name: str
#     current_value: float
#     threshold_value: float
#     message: str
#     agent_id: Optional[str] = None
#     context: Optional[Dict[str, Any]] = None

# class PerformanceMonitor:
#     """성능 모니터링 시스템"""
    
#     def __init__(self, 
#                  collection_interval: int = 30,
#                  history_retention_hours: int = 24,
#                  max_metrics_per_type: int = 1000):
#         self.collection_interval = collection_interval
#         self.history_retention_hours = history_retention_hours
#         self.max_metrics_per_type = max_metrics_per_type
        
#         # 메트릭 저장소
#         self.metrics_history: Dict[str, deque] = defaultdict(
#             lambda: deque(maxlen=max_metrics_per_type)
#         )
#         self.system_metrics_history: deque = deque(maxlen=max_metrics_per_type)
#         self.agent_snapshots: Dict[str, AgentPerformanceSnapshot] = {}
        
#         # 임계값 설정
#         self.thresholds = self._initialize_thresholds()
        
#         # 알림 시스템
#         self.alerts: List[PerformanceAlert] = []
#         self.alert_callbacks: List[Callable] = []
        
#         # 모니터링 상태
#         self.is_monitoring = False
#         self.monitor_thread = None
#         self._lock = threading.Lock()
        
#         # 성능 통계
#         self.performance_stats = {
#             'monitoring_start_time': None,
#             'total_metrics_collected': 0,
#             'total_alerts_generated': 0,
#             'agent_count': 0
#         }
    
#     def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
#         """기본 임계값 설정"""
#         return {
#             'response_time': {
#                 'warning': 2.0,  # 2초
#                 'critical': 5.0  # 5초
#             },
#             'memory_usage': {
#                 'warning': 80.0,  # 80%
#                 'critical': 95.0  # 95%
#             },
#             'error_rate': {
#                 'warning': 0.05,  # 5%
#                 'critical': 0.15   # 15%
#             },
#             'cpu_usage': {
#                 'warning': 70.0,  # 70%
#                 'critical': 90.0   # 90%
#             },
#             'throughput': {
#                 'warning': 10.0,   # 10 req/min 미만
#                 'critical': 5.0    # 5 req/min 미만
#             }
#         }
    
#     async def start_monitoring(self):
#         """모니터링 시작"""
#         if self.is_monitoring:
#             logger.warning("Performance monitoring is already running")
#             return
        
#         self.is_monitoring = True
#         self.performance_stats['monitoring_start_time'] = datetime.utcnow()
        
#         # 별도 스레드에서 시스템 메트릭 수집
#         self.monitor_thread = threading.Thread(
#             target=self._system_monitoring_loop,
#             daemon=True
#         )
#         self.monitor_thread.start()
        
#         logger.info("Performance monitoring started")
    
#     def stop_monitoring(self):
#         """모니터링 중지"""
#         self.is_monitoring = False
#         if self.monitor_thread:
#             self.monitor_thread.join(timeout=5)
        
#         logger.info("Performance monitoring stopped")
    
#     def _system_monitoring_loop(self):
#         """시스템 메트릭 수집 루프"""
#         while self.is_monitoring:
#             try:
#                 self._collect_system_metrics()
#                 time.sleep(self.collection_interval)
#             except Exception as e:
#                 logger.error(f"Error in system monitoring loop: {str(e)}")
#                 time.sleep(self.collection_interval)
    
#     def _collect_system_metrics(self):
#         """시스템 메트릭 수집"""
#         try:
#             # CPU 사용률
#             cpu_percent = psutil.cpu_percent(interval=1)
            
#             # 메모리 정보
#             memory = psutil.virtual_memory()
            
#             # 디스크 사용률
#             disk = psutil.disk_usage('/')
            
#             # 네트워크 I/O
#             network = psutil.net_io_counters()
            
#             # 스레드 수
#             active_threads = threading.active_count()
            
#             system_metrics = SystemMetrics(
#                 timestamp=datetime.utcnow(),
#                 cpu_percent=cpu_percent,
#                 memory_percent=memory.percent,
#                 memory_used_mb=memory.used / (1024 * 1024),
#                 memory_available_mb=memory.available / (1024 * 1024),
#                 disk_usage_percent=disk.percent,
#                 network_io_bytes_sent=network.bytes_sent,
#                 network_io_bytes_recv=network.bytes_recv,
#                 active_threads=active_threads
#             )
            
#             with self._lock:
#                 self.system_metrics_history.append(system_metrics)
#                 self.performance_stats['total_metrics_collected'] += 1
            
#             # 임계값 확인 및 알림 생성
#             self._check_system_thresholds(system_metrics)
            
#         except Exception as e:
#             logger.error(f"Error collecting system metrics: {str(e)}")
    
#     def record_metric(self, 
#                      metric_type: MetricType,
#                      metric_name: str,
#                      value: float,
#                      unit: str,
#                      agent_id: Optional[str] = None,
#                      context: Optional[Dict[str, Any]] = None,
#                      tags: Optional[List[str]] = None):
#         """개별 메트릭 기록"""
#         try:
#             metric = PerformanceMetric(
#                 timestamp=datetime.utcnow(),
#                 metric_type=metric_type,
#                 metric_name=metric_name,
#                 value=value,
#                 unit=unit,
#                 agent_id=agent_id,
#                 context=context or {},
#                 tags=tags or []
#             )
            
#             metric_key = f"{metric_type.value}:{metric_name}"
#             if agent_id:
#                 metric_key = f"{agent_id}:{metric_key}"
            
#             with self._lock:
#                 self.metrics_history[metric_key].append(metric)
#                 self.performance_stats['total_metrics_collected'] += 1
            
#             # 임계값 확인
#             self._check_metric_threshold(metric)
            
#         except Exception as e:
#             logger.error(f"Error recording metric: {str(e)}")
    
#     async def record_response_time(self, 
#                                   agent_id: str,
#                                   operation: str,
#                                   response_time: float,
#                                   success: bool = True,
#                                   context: Optional[Dict[str, Any]] = None):
#         """응답 시간 기록"""
#         self.record_metric(
#             metric_type=MetricType.RESPONSE_TIME,
#             metric_name=f"{operation}_response_time",
#             value=response_time,
#             unit="seconds",
#             agent_id=agent_id,
#             context={
#                 **(context or {}),
#                 'operation': operation,
#                 'success': success
#             },
#             tags=['response_time', operation]
#         )
        
#         # 에이전트 스냅샷 업데이트
#         await self._update_agent_snapshot(agent_id, response_time, success)
    
#     async def record_memory_usage(self,
#                                  agent_id: str,
#                                  memory_type: MemoryType,
#                                  memory_count: int,
#                                  memory_size_mb: float):
#         """메모리 사용량 기록"""
#         self.record_metric(
#             metric_type=MetricType.MEMORY_USAGE,
#             metric_name=f"{memory_type.value}_memory_usage",
#             value=memory_size_mb,
#             unit="MB",
#             agent_id=agent_id,
#             context={
#                 'memory_type': memory_type.value,
#                 'memory_count': memory_count
#             },
#             tags=['memory', memory_type.value]
#         )
        
#         # 에이전트 스냅샷의 메모리 정보 업데이트
#         with self._lock:
#             if agent_id not in self.agent_snapshots:
#                 self.agent_snapshots[agent_id] = AgentPerformanceSnapshot(
#                     agent_id=agent_id,
#                     timestamp=datetime.utcnow(),
#                     total_requests=0,
#                     successful_requests=0,
#                     failed_requests=0,
#                     avg_response_time=0.0,
#                     memory_usage_mb=0.0,
#                     active_memories={},
#                     last_activity=datetime.utcnow()
#                 )
            
#             snapshot = self.agent_snapshots[agent_id]
#             snapshot.active_memories[memory_type.value] = memory_count
#             snapshot.memory_usage_mb += memory_size_mb
#             snapshot.last_activity = datetime.utcnow()
    
#     async def record_throughput(self,
#                                agent_id: str,
#                                operation: str,
#                                requests_per_minute: float):
#         """처리량 기록"""
#         self.record_metric(
#             metric_type=MetricType.THROUGHPUT,
#             metric_name=f"{operation}_throughput",
#             value=requests_per_minute,
#             unit="req/min",
#             agent_id=agent_id,
#             context={'operation': operation},
#             tags=['throughput', operation]
#         )
    
#     async def record_error_rate(self,
#                                agent_id: str,
#                                operation: str,
#                                error_rate: float,
#                                total_requests: int,
#                                failed_requests: int):
#         """에러율 기록"""
#         self.record_metric(
#             metric_type=MetricType.ERROR_RATE,
#             metric_name=f"{operation}_error_rate",
#             value=error_rate,
#             unit="percentage",
#             agent_id=agent_id,
#             context={
#                 'operation': operation,
#                 'total_requests': total_requests,
#                 'failed_requests': failed_requests
#             },
#             tags=['error_rate', operation]
#         )
    
#     async def _update_agent_snapshot(self, 
#                                    agent_id: str, 
#                                    response_time: float, 
#                                    success: bool):
#         """에이전트 성능 스냅샷 업데이트"""
#         with self._lock:
#             if agent_id not in self.agent_snapshots:
#                 self.agent_snapshots[agent_id] = AgentPerformanceSnapshot(
#                     agent_id=agent_id,
#                     timestamp=datetime.utcnow(),
#                     total_requests=0,
#                     successful_requests=0,
#                     failed_requests=0,
#                     avg_response_time=0.0,
#                     memory_usage_mb=0.0,
#                     active_memories={},
#                     last_activity=datetime.utcnow()
#                 )
            
#             snapshot = self.agent_snapshots[agent_id]
#             snapshot.total_requests += 1
            
#             if success:
#                 snapshot.successful_requests += 1
#             else:
#                 snapshot.failed_requests += 1
            
#             # 이동 평균으로 응답 시간 업데이트
#             total_requests = snapshot.total_requests
#             snapshot.avg_response_time = (
#                 (snapshot.avg_response_time * (total_requests - 1) + response_time) 
#                 / total_requests
#             )
            
#             snapshot.last_activity = datetime.utcnow()
#             snapshot.timestamp = datetime.utcnow()
    
#     def _check_system_thresholds(self, system_metrics: SystemMetrics):
#         """시스템 메트릭 임계값 확인"""
#         checks = [
#             ('cpu_usage', system_metrics.cpu_percent),
#             ('memory_usage', system_metrics.memory_percent),
#             ('disk_usage', system_metrics.disk_usage_percent)
#         ]
        
#         for metric_name, value in checks:
#             if metric_name in self.thresholds:
#                 self._check_threshold(metric_name, value, None, {
#                     'system_metric': True,
#                     'timestamp': system_metrics.timestamp.isoformat()
#                 })
    
#     def _check_metric_threshold(self, metric: PerformanceMetric):
#         """개별 메트릭 임계값 확인"""
#         metric_name = metric.metric_name
        
#         # 기본 메트릭 이름으로 임계값 찾기
#         threshold_key = None
#         for key in self.thresholds.keys():
#             if key in metric_name:
#                 threshold_key = key
#                 break
        
#         if threshold_key:
#             self._check_threshold(
#                 threshold_key, 
#                 metric.value, 
#                 metric.agent_id,
#                 {
#                     'metric_name': metric_name,
#                     'metric_type': metric.metric_type.value,
#                     'timestamp': metric.timestamp.isoformat(),
#                     'context': metric.context
#                 }
#             )
    
#     def _check_threshold(self, 
#                         metric_name: str, 
#                         value: float, 
#                         agent_id: Optional[str],
#                         context: Dict[str, Any]):
#         """임계값 확인 및 알림 생성"""
#         if metric_name not in self.thresholds:
#             return
        
#         thresholds = self.thresholds[metric_name]
        
#         severity = None
#         threshold_value = None
        
#         if value >= thresholds['critical']:
#             severity = 'critical'
#             threshold_value = thresholds['critical']
#         elif value >= thresholds['warning']:
#             severity = 'warning'
#             threshold_value = thresholds['warning']
        
#         if severity:
#             self._generate_alert(
#                 severity=severity,
#                 metric_name=metric_name,
#                 current_value=value,
#                 threshold_value=threshold_value,
#                 agent_id=agent_id,
#                 context=context
#             )
    
#     def _generate_alert(self,
#                        severity: str,
#                        metric_name: str,
#                        current_value: float,
#                        threshold_value: float,
#                        agent_id: Optional[str],
#                        context: Dict[str, Any]):
#         """성능 알림 생성"""
#         alert_id = f"{metric_name}_{agent_id or 'system'}_{int(time.time())}"
        
#         message = f"{metric_name.title()} {severity}: {current_value:.2f}"
#         if agent_id:
#             message += f" for agent {agent_id}"
#         message += f" (threshold: {threshold_value:.2f})"
        
#         alert = PerformanceAlert(
#             alert_id=alert_id,
#             timestamp=datetime.utcnow(),
#             severity=severity,
#             metric_name=metric_name,
#             current_value=current_value,
#             threshold_value=threshold_value,
#             message=message,
#             agent_id=agent_id,
#             context=context
#         )
        
#         with self._lock:
#             self.alerts.append(alert)
#             self.performance_stats['total_alerts_generated'] += 1
        
#         # 알림 콜백 실행
#         for callback in self.alert_callbacks:
#             try:
#                 callback(alert)
#             except Exception as e:
#                 logger.error(f"Error in alert callback: {str(e)}")
        
#         logger.warning(f"Performance alert: {message}")
    
#     def get_metrics_summary(self, 
#                            time_range_hours: int = 1,
#                            agent_id: Optional[str] = None) -> Dict[str, Any]:
#         """메트릭 요약 정보 조회"""
#         cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        
#         summary = {
#             'time_range_hours': time_range_hours,
#             'agent_id': agent_id,
#             'metrics': {},
#             'system_metrics': {},
#             'alerts': []
#         }
        
#         with self._lock:
#             # 개별 메트릭 요약
#             for metric_key, metrics in self.metrics_history.items():
#                 if agent_id and not metric_key.startswith(f"{agent_id}:"):
#                     continue
                
#                 recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
#                 if recent_metrics:
#                     values = [m.value for m in recent_metrics]
#                     summary['metrics'][metric_key] = {
#                         'count': len(values),
#                         'min': min(values),
#                         'max': max(values),
#                         'avg': sum(values) / len(values),
#                         'latest': values[-1] if values else None,
#                         'unit': recent_metrics[0].unit
#                     }
            
#             # 시스템 메트릭 요약
#             recent_system_metrics = [
#                 m for m in self.system_metrics_history 
#                 if m.timestamp >= cutoff_time
#             ]
            
#             if recent_system_metrics:
#                 cpu_values = [m.cpu_percent for m in recent_system_metrics]
#                 memory_values = [m.memory_percent for m in recent_system_metrics]
                
#                 summary['system_metrics'] = {
#                     'cpu_usage': {
#                         'avg': sum(cpu_values) / len(cpu_values),
#                         'max': max(cpu_values),
#                         'latest': cpu_values[-1]
#                     },
#                     'memory_usage': {
#                         'avg': sum(memory_values) / len(memory_values),
#                         'max': max(memory_values),
#                         'latest': memory_values[-1]
#                     },
#                     'sample_count': len(recent_system_metrics)
#                 }
            
#             # 최근 알림
#             recent_alerts = [
#                 a for a in self.alerts 
#                 if a.timestamp >= cutoff_time and (not agent_id or a.agent_id == agent_id)
#             ]
#             summary['alerts'] = [asdict(alert) for alert in recent_alerts[-10:]]
        
#         return summary
    
#     def get_agent_performance(self, agent_id: str) -> Optional[Dict[str, Any]]:
#         """특정 에이전트 성능 정보 조회"""
#         with self._lock:
#             if agent_id not in self.agent_snapshots:
#                 return None
            
#             snapshot = self.agent_snapshots[agent_id]
            
#             # 에러율 계산
#             error_rate = 0.0
#             if snapshot.total_requests > 0:
#                 error_rate = snapshot.failed_requests / snapshot.total_requests
            
#             # 최근 메트릭 조회
#             recent_metrics = self.get_metrics_summary(time_range_hours=1, agent_id=agent_id)
            
#             return {
#                 'agent_id': agent_id,
#                 'snapshot': asdict(snapshot),
#                 'performance_metrics': {
#                     'error_rate': error_rate,
#                     'success_rate': 1.0 - error_rate,
#                     'requests_per_hour': snapshot.total_requests  # 실제로는 시간 기반 계산 필요
#                 },
#                 'recent_metrics': recent_metrics,
#                 'health_status': self._calculate_agent_health(snapshot)
#             }
    
#     def _calculate_agent_health(self, snapshot: AgentPerformanceSnapshot) -> str:
#         """에이전트 건강 상태 계산"""
#         now = datetime.utcnow()
        
#         # 최근 활동 확인
#         if (now - snapshot.last_activity).total_seconds() > 300:  # 5분
#             return 'inactive'
        
#         # 에러율 확인
#         error_rate = 0.0
#         if snapshot.total_requests > 0:
#             error_rate = snapshot.failed_requests / snapshot.total_requests
        
#         if error_rate > 0.15:  # 15% 이상
#             return 'critical'
#         elif error_rate > 0.05:  # 5% 이상
#             return 'warning'
        
#         # 응답 시간 확인
#         if snapshot.avg_response_time > 5.0:  # 5초 이상
#             return 'critical'
#         elif snapshot.avg_response_time > 2.0:  # 2초 이상
#             return 'warning'
        
#         return 'healthy'
    
#     def get_all_agents_performance(self) -> Dict[str, Dict[str, Any]]:
#         """모든 에이전트 성능 정보 조회"""
#         agents_performance = {}
        
#         with self._lock:
#             for agent_id in self.agent_snapshots.keys():
#                 agents_performance[agent_id] = self.get_agent_performance(agent_id)
        
#         return agents_performance
    
#     def get_system_health(self) -> Dict[str, Any]:
#         """전체 시스템 건강 상태 조회"""
#         with self._lock:
#             latest_system_metrics = None
#             if self.system_metrics_history:
#                 latest_system_metrics = self.system_metrics_history[-1]
            
#             active_agents = len(self.agent_snapshots)
#             healthy_agents = sum(
#                 1 for agent_id in self.agent_snapshots.keys()
#                 if self.get_agent_performance(agent_id)['health_status'] == 'healthy'
#             )
            
#             recent_alerts = [
#                 a for a in self.alerts 
#                 if a.timestamp >= datetime.utcnow() - timedelta(hours=1)
#             ]
            
#             critical_alerts = len([a for a in recent_alerts if a.severity == 'critical'])
#             warning_alerts = len([a for a in recent_alerts if a.severity == 'warning'])
            
#             # 전체 건강 상태 결정
#             overall_health = 'healthy'
#             if critical_alerts > 0:
#                 overall_health = 'critical'
#             elif warning_alerts > 0 or (active_agents > 0 and healthy_agents / active_agents < 0.8):
#                 overall_health = 'warning'
            
#             return {
#                 'overall_health': overall_health,
#                 'system_metrics': asdict(latest_system_metrics) if latest_system_metrics else None,
#                 'agent_summary': {
#                     'total_agents': active_agents,
#                     'healthy_agents': healthy_agents,
#                     'health_percentage': (healthy_agents / active_agents * 100) if active_agents > 0 else 0
#                 },
#                 'alerts_summary': {
#                     'total_recent_alerts': len(recent_alerts),
#                     'critical_alerts': critical_alerts,
#                     'warning_alerts': warning_alerts
#                 },
#                 'monitoring_stats': self.performance_stats.copy(),
#                 'uptime_hours': (
#                     (datetime.utcnow() - self.performance_stats['monitoring_start_time']).total_seconds() / 3600
#                     if self.performance_stats['monitoring_start_time'] else 0
#                 )
#             }
    
#     def set_threshold(self, metric_name: str, warning: float, critical: float):
#         """임계값 설정"""
#         self.thresholds[metric_name] = {
#             'warning': warning,
#             'critical': critical
#         }
#         logger.info(f"Updated threshold for {metric_name}: warning={warning}, critical={critical}")
    
#     def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
#         """알림 콜백 추가"""
#         self.alert_callbacks.append(callback)
    
#     def clear_old_data(self, retention_hours: int = None):
#         """오래된 데이터 정리"""
#         retention_hours = retention_hours or self.history_retention_hours
#         cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
        
#         cleaned_count = 0
        
#         with self._lock:
#             # 메트릭 히스토리 정리
#             for metric_key in self.metrics_history:
#                 original_length = len(self.metrics_history[metric_key])
#                 self.metrics_history[metric_key] = deque(
#                     [m for m in self.metrics_history[metric_key] if m.timestamp >= cutoff_time],
#                     maxlen=self.max_metrics_per_type
#                 )
#                 cleaned_count += original_length - len(self.metrics_history[metric_key])
            
#             # 시스템 메트릭 정리
#             original_length = len(self.system_metrics_history)
#             self.system_metrics_history = deque(
#                 [m for m in self.system_metrics_history if m.timestamp >= cutoff_time],
#                 maxlen=self.max_metrics_per_type
#             )
#             cleaned_count += original_length - len(self.system_metrics_history)
            
#             # 알림 정리
#             original_length = len(self.alerts)
#             self.alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
#             cleaned_count += original_length - len(self.alerts)
        
#         logger.info(f"Cleaned {cleaned_count} old performance records")
#         return cleaned_count
    
#     def export_metrics(self, 
#                       time_range_hours: int = 24,
#                       agent_id: Optional[str] = None) -> Dict[str, Any]:
#         """메트릭 데이터 내보내기"""
#         cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        
#         export_data = {
#             'export_timestamp': datetime.utcnow().isoformat(),
#             'time_range_hours': time_range_hours,
#             'agent_id': agent_id,
#             'metrics': [],
#             'system_metrics': [],
#             'alerts': [],
#             'agent_snapshots': {}
#         }
        
#         with self._lock:
#             # 개별 메트릭 내보내기
#             for metric_key, metrics in self.metrics_history.items():
#                 if agent_id and not metric_key.startswith(f"{agent_id}:"):
#                     continue
                
#                 recent_metrics = [
#                     asdict(m) for m in metrics 
#                     if m.timestamp >= cutoff_time
#                 ]
                
#                 for metric_data in recent_metrics:
#                     metric_data['timestamp'] = metric_data['timestamp'].isoformat()
#                     metric_data['metric_type'] = metric_data['metric_type'].value
                
#                 export_data['metrics'].extend(recent_metrics)
            
#             # 시스템 메트릭 내보내기
#             recent_system_metrics = [
#                 m for m in self.system_metrics_history 
#                 if m.timestamp >= cutoff_time
#             ]
            
#             for system_metric in recent_system_metrics:
#                 system_data = asdict(system_metric)
#                 system_data['timestamp'] = system_data['timestamp'].isoformat()
#                 export_data['system_metrics'].append(system_data)
            
#             # 알림 내보내기
#             recent_alerts = [
#                 a for a in self.alerts 
#                 if a.timestamp >= cutoff_time and (not agent_id or a.agent_id == agent_id)
#             ]
            
#             for alert in recent_alerts:
#                 alert_data = asdict(alert)
#                 alert_data['timestamp'] = alert_data['timestamp'].isoformat()
#                 export_data['alerts'].append(alert_data)
            
#             # 에이전트 스냅샷 내보내기
#             for aid, snapshot in self.agent_snapshots.items():
#                 if agent_id and aid != agent_id:
#                     continue
                
#                 snapshot_data = asdict(snapshot)
#                 snapshot_data['timestamp'] = snapshot_data['timestamp'].isoformat()
#                 snapshot_data['last_activity'] = snapshot_data['last_activity'].isoformat()
#                 export_data['agent_snapshots'][aid] = snapshot_data
        
#         return export_data
    
#     async def health_check(self) -> Dict[str, Any]:
#         """모니터링 시스템 건강 확인"""
#         health_status = {
#             'monitoring_active': self.is_monitoring,
#             'monitor_thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False,
#             'metrics_collected': self.performance_stats['total_metrics_collected'],
#             'alerts_generated': self.performance_stats['total_alerts_generated'],
#             'active_agents': len(self.agent_snapshots),
#             'memory_usage': {
#                 'metrics_history_size': sum(len(deque_obj) for deque_obj in self.metrics_history.values()),
#                 'system_metrics_size': len(self.system_metrics_history),
#                 'alerts_size': len(self.alerts)
#             },
#             'status': 'healthy'
#         }
        
#         # 문제 감지
#         issues = []
        
#         if not self.is_monitoring:
#             issues.append("Monitoring is not active")
#             health_status['status'] = 'critical'
        
#         if self.monitor_thread and not self.monitor_thread.is_alive():
#             issues.append("Monitor thread is not alive")
#             health_status['status'] = 'critical'
        
#         if health_status['memory_usage']['metrics_history_size'] > self.max_metrics_per_type * 10:
#             issues.append("High memory usage detected")
#             if health_status['status'] == 'healthy':
#                 health_status['status'] = 'warning'
        
#         health_status['issues'] = issues
        
#         return health_status

# # 전역 모니터 인스턴스
# _global_monitor: Optional[PerformanceMonitor] = None

# def get_performance_monitor() -> PerformanceMonitor:
#     """전역 성능 모니터 인스턴스 반환"""
#     global _global_monitor
#     if _global_monitor is None:
#         _global_monitor = PerformanceMonitor()
#     return _global_monitor

# # 데코레이터 함수들
# def monitor_performance(operation_name: str):
#     """성능 모니터링 데코레이터"""
#     def decorator(func):
#         if asyncio.iscoroutinefunction(func):
#             async def async_wrapper(*args, **kwargs):
#                 monitor = get_performance_monitor()
#                 start_time = time.time()
#                 success = True
#                 error = None
                
#                 try:
#                     result = await func(*args, **kwargs)
#                     return result
#                 except Exception as e:
#                     success = False
#                     error = str(e)
#                     raise
#                 finally:
#                     end_time = time.time()
#                     response_time = end_time - start_time
                    
#                     # 에이전트 ID 추출 (첫 번째 인자가 에이전트 ID라고 가정)
#                     agent_id = None
#                     if args and isinstance(args[0], str):
#                         agent_id = args[0]
#                     elif 'agent_id' in kwargs:
#                         agent_id = kwargs['agent_id']
                    
#                     # 응답 시간 기록
#                     await monitor.record_response_time(
#                         agent_id=agent_id or 'unknown',
#                         operation=operation_name,
#                         response_time=response_time,
#                         success=success,
#                         context={'error': error} if error else None
#                     )
            
#             return async_wrapper
#         else:
#             def sync_wrapper(*args, **kwargs):
#                 monitor = get_performance_monitor()
#                 start_time = time.time()
#                 success = True
#                 error = None
                
#                 try:
#                     result = func(*args, **kwargs)
#                     return result
#                 except Exception as e:
#                     success = False
#                     error = str(e)
#                     raise
#                 finally:
#                     end_time = time.time()
#                     response_time = end_time - start_time
                    
#                     # 에이전트 ID 추출
#                     agent_id = None
#                     if args and isinstance(args[0], str):
#                         agent_id = args[0]
#                     elif 'agent_id' in kwargs:
#                         agent_id = kwargs['agent_id']
                    
#                     # 동기 함수에서는 비동기 기록을 직접 호출할 수 없으므로
#                     # 동기적으로 메트릭 기록
#                     monitor.record_metric(
#                         metric_type=MetricType.RESPONSE_TIME,
#                         metric_name=f"{operation_name}_response_time",
#                         value=response_time,
#                         unit="seconds",
#                         agent_id=agent_id or 'unknown',
#                         context={
#                             'operation': operation_name,
#                             'success': success,
#                             'error': error
#                         } if error else {
#                             'operation': operation_name,
#                             'success': success
#                         }
#                     )
            
#             return sync_wrapper
    
#     return decorator

# def monitor_memory_usage(memory_type: MemoryType):
#     """메모리 사용량 모니터링 데코레이터"""
#     def decorator(func):
#         if asyncio.iscoroutinefunction(func):
#             async def async_wrapper(*args, **kwargs):
#                 monitor = get_performance_monitor()
                
#                 # 메모리 사용량 측정 (간단한 예시)
#                 import sys
#                 before_memory = sys.getsizeof(args) + sys.getsizeof(kwargs)
                
#                 try:
#                     result = await func(*args, **kwargs)
#                     after_memory = sys.getsizeof(result) if result else 0
                    
#                     # 에이전트 ID 추출
#                     agent_id = None
#                     if args and isinstance(args[0], str):
#                         agent_id = args[0]
#                     elif 'agent_id' in kwargs:
#                         agent_id = kwargs['agent_id']
                    
#                     # 메모리 사용량 기록
#                     memory_size_mb = (before_memory + after_memory) / (1024 * 1024)
#                     await monitor.record_memory_usage(
#                         agent_id=agent_id or 'unknown',
#                         memory_type=memory_type,
#                         memory_count=1,  # 실제로는 더 정확한 계산 필요
#                         memory_size_mb=memory_size_mb
#                     )
                    
#                     return result
                    
#                 except Exception as e:
#                     raise
            
#             return async_wrapper
#         else:
#             # 동기 함수용 래퍼
#             def sync_wrapper(*args, **kwargs):
#                 return func(*args, **kwargs)
#             return sync_wrapper
    
#     return decorator

# # 컨텍스트 매니저
# class PerformanceContext:
#     """성능 측정 컨텍스트 매니저"""
    
#     def __init__(self, 
#                  operation_name: str,
#                  agent_id: str,
#                  monitor: Optional[PerformanceMonitor] = None):
#         self.operation_name = operation_name
#         self.agent_id = agent_id
#         self.monitor = monitor or get_performance_monitor()
#         self.start_time = None
#         self.context_data = {}
    
#     def __enter__(self):
#         self.start_time = time.time()
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         if self.start_time:
#             end_time = time.time()
#             response_time = end_time - self.start_time
#             success = exc_type is None
            
#             # 비동기 기록을 위한 이벤트 루프 확인
#             try:
#                 loop = asyncio.get_event_loop()
#                 if loop.is_running():
#                     # 이미 실행 중인 루프가 있으면 태스크로 예약
#                     asyncio.create_task(
#                         self.monitor.record_response_time(
#                             agent_id=self.agent_id,
#                             operation=self.operation_name,
#                             response_time=response_time,
#                             success=success,
#                             context={
#                                 **self.context_data,
#                                 'error': str(exc_val) if exc_val else None
#                             }
#                         )
#                     )
#                 else:
#                     # 새 루프에서 실행
#                     asyncio.run(
#                         self.monitor.record_response_time(
#                             agent_id=self.agent_id,
#                             operation=self.operation_name,
#                             response_time=response_time,
#                             success=success,
#                             context={
#                                 **self.context_data,
#                                 'error': str(exc_val) if exc_val else None
#                             }
#                         )
#                     )
#             except RuntimeError:
#                 # 이벤트 루프가 없으면 동기적으로 기록
#                 self.monitor.record_metric(
#                     metric_type=MetricType.RESPONSE_TIME,
#                     metric_name=f"{self.operation_name}_response_time",
#                     value=response_time,
#                     unit="seconds",
#                     agent_id=self.agent_id,
#                     context={
#                         **self.context_data,
#                         'operation': self.operation_name,
#                         'success': success,
#                         'error': str(exc_val) if exc_val else None
#                     }
#                 )
    
#     def add_context(self, key: str, value: Any):
#         """컨텍스트 데이터 추가"""
#         self.context_data[key] = value

# # 비동기 컨텍스트 매니저
# class AsyncPerformanceContext:
#     """비동기 성능 측정 컨텍스트 매니저"""
    
#     def __init__(self, 
#                  operation_name: str,
#                  agent_id: str,
#                  monitor: Optional[PerformanceMonitor] = None):
#         self.operation_name = operation_name
#         self.agent_id = agent_id
#         self.monitor = monitor or get_performance_monitor()
#         self.start_time = None
#         self.context_data = {}
    
#     async def __aenter__(self):
#         self.start_time = time.time()
#         return self
    
#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         if self.start_time:
#             end_time = time.time()
#             response_time = end_time - self.start_time
#             success = exc_type is None
            
#             await self.monitor.record_response_time(
#                 agent_id=self.agent_id,
#                 operation=self.operation_name,
#                 response_time=response_time,
#                 success=success,
#                 context={
#                     **self.context_data,
#                     'error': str(exc_val) if exc_val else None
#                 }
#             )
    
#     def add_context(self, key: str, value: Any):
#         """컨텍스트 데이터 추가"""
#         self.context_data[key] = value

# # 유틸리티 함수들
# async def start_global_monitoring():
#     """전역 모니터링 시작"""
#     monitor = get_performance_monitor()
#     await monitor.start_monitoring()
    
#     # 기본 알림 콜백 등록
#     def default_alert_callback(alert: PerformanceAlert):
#         logger.warning(f"Performance Alert: {alert.message}")
    
#     monitor.add_alert_callback(default_alert_callback)
    
#     return monitor

# def stop_global_monitoring():
#     """전역 모니터링 중지"""
#     global _global_monitor
#     if _global_monitor:
#         _global_monitor.stop_monitoring()

# def configure_thresholds(custom_thresholds: Dict[str, Dict[str, float]]):
#     """사용자 정의 임계값 설정"""
#     monitor = get_performance_monitor()
#     for metric_name, thresholds in custom_thresholds.items():
#         if 'warning' in thresholds and 'critical' in thresholds:
#             monitor.set_threshold(
#                 metric_name=metric_name,
#                 warning=thresholds['warning'],
#                 critical=thresholds['critical']
#             )

# # 성능 리포트 생성
# class PerformanceReporter:
#     """성능 리포트 생성기"""
    
#     def __init__(self, monitor: Optional[PerformanceMonitor] = None):
#         self.monitor = monitor or get_performance_monitor()
    
#     def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
#         """일일 성능 리포트 생성"""
#         target_date = date or datetime.utcnow().date()
        
#         report = {
#             'report_date': target_date.isoformat(),
#             'generated_at': datetime.utcnow().isoformat(),
#             'summary': {},
#             'agent_performance': {},
#             'system_performance': {},
#             'alerts_summary': {},
#             'recommendations': []
#         }
        
#         # 24시간 메트릭 요약
#         metrics_summary = self.monitor.get_metrics_summary(time_range_hours=24)
#         report['summary'] = metrics_summary
        
#         # 에이전트별 성능
#         agents_performance = self.monitor.get_all_agents_performance()
#         report['agent_performance'] = agents_performance
        
#         # 시스템 건강 상태
#         system_health = self.monitor.get_system_health()
#         report['system_performance'] = system_health
        
#         # 알림 요약
#         recent_alerts = [
#             alert for alert in self.monitor.alerts
#             if alert.timestamp.date() == target_date
#         ]
#         report['alerts_summary'] = {
#             'total_alerts': len(recent_alerts),
#             'critical_alerts': len([a for a in recent_alerts if a.severity == 'critical']),
#             'warning_alerts': len([a for a in recent_alerts if a.severity == 'warning']),
#             'alerts_by_type': self._group_alerts_by_type(recent_alerts)
#         }
        
#         # 권장사항 생성
#         report['recommendations'] = self._generate_recommendations(
#             metrics_summary, agents_performance, system_health, recent_alerts
#         )
        
#         return report
    
#     def _group_alerts_by_type(self, alerts: List[PerformanceAlert]) -> Dict[str, int]:
#         """알림을 타입별로 그룹화"""
#         groups = defaultdict(int)
#         for alert in alerts:
#             groups[alert.metric_name] += 1
#         return dict(groups)
    
#     def _generate_recommendations(self, 
#                                  metrics_summary: Dict[str, Any],
#                                  agents_performance: Dict[str, Dict[str, Any]],
#                                  system_health: Dict[str, Any],
#                                  alerts: List[PerformanceAlert]) -> List[str]:
#         """권장사항 생성"""
#         recommendations = []
        
#         # 시스템 리소스 기반 권장사항
#         if system_health.get('system_metrics'):
#             cpu_usage = system_health['system_metrics'].get('cpu_percent', 0)
#             memory_usage = system_health['system_metrics'].get('memory_percent', 0)
            
#             if cpu_usage > 80:
#                 recommendations.append("CPU 사용률이 높습니다. 워크로드 분산을 고려하세요.")
            
#             if memory_usage > 80:
#                 recommendations.append("메모리 사용률이 높습니다. 메모리 정리 작업을 실행하세요.")
        
#         # 에이전트 성능 기반 권장사항
#         unhealthy_agents = [
#             agent_id for agent_id, perf in agents_performance.items()
#             if perf and perf.get('health_status') != 'healthy'
#         ]
        
#         if unhealthy_agents:
#             recommendations.append(
#                 f"다음 에이전트들의 성능을 점검하세요: {', '.join(unhealthy_agents[:5])}"
#             )
        
#         # 응답 시간 기반 권장사항
#         slow_operations = []
#         for metric_key, metric_data in metrics_summary.get('metrics', {}).items():
#             if 'response_time' in metric_key and metric_data.get('avg', 0) > 3.0:
#                 slow_operations.append(metric_key)
        
#         if slow_operations:
#             recommendations.append(
#                 "응답 시간이 느린 작업들을 최적화하세요: " + 
#                 ', '.join(slow_operations[:3])
#             )
        
#         # 알림 기반 권장사항
#         critical_alerts = [a for a in alerts if a.severity == 'critical']
#         if len(critical_alerts) > 5:
#             recommendations.append("중요 알림이 많이 발생했습니다. 시스템 점검이 필요합니다.")
        
#         return recommendations

# if __name__ == "__main__":
#     # 테스트 코드
#     async def test_performance_monitor():
#         monitor = PerformanceMonitor()
#         await monitor.start_monitoring()
        
#         # 테스트 메트릭 기록
#         await monitor.record_response_time(
#             agent_id="test_agent",
#             operation="test_operation",
#             response_time=1.5
#         )
        
#         await monitor.record_memory_usage(
#             agent_id="test_agent",
#             memory_type=MemoryType.WORKING,
#             memory_count=10,
#             memory_size_mb=50.0
#         )
        
#         # 성능 요약 조회
#         summary = monitor.get_metrics_summary(time_range_hours=1)
#         print("Performance Summary:", json.dumps(summary, indent=2, default=str))
        
#         # 시스템 건강 상태 조회
#         health = monitor.get_system_health()
#         print("System Health:", json.dumps(health, indent=2, default=str))
        
#         monitor.stop_monitoring()
    
#     # 테스트 실행
#     asyncio.run(test_performance_monitor())# backend/evaluation/performance_monitor.py

# import asyncio
# import time
# import psutil
# import threading
# from datetime import datetime, timedelta
# from typing import Dict, List, Any, Optional, Callable
# from dataclasses import dataclass, asdict
# from collections import defaultdict, deque
# import json
# import logging
# from enum import Enum

# from models.memory import MemoryType
# from utils.logger import get_logger

# logger = get_logger(__name__)

# class MetricType(Enum):
#     RESPONSE_TIME = "response_time"
#     MEMORY_USAGE = "memory_usage"
#     THROUGHPUT = "throughput"
#     ERROR_RATE = "error_rate"
#     SYSTEM_RESOURCE = "system_resource"
#     CUSTOM = "custom"

# @dataclass
# class PerformanceMetric:
#     """성능 메트릭 데이터 클래스"""
#     timestamp: datetime
#     metric_type: MetricType
#     metric_name: str
#     value: float
#     unit: str
#     agent_id: Optional[str] = None
#     context: Optional[Dict[str, Any]] = None
#     tags: Optional[List[str]] = None

# @dataclass
# class SystemMetrics:
#     """시스템 메트릭 스냅샷"""
#     timestamp: datetime
#     cpu_percent: float
#     memory_percent: float
#     memory_used_mb: float
#     memory_available_mb: float
#     disk_usage_percent: float
#     network_io_bytes_sent: int
#     network_io_bytes_recv: int
#     active_threads: int

# @dataclass
# class AgentPerformanceSnapshot: