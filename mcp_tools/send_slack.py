import asyncio
import time
import random
from typing import Dict, Any
from ..models.schemas import MCPToolResult, MCPToolType


class SendSlackTool:
    def __init__(self):
        self.tool_type = MCPToolType.SEND_SLACK
        self.performance_stats = {
            "avg_response_time": 0.8,
            "success_rate": 0.92,
            "message_limit": 4000,  # characters
            "api_rate_limit": 50,  # per minute
        }
        self.api_calls_count = 0
        self.last_reset_time = time.time()

    async def execute(
        self, parameters: Dict[str, Any], context: Dict[str, Any] = None
    ) -> MCPToolResult:
        """Slack 메시지 전송 도구 실행"""
        start_time = time.time()

        message = parameters.get("message", "")
        channel = parameters.get("channel", "#general")
        user = parameters.get("user", None)

        try:
            # API 호출 제한 확인
            current_time = time.time()
            if current_time - self.last_reset_time > 60:  # 1분 경과
                self.api_calls_count = 0
                self.last_reset_time = current_time

            if self.api_calls_count >= self.performance_stats["api_rate_limit"]:
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error="API rate limit exceeded",
                )

            # 메시지 길이 제한 확인
            if len(message) > self.performance_stats["message_limit"]:
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error=f"Message too long: {len(message)} > {self.performance_stats['message_limit']}",
                )

            # 실행 시간 시뮬레이션
            execution_time = 0.8 + random.uniform(0, 0.4)
            await asyncio.sleep(execution_time)

            # 성공/실패 시뮬레이션
            success = random.random() < self.performance_stats["success_rate"]
            self.api_calls_count += 1

            if success:
                result_data = {
                    "message": message,
                    "channel": channel,
                    "timestamp": current_time,
                    "message_id": f"slack_msg_{int(current_time * 1000)}",
                }

                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=True,
                    result=result_data,
                    execution_time=time.time() - start_time,
                )
            else:
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error="Slack API error - channel not found",
                )

        except Exception as e:
            return MCPToolResult(
                tool_type=self.tool_type,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                error=str(e),
            )

    def get_performance_stats(self) -> Dict[str, Any]:
        return {
            **self.performance_stats,
            "current_api_calls": self.api_calls_count,
            "time_until_reset": max(0, 60 - (time.time() - self.last_reset_time)),
        }
