from typing import Dict, Any, Optional
import asyncio
import json
from datetime import datetime
import logging

class AgenticExecutor:
    def __init__(self, mcp_connector, working_memory):
        self.mcp_connector = mcp_connector
        self.working_memory = working_memory
        self.logger = logging.getLogger(__name__)
        
    async def execute_tool(self, tool_name: str, parameters: Dict, session_id: str) -> Dict:
        """MCP 도구 실행"""
        start_time = datetime.utcnow()
        
        try:
            # Working Memory에서 현재 컨텍스트 조회
            context = await self.working_memory.get_context(session_id)
            
            # 도구 실행 전 파라미터 보강
            enhanced_parameters = await self._enhance_parameters(
                parameters, context, tool_name
            )
            
            # MCP 도구 호출
            result = await self.mcp_connector.call_tool(
                tool_name, enhanced_parameters
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # 실행 결과 처리
            processed_result = {
                "success": True,
                "output": result.get("output", ""),
                "execution_time": execution_time,
                "tool_name": tool_name,
                "parameters_used": enhanced_parameters,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Working Memory 업데이트
            await self.working_memory.add_tool_execution(
                session_id, tool_name, processed_result
            )
            
            return processed_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(f"Tool execution failed: {tool_name} - {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "tool_name": tool_name,
                "parameters_used": parameters,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _enhance_parameters(self, parameters: Dict, context: Dict, tool_name: str) -> Dict:
        """컨텍스트 정보를 활용하여 파라미터 보강"""
        enhanced = parameters.copy()
        
        # 사용자 정보 자동 추가
        if "user_id" not in enhanced and "user_id" in context:
            enhanced["user_id"] = context["user_id"]
        
        # 도구별 특수 파라미터 처리
        if tool_name == "create_rfq_cover":
            # RFQ 커버 생성 시 기본값 제공
            if "company_name" not in enhanced:
                enhanced["company_name"] = context.get("default_company", "Unknown Company")
            if "deadline" not in enhanced:
                enhanced["deadline"] = "TBD"
                
        elif tool_name == "send_slack_message":
            # 슬랙 메시지 전송 시 채널 기본값
            if "channel" not in enhanced:
                enhanced["channel"] = "#general"
            if "mentions" not in enhanced:
                enhanced["mentions"] = []
                
        elif tool_name == "search_database":
            # 데이터베이스 검색 시 기본 필터
            if "filters" not in enhanced:
                enhanced["filters"] = {}
            if "limit" not in enhanced:
                enhanced["limit"] = 10
        
        return enhanced
    
    async def execute_parallel_tools(self, tool_configs: list, session_id: str) -> list:
        """여러 도구를 병렬로 실행"""
        tasks = []
        for config in tool_configs:
            task = self.execute_tool(
                config["name"], 
                config["parameters"], 
                session_id
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "tool_name": tool_configs[i]["name"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                processed_results.append(result)
        
        return processed_results