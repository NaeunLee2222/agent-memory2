from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
import logging
from tools.document_tools import create_rfq_cover, combine_rfq_cover, modify_tbe_content
from tools.communication_tools import send_slack_message
from tools.data_tools import search_database
from tools.utility_tools import analyze_text, generate_content

app = FastAPI(title="MCP Tools Server")

class ToolRequest(BaseModel):
    tool: str
    parameters: Dict[str, Any]
    timestamp: str

class ToolResponse(BaseModel):
    result: Any
    success: bool
    execution_time: float
    metadata: Dict[str, Any] = {}

# 도구 매핑
TOOLS_MAP = {
    "create_rfq_cover": create_rfq_cover,
    "combine_rfq_cover": combine_rfq_cover,
    "modify_tbe_content": modify_tbe_content,
    "send_slack_message": send_slack_message,
    "search_database": search_database,
    "analyze_text": analyze_text,
    "generate_content": generate_content
}

@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: ToolRequest):
    """MCP 도구 실행"""
    try:
        if tool_name not in TOOLS_MAP:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        tool_function = TOOLS_MAP[tool_name]
        result = await tool_function(**request.parameters)
        
        return ToolResponse(
            result=result,
            success=True,
            execution_time=1.0,  # 실제 측정 필요
            metadata={"tool": tool_name}
        )
        
    except Exception as e:
        logging.error(f"Tool execution error: {str(e)}")
        return ToolResponse(
            result=None,
            success=False,
            execution_time=0.0,
            metadata={"error": str(e)}
        )

@app.get("/tools")
async def list_tools():
    """사용 가능한 도구 목록"""
    return {
        "tools": list(TOOLS_MAP.keys()),
        "count": len(TOOLS_MAP)
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "tools_available": len(TOOLS_MAP)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)