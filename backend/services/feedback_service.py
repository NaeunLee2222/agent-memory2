# import asyncio
# import time
# import json
# from typing import Dict, Any, List
# from collections import defaultdict
# from datetime import datetime, timedelta
# from .memory_service import EnhancedMemoryService
# from ..models.schemas import (
#     FeedbackRequest, FeedbackResponse, PerformanceFeedback, UserFeedback,
#     MCPToolType, WorkflowPattern
# )

# class EnhancedFeedbackService:
#     def __init__(self, memory_service: EnhancedMemoryService):
#         self.memory_service = memory_service
#         self.user_preferences = defaultdict(dict)
#         self.performance_feedback = []
#         self.optimization_history = defaultdict(list)
        
#     async def process_immediate_feedback(self, feedback: FeedbackRequest) -> FeedbackResponse:
#         """5초 이내 즉시 피드백 처리"""
#         start_time = time.time()
        
#         optimizations = []
        
#         try:
#             # 사용자 피드백 저장
#             user_feedback = UserFeedback(
#                 feedback_id=f"fb_{int(time.time() * 1000)}",
#                 user_id=feedback.user_id,
#                 session_id=feedback.session_id,
#                 feedback_type=feedback.feedback_type,
#                 content=feedback.content,
#                 rating=feedback.rating,
#                 timestamp=datetime.now()
#             )
            
#             # 피드백 유형별 즉시 적용
#             if feedback.feedback_type == "style_preference":
#                 # 메시지 스타일 선호도 업데이트
#                 style = self._extract_style_preference(feedback.content)
#                 self.user_preferences[feedback.user_id]["message_style"] = style
#                 optimizations.append(f"메시지 스타일을 {style}로 변경")
                
#                 # Working Memory에 즉시 적용
#                 await self.memory_service.store_working_memory(
#                     session_id=feedback.session_id,
#                     key="style_preference",
#                     value=style,
#                     ttl=1800
#                 )
                
#             elif feedback.feedback_type == "tool_performance":
#                 # 도구 성능 피드백 처리
#                 tool_optimization = self._process_tool_feedback(feedback.content)
#                 if tool_optimization:
#                     optimizations.extend(tool_optimization)
                    
#             elif feedback.feedback_type == "workflow_efficiency":
#                 # 워크플로우 효율성 피드백
#                 workflow_improvements = await self._optimize_workflow_from_feedback(
#                     feedback.user_id, 
#                     feedback.session_id, 
#                     feedback.content
#                 )
#                 optimizations.extend(workflow_improvements)
                
#             elif feedback.feedback_type == "response_quality":
#                 # 응답 품질 개선
#                 quality_improvements = self._improve_response_quality(
#                     feedback.content, 
#                     feedback.rating or 3.0
#                 )
#                 optimizations.extend(quality_improvements)
            
#             # 크로스 에이전트 학습을 위한 선호도 공유
#             await self._share_user_preferences(feedback.user_id)
            
#             # 장기 메모리에 피드백 저장
#             await self._store_feedback_in_memory(user_feedback)
            
#             processing_time = time.time() - start_time
            
#             # 예상 개선 효과 계산
#             expected_improvements = self._calculate_expected_improvements(optimizations)
            
#             return FeedbackResponse(
#                 applied=True,
#                 processing_time=processing_time,
#                 optimizations=optimizations,
#                 expected_improvements=expected_improvements
#             )
            
#         except Exception as e:
#             processing_time = time.time() - start_time
#             return FeedbackResponse(
#                 applied=False,
#                 processing_time=processing_time,
#                 optimizations=[f"오류 발생: {str(e)}"],
#                 expected_improvements={}
#             )
    
#     async def process_performance_feedback(self, tool_type: MCPToolType, execution_time: float, success: bool, error_type: str = None):
#         """도구 성능 피드백 처리"""
#         feedback = PerformanceFeedback(
#             feedback_id=f"perf_{int(time.time() * 1000)}",
#             tool_type=tool_type,
#             execution_time=execution_time,
#             success=success,
#             error_type=error_type,
#             timestamp=datetime.now()
#         )
        
#         self.performance_feedback.append(feedback)
        
#         # 성능 최적화 로직
#         optimizations = []
        
#         # 실행 시간이 임계값을 초과하는 경우
#         if execution_time > 3.0:  # 3초 이상
#             optimization = await self._optimize_slow_tool(tool_type, execution_time)
#             if optimization:
#                 optimizations.extend(optimization)
#                 feedback.optimization_applied = optimization
        
#         # 실패율이 높은 경우
#         recent_failures = [f for f in self.performance_feedback[-20:] 
#                           if f.tool_type == tool_type and not f.success]
        
#         if len(recent_failures) >= 5:  # 최근 20회 중 5회 이상 실패
#             reliability_optimization = await self._improve_tool_reliability(tool_type)
#             optimizations.extend(reliability_optimization)
#             feedback.optimization_applied.extend(reliability_optimization)
        
#         return optimizations
    
#     def _extract_style_preference(self, feedback_content: str) -> str:
#         """피드백에서 스타일 선호도 추출"""
#         content_lower = feedback_content.lower()
        
#         if any(word in content_lower for word in ["친근", "캐주얼", "편한"]):
#             return "casual"
#         elif any(word in content_lower for word in ["공식", "정중", "비즈니스"]):
#             return "professional"
#         elif any(word in content_lower for word in ["기술적", "자세한", "전문적"]):
#             return "technical"
#         elif any(word in content_lower for word in ["간단", "짧게", "요약"]):
#             return "concise"
#         else:
#             return "balanced"
    
#     def _process_tool_feedback(self, feedback_content: str) -> List[str]:
#         """도구 성능 피드백 처리"""
#         optimizations = []
#         content_lower = feedback_content.lower()
        
#         if any(word in content_lower for word in ["느려", "오래", "지연"]):
#             optimizations.append("도구 실행 속도 최적화 적용")
#             optimizations.append("캐싱 메커니즘 강화")
            
