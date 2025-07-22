import asyncio
from typing import Dict, Any, List, Type
from ..models.schemas import MCPToolCall, MCPToolResult, MCPToolType
from ..mcp_tools.search_db import SearchDBTool
from ..mcp_tools.send_slack import SendSlackTool
from ..mcp_tools.generate_msg import GenerateMessageTool
from ..mcp_tools.emergency_mail import EmergencyMailDataGeneratorTool


class MCPService:
    def __init__(self):
        self.tools = {
            MCPToolType.SEARCH_DB: SearchDBTool(),
            MCPToolType.SEND_SLACK: SendSlackTool(),
            MCPToolType.GENERATE_MSG: GenerateMessageTool(),
            MCPToolType.EMERGENCY_MAIL: EmergencyMailDataGeneratorTool(),
        }
        self.performance_history = []

    async def execute_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """MCP 도구 실행"""
        if tool_call.tool_type not in self.tools:
            return MCPToolResult(
                tool_type=tool_call.tool_type,
                success=False,
                result=None,
                execution_time=0,
                error=f"Tool {tool_call.tool_type} not found",
            )

        tool = self.tools[tool_call.tool_type]
        result = await tool.execute(tool_call.parameters, tool_call.context)

        # 성능 히스토리 기록
        self.performance_history.append(
            {
                "tool_type": tool_call.tool_type,
                "execution_time": result.execution_time,
                "success": result.success,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        # 히스토리 크기 제한
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]

        return result

    async def execute_workflow(
        self, tool_calls: List[MCPToolCall]
    ) -> List[MCPToolResult]:
        """워크플로우 실행 (도구 체인)"""
        results = []

        for tool_call in tool_calls:
            # 이전 결과를 다음 도구의 컨텍스트에 포함
            if results:
                tool_call.context = tool_call.context or {}
                tool_call.context["previous_results"] = [
                    r.result for r in results if r.success
                ]

            result = await self.execute_tool(tool_call)
            results.append(result)

            # 실패 시 워크플로우 중단 (옵션)
            if not result.success:
                break

        return results

    def get_tool_performance_stats(self, tool_type: MCPToolType) -> Dict[str, Any]:
        """특정 도구의 성능 통계 반환"""
        if tool_type not in self.tools:
            return {}

        tool_data = [h for h in self.performance_history if h["tool_type"] == tool_type]

        if not tool_data:
            return self.tools[tool_type].get_performance_stats()

        success_count = sum(1 for d in tool_data if d["success"])
        avg_time = sum(d["execution_time"] for d in tool_data) / len(tool_data)

        return {
            **self.tools[tool_type].get_performance_stats(),
            "recent_success_rate": success_count / len(tool_data),
            "recent_avg_time": avg_time,
            "usage_count": len(tool_data),
        }

    def get_all_performance_stats(self) -> Dict[MCPToolType, Dict[str, Any]]:
        """모든 도구의 성능 통계 반환"""
        return {
            tool_type: self.get_tool_performance_stats(tool_type)
            for tool_type in self.tools.keys()
        }

    def suggest_optimal_tool_combination(
        self, task_description: str
    ) -> List[MCPToolType]:
        """작업 설명을 바탕으로 최적 도구 조합 제안"""
        # 간단한 키워드 기반 매칭 (실제로는 더 정교한 NLP 필요)
        keywords = task_description.lower()

        suggested_tools = []

        if any(word in keywords for word in ["메시지", "생성", "작성"]):
            suggested_tools.append(MCPToolType.GENERATE_MSG)

        if any(word in keywords for word in ["slack", "알림", "전송", "발송"]):
            suggested_tools.append(MCPToolType.SEND_SLACK)

        return suggested_tools
