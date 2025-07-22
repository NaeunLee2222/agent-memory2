import asyncio
import time
import random
from typing import Dict, Any
from openai import OpenAI
from ..models.schemas import MCPToolResult, MCPToolType
from ..utils.config import config


class GenerateMessageTool:
    def __init__(self):
        self.tool_type = MCPToolType.GENERATE_MSG
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.performance_stats = {
            "avg_response_time": 2.1,
            "success_rate": 0.94,
            "template_cache": {},
        }

    async def execute(
        self, parameters: Dict[str, Any], context: Dict[str, Any] = None
    ) -> MCPToolResult:
        """메시지 생성 도구 실행"""
        start_time = time.time()

        message_type = parameters.get("type", "general")
        content = parameters.get("content", "")
        style = parameters.get(
            "style", "professional"
        )  # professional, casual, technical
        length = parameters.get("length", "medium")  # short, medium, long

        try:
            # 템플릿 캐싱 최적화 시뮬레이션
            cache_key = f"{message_type}_{style}_{length}"
            if cache_key in self.performance_stats["template_cache"]:
                execution_time = 1.1 + random.uniform(0, 0.2)  # 캐시 적용으로 빠름
            else:
                execution_time = 2.1 + random.uniform(0, 0.5)  # 새로 생성
                self.performance_stats["template_cache"][cache_key] = True

            await asyncio.sleep(execution_time)

            # 스타일별 메시지 생성 로직
            if style == "professional":
                generated_message = (
                    f"안녕하세요,\n\n{content}에 대해 알려드립니다.\n\n감사합니다."
                )
            elif style == "casual":
                generated_message = f"안녕! {content} 관련해서 알려줄게 😊"
            elif style == "technical":
                generated_message = f"[시스템 알림] {content}\n\n세부 정보:\n- 타임스탬프: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                generated_message = content

            # 길이 조정
            if length == "short":
                generated_message = (
                    generated_message[:100] + "..."
                    if len(generated_message) > 100
                    else generated_message
                )
            elif length == "long":
                generated_message += (
                    "\n\n추가적으로 필요한 정보가 있으시면 언제든 문의해 주세요."
                )

            # 성공/실패 시뮬레이션
            success = random.random() < self.performance_stats["success_rate"]

            if success:
                result_data = {
                    "generated_message": generated_message,
                    "style": style,
                    "length": length,
                    "word_count": len(generated_message.split()),
                    "cached": cache_key in self.performance_stats["template_cache"],
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
                    error="Message generation failed - content policy violation",
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
            "cached_templates": len(self.performance_stats["template_cache"]),
        }