#         elif any(word in content_lower for word in ["실패", "오류", "에러"]):
#             optimizations.append("도구 안정성 개선")
#             optimizations.append("예외 처리 강화")
            
#         elif any(word in content_lower for word in ["부정확", "틀린", "잘못"]):
#             optimizations.append("도구 정확도 개선")
#             optimizations.append("검증 로직 추가")
        
#         return optimizations
    
#     async def _optimize_workflow_from_feedback(self, user_id: str, session_id: str, feedback_content: str) -> List[str]:
#         """워크플로우 피드백 기반 최적화"""
#         optimizations = []
        
#         # 현재 세션의 워크플로우 정보 조회
#         workflow_data, _ = await self.memory_service.get_working_memory(session_id, "current_workflow")
        
#         if workflow_data:
#             content_lower = feedback_content.lower()
            
#             if any(word in content_lower for word in ["단계", "복잡", "간소화"]):
#                 optimizations.append("워크플로우 단계 최적화")
#                 # 불필요한 단계 제거 로직
                
#             elif any(word in content_lower for word in ["순서", "흐름", "로직"]):
#                 optimizations.append("실행 순서 재배치")
#                 # 병렬 처리 가능한 단계 식별
                
#             elif any(word in content_lower for word in ["도구", "선택", "대체"]):
#                 optimizations.append("최적 도구 조합 재선택")
#                 # 성능이 더 좋은 도구로 대체
        
#         return optimizations
    
#     def _improve_response_quality(self, feedback_content: str, rating: float) -> List[str]:
#         """응답 품질 개선"""
#         optimizations = []
        
#         if rating < 3.0:
#             content_lower = feedback_content.lower()
            
#             if any(word in content_lower for word in ["길어", "장황", "너무"]):
#                 optimizations.append("응답 길이 최적화")
                
#             elif any(word in content_lower for word in ["짧아", "부족", "더"]):
#                 optimizations.append("응답 상세도 증가")
                
#             elif any(word in content_lower for word in ["관련없", "부정확", "틀린"]):
#                 optimizations.append("응답 관련성 개선")
#                 optimizations.append("컨텍스트 이해도 향상")
        
#         return optimizations
    
#     async def _optimize_slow_tool(self, tool_type: MCPToolType, execution_time: float) -> List[str]:
#         """느린 도구 최적화"""
#         optimizations = []
        
#         if tool_type == MCPToolType.SEARCH_DB:
#             optimizations.append("데이터베이스 쿼리 최적화")
#             optimizations.append("인덱스 추가 제안")
#             optimizations.append("결과 캐싱 적용")
            
#         elif tool_type == MCPToolType.GENERATE_MSG:
#             optimizations.append("메시지 템플릿 캐싱")
#             optimizations.append("생성 알고리즘 최적화")
            
#         elif tool_type == MCPToolType.SEND_SLACK:
#             optimizations.append("배치 전송 최적화")
#             optimizations.append("API 호출 효율화")
        
#         # 최적화 이력에 기록
#         self.optimization_history[tool_type].append({
#             "timestamp": datetime.now(),
#             "execution_time": execution_time,
#             "optimizations": optimizations
#         })
        
#         return optimizations
    
#     async def _improve_tool_reliability(self, tool_type: MCPToolType) -> List[str]:
#         """도구 신뢰성 개선"""
#         optimizations = []
        
#         # 최근 실패 패턴 분석
#         recent_failures = [f for f in self.performance_feedback[-50:] 
#                           if f.tool_type == tool_type and not f.success]
        
#         error_types = [f.error_type for f in recent_failures if f.error_type]
        
#         if error_types:
#             # 가장 빈번한 오류 유형
#             most_common_error = max(set(error_types), key=error_types.count)
            
#             if "timeout" in most_common_error.lower():
#                 optimizations.append("타임아웃 설정 최적화")
#                 optimizations.append("재시도 로직 개선")
                
#             elif "connection" in most_common_error.lower():
#                 optimizations.append("연결 풀 최적화")
#                 optimizations.append("연결 안정성 개선")
                
#             elif "rate limit" in most_common_error.lower():
#                 optimizations.append("속도 제한 대응")
#                 optimizations.append("요청 간격 조정")
        
#         return optimizations
    
#     async def _share_user_preferences(self, user_id: str):
#         """사용자 선호도 크로스 에이전트 공유"""
#         if user_id in self.user_preferences:
#             preferences = self.user_preferences[user_id]
            
#             # 메모리에 선호도 저장하여 다른 세션에서 활용 가능하게 함
#             await self.memory_service.store_working_memory(
#                 session_id=f"preferences_{user_id}",
#                 key="shared_preferences",
#                 value=preferences,
#                 ttl=86400  # 24시간
#             )
            
#             # 장기 메모리에도 저장
#             preference_text = f"사용자 {user_id} 선호도: " + ", ".join([
#                 f"{k}: {v}" for k, v in preferences.items()
#             ])
            
#             self.memory_service.mem0.add(
#                 preference_text,
#                 user_id=user_id,
#                 metadata={"type": "preference", "shared": True}
#             )
    
#     async def _store_feedback_in_memory(self, feedback: UserFeedback):
#         """피드백을 장기 메모리에 저장"""
#         feedback_text = (
#             f"사용자 피드백: {feedback.feedback_type} - {feedback.content} "
#             f"(평점: {feedback.rating})"
#         )
        
#         self.memory_service.mem0.add(
#             feedback_text,
#             user_id=feedback.user_id,
#             metadata={
#                 "type": "feedback",
#                 "feedback_type": feedback.feedback_type,
#                 "rating": feedback.rating,
#                 "timestamp": feedback.timestamp.isoformat()
#             }
#         )
    
#     def _calculate_expected_improvements(self, optimizations: List[str]) -> Dict[str, float]:
#         """최적화로 인한 예상 개선 효과 계산"""
#         improvements = {}
        
#         for optimization in optimizations:
#             if "속도" in optimization or "캐싱" in optimization:
#                 improvements["response_time_improvement"] = improvements.get("response_time_improvement", 0) + 0.25
                
