import asyncio
import time
import json
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime, timedelta
from .memory_service import EnhancedMemoryService
from ..models.schemas import (
    FeedbackRequest, FeedbackResponse, PerformanceFeedback, UserFeedback,
    MCPToolType, WorkflowPattern
)

class EnhancedFeedbackService:
    def __init__(self, memory_service: EnhancedMemoryService):
        self.memory_service = memory_service
        self.user_preferences = defaultdict(dict)
        self.performance_feedback = []
        self.optimization_history = defaultdict(list)
        
    async def process_immediate_feedback(self, feedback: FeedbackRequest) -> FeedbackResponse:
        """5초 이내 즉시 피드백 처리"""
        start_time = time.time()
        
        optimizations = []
        
        try:
            # 사용자 피드백 저장
            user_feedback = UserFeedback(
                feedback_id=f"fb_{int(time.time() * 1000)}",
                user_id=feedback.user_id,
                session_id=feedback.session_id,
                feedback_type=feedback.feedback_type,
                content=feedback.content,
                rating=feedback.rating,
                timestamp=datetime.now()
            )
            
            # 피드백 유형별 즉시 적용
            if feedback.feedback_type == "style_preference":
                # 메시지 스타일 선호도 업데이트
                style = self._extract_style_preference(feedback.content)
                self.user_preferences[feedback.user_id]["message_style"] = style
                optimizations.append(f"메시지 스타일을 {style}로 변경")
                
                # Working Memory에 즉시 적용
                await self.memory_service.store_working_memory(
                    session_id=feedback.session_id,
                    key="style_preference",
                    value=style,
                    ttl=1800
                )
                
            elif feedback.feedback_type == "tool_performance":
                # 도구 성능 피드백 처리
                tool_optimization = self._process_tool_feedback(feedback.content)
                if tool_optimization:
                    optimizations.extend(tool_optimization)
                    
            elif feedback.feedback_type == "workflow_efficiency":
                # 워크플로우 효율성 피드백
                workflow_improvements = await self._optimize_workflow_from_feedback(
                    feedback.user_id, 
                    feedback.session_id, 
                    feedback.content
                )
                optimizations.extend(workflow_improvements)
                
            elif feedback.feedback_type == "response_quality":
                # 응답 품질 개선
                quality_improvements = self._improve_response_quality(
                    feedback.content, 
                    feedback.rating or 3.0
                )
                optimizations.extend(quality_improvements)
            
            # 크로스 에이전트 학습을 위한 선호도 공유
            await self._share_user_preferences(feedback.user_id)
            
            # 장기 메모리에 피드백 저장
            await self._store_feedback_in_memory(user_feedback)
            
            processing_time = time.time() - start_time
            
            # 예상 개선 효과 계산
            expected_improvements = self._calculate_expected_improvements(optimizations)
            
            return FeedbackResponse(
                applied=True,
                processing_time=processing_time,
                optimizations=optimizations,
                expected_improvements=expected_improvements
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return FeedbackResponse(
                applied=False,
                processing_time=processing_time,
                optimizations=[f"오류 발생: {str(e)}"],
                expected_improvements={}
            )
    
    async def process_performance_feedback(self, tool_type: MCPToolType, execution_time: float, success: bool, error_type: str = None):
        """도구 성능 피드백 처리"""
        feedback = PerformanceFeedback(
            feedback_id=f"perf_{int(time.time() * 1000)}",
            tool_type=tool_type,
            execution_time=execution_time,
            success=success,
            error_type=error_type,
            timestamp=datetime.now()
        )
        
        self.performance_feedback.append(feedback)
        
        # 성능 최적화 로직
        optimizations = []
        
        # 실행 시간이 임계값을 초과하는 경우
        if execution_time > 3.0:  # 3초 이상
            optimization = await self._optimize_slow_tool(tool_type, execution_time)
            if optimization:
                optimizations.extend(optimization)
                feedback.optimization_applied = optimization
        
        # 실패율이 높은 경우
        recent_failures = [f for f in self.performance_feedback[-20:] 
                          if f.tool_type == tool_type and not f.success]
        
        if len(recent_failures) >= 5:  # 최근 20회 중 5회 이상 실패
            reliability_optimization = await self._improve_tool_reliability(tool_type)
            optimizations.extend(reliability_optimization)
            feedback.optimization_applied.extend(reliability_optimization)
        
        return optimizations
    
    def _extract_style_preference(self, feedback_content: str) -> str:
        """피드백에서 스타일 선호도 추출"""
        content_lower = feedback_content.lower()
        
        if any(word in content_lower for word in ["친근", "캐주얼", "편한"]):
            return "casual"
        elif any(word in content_lower for word in ["공식", "정중", "비즈니스"]):
            return "professional"
        elif any(word in content_lower for word in ["기술적", "자세한", "전문적"]):
            return "technical"
        elif any(word in content_lower for word in ["간단", "짧게", "요약"]):
            return "concise"
        else:
            return "balanced"
    
    def _process_tool_feedback(self, feedback_content: str) -> List[str]:
        """도구 성능 피드백 처리"""
        optimizations = []
        content_lower = feedback_content.lower()
        
        if any(word in content_lower for word in ["느려", "오래", "지연"]):
            optimizations.append("도구 실행 속도 최적화 적용")
            optimizations.append("캐싱 메커니즘 강화")
            
        elif any(word in content_lower for word in ["실패", "오류", "에러"]):
            optimizations.append("도구 안정성 개선")
            optimizations.append("예외 처리 강화")
            
        elif any(word in content_lower for word in ["부정확", "틀린", "잘못"]):
            optimizations.append("도구 정확도 개선")
            optimizations.append("검증 로직 추가")
        
        return optimizations
    
    async def _optimize_workflow_from_feedback(self, user_id: str, session_id: str, feedback_content: str) -> List[str]:
        """워크플로우 피드백 기반 최적화"""
        optimizations = []
        
        # 현재 세션의 워크플로우 정보 조회
        workflow_data, _ = await self.memory_service.get_working_memory(session_id, "current_workflow")
        
        if workflow_data:
            content_lower = feedback_content.lower()
            
            if any(word in content_lower for word in ["단계", "복잡", "간소화"]):
                optimizations.append("워크플로우 단계 최적화")
                # 불필요한 단계 제거 로직
                
            elif any(word in content_lower for word in ["순서", "흐름", "로직"]):
                optimizations.append("실행 순서 재배치")
                # 병렬 처리 가능한 단계 식별
                
            elif any(word in content_lower for word in ["도구", "선택", "대체"]):
                optimizations.append("최적 도구 조합 재선택")
                # 성능이 더 좋은 도구로 대체
        
        return optimizations
    
    def _improve_response_quality(self, feedback_content: str, rating: float) -> List[str]:
        """응답 품질 개선"""
        optimizations = []
        
        if rating < 3.0:
            content_lower = feedback_content.lower()
            
            if any(word in content_lower for word in ["길어", "장황", "너무"]):
                optimizations.append("응답 길이 최적화")
                
            elif any(word in content_lower for word in ["짧아", "부족", "더"]):
                optimizations.append("응답 상세도 증가")
                
            elif any(word in content_lower for word in ["관련없", "부정확", "틀린"]):
                optimizations.append("응답 관련성 개선")
                optimizations.append("컨텍스트 이해도 향상")
        
        return optimizations
    
    async def _optimize_slow_tool(self, tool_type: MCPToolType, execution_time: float) -> List[str]:
        """느린 도구 최적화"""
        optimizations = []
        
        if tool_type == MCPToolType.SEARCH_DB:
            optimizations.append("데이터베이스 쿼리 최적화")
            optimizations.append("인덱스 추가 제안")
            optimizations.append("결과 캐싱 적용")
            
        elif tool_type == MCPToolType.GENERATE_MSG:
            optimizations.append("메시지 템플릿 캐싱")
            optimizations.append("생성 알고리즘 최적화")
            
        elif tool_type == MCPToolType.SEND_SLACK:
            optimizations.append("배치 전송 최적화")
            optimizations.append("API 호출 효율화")
        
        # 최적화 이력에 기록
        self.optimization_history[tool_type].append({
            "timestamp": datetime.now(),
            "execution_time": execution_time,
            "optimizations": optimizations
        })
        
        return optimizations
    
    async def _improve_tool_reliability(self, tool_type: MCPToolType) -> List[str]:
        """도구 신뢰성 개선"""
        optimizations = []
        
        # 최근 실패 패턴 분석
        recent_failures = [f for f in self.performance_feedback[-50:] 
                          if f.tool_type == tool_type and not f.success]
        
        error_types = [f.error_type for f in recent_failures if f.error_type]
        
        if error_types:
            # 가장 빈번한 오류 유형
            most_common_error = max(set(error_types), key=error_types.count)
            
            if "timeout" in most_common_error.lower():
                optimizations.append("타임아웃 설정 최적화")
                optimizations.append("재시도 로직 개선")
                
            elif "connection" in most_common_error.lower():
                optimizations.append("연결 풀 최적화")
                optimizations.append("연결 안정성 개선")
                
            elif "rate limit" in most_common_error.lower():
                optimizations.append("속도 제한 대응")
                optimizations.append("요청 간격 조정")
        
        return optimizations
    
    async def _share_user_preferences(self, user_id: str):
        """사용자 선호도 크로스 에이전트 공유"""
        if user_id in self.user_preferences:
            preferences = self.user_preferences[user_id]
            
            # 메모리에 선호도 저장하여 다른 세션에서 활용 가능하게 함
            await self.memory_service.store_working_memory(
                session_id=f"preferences_{user_id}",
                key="shared_preferences",
                value=preferences,
                ttl=86400  # 24시간
            )
            
            # 장기 메모리에도 저장
            preference_text = f"사용자 {user_id} 선호도: " + ", ".join([
                f"{k}: {v}" for k, v in preferences.items()
            ])
            
            self.memory_service.mem0.add(
                preference_text,
                user_id=user_id,
                metadata={"type": "preference", "shared": True}
            )
    
    async def _store_feedback_in_memory(self, feedback: UserFeedback):
        """피드백을 장기 메모리에 저장"""
        feedback_text = (
            f"사용자 피드백: {feedback.feedback_type} - {feedback.content} "
            f"(평점: {feedback.rating})"
        )
        
        self.memory_service.mem0.add(
            feedback_text,
            user_id=feedback.user_id,
            metadata={
                "type": "feedback",
                "feedback_type": feedback.feedback_type,
                "rating": feedback.rating,
                "timestamp": feedback.timestamp.isoformat()
            }
        )
    
    def _calculate_expected_improvements(self, optimizations: List[str]) -> Dict[str, float]:
        """최적화로 인한 예상 개선 효과 계산"""
        improvements = {}
        
        for optimization in optimizations:
            if "속도" in optimization or "캐싱" in optimization:
                improvements["response_time_improvement"] = improvements.get("response_time_improvement", 0) + 0.25
                
            elif "안정성" in optimization or "신뢰성" in optimization:
                improvements["reliability_improvement"] = improvements.get("reliability_improvement", 0) + 0.15
                
            elif "정확도" in optimization or "품질" in optimization:
                improvements["accuracy_improvement"] = improvements.get("accuracy_improvement", 0) + 0.20
                
            elif "만족도" in optimization or "사용자" in optimization:
                improvements["user_satisfaction_improvement"] = improvements.get("user_satisfaction_improvement", 0) + 0.30
        
        return improvements
    
    async def get_optimization_history(self, tool_type: MCPToolType = None) -> Dict[str, Any]:
        """최적화 이력 조회"""
        if tool_type:
            return {
                str(tool_type): self.optimization_history.get(tool_type, [])
            }
        return {str(k): v for k, v in self.optimization_history.items()}
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """사용자 선호도 조회"""
        # 메모리에서도 조회 (크로스 에이전트 학습용)
        preferences, _ = await self.memory_service.get_working_memory(f"preferences_{user_id}", "shared_preferences")
        
        # 현재 세션 선호도와 병합
        current_preferences = self.user_preferences.get(user_id, {})
        
        return {**preferences.get("shared_preferences", {}), **current_preferences}import asyncio
import time
import json
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime, timedelta
from .memory_service import EnhancedMemoryService
from ..models.schemas import (
    FeedbackRequest, FeedbackResponse, PerformanceFeedback, UserFeedback,
    MCPToolType, WorkflowPattern
)

class EnhancedFeedbackService:
    def __init__(self, memory_service: EnhancedMemoryService):
        self.memory_service = memory_service
        self.user_preferences = defaultdict(dict)
        self.performance_feedback = []
        self.optimization_history = defaultdict(list)
        
    async def process_immediate_feedback(self, feedback: FeedbackRequest) -> FeedbackResponse:
        """5초 이내 즉시 피드백 처리"""
        start_time = time.time()
        
        optimizations = []
        
        try:
            # 사용자 피드백 저장
            user_feedback = UserFeedback(
                feedback_id=f"fb_{int(time.time() * 1000)}",
                user_id=feedback.user_id,
                session_id=feedback.session_id,
                feedback_type=feedback.feedback_type,
                content=feedback.content,
                rating=feedback.rating,
                timestamp=datetime.now()
            )
            
            # 피드백 유형별 즉시 적용
            if feedback.feedback_type == "style_preference":
                # 메시지 스타일 선호도 업데이트
                style = self._extract_style_preference(feedback.content)
                self.user_preferences[feedback.user_id]["message_style"] = style
                optimizations.append(f"메시지 스타일을 {style}로 변경")
                
                # Working Memory에 즉시 적용
                await self.memory_service.store_working_memory(
                    session_id=feedback.session_id,
                    key="style_preference",
                    value=style,
                    ttl=1800
                )
                
            elif feedback.feedback_type == "tool_performance":
                # 도구 성능 피드백 처리
                tool_optimization = self._process_tool_feedback(feedback.content)
                if tool_optimization:
                    optimizations.extend(tool_optimization)
                    
            elif feedback.feedback_type == "workflow_efficiency":
                # 워크플로우 효율성 피드백
                workflow_improvements = await self._optimize_workflow_from_feedback(
                    feedback.user_id, 
                    feedback.session_id, 
                    feedback.content
                )
                optimizations.extend(workflow_improvements)
                
            elif feedback.feedback_type == "response_quality":
                # 응답 품질 개선
                quality_improvements = self._improve_response_quality(
                    feedback.content, 
                    feedback.rating or 3.0
                )
                optimizations.extend(quality_improvements)
            
            # 크로스 에이전트 학습을 위한 선호도 공유
            await self._share_user_preferences(feedback.user_id)
            
            # 장기 메모리에 피드백 저장
            await self._store_feedback_in_memory(user_feedback)
            
            processing_time = time.time() - start_time
            
            # 예상 개선 효과 계산
            expected_improvements = self._calculate_expected_improvements(optimizations)
            
            return FeedbackResponse(
                applied=True,
                processing_time=processing_time,
                optimizations=optimizations,
                expected_improvements=expected_improvements
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return FeedbackResponse(
                applied=False,
                processing_time=processing_time,
                optimizations=[f"오류 발생: {str(e)}"],
                expected_improvements={}
            )
    
    async def process_performance_feedback(self, tool_type: MCPToolType, execution_time: float, success: bool, error_type: str = None):
        """도구 성능 피드백 처리"""
        feedback = PerformanceFeedback(
            feedback_id=f"perf_{int(time.time() * 1000)}",
            tool_type=tool_type,
            execution_time=execution_time,
            success=success,
            error_type=error_type,
            timestamp=datetime.now()
        )
        
        self.performance_feedback.append(feedback)
        
        # 성능 최적화 로직
        optimizations = []
        
        # 실행 시간이 임계값을 초과하는 경우
        if execution_time > 3.0:  # 3초 이상
            optimization = await self._optimize_slow_tool(tool_type, execution_time)
            if optimization:
                optimizations.extend(optimization)
                feedback.optimization_applied = optimization
        
        # 실패율이 높은 경우
        recent_failures = [f for f in self.performance_feedback[-20:] 
                          if f.tool_type == tool_type and not f.success]
        
        if len(recent_failures) >= 5:  # 최근 20회 중 5회 이상 실패
            reliability_optimization = await self._improve_tool_reliability(tool_type)
            optimizations.extend(reliability_optimization)
            feedback.optimization_applied.extend(reliability_optimization)
        
        return optimizations
    
    def _extract_style_preference(self, feedback_content: str) -> str:
        """피드백에서 스타일 선호도 추출"""
        content_lower = feedback_content.lower()
        
        if any(word in content_lower for word in ["친근", "캐주얼", "편한"]):
            return "casual"
        elif any(word in content_lower for word in ["공식", "정중", "비즈니스"]):
            return "professional"
        elif any(word in content_lower for word in ["기술적", "자세한", "전문적"]):
            return "technical"
        elif any(word in content_lower for word in ["간단", "짧게", "요약"]):
            return "concise"
        else:
            return "balanced"
    
    def _process_tool_feedback(self, feedback_content: str) -> List[str]:
        """도구 성능 피드백 처리"""
        optimizations = []
        content_lower = feedback_content.lower()
        
        if any(word in content_lower for word in ["느려", "오래", "지연"]):
            optimizations.append("도구 실행 속도 최적화 적용")
            optimizations.append("캐싱 메커니즘 강화")
            
        elif any(word in content_lower for word in ["실패", "오류", "에러"]):
            optimizations.append("도구 안정성 개선")
            optimizations.append("예외 처리 강화")
            
        elif any(word in content_lower for word in ["부정확", "틀린", "잘못"]):
            optimizations.append("도구 정확도 개선")
            optimizations.append("검증 로직 추가")
        
        return optimizations
    
    async def _optimize_workflow_from_feedback(self, user_id: str, session_id: str, feedback_content: str) -> List[str]:
        """워크플로우 피드백 기반 최적화"""
        optimizations = []
        
        # 현재 세션의 워크플로우 정보 조회
        workflow_data, _ = await self.memory_service.get_working_memory(session_id, "current_workflow")
        
        if workflow_data:
            content_lower = feedback_content.lower()
            
            if any(word in content_lower for word in ["단계", "복잡", "간소화"]):
                optimizations.append("워크플로우 단계 최적화")
                # 불필요한 단계 제거 로직
                
            elif any(word in content_lower for word in ["순서", "흐름", "로직"]):
                optimizations.append("실행 순서 재배치")
                # 병렬 처리 가능한 단계 식별
                
            elif any(word in content_lower for word in ["도구", "선택", "대체"]):
                optimizations.append("최적 도구 조합 재선택")
                # 성능이 더 좋은 도구로 대체
        
        return optimizations
    
    def _improve_response_quality(self, feedback_content: str, rating: float) -> List[str]:
        """응답 품질 개선"""
        optimizations = []
        
        if rating < 3.0:
            content_lower = feedback_content.lower()
            
            if any(word in content_lower for word in ["길어", "장황", "너무"]):
                optimizations.append("응답 길이 최적화")
                
            elif any(word in content_lower for word in ["짧아", "부족", "더"]):
                optimizations.append("응답 상세도 증가")
                
            elif any(word in content_lower for word in ["관련없", "부정확", "틀린"]):
                optimizations.append("응답 관련성 개선")
                optimizations.append("컨텍스트 이해도 향상")
        
        return optimizations
    
    async def _optimize_slow_tool(self, tool_type: MCPToolType, execution_time: float) -> List[str]:
        """느린 도구 최적화"""
        optimizations = []
        
        if tool_type == MCPToolType.SEARCH_DB:
            optimizations.append("데이터베이스 쿼리 최적화")
            optimizations.append("인덱스 추가 제안")
            optimizations.append("결과 캐싱 적용")
            
        elif tool_type == MCPToolType.GENERATE_MSG:
            optimizations.append("메시지 템플릿 캐싱")
            optimizations.append("생성 알고리즘 최적화")
            
        elif tool_type == MCPToolType.SEND_SLACK:
            optimizations.append("배치 전송 최적화")
            optimizations.append("API 호출 효율화")
        
        # 최적화 이력에 기록
        self.optimization_history[tool_type].append({
            "timestamp": datetime.now(),
            "execution_time": execution_time,
            "optimizations": optimizations
        })
        
        return optimizations
    
    async def _improve_tool_reliability(self, tool_type: MCPToolType) -> List[str]:
        """도구 신뢰성 개선"""
        optimizations = []
        
        # 최근 실패 패턴 분석
        recent_failures = [f for f in self.performance_feedback[-50:] 
                          if f.tool_type == tool_type and not f.success]
        
        error_types = [f.error_type for f in recent_failures if f.error_type]
        
        if error_types:
            # 가장 빈번한 오류 유형
            most_common_error = max(set(error_types), key=error_types.count)
            
            if "timeout" in most_common_error.lower():
                optimizations.append("타임아웃 설정 최적화")
                optimizations.append("재시도 로직 개선")
                
            elif "connection" in most_common_error.lower():
                optimizations.append("연결 풀 최적화")
                optimizations.append("연결 안정성 개선")
                
            elif "rate limit" in most_common_error.lower():
                optimizations.append("속도 제한 대응")
                optimizations.append("요청 간격 조정")
        
        return optimizations
    
    async def _share_user_preferences(self, user_id: str):
        """사용자 선호도 크로스 에이전트 공유"""
        if user_id in self.user_preferences:
            preferences = self.user_preferences[user_id]
            
            # 메모리에 선호도 저장하여 다른 세션에서 활용 가능하게 함
            await self.memory_service.store_working_memory(
                session_id=f"preferences_{user_id}",
                key="shared_preferences",
                value=preferences,
                ttl=86400  # 24시간
            )
            
            # 장기 메모리에도 저장
            preference_text = f"사용자 {user_id} 선호도: " + ", ".join([
                f"{k}: {v}" for k, v in preferences.items()
            ])
            
            self.memory_service.mem0.add(
                preference_text,
                user_id=user_id,
                metadata={"type": "preference", "shared": True}
            )
    
    async def _store_feedback_in_memory(self, feedback: UserFeedback):
        """피드백을 장기 메모리에 저장"""
        feedback_text = (
            f"사용자 피드백: {feedback.feedback_type} - {feedback.content} "
            f"(평점: {feedback.rating})"
        )
        
        self.memory_service.mem0.add(
            feedback_text,
            user_id=feedback.user_id,
            metadata={
                "type": "feedback",
                "feedback_type": feedback.feedback_type,
                "rating": feedback.rating,
                "timestamp": feedback.timestamp.isoformat()
            }
        )
    
    def _calculate_expected_improvements(self, optimizations: List[str]) -> Dict[str, float]:
        """최적화로 인한 예상 개선 효과 계산"""
        improvements = {}
        
        for optimization in optimizations:
            if "속도" in optimization or "캐싱" in optimization:
                improvements["response_time_improvement"] = improvements.get("response_time_improvement", 0) + 0.25
                
            elif "안정성" in optimization or "신뢰성" in optimization:
                improvements["reliability_improvement"] = improvements.get("reliability_improvement", 0) + 0.15
                
            elif "정확도" in optimization or "품질" in optimization:
                improvements["accuracy_improvement"] = improvements.get("accuracy_improvement", 0) + 0.20
                
            elif "만족도" in optimization or "사용자" in optimization:
                improvements["user_satisfaction_improvement"] = improvements.get("user_satisfaction_improvement", 0) + 0.30
        
        return improvements
    
    async def get_optimization_history(self, tool_type: MCPToolType = None) -> Dict[str, Any]:
        """최적화 이력 조회"""
        if tool_type:
            return {
                str(tool_type): self.optimization_history.get(tool_type, [])
            }
        return {str(k): v for k, v in self.optimization_history.items()}
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """사용자 선호도 조회"""
        # 메모리에서도 조회 (크로스 에이전트 학습용)
        preferences, _ = await self.memory_service.get_working_memory(f"preferences_{user_id}", "shared_preferences")
        
        # 현재 세션 선호도와 병합
        current_preferences = self.user_preferences.get(user_id, {})
        
        return {**preferences.get("shared_preferences", {}), **current_preferences}