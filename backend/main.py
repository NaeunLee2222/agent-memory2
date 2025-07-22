from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Union
import asyncio
import json
import uuid
from datetime import datetime
import logging

# 기존 메모리 시스템 및 피드백 모듈 (이미 구현되어 있다고 가정)
from memory.working_memory import WorkingMemoryManager
from memory.episodic_memory import EpisodicMemoryManager
from memory.semantic_memory import SemanticMemoryManager
from memory.procedural_memory import ProceduralMemoryManager
from feedback.collector import FeedbackCollector
from feedback.processor import FeedbackProcessor

# MCP 도구 연결 모듈
from mcp.connector import MCPConnector
from mcp.tool_registry import ToolRegistry

# 에이전트 핵심 로직 모듈
from agent.planner import AgenticPlanner
from agent.executor import AgenticExecutor
from agent.reasoner import AgenticReasoner

app = FastAPI(title="Agentic AI Platform")

# Request/Response 모델
class ChatRequest(BaseModel):
    message: str
    user_id: str
    mode: str = "basic"  # "basic" or "flow"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    execution_trace: List[Dict]
    metadata: Dict

class AgenticAIBackend:
    def __init__(self):
        # 메모리 시스템 초기화
        self.working_memory = WorkingMemoryManager()
        self.episodic_memory = EpisodicMemoryManager()
        self.semantic_memory = SemanticMemoryManager()
        self.procedural_memory = ProceduralMemoryManager()
        
        # 피드백 시스템 초기화
        self.feedback_collector = FeedbackCollector()
        self.feedback_processor = FeedbackProcessor()
        
        # MCP 도구 시스템 초기화
        self.mcp_connector = MCPConnector()
        self.tool_registry = ToolRegistry()
        
        # 에이전트 핵심 로직 초기화
        self.planner = AgenticPlanner(self.semantic_memory, self.procedural_memory)
        self.executor = AgenticExecutor(self.mcp_connector, self.working_memory)
        self.reasoner = AgenticReasoner(self.episodic_memory, self.semantic_memory)
        
        # 사용 가능한 도구들 등록
        self._register_available_tools()
    
    def _register_available_tools(self):
        """사용 가능한 MCP 도구들을 등록"""
        available_tools = [
            {
                "name": "create_rfq_cover",
                "description": "RFQ 커버 페이지 생성",
                "category": "document_generation",
                "parameters": {
                    "company_name": "str",
                    "project_title": "str", 
                    "deadline": "str"
                }
            },
            {
                "name": "combine_rfq_cover", 
                "description": "RFQ 문서들을 결합",
                "category": "document_processing",
                "parameters": {
                    "documents": "list",
                    "output_format": "str"
                }
            },
            {
                "name": "modify_tbe_content",
                "description": "TBE 콘텐츠 수정",
                "category": "content_editing",
                "parameters": {
                    "content": "str",
                    "modifications": "list"
                }
            },
            {
                "name": "search_database",
                "description": "데이터베이스 검색",
                "category": "data_retrieval",
                "parameters": {
                    "query": "str",
                    "filters": "dict"
                }
            },
            {
                "name": "send_slack_message",
                "description": "슬랙 메시지 전송",
                "category": "communication",
                "parameters": {
                    "channel": "str",
                    "message": "str",
                    "mentions": "list"
                }
            }
        ]
        
        for tool in available_tools:
            self.tool_registry.register_tool(tool)
    
    async def process_request(self, request: ChatRequest) -> ChatResponse:
        """메인 요청 처리 로직"""
        try:
            # 1. 세션 관리
            session_id = request.session_id or str(uuid.uuid4())
            
            # 2. Working Memory에 요청 컨텍스트 저장
            context = await self._create_request_context(request, session_id)
            
            # 3. 요청 분석 및 의도 파악
            analyzed_request = await self.reasoner.analyze_request(
                request.message, context
            )
            
            # 4. 모드에 따른 실행
            if request.mode == "flow":
                response = await self._execute_flow_mode(analyzed_request, session_id)
            else:
                response = await self._execute_basic_mode(analyzed_request, session_id)
            
            # 5. 실행 결과를 에피소드 메모리에 저장
            await self._store_execution_episode(session_id, request, response)
            
            return response
            
        except Exception as e:
            logging.error(f"Request processing error: {str(e)}")
            # 에러 피드백 수집
            await self.feedback_collector.collect_error_feedback(
                session_id, str(e), request.message
            )
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _create_request_context(self, request: ChatRequest, session_id: str) -> Dict:
        """요청 컨텍스트 생성"""
        context = {
            "session_id": session_id,
            "user_id": request.user_id,
            "mode": request.mode,
            "original_message": request.message,
            "timestamp": datetime.utcnow().isoformat(),
            "available_tools": self.tool_registry.get_all_tools()
        }
        
        # Working Memory에 컨텍스트 저장
        await self.working_memory.store_context(session_id, context)
        
        return context
    
    async def _execute_flow_mode(self, analyzed_request: Dict, session_id: str) -> ChatResponse:
        """플로우 모드: 단계별 계획 수립 및 실행"""
        
        # 1. 복합 작업을 단계별로 분해
        execution_plan = await self.planner.create_execution_plan(
            analyzed_request["intent"],
            analyzed_request["entities"],
            analyzed_request["requirements"]
        )
        
        # 2. 각 단계별 실행
        execution_trace = []
        final_results = []
        
        for step in execution_plan["steps"]:
            step_result = await self._execute_step(step, session_id)
            execution_trace.append(step_result)
            
            # 단계 실행 후 Working Memory 업데이트
            await self.working_memory.update_step_result(
                session_id, step["step_id"], step_result
            )
            
            if step_result["success"]:
                final_results.append(step_result["output"])
            else:
                # 실패 시 대안 단계 시도
                alternative_step = await self.planner.find_alternative_step(
                    step, step_result["error"]
                )
                if alternative_step:
                    alt_result = await self._execute_step(alternative_step, session_id)
                    execution_trace.append(alt_result)
                    if alt_result["success"]:
                        final_results.append(alt_result["output"])
        
        # 3. 최종 결과 합성
        synthesized_response = await self._synthesize_results(final_results, execution_plan)
        
        return ChatResponse(
            response=synthesized_response,
            session_id=session_id,
            execution_trace=execution_trace,
            metadata={
                "mode": "flow",
                "steps_executed": len(execution_trace),
                "success_rate": sum(1 for t in execution_trace if t["success"]) / len(execution_trace),
                "execution_plan": execution_plan
            }
        )
    
    async def _execute_basic_mode(self, analyzed_request: Dict, session_id: str) -> ChatResponse:
        """기본 모드: 자율적 도구 선택 및 실행"""
        
        # 1. 과거 유사한 경험 검색
        similar_episodes = await self.episodic_memory.find_similar_episodes(
            analyzed_request["intent"], limit=3
        )
        
        # 2. 최적 도구 선택
        selected_tools = await self.reasoner.select_optimal_tools(
            analyzed_request["intent"],
            analyzed_request["entities"], 
            similar_episodes,
            self.tool_registry.get_all_tools()
        )
        
        # 3. 도구 실행
        execution_trace = []
        results = []
        
        for tool_config in selected_tools:
            tool_result = await self.executor.execute_tool(
                tool_config["name"],
                tool_config["parameters"],
                session_id
            )
            
            execution_trace.append({
                "tool": tool_config["name"],
                "parameters": tool_config["parameters"],
                "result": tool_result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if tool_result["success"]:
                results.append(tool_result["output"])
        
        # 4. 결과 합성
        final_response = await self._synthesize_basic_results(results, analyzed_request)
        
        return ChatResponse(
            response=final_response,
            session_id=session_id,
            execution_trace=execution_trace,
            metadata={
                "mode": "basic",
                "tools_used": len(selected_tools),
                "success_rate": sum(1 for t in execution_trace if t["result"]["success"]) / len(execution_trace) if execution_trace else 0
            }
        )
    
    async def _execute_step(self, step: Dict, session_id: str) -> Dict:
        """단일 단계 실행"""
        try:
            # 단계에서 지정된 도구 실행
            tool_result = await self.executor.execute_tool(
                step["tool"],
                step["parameters"],
                session_id
            )
            
            # 피드백 수집
            await self.feedback_collector.collect_step_feedback(
                session_id, step["step_id"], tool_result
            )
            
            return {
                "step_id": step["step_id"],
                "tool": step["tool"],
                "success": tool_result["success"],
                "output": tool_result.get("output"),
                "error": tool_result.get("error"),
                "execution_time": tool_result.get("execution_time", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "step_id": step["step_id"],
                "tool": step["tool"],
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _synthesize_results(self, results: List, execution_plan: Dict) -> str:
        """플로우 모드 결과 합성"""
        if not results:
            return "요청을 처리할 수 없었습니다. 다시 시도해 주세요."
        
        # 결과들을 논리적으로 조합
        if execution_plan["goal_type"] == "document_generation":
            return f"요청하신 문서 작업을 완료했습니다. {len(results)}개의 단계를 거쳐 처리되었습니다."
        elif execution_plan["goal_type"] == "data_processing":
            return f"데이터 처리가 완료되었습니다. 총 {len(results)}개의 작업이 수행되었습니다."
        elif execution_plan["goal_type"] == "communication":
            return f"메시지 전송이 완료되었습니다."
        else:
            return f"요청하신 작업을 완료했습니다. {len(results)}개의 단계가 성공적으로 처리되었습니다."
    
    async def _synthesize_basic_results(self, results: List, analyzed_request: Dict) -> str:
        """기본 모드 결과 합성"""
        if not results:
            return "요청을 처리할 수 없었습니다. 사용 가능한 도구로 처리할 수 없는 요청입니다."
        
        intent = analyzed_request.get("intent", "unknown")
        
        if "문서" in intent or "document" in intent.lower():
            return f"문서 관련 작업이 완료되었습니다. {len(results)}개의 도구를 사용하여 처리했습니다."
        elif "검색" in intent or "search" in intent.lower():
            return f"검색이 완료되었습니다. 요청하신 정보를 찾았습니다."
        elif "메시지" in intent or "message" in intent.lower():
            return f"메시지 전송이 완료되었습니다."
        else:
            return f"요청하신 '{intent}' 작업이 완료되었습니다."
    
    async def _store_execution_episode(self, session_id: str, request: ChatRequest, response: ChatResponse):
        """실행 에피소드를 메모리에 저장"""
        episode_data = {
            "session_id": session_id,
            "user_id": request.user_id,
            "mode": request.mode,
            "original_request": request.message,
            "response": response.response,
            "execution_trace": response.execution_trace,
            "success": response.metadata.get("success_rate", 0) > 0.5,
            "timestamp": datetime.utcnow().isoformat(),
            "tools_used": [trace.get("tool") for trace in response.execution_trace if trace.get("tool")],
            "performance_metrics": {
                "response_length": len(response.response),
                "steps_count": len(response.execution_trace),
                "success_rate": response.metadata.get("success_rate", 0)
            }
        }
        
        await self.episodic_memory.store_episode(episode_data)

# 전역 백엔드 인스턴스
backend = AgenticAIBackend()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """메인 채팅 엔드포인트"""
    return await backend.process_request(request)

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "working_memory": await backend.working_memory.health_check(),
            "episodic_memory": await backend.episodic_memory.health_check(),
            "semantic_memory": await backend.semantic_memory.health_check(),
            "mcp_connector": await backend.mcp_connector.health_check()
        }
    }

@app.post("/feedback")
async def submit_feedback(session_id: str, rating: int, comments: str = ""):
    """사용자 피드백 수집"""
    feedback_data = {
        "session_id": session_id,
        "rating": rating,
        "comments": comments,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await backend.feedback_collector.collect_user_feedback(feedback_data)
    return {"status": "feedback_received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)