#             elif "안정성" in optimization or "신뢰성" in optimization:
#                 improvements["reliability_improvement"] = improvements.get("reliability_improvement", 0) + 0.15
                
#             elif "정확도" in optimization or "품질" in optimization:
#                 improvements["accuracy_improvement"] = improvements.get("accuracy_improvement", 0) + 0.20
                
#             elif "만족도" in optimization or "사용자" in optimization:
#                 improvements["user_satisfaction_improvement"] = improvements.get("user_satisfaction_improvement", 0) + 0.30
        
#         return improvements
    
#     async def get_optimization_history(self, tool_type: MCPToolType = None) -> Dict[str, Any]:
#         """최적화 이력 조회"""
#         if tool_type:
#             return {
#                 str(tool_type): self.optimization_history.get(tool_type, [])
#             }
#         return {str(k): v for k, v in self.optimization_history.items()}
    
#     async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
#         """사용자 선호도 조회"""
#         # 메모리에서도 조회 (크로스 에이전트 학습용)
#         preferences, _ = await self.memory_service.get_working_memory(f"preferences_{user_id}", "shared_preferences")
        
#         # 현재 세션 선호도와 병합
#         current_preferences = self.user_preferences.get(user_id, {})
        
#         return {**preferences.get("shared_preferences", {}), **current_preferences}import asyncio
# import time
# import json
# from typing import Dict, Any, List
# from collections import defaultdict
# from datetime import datetime, timedelta
# from .memory_service import EnhancedMemoryService
# from ..models.schemas import (
#     FeedbackRequest, FeedbackResponse, PerformanceFeedback, UserFeedback,
#     MCPToolType, WorkflowPattern
# )

# class EnhancedFeedbackService:
#     def __init__(self, memory_service: EnhancedMemoryService):
#         self.memory_service = memory_service
#         self.user_preferences = defaultdict(dict)
#         self.performance_feedback = []
#         self.optimization_history = defaultdict(list)
        
#     async def process_immediate_feedback(self, feedback: FeedbackRequest) -> FeedbackResponse:
#         """5초 이내 즉시 피드백 처리"""
#         start_time = time.time()
        
#         optimizations = []
        
#         try:
#             # 사용자 피드백 저장
#             user_feedback = UserFeedback(
#                 feedback_id=f"fb_{int(time.time() * 1000)}",
#                 user_id=feedback.user_id,
#                 session_id=feedback.session_id,
#                 feedback_type=feedback.feedback_type,
#                 content=feedback.content,
#                 rating=feedback.rating,
#                 timestamp=datetime.now()
#             )
            
#             # 피드백 유형별 즉시 적용
#             if feedback.feedback_type == "style_preference":
#                 # 메시지 스타일 선호도 업데이트
#                 style = self._extract_style_preference(feedback.content)
#                 self.user_preferences[feedback.user_id]["message_style"] = style
#                 optimizations.append(f"메시지 스타일을 {style}로 변경")
                
#                 # Working Memory에 즉시 적용
#                 await self.memory_service.store_working_memory(
#                     session_id=feedback.session_id,
#                     key="style_preference",
#                     value=style,
#                     ttl=1800
#                 )
                
#             elif feedback.feedback_type == "tool_performance":
#                 # 도구 성능 피드백 처리
#                 tool_optimization = self._process_tool_feedback(feedback.content)
#                 if tool_optimization:
#                     optimizations.extend(tool_optimization)
                    
#             elif feedback.feedback_type == "workflow_efficiency":
#                 # 워크플로우 효율성 피드백
#                 workflow_improvements = await self._optimize_workflow_from_feedback(
#                     feedback.user_id, 
#                     feedback.session_id, 
#                     feedback.content
#                 )
#                 optimizations.extend(workflow_improvements)
                
#             elif feedback.feedback_type == "response_quality":
#                 # 응답 품질 개선
#                 quality_improvements = self._improve_response_quality(
#                     feedback.content, 
#                     feedback.rating or 3.0
#                 )
#                 optimizations.extend(quality_improvements)
            
#             # 크로스 에이전트 학습을 위한 선호도 공유
#             await self._share_user_preferences(feedback.user_id)
            
#             # 장기 메모리에 피드백 저장
#             await self._store_feedback_in_memory(user_feedback)
            
#             processing_time = time.time() - start_time
            
#             # 예상 개선 효과 계산
#             expected_improvements = self._calculate_expected_improvements(optimizations)
            
#             return FeedbackResponse(
#                 applied=True,
#                 processing_time=processing_time,
#                 optimizations=optimizations,
#                 expected_improvements=expected_improvements
#             )
            
#         except Exception as e:
#             processing_time = time.time() - start_time
#             return FeedbackResponse(
#                 applied=False,
#                 processing_time=processing_time,
#                 optimizations=[f"오류 발생: {str(e)}"],
#                 expected_improvements={}
#             )
    
#     async def process_performance_feedback(self, tool_type: MCPToolType, execution_time: float, success: bool, error_type: str = None):
#         """도구 성능 피드백 처리"""
#         feedback = PerformanceFeedback(
#             feedback_id=f"perf_{int(time.time() * 1000)}",
#             tool_type=tool_type,
#             execution_time=execution_time,
#             success=success,
#             error_type=error_type,
#             timestamp=datetime.now()
#         )
        
#         self.performance_feedback.append(feedback)
        
#         # 성능 최적화 로직
#         optimizations = []
        
#         # 실행 시간이 임계값을 초과하는 경우
#         if execution_time > 3.0:  # 3초 이상
#             optimization = await self._optimize_slow_tool(tool_type, execution_time)
#             if optimization:
#                 optimizations.extend(optimization)
#                 feedback.optimization_applied = optimization
        
#         # 실패율이 높은 경우
#         recent_failures = [f for f in self.performance_feedback[-20:] 
#                           if f.tool_type == tool_type and not f.success]
        
