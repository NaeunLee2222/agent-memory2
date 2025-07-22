import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import OpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from ..services.memory_service import EnhancedMemoryService
from ..services.mcp_service import MCPService
from ..services.feedback_service import EnhancedFeedbackService
from ..models.schemas import (
    AgentMode,
    ChatResponse,
    WorkflowStep,
    WorkflowPattern,
    MCPToolCall,
    MCPToolType,
    MemoryType,
    EpisodicMemory,
)
from ..utils.config import config


class EnhancedAgentService:
    def __init__(
        self,
        memory_service: EnhancedMemoryService,
        mcp_service: MCPService,
        feedback_service: EnhancedFeedbackService,
    ):
        self.memory_service = memory_service
        self.mcp_service = mcp_service
        self.feedback_service = feedback_service
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.checkpointer = MemorySaver()

        # 워크플로우 패턴 저장소
        self.learned_patterns = {}

    async def process_chat(
        self,
        message: str,
        user_id: str,
        session_id: str,
        mode: AgentMode,
        context: Dict[str, Any] = None,
    ) -> ChatResponse:
        """채팅 메시지 처리"""
        start_time = time.time()
        context = context or {}

        # 1. 관련 메모리 검색
        memories, memory_retrieval_time = (
            await self.memory_service.retrieve_relevant_memories(
                user_id=user_id,
                query=message,
                memory_types=[
                    MemoryType.PROCEDURAL,
                    MemoryType.EPISODIC,
                    MemoryType.SEMANTIC,
                ],
                limit=3,
            )
        )

        # 2. 사용자 선호도 적용
        user_preferences = await self.feedback_service.get_user_preferences(user_id)

        # 3. 모드별 처리
        if mode == AgentMode.FLOW:
            workflow_result = await self._process_flow_mode(
                message, user_id, session_id, memories, user_preferences, context
            )
        else:
            workflow_result = await self._process_basic_mode(
                message, user_id, session_id, memories, user_preferences, context
            )

        # 4. 응답 생성
        response_text = await self._generate_response(
            message, workflow_result, user_preferences
        )

        # 5. 에피소드 메모리에 상호작용 저장
        episode = EpisodicMemory(
            episode_id=f"{session_id}_{int(time.time() * 1000)}",
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now(),
            interaction_type="chat_interaction",
            context={
                "message": message,
                "mode": mode,
                "response": response_text,
                "tools_used": [
                    result.tool_type for result in workflow_result["tools_used"]
                ],
                "processing_time": time.time() - start_time,
            },
            workflow_executed=workflow_result.get("workflow_pattern"),
            lessons_learned=workflow_result.get("lessons_learned", []),
        )

        await self.memory_service.store_episodic_memory(episode)

        # 6. 성능 피드백 처리
        for tool_result in workflow_result["tools_used"]:
            await self.feedback_service.process_performance_feedback(
                tool_type=tool_result.tool_type,
                execution_time=tool_result.execution_time,
                success=tool_result.success,
                error_type=tool_result.error,
            )

        total_processing_time = time.time() - start_time

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            workflow_executed=workflow_result.get("workflow_pattern"),
            memory_used={
                MemoryType.WORKING: [f"세션 컨텍스트: {len(context)} 항목"],
                MemoryType.EPISODIC: [
                    m["content"][:100] for m in memories[MemoryType.EPISODIC][:2]
                ],
                MemoryType.SEMANTIC: [
                    m["content"][:100] for m in memories[MemoryType.SEMANTIC][:2]
                ],
                MemoryType.PROCEDURAL: [
                    m["content"][:100] for m in memories[MemoryType.PROCEDURAL][:2]
                ],
            },
            processing_time=total_processing_time,
            tools_used=workflow_result["tools_used"],
            confidence_score=workflow_result.get("confidence_score", 0.8),
            optimization_applied=workflow_result.get("optimizations", []),
        )

    async def _process_flow_mode(
        self,
        message: str,
        user_id: str,
        session_id: str,
        memories: Dict[MemoryType, List],
        user_preferences: Dict,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """플로우 모드 처리 - 구조화된 Step-Action-Tool 실행"""

        # 1. 유사한 절차 패턴 검색
        similar_procedures, _ = await self.memory_service.retrieve_similar_procedures(
            message, user_id, limit=3
        )

        # 2. 새로운 워크플로우 계획 또는 기존 패턴 재사용
        if similar_procedures and similar_procedures[0].get("relevance_score", 0) > 0.8:
            # 기존 패턴 재사용
            workflow_pattern = await self._reuse_workflow_pattern(
                similar_procedures[0], context
            )
            optimization_note = ["기존 성공 패턴 재사용"]
        else:
            # 새로운 워크플로우 계획
            workflow_pattern = await self._plan_new_workflow(
                message, memories, user_preferences, context
            )
            optimization_note = ["새로운 워크플로우 생성"]

        # 3. 워크플로우 실행
        execution_results = await self._execute_workflow(workflow_pattern)

        # 4. 성공한 패턴을 절차 메모리에 저장
        if all(result.success for result in execution_results):
            workflow_pattern.success_rate = 1.0
            workflow_pattern.usage_count = workflow_pattern.usage_count + 1
            await self.memory_service.store_procedural_memory(workflow_pattern, user_id)
            optimization_note.append("성공 패턴 학습 완료")

        return {
            "workflow_pattern": workflow_pattern,
            "tools_used": execution_results,
            "confidence_score": (
                0.9 if all(r.success for r in execution_results) else 0.6
            ),
            "optimizations": optimization_note,
            "lessons_learned": self._extract_lessons_from_execution(execution_results),
        }

    async def _process_basic_mode(
        self,
        message: str,
        user_id: str,
        session_id: str,
        memories: Dict[MemoryType, List],
        user_preferences: Dict,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """기본 모드 처리 - 자율적 도구 선택 및 실행"""

        # 1. 자연어 의도 분석
        intent_analysis = await self._analyze_user_intent(
            message, memories, user_preferences
        )

        # 2. 최적 도구 조합 추천
        suggested_tools = self.mcp_service.suggest_optimal_tool_combination(message)

        # 3. 에피소드 메모리 기반 도구 선택 개선
        if memories[MemoryType.EPISODIC]:
            refined_tools = await self._refine_tools_from_episodes(
                suggested_tools, memories[MemoryType.EPISODIC]
            )
        else:
            refined_tools = suggested_tools

        # 4. 도구 실행
        tool_calls = []
        for tool_type in refined_tools[:3]:  # 최대 3개 도구
            tool_call = MCPToolCall(
                tool_type=tool_type,
                parameters=self._generate_tool_parameters(
                    tool_type, message, intent_analysis
                ),
                context=context,
            )
            tool_calls.append(tool_call)

        execution_results = await self.mcp_service.execute_workflow(tool_calls)

        # 5. 실행 결과 기반 학습
        lessons_learned = []
        if execution_results:
            success_rate = sum(1 for r in execution_results if r.success) / len(
                execution_results
            )
            if success_rate > 0.8:
                lessons_learned.append(
                    f"도구 조합 {[r.tool_type for r in execution_results]} 성공률 높음"
                )

        return {
            "workflow_pattern": None,  # 기본 모드는 고정 워크플로우 없음
            "tools_used": execution_results,
            "confidence_score": intent_analysis.get("confidence", 0.7),
            "optimizations": [f"자율 선택: {len(refined_tools)}개 도구 활용"],
            "lessons_learned": lessons_learned,
        }

    async def _plan_new_workflow(
        self,
        message: str,
        memories: Dict[MemoryType, List],
        user_preferences: Dict,
        context: Dict[str, Any],
    ) -> WorkflowPattern:
        """새로운 워크플로우 계획"""

        # AI를 통한 워크플로우 계획 생성
        system_prompt = """
        사용자 요청을 분석하여 Step-Action-Tool 워크플로우를 계획하세요.
        
        사용 가능한 도구:
        - SEARCH_DB: 데이터베이스 검색
        - GENERATE_MSG: 메시지 생성
        - SEND_SLACK: Slack 알림 전송
        - EMERGENCY_MAIL: 비상 메일 데이터 생성
        - SEND_EMAIL: 이메일 전송
        
        3-5단계의 논리적 순서로 계획하세요.
        """

        user_prompt = f"""
        요청: {message}
        컨텍스트: {context}
        사용자 선호도: {user_preferences}
        
        JSON 형태로 워크플로우를 계획하세요:
        {{
            "pattern_name": "워크플로우 이름",
            "steps": [
                {{"step_id": 1, "step_name": "단계명", "action": "액션", "tool_type": "SEARCH_DB", "parameters": {{}}}},
                ...
            ]
        }}
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )

            plan_json = json.loads(response.choices[0].message.content)

            # WorkflowPattern 객체 생성
            steps = []
            for step_data in plan_json["steps"]:
                tool_calls = [
                    MCPToolCall(
                        tool_type=MCPToolType(step_data["tool_type"]),
                        parameters=step_data.get("parameters", {}),
                        context=context,
                    )
                ]

                step = WorkflowStep(
                    step_id=step_data["step_id"],
                    step_name=step_data["step_name"],
                    action=step_data["action"],
                    tool_calls=tool_calls,
                )
                steps.append(step)

            workflow_pattern = WorkflowPattern(
                pattern_id=f"wf_{int(time.time() * 1000)}",
                pattern_name=plan_json["pattern_name"],
                steps=steps,
                success_rate=0.0,  # 초기값
                avg_execution_time=0.0,
                usage_count=0,
                last_used=datetime.now(),
            )

            return workflow_pattern

        except Exception as e:
            # 기본 워크플로우 반환
            return self._create_default_workflow(message)

    async def _reuse_workflow_pattern(
        self, similar_procedure: Dict, context: Dict[str, Any]
    ) -> WorkflowPattern:
        """기존 워크플로우 패턴 재사용"""
        pattern_id = similar_procedure.get("pattern_id", "default")

        # 기본 패턴 생성 (실제로는 저장된 패턴을 불러와야 함)
        return self._create_default_workflow("재사용 워크플로우")

    def _create_default_workflow(self, message: str) -> WorkflowPattern:
        """기본 워크플로우 생성"""
        steps = [
            WorkflowStep(
                step_id=1,
                step_name="데이터 수집",
                action="정보 조회",
                tool_calls=[
                    MCPToolCall(
                        tool_type=MCPToolType.SEARCH_DB,
                        parameters={"query": message},
                        context={},
                    )
                ],
            ),
            WorkflowStep(
                step_id=2,
                step_name="응답 생성",
                action="메시지 작성",
                tool_calls=[
                    MCPToolCall(
                        tool_type=MCPToolType.GENERATE_MSG,
                        parameters={"content": "조회 결과", "style": "professional"},
                        context={},
                    )
                ],
            ),
            WorkflowStep(
                step_id=3,
                step_name="결과 전달",
                action="알림 발송",
                tool_calls=[
                    MCPToolCall(
                        tool_type=MCPToolType.SEND_SLACK,
                        parameters={"message": "결과 메시지", "channel": "#general"},
                        context={},
                    )
                ],
            ),
        ]

        return WorkflowPattern(
            pattern_id=f"default_wf_{int(time.time())}",
            pattern_name="기본 처리 워크플로우",
            steps=steps,
            success_rate=0.8,
            avg_execution_time=5.0,
            usage_count=1,
            last_used=datetime.now(),
        )

    async def _execute_workflow(self, workflow_pattern: WorkflowPattern) -> List:
        """워크플로우 실행"""
        results = []

        for step in workflow_pattern.steps:
            step.status = "running"
            step_start_time = time.time()

            # 단계별 도구 실행
            step_results = await self.mcp_service.execute_workflow(step.tool_calls)

            step.execution_time = time.time() - step_start_time
            step.result = step_results

            if all(r.success for r in step_results):
                step.status = "completed"
            else:
                step.status = "failed"
                break  # 실패 시 워크플로우 중단

            results.extend(step_results)

        return results

    async def _analyze_user_intent(
        self, message: str, memories: Dict[MemoryType, List], user_preferences: Dict
    ) -> Dict[str, Any]:
        """사용자 의도 분석"""

        # 메모리 컨텍스트 구성
        memory_context = ""
        for memory_type, memory_list in memories.items():
            if memory_list:
                memory_context += (
                    f"\n{memory_type}: {memory_list[0].get('content', '')[:100]}"
                )

        system_prompt = """
        사용자의 메시지를 분석하여 의도와 필요한 도구를 파악하세요.
        분석 결과를 JSON으로 반환하세요.
        """

        user_prompt = f"""
        메시지: {message}
        메모리 컨텍스트: {memory_context}
        사용자 선호도: {user_preferences}
        
        다음 형태로 분석하세요:
        {{
            "primary_intent": "주요 의도",
            "urgency": "low|medium|high",
            "domain": "도메인 영역",
            "required_tools": ["필요한 도구 목록"],
            "confidence": 0.8
        }}
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            # 기본 분석 반환
            return {
                "primary_intent": "일반 문의",
                "urgency": "medium",
                "domain": "general",
                "required_tools": ["SEARCH_DB", "GENERATE_MSG"],
                "confidence": 0.5,
            }

    async def _refine_tools_from_episodes(
        self, suggested_tools: List[MCPToolType], episodes: List[Dict]
    ) -> List[MCPToolType]:
        """에피소드 메모리 기반 도구 선택 개선"""
        refined_tools = suggested_tools.copy()

        # 과거 성공 경험에서 효과적이었던 도구 우선순위 조정
        for episode in episodes:
            if "성공" in episode.get("content", ""):
                # 성공한 에피소드에서 언급된 도구들의 우선순위 증가
                # 실제로는 더 정교한 NLP 분석 필요
                pass

        return refined_tools

    def _generate_tool_parameters(
        self, tool_type: MCPToolType, message: str, intent_analysis: Dict
    ) -> Dict[str, Any]:
        """도구별 파라미터 생성"""

        if tool_type == MCPToolType.SEARCH_DB:
            return {
                "query": message[:100],  # 쿼리 길이 제한
                "table": "main_data",
                "filters": {},
            }

        elif tool_type == MCPToolType.GENERATE_MSG:
            style = "professional"
            if intent_analysis.get("urgency") == "high":
                style = "urgent"
            return {"content": message, "style": style, "length": "medium"}

        elif tool_type == MCPToolType.SEND_SLACK:
            return {"message": f"알림: {message}", "channel": "#general"}

        elif tool_type == MCPToolType.EMERGENCY_MAIL:
            return {
                "type": "general",
                "severity": intent_analysis.get("urgency", "medium"),
                "description": message,
            }

        else:
            return {}

    async def _generate_response(
        self, message: str, workflow_result: Dict, user_preferences: Dict
    ) -> str:
        """최종 응답 생성"""

        # 사용자 선호 스타일 적용
        style = user_preferences.get("message_style", "professional")

        tools_used = [r.tool_type for r in workflow_result["tools_used"] if r.success]
        success_count = sum(1 for r in workflow_result["tools_used"] if r.success)

        if success_count == len(workflow_result["tools_used"]):
            base_response = f"요청을 성공적으로 처리했습니다. 사용된 도구: {', '.join(map(str, tools_used))}"
        else:
            base_response = f"요청을 부분적으로 처리했습니다. 성공한 도구: {success_count}/{len(workflow_result['tools_used'])}"

        # 스타일에 따른 응답 조정
        if style == "casual":
            response = f"안녕하세요! {base_response} 😊"
        elif style == "technical":
            response = f"[처리 완료] {base_response}\n실행 시간: {workflow_result.get('processing_time', 0):.2f}초"
        elif style == "concise":
            response = base_response
        else:  # professional
            response = f"안녕하세요,\n\n{base_response}\n\n감사합니다."

        return response

    def _extract_lessons_from_execution(self, execution_results: List) -> List[str]:
        """실행 결과에서 교훈 추출"""
        lessons = []

        success_count = sum(1 for r in execution_results if r.success)
        total_time = sum(r.execution_time for r in execution_results)

        if success_count == len(execution_results):
            lessons.append("모든 도구 실행 성공")

        if total_time > 10.0:
            lessons.append("실행 시간 최적화 필요")

        # 실패한 도구가 있는 경우
        failed_tools = [r.tool_type for r in execution_results if not r.success]
        if failed_tools:
            lessons.append(f"실패 도구: {failed_tools} - 대안 도구 검토 필요")

        return lessons
