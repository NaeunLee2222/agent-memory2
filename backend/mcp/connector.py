import asyncio
import json
import httpx
from typing import Dict, Any, Optional
import logging
from datetime import datetime

class MCPConnector:
    def __init__(self):
        self.base_url = "http://localhost:3000"  # MCP 서버 주소
        self.timeout = 30.0
        self.logger = logging.getLogger(__name__)
        
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 도구 호출"""
        start_time = datetime.utcnow()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "tool": tool_name,
                    "parameters": parameters,
                    "timestamp": start_time.isoformat()
                }
                
                response = await client.post(
                    f"{self.base_url}/tools/{tool_name}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                result = response.json()
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                return {
                    "output": result.get("result", ""),
                    "success": True,
                    "execution_time": execution_time,
                    "metadata": result.get("metadata", {})
                }
                
        except httpx.TimeoutException:
            self.logger.error(f"Tool {tool_name} timeout after {self.timeout}s")
            return {
                "error": f"Tool execution timeout: {tool_name}",
                "success": False,
                "execution_time": self.timeout
            }
            
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error calling tool {tool_name}: {str(e)}")
            return {
                "error": f"HTTP error: {str(e)}",
                "success": False,
                "execution_time": (datetime.utcnow() - start_time).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(f"Unexpected error calling tool {tool_name}: {str(e)}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "success": False,
                "execution_time": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """MCP 서버 헬스 체크"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return {"status": "healthy", "details": response.json()}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/tools")
                response.raise_for_status()
                return response.json().get("tools", [])
        except Exception as e:
            self.logger.error(f"Failed to get available tools: {str(e)}")
            return []