#         if len(recent_failures) >= 5:  # 최근 20회 중 5회 이상 실패
#             reliability_optimization = await self._improve_tool_reliability(tool_type)
#             optimizations.extend(reliability_optimization)
#             feedback.optimization_applied.extend(reliability_optimization)
        
#         return optimizations
    
#     def _extract_style_preference(self, feedback_content: str) -> str:
#         """피드백에서 스타일 선호도 추출"""
#         content_lower = feedback_content.lower()
        
#         if any(word in content_lower for word in ["친근", "캐주얼", "편한"]):
#             return "casual"
#         elif any(word in content_lower for word in ["공식", "정중", "비즈니스"]):
#             return "professional"
#         elif any(word in content_lower for word in ["기술적", "자세한", "전문적"]):
#             return "technical"
#         elif any(word in content_lower for word in ["간단", "짧게", "요약"]):
#             return "concise"
#         else:
#             return "balanced"
    
#     def _process_tool_feedback(self, feedback_content: str) -> List[str]:
#         """도구 성능 피드백 처리"""
#         optimizations = []
#         content_lower = feedback_content.lower()
        
#         if any(word in content_lower for word in ["느려", "오래", "지연"]):
#             optimizations.append("도구 실행 속도 최적화 적용")
#             optimizations.append("캐싱 메커니즘 강화")
            
#         elif any(word in content_lower for word in ["실패", "오류", "에러"]):
#             optimizations.append("도구 안정성 개선")
#             optimizations.append("예외 처리 강화")
            
#         elif any(word in content_lower for word in ["부정확", "틀린", "잘못"]):
#             optimizations.append("도구 정확도 개선")
#             optimizations.append("검증 로직 추가")
        
#         return optimizations
    
#     async def _optimize_workflow_from_feedback(self, user_id: str, session_id: str, feedback_content: str) -> List[str]:
#         """워크플로우 피드백 기반 최적화"""
#         optimizations = []
        
#         # 현재 세션의 워크플로우 정보 조회
#         workflow_data, _ = await self.memory_service.get_working_memory(session_id, "current_workflow")
        
#         if workflow_data:
#             content_lower = feedback_content.lower()
            
#             if any(word in content_lower for word in ["단계", "복잡", "간소화"]):
#                 optimizations.append("워크플로우 단계 최적화")
#                 # 불필요한 단계 제거 로직
                
#             elif any(word in content_lower for word in ["순서", "흐름", "로직"]):
#                 optimizations.append("실행 순서 재배치")
#                 # 병렬 처리 가능한 단계 식별
                
#             elif any(word in content_lower for word in ["도구", "선택", "대체"]):
#                 optimizations.append("최적 도구 조합 재선택")
#                 # 성능이 더 좋은 도구로 대체
        
#         return optimizations
    
#     def _improve_response_quality(self, feedback_content: str, rating: float) -> List[str]:
#         """응답 품질 개선"""
#         optimizations = []
        
#         if rating < 3.0:
#             content_lower = feedback_content.lower()
            
#             if any(word in content_lower for word in ["길어", "장황", "너무"]):
#                 optimizations.append("응답 길이 최적화")
                
#             elif any(word in content_lower for word in ["짧아", "부족", "더"]):
#                 optimizations.append("응답 상세도 증가")
                
#             elif any(word in content_lower for word in ["관련없", "부정확", "틀린"]):
#                 optimizations.append("응답 관련성 개선")
#                 optimizations.append("컨텍스트 이해도 향상")
        
#         return optimizations
    
#     async def _optimize_slow_tool(self, tool_type: MCPToolType, execution_time: float) -> List[str]:
#         """느린 도구 최적화"""
#         optimizations = []
        
#         if tool_type == MCPToolType.SEARCH_DB:
#             optimizations.append("데이터베이스 쿼리 최적화")
#             optimizations.append("인덱스 추가 제안")
#             optimizations.append("결과 캐싱 적용")
            
#         elif tool_type == MCPToolType.GENERATE_MSG:
#             optimizations.append("메시지 템플릿 캐싱")
#             optimizations.append("생성 알고리즘 최적화")
            
#         elif tool_type == MCPToolType.SEND_SLACK:
#             optimizations.append("배치 전송 최적화")
#             optimizations.append("API 호출 효율화")
        
#         # 최적화 이력에 기록
#         self.optimization_history[tool_type].append({
#             "timestamp": datetime.now(),
#             "execution_time": execution_time,
#             "optimizations": optimizations
#         })
        
#         return optimizations
    
#     async def _improve_tool_reliability(self, tool_type: MCPToolType) -> List[str]:
#         """도구 신뢰성 개선"""
#         optimizations = []
        
#         # 최근 실패 패턴 분석
#         recent_failures = [f for f in self.performance_feedback[-50:] 
#                           if f.tool_type == tool_type and not f.success]
        
#         error_types = [f.error_type for f in recent_failures if f.error_type]
        
#         if error_types:
#             # 가장 빈번한 오류 유형
#             most_common_error = max(set(error_types), key=error_types.count)
            
#             if "timeout" in most_common_error.lower():
#                 optimizations.append("타임아웃 설정 최적화")
#                 optimizations.append("재시도 로직 개선")
                
#             elif "connection" in most_common_error.lower():
#                 optimizations.append("연결 풀 최적화")
#                 optimizations.append("연결 안정성 개선")
                
#             elif "rate limit" in most_common_error.lower():
#                 optimizations.append("속도 제한 대응")
#                 optimizations.append("요청 간격 조정")
        
#         return optimizations
    
#     async def _share_user_preferences(self, user_id: str):
#         """사용자 선호도 크로스 에이전트 공유"""
#         if user_id in self.user_preferences:
#             preferences = self.user_preferences[user_id]
            
#             # 메모리에 선호도 저장하여 다른 세션에서 활용 가능하게 함
#             await self.memory_service.store_working_memory(
#                 session_id=f"preferences_{user_id}",
#                 key="shared_preferences",
#                 value=preferences,
#                 ttl=86400  # 24시간
#             )
            
