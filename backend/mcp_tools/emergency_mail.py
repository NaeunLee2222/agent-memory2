import asyncio
import time
import random
from typing import Dict, Any
from ..models.schemas import MCPToolResult, MCPToolType


class EmergencyMailDataGeneratorTool:
    def __init__(self):
        self.tool_type = MCPToolType.EMERGENCY_MAIL
        self.performance_stats = {
            "avg_response_time": 0.9,
            "success_rate": 0.98,
            "data_templates": {
                "she_emergency": {
                    "priority": "high",
                    "recipients": ["safety@company.com", "manager@company.com"],
                    "template": "SHE 비상 상황 발생",
                },
                "system_emergency": {
                    "priority": "critical",
                    "recipients": ["ops@company.com", "admin@company.com"],
                    "template": "시스템 비상 상황 발생",
                },
            },
        }

    async def execute(
        self, parameters: Dict[str, Any], context: Dict[str, Any] = None
    ) -> MCPToolResult:
        """비상 메일 데이터 생성 도구 실행"""
        start_time = time.time()

        emergency_type = parameters.get("type", "general")
        severity = parameters.get("severity", "medium")
        location = parameters.get("location", "unknown")
        description = parameters.get("description", "")

        try:
            # 실행 시간 시뮬레이션
            execution_time = 0.9 + random.uniform(0, 0.2)
            await asyncio.sleep(execution_time)

            # 비상 유형별 데이터 생성
            template_data = self.performance_stats["data_templates"].get(
                emergency_type,
                self.performance_stats["data_templates"]["system_emergency"],
            )

            # 심각도에 따른 우선순위 조정
            priority_map = {"low": "medium", "medium": "high", "high": "critical"}
            final_priority = priority_map.get(severity, "high")

            # 수신자 목록 생성
            recipients = template_data["recipients"].copy()
            if final_priority == "critical":
                recipients.extend(["ceo@company.com", "emergency@company.com"])

            # 성공/실패 시뮬레이션
            success = random.random() < self.performance_stats["success_rate"]

            if success:
                result_data = {
                    "emergency_id": f"EMG_{int(time.time() * 1000)}",
                    "type": emergency_type,
                    "priority": final_priority,
                    "severity": severity,
                    "location": location,
                    "description": description,
                    "recipients": recipients,
                    "template": template_data["template"],
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "escalation_required": final_priority == "critical",
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
                    error="Emergency data generation failed - template not found",
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
        return self.performance_stats.copy()
