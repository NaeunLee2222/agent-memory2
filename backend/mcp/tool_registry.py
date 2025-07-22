from typing import Dict, List, Optional, Any
import json
from datetime import datetime

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.tool_categories = {}
        self.tool_performance = {}
        
    def register_tool(self, tool_config: Dict[str, Any]):
        """도구 등록"""
        tool_name = tool_config["name"]
        self.tools[tool_name] = {
            **tool_config,
            "registered_at": datetime.utcnow().isoformat(),
            "usage_count": 0,
            "success_rate": 1.0
        }
        
        # 카테고리별 분류
        category = tool_config.get("category", "general")
        if category not in self.tool_categories:
            self.tool_categories[category] = []
        self.tool_categories[category].append(tool_name)
        
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """도구 정보 조회"""
        return self.tools.get(tool_name)
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 도구 조회"""
        tool_names = self.tool_categories.get(category, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """모든 도구 조회"""
        return list(self.tools.values())
    
    def update_tool_performance(self, tool_name: str, success: bool, execution_time: float):
        """도구 성능 업데이트"""
        if tool_name not in self.tools:
            return
        
        tool = self.tools[tool_name]
        tool["usage_count"] += 1
        
        # 성공률 업데이트 (지수 이동 평균)
        current_success_rate = tool["success_rate"]
        alpha = 0.1  # 학습률
        new_success_rate = (1 - alpha) * current_success_rate + alpha * (1.0 if success else 0.0)
        tool["success_rate"] = new_success_rate
        
        # 성능 메트릭 저장
        if tool_name not in self.tool_performance:
            self.tool_performance[tool_name] = {
                "execution_times": [],
                "recent_successes": []
            }
        
        perf = self.tool_performance[tool_name]
        perf["execution_times"].append(execution_time)
        perf["recent_successes"].append(success)
        
        # 최근 100개 기록만 유지
        if len(perf["execution_times"]) > 100:
            perf["execution_times"] = perf["execution_times"][-100:]
            perf["recent_successes"] = perf["recent_successes"][-100:]
    
    def get_tool_statistics(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """도구 통계 정보"""
        if tool_name not in self.tools:
            return None
        
        tool = self.tools[tool_name]
        perf = self.tool_performance.get(tool_name, {})
        
        stats = {
            "name": tool_name,
            "usage_count": tool["usage_count"],
            "success_rate": tool["success_rate"],
            "category": tool.get("category", "general")
        }
        
        if "execution_times" in perf and perf["execution_times"]:
            import statistics
            stats["avg_execution_time"] = statistics.mean(perf["execution_times"])
            stats["median_execution_time"] = statistics.median(perf["execution_times"])
        
        return stats