#             # 장기 메모리에도 저장
#             preference_text = f"사용자 {user_id} 선호도: " + ", ".join([
#                 f"{k}: {v}" for k, v in preferences.items()
#             ])
            
#             self.memory_service.mem0.add(
#                 preference_text,
#                 user_id=user_id,
#                 metadata={"type": "preference", "shared": True}
#             )
    
#     async def _store_feedback_in_memory(self, feedback: UserFeedback):
#         """피드백을 장기 메모리에 저장"""
#         feedback_text = (
#             f"사용자 피드백: {feedback.feedback_type} - {feedback.content} "
#             f"(평점: {feedback.rating})"
#         )
        
#         self.memory_service.mem0.add(
#             feedback_text,
#             user_id=feedback.user_id,
#             metadata={
#                 "type": "feedback",
#                 "feedback_type": feedback.feedback_type,
#                 "rating": feedback.rating,
#                 "timestamp": feedback.timestamp.isoformat()
#             }
#         )
    
#     def _calculate_expected_improvements(self, optimizations: List[str]) -> Dict[str, float]:
#         """최적화로 인한 예상 개선 효과 계산"""
#         improvements = {}
        
#         for optimization in optimizations:
#             if "속도" in optimization or "캐싱" in optimization:
#                 improvements["response_time_improvement"] = improvements.get("response_time_improvement", 0) + 0.25
                
#             elif "안정성" in optimization or "신뢰성" in optimization:
#                 improvements["reliability_improvement"] = improvements.get("reliability_improvement", 0) + 0.15
                
#             elif "정확도" in optimization or "품질" in optimization:
#                 improvements["accuracy_improvement"] = improvements.get("accuracy_improvement", 0) + 0.20
                
#             elif "만족도" in optimization or "사용자" in optimization:
#                 improvements["user_satisfaction_improvement"] = improvements.get("user_satisfaction_improvement", 0) + 0.30
        
#         return improvements
    
#     async def get_optimization_history(self, tool_type: MCPToolType = None) -> Dict[str, Any]:
#         """최적화 이력 조회"""
#         if tool_type:
#             return {
#                 str(tool_type): self.optimization_history.get(tool_type, [])
#             }
#         return {str(k): v for k, v in self.optimization_history.items()}
    
#     async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
#         """사용자 선호도 조회"""
#         # 메모리에서도 조회 (크로스 에이전트 학습용)
#         preferences, _ = await self.memory_service.get_working_memory(f"preferences_{user_id}", "shared_preferences")
        
#         # 현재 세션 선호도와 병합
#         current_preferences = self.user_preferences.get(user_id, {})
        
#         return {**preferences.get("shared_preferences", {}), **current_preferences}

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from ..models.database import Feedback, FeedbackAnalysis, Agent, AgentExecution
from ..models.memory import MemoryService
from ..core.config import settings
from ..utils.validators import validate_feedback_data
from ..utils.exceptions import FeedbackProcessingError

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    EXPLICIT_POSITIVE = "explicit_positive"
    EXPLICIT_NEGATIVE = "explicit_negative"
    IMPLICIT_SUCCESS = "implicit_success"
    IMPLICIT_FAILURE = "implicit_failure"
    PERFORMANCE_METRIC = "performance_metric"

class FeedbackPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class FeedbackData:
    execution_id: str
    feedback_type: FeedbackType
    content: Dict[str, Any]
    source: str
    priority: FeedbackPriority
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

class FeedbackCollector:
    """피드백 수집을 담당하는 클래스"""
    
    def __init__(self, db_session: AsyncSession, memory_service: MemoryService):
        self.db_session = db_session
        self.memory_service = memory_service
        
    async def collect_explicit_feedback(
        self, 
        execution_id: str, 
        rating: int, 
        comment: str,
        user_id: str
    ) -> str:
        """사용자의 명시적 피드백 수집"""
        try:
            feedback_type = (
                FeedbackType.EXPLICIT_POSITIVE if rating >= 3 
                else FeedbackType.EXPLICIT_NEGATIVE
            )
            
            feedback_data = FeedbackData(
                execution_id=execution_id,
                feedback_type=feedback_type,
                content={
                    "rating": rating,
                    "comment": comment,
                    "user_id": user_id
                },
                source="user_input",
                priority=FeedbackPriority.HIGH,
                metadata={"collection_method": "explicit_form"}
            )
            
            return await self._store_feedback(feedback_data)
            
        except Exception as e:
            logger.error(f"명시적 피드백 수집 실패: {e}")
            raise FeedbackProcessingError(f"피드백 수집 실패: {str(e)}")
    
    async def collect_implicit_feedback(
        self, 
        execution_id: str, 
        performance_metrics: Dict[str, Any]
    ) -> str:
        """시스템 성능 지표 기반 암시적 피드백 수집"""
        try:
            # 성공/실패 판단 로직
            success_indicators = [
                performance_metrics.get("execution_time", float('inf')) < 30.0,
                performance_metrics.get("error_count", 1) == 0,
                performance_metrics.get("completion_rate", 0) > 0.8
            ]
            
            is_success = sum(success_indicators) >= 2
            feedback_type = (
                FeedbackType.IMPLICIT_SUCCESS if is_success 
                else FeedbackType.IMPLICIT_FAILURE
            )
            
            feedback_data = FeedbackData(
                execution_id=execution_id,
                feedback_type=feedback_type,
                content=performance_metrics,
                source="system_metrics",
                priority=FeedbackPriority.MEDIUM,
                metadata={"auto_generated": True}
            )
            
            return await self._store_feedback(feedback_data)
            
        except Exception as e:
            logger.error(f"암시적 피드백 수집 실패: {e}")
            raise FeedbackProcessingError(f"성능 피드백 수집 실패: {str(e)}")
    
    async def collect_performance_feedback(
        self, 
        execution_id: str, 
        metrics: Dict[str, float]
    ) -> str:
        """성능 지표 피드백 수집"""
        try:
            feedback_data = FeedbackData(
                execution_id=execution_id,
                feedback_type=FeedbackType.PERFORMANCE_METRIC,
                content=metrics,
                source="performance_monitor",
                priority=FeedbackPriority.MEDIUM,
                metadata={"metric_type": "performance"}
            )
            
            return await self._store_feedback(feedback_data)
            
        except Exception as e:
            logger.error(f"성능 피드백 수집 실패: {e}")
            raise FeedbackProcessingError(f"성능 피드백 수집 실패: {str(e)}")
    
    async def _store_feedback(self, feedback_data: FeedbackData) -> str:
        """피드백 데이터베이스 저장"""
        feedback = Feedback(
            id=str(uuid.uuid4()),
            execution_id=feedback_data.execution_id,
            feedback_type=feedback_data.feedback_type.value,
            content=feedback_data.content,
            source=feedback_data.source,
            priority=feedback_data.priority.value,
            metadata=feedback_data.metadata or {},
            created_at=datetime.utcnow()
        )
        
        self.db_session.add(feedback)
        await self.db_session.commit()
        
        logger.info(f"피드백 저장 완료: {feedback.id}")
        return feedback.id

