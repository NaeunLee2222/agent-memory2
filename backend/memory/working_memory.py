import redis
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class WorkingMemoryManager:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.default_ttl = 3600  # 1시간
        
    async def store_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """세션 컨텍스트 저장"""
        try:
            key = f"session:{session_id}"
            value = json.dumps(context, default=str)
            self.redis_client.setex(key, self.default_ttl, value)
            return True
        except Exception as e:
            print(f"Error storing context: {e}")
            return False
    
    async def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 컨텍스트 조회"""
        try:
            key = f"session:{session_id}"
            value = self.redis_client.get(key)
            if value:
                return json.loads(value.decode('utf-8'))
            return None
        except Exception as e:
            print(f"Error getting context: {e}")
            return None
    
    async def update_step_result(self, session_id: str, step_id: str, result: Dict[str, Any]) -> bool:
        """단계 실행 결과 업데이트"""
        try:
            context = await self.get_context(session_id)
            if context:
                if 'step_results' not in context:
                    context['step_results'] = {}
                context['step_results'][step_id] = result
                return await self.store_context(session_id, context)
            return False
        except Exception as e:
            print(f"Error updating step result: {e}")
            return False
    
    async def add_tool_execution(self, session_id: str, tool_name: str, result: Dict[str, Any]) -> bool:
        """도구 실행 결과 추가"""
        try:
            context = await self.get_context(session_id)
            if context:
                if 'tool_executions' not in context:
                    context['tool_executions'] = []
                context['tool_executions'].append({
                    'tool_name': tool_name,
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat()
                })
                return await self.store_context(session_id, context)
            return False
        except Exception as e:
            print(f"Error adding tool execution: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            self.redis_client.ping()
            return {"status": "healthy", "component": "working_memory"}
        except Exception as e:
            return {"status": "unhealthy", "component": "working_memory", "error": str(e)}