class FeedbackAnalyzer:
    """피드백 분석을 담당하는 클래스"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        
    async def analyze_feedback_batch(self, limit: int = 100) -> List[Dict[str, Any]]:
        """배치 피드백 분석"""
        try:
            # 미분석 피드백 조회
            query = (
                select(Feedback)
                .where(Feedback.analyzed_at.is_(None))
                .order_by(desc(Feedback.priority), Feedback.created_at)
                .limit(limit)
            )
            
            result = await self.db_session.execute(query)
            feedbacks = result.scalars().all()
            
            analyses = []
            for feedback in feedbacks:
                analysis = await self._analyze_single_feedback(feedback)
                analyses.append(analysis)
                
                # 분석 완료 표시
                feedback.analyzed_at = datetime.utcnow()
            
            await self.db_session.commit()
            return analyses
            
        except Exception as e:
            logger.error(f"배치 피드백 분석 실패: {e}")
            raise FeedbackProcessingError(f"피드백 분석 실패: {str(e)}")
    
    async def _analyze_single_feedback(self, feedback: Feedback) -> Dict[str, Any]:
        """개별 피드백 분석"""
        try:
            analysis_result = {
                "feedback_id": feedback.id,
                "sentiment_score": 0.0,
                "confidence_level": 0.0,
                "key_insights": [],
                "recommended_actions": [],
                "impact_assessment": {}
            }
            
            # 피드백 타입별 분석
            if feedback.feedback_type in ["explicit_positive", "explicit_negative"]:
                analysis_result.update(await self._analyze_explicit_feedback(feedback))
            elif feedback.feedback_type in ["implicit_success", "implicit_failure"]:
                analysis_result.update(await self._analyze_implicit_feedback(feedback))
            elif feedback.feedback_type == "performance_metric":
                analysis_result.update(await self._analyze_performance_feedback(feedback))
            
            # 분석 결과 저장
            await self._store_analysis(feedback.id, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"개별 피드백 분석 실패: {e}")
            return {"error": str(e)}
    
    async def _analyze_explicit_feedback(self, feedback: Feedback) -> Dict[str, Any]:
        """명시적 피드백 분석"""
        content = feedback.content
        rating = content.get("rating", 0)
        comment = content.get("comment", "")
        
        # 간단한 감정 분석 (실제로는 더 정교한 NLP 모델 사용)
        sentiment_score = (rating - 2.5) / 2.5  # -1 to 1 범위로 정규화
        
        insights = []
        if rating >= 4:
            insights.append("사용자 만족도 높음")
        elif rating <= 2:
            insights.append("사용자 불만족 - 개선 필요")
        
        if comment:
            if len(comment) > 50:
                insights.append("상세한 피드백 제공됨")
        
        return {
            "sentiment_score": sentiment_score,
            "confidence_level": 0.8,
            "key_insights": insights,
            "recommended_actions": self._generate_action_recommendations(rating, comment)
        }
    
    async def _analyze_implicit_feedback(self, feedback: Feedback) -> Dict[str, Any]:
        """암시적 피드백 분석"""
        content = feedback.content
        
        # 성능 지표 기반 점수 계산
        execution_time = content.get("execution_time", float('inf'))
        error_count = content.get("error_count", 1)
        completion_rate = content.get("completion_rate", 0)
        
        performance_score = min(1.0, (30.0 - execution_time) / 30.0)  # 실행 시간 점수
        error_score = 1.0 if error_count == 0 else 0.0  # 오류 점수
        completion_score = completion_rate  # 완료율 점수
        
        overall_score = (performance_score + error_score + completion_score) / 3
        
        return {
            "sentiment_score": overall_score * 2 - 1,  # -1 to 1 범위
            "confidence_level": 0.6,
            "key_insights": [f"전체 성능 점수: {overall_score:.2f}"],
            "recommended_actions": self._generate_performance_recommendations(content)
        }
    
    async def _analyze_performance_feedback(self, feedback: Feedback) -> Dict[str, Any]:
        """성능 피드백 분석"""
        metrics = feedback.content
        
        # 성능 임계값 기반 분석
        analysis = {
            "cpu_usage": metrics.get("cpu_usage", 0),
            "memory_usage": metrics.get("memory_usage", 0),
            "response_time": metrics.get("response_time", 0),
        }
        
        # 성능 등급 계산
        performance_grade = "A"
        if analysis["cpu_usage"] > 80 or analysis["memory_usage"] > 80:
            performance_grade = "C"
        elif analysis["response_time"] > 5.0:
            performance_grade = "B"
        
        return {
            "sentiment_score": 0.0,
            "confidence_level": 0.9,
            "key_insights": [f"성능 등급: {performance_grade}"],
            "recommended_actions": self._generate_performance_optimization_actions(analysis)
        }
    
    def _generate_action_recommendations(self, rating: int, comment: str) -> List[str]:
        """액션 추천 생성"""
        actions = []
        
        if rating <= 2:
            actions.append("에이전트 응답 품질 개선")
            actions.append("사용자 가이드 강화")
        elif rating >= 4:
            actions.append("현재 접근 방식 유지")
            actions.append("유사 케이스에 패턴 적용")
        
        if "느려" in comment or "slow" in comment.lower():
            actions.append("응답 속도 최적화")
        
        return actions
    
    def _generate_performance_recommendations(self, metrics: Dict) -> List[str]:
        """성능 기반 추천 생성"""
        actions = []
        
        if metrics.get("execution_time", 0) > 20:
            actions.append("실행 시간 최적화")
        
        if metrics.get("error_count", 0) > 0:
            actions.append("오류 처리 로직 개선")
        
        if metrics.get("completion_rate", 1) < 0.8:
            actions.append("작업 완료율 향상 방안 검토")
        
        return actions
    
    def _generate_performance_optimization_actions(self, analysis: Dict) -> List[str]:
        """성능 최적화 액션 생성"""
        actions = []
        
        if analysis["cpu_usage"] > 70:
            actions.append("CPU 사용량 최적화")
        
        if analysis["memory_usage"] > 70:
            actions.append("메모리 사용량 최적화")
        
        if analysis["response_time"] > 3.0:
            actions.append("응답 시간 개선")
        
        return actions
    
    async def _store_analysis(self, feedback_id: str, analysis: Dict[str, Any]):
        """분석 결과 저장"""
        analysis_record = FeedbackAnalysis(
            id=str(uuid.uuid4()),
            feedback_id=feedback_id,
            analysis_result=analysis,
            created_at=datetime.utcnow()
        )
        
        self.db_session.add(analysis_record)

class FeedbackProcessor:
    """피드백 처리 및 적용을 담당하는 클래스"""
    
    def __init__(self, db_session: AsyncSession, memory_service: MemoryService):
        self.db_session = db_session
        self.memory_service = memory_service
        
    async def process_feedback_for_improvement(self, agent_id: str) -> Dict[str, Any]:
        """에이전트 개선을 위한 피드백 처리"""
        try:
            # 최근 피드백 조회 (지난 30일)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            query = (
                select(Feedback)
                .join(AgentExecution, Feedback.execution_id == AgentExecution.id)
                .where(
                    and_(
                        AgentExecution.agent_id == agent_id,
                        Feedback.created_at >= cutoff_date,
                        Feedback.analyzed_at.is_not(None)
                    )
                )
                .options(selectinload(Feedback.analysis))
            )
            
            result = await self.db_session.execute(query)
            feedbacks = result.scalars().all()
            
            if not feedbacks:
                return {"message": "처리할 피드백이 없습니다."}
            
            # 피드백 분석 및 개선사항 도출
            improvement_plan = await self._generate_improvement_plan(feedbacks)
            
            # 메모리에 학습 내용 저장
            await self._update_agent_memory(agent_id, improvement_plan)
            
            return improvement_plan
            
        except Exception as e:
            logger.error(f"피드백 처리 실패: {e}")
            raise FeedbackProcessingError(f"피드백 처리 실패: {str(e)}")
    
    async def _generate_improvement_plan(self, feedbacks: List[Feedback]) -> Dict[str, Any]:
        """개선 계획 생성"""
        # 피드백 분류 및 집계
        positive_feedback = [f for f in feedbacks if f.feedback_type.endswith("positive") or f.feedback_type.endswith("success")]
        negative_feedback = [f for f in feedbacks if f.feedback_type.endswith("negative") or f.feedback_type.endswith("failure")]
        
        # 주요 이슈 및 성공 패턴 식별
        common_issues = await self._identify_common_issues(negative_feedback)
        success_patterns = await self._identify_success_patterns(positive_feedback)
        
        # 우선순위 기반 개선사항
        priority_improvements = await self._prioritize_improvements(common_issues, success_patterns)
        
        return {
            "total_feedbacks": len(feedbacks),
            "positive_ratio": len(positive_feedback) / len(feedbacks),
            "common_issues": common_issues,
            "success_patterns": success_patterns,
            "priority_improvements": priority_improvements,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _identify_common_issues(self, negative_feedbacks: List[Feedback]) -> List[Dict[str, Any]]:
        """공통 이슈 식별"""
        issues = {}
        
        for feedback in negative_feedbacks:
            if hasattr(feedback, 'analysis') and feedback.analysis:
                for insight in feedback.analysis[0].analysis_result.get("key_insights", []):
                    if insight in issues:
                        issues[insight]["count"] += 1
                    else:
                        issues[insight] = {"count": 1, "examples": []}
                    
                    issues[insight]["examples"].append(feedback.id)
        
        # 빈도순 정렬
        return [
            {"issue": issue, "frequency": data["count"], "impact": "high" if data["count"] > 3 else "medium"}
            for issue, data in sorted(issues.items(), key=lambda x: x[1]["count"], reverse=True)
        ]
    
    async def _identify_success_patterns(self, positive_feedbacks: List[Feedback]) -> List[Dict[str, Any]]:
        """성공 패턴 식별"""
        patterns = {}
        
        for feedback in positive_feedbacks:
            if hasattr(feedback, 'analysis') and feedback.analysis:
                for insight in feedback.analysis[0].analysis_result.get("key_insights", []):
                    if insight in patterns:
                        patterns[insight]["count"] += 1
                    else:
                        patterns[insight] = {"count": 1}
        
        return [
            {"pattern": pattern, "frequency": data["count"], "reliability": "high" if data["count"] > 3 else "medium"}
            for pattern, data in sorted(patterns.items(), key=lambda x: x[1]["count"], reverse=True)
        ]
    
    async def _prioritize_improvements(self, issues: List[Dict], patterns: List[Dict]) -> List[Dict[str, Any]]:
        """개선사항 우선순위 결정"""
        improvements = []
        
        # 고빈도 이슈 우선 처리
        for issue in issues[:3]:  # 상위 3개 이슈
            improvements.append({
                "type": "issue_resolution",
                "description": f"{issue['issue']} 해결",
                "priority": "high" if issue["frequency"] > 5 else "medium",
                "estimated_effort": "medium"
            })
        
        # 성공 패턴 강화
        for pattern in patterns[:2]:  # 상위 2개 패턴
            improvements.append({
                "type": "pattern_reinforcement",
                "description": f"{pattern['pattern']} 패턴 강화",
                "priority": "medium",
                "estimated_effort": "low"
            })
        
        return improvements
    
    async def _update_agent_memory(self, agent_id: str, improvement_plan: Dict[str, Any]):
        """에이전트 메모리에 학습 내용 업데이트"""
        # 절차 메모리 업데이트 (개선된 프로세스)
        for improvement in improvement_plan["priority_improvements"]:
            await self.memory_service.store_procedural_memory(
                agent_id=agent_id,
                process_name=f"improvement_{improvement['type']}",
                steps={
                    "description": improvement["description"],
                    "priority": improvement["priority"],
                    "learned_from": "feedback_analysis"
                },
                metadata={
                    "source": "feedback_processor",
                    "improvement_plan_id": improvement_plan.get("id"),
                    "created_at": datetime.utcnow().isoformat()
                }
            )
        
        # 시맨틱 메모리 업데이트 (학습된 지식)
        await self.memory_service.store_semantic_memory(
            agent_id=agent_id,
            concept="feedback_learnings",
            knowledge={
                "common_issues": improvement_plan["common_issues"],
                "success_patterns": improvement_plan["success_patterns"],
                "performance_metrics": {
                    "positive_feedback_ratio": improvement_plan["positive_ratio"],
                    "total_feedback_count": improvement_plan["total_feedbacks"]
                }
            },
            metadata={
                "source": "feedback_analysis",
                "analysis_date": improvement_plan["generated_at"]
            }
        )

class FeedbackService:
    """피드백 시스템 통합 서비스"""
    
    def __init__(self, db_session: AsyncSession, memory_service: MemoryService):
        self.db_session = db_session
        self.memory_service = memory_service
        self.collector = FeedbackCollector(db_session, memory_service)
        self.analyzer = FeedbackAnalyzer(db_session)
        self.processor = FeedbackProcessor(db_session, memory_service)
    
    async def submit_user_feedback(
        self, 
        execution_id: str, 
        rating: int, 
        comment: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """사용자 피드백 제출"""
        try:
            # 피드백 수집
            feedback_id = await self.collector.collect_explicit_feedback(
                execution_id, rating, comment, user_id
            )
            
            # 즉시 분석 (고우선순위 피드백의 경우)
            if rating <= 2:  # 부정적 피드백은 즉시 분석
                feedback = await self.db_session.get(Feedback, feedback_id)
                await self.analyzer._analyze_single_feedback(feedback)
                await self.db_session.commit()
            
            return {
                "feedback_id": feedback_id,
                "status": "submitted",
                "message": "피드백이 성공적으로 제출되었습니다."
            }
            
        except Exception as e:
            logger.error(f"사용자 피드백 제출 실패: {e}")
            raise FeedbackProcessingError(f"피드백 제출 실패: {str(e)}")
    
    async def process_system_feedback(
        self, 
        execution_id: str, 
        performance_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """시스템 피드백 처리"""
        try:
            # 암시적 피드백 수집
            feedback_id = await self.collector.collect_implicit_feedback(
                execution_id, performance_metrics
            )
            
            # 성능 피드백 추가 수집
            if "cpu_usage" in performance_metrics:
                perf_feedback_id = await self.collector.collect_performance_feedback(
                    execution_id, {
                        "cpu_usage": performance_metrics["cpu_usage"],
                        "memory_usage": performance_metrics.get("memory_usage", 0),
                        "response_time": performance_metrics.get("response_time", 0)
                    }
                )
            
            return {
                "feedback_ids": [feedback_id],
                "status": "processed",
                "message": "시스템 피드백이 처리되었습니다."
            }
            
        except Exception as e:
            logger.error(f"시스템 피드백 처리 실패: {e}")
            raise FeedbackProcessingError(f"시스템 피드백 처리 실패: {str(e)}")
    
    async def get_feedback_summary(self, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """피드백 요약 조회"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 기본 통계 쿼리
            query = (
                select(
                    func.count(Feedback.id).label("total_count"),
                    func.avg(
                        func.case(
                            (Feedback.feedback_type.in_(["explicit_positive", "implicit_success"]), 1),
                            else_=0
                        )
                    ).label("positive_ratio")
                )
                .select_from(Feedback)
                .join(AgentExecution, Feedback.execution_id == AgentExecution.id)
                .where(
                    and_(
                        AgentExecution.agent_id == agent_id,
                        Feedback.created_at >= cutoff_date
                    )
                )
            )
            
            result = await self.db_session.execute(query)
            stats = result.first()
            
            return {
                "period_days": days,
                "total_feedback_count": stats.total_count or 0,
                "positive_feedback_ratio": float(stats.positive_ratio or 0),
                "analysis_coverage": "100%",  # 실제로는 분석된 피드백 비율 계산
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"피드백 요약 조회 실패: {e}")
            raise FeedbackProcessingError(f"피드백 요약 조회 실패: {str(e)}")
    
    async def run_feedback_analysis_batch(self) -> Dict[str, Any]:
        """배치 피드백 분석 실행"""
        try:
            analyses = await self.analyzer.analyze_feedback_batch()
            return {
                "processed_count": len(analyses),
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"배치 분석 실행 실패: {e}")
            raise FeedbackProcessingError(f"배치 분석 실행 실패: {str(e)}")
    
    async def trigger_agent_improvement(self, agent_id: str) -> Dict[str, Any]:
        """에이전트 개선 프로세스 실행"""
        try:
            improvement_plan = await self.processor.process_feedback_for_improvement(agent_id)
            return {
                "agent_id": agent_id,
                "improvement_plan": improvement_plan,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"에이전트 개선 실행 실패: {e}")
            raise FeedbackProcessingError(f"에이전트 개선 실행 실패: {str(e)}")