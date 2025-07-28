from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging
import os
from dotenv import load_dotenv
import openai
from backend.mcp.connector import MCPConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic AI Platform", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

mcp_connector = MCPConnector()

# 전역 변수 추가
procedural_service = None

@app.on_event("startup")
async def startup_event():
    global procedural_service
    # # memory_service와 mcp_service 초기화 후
    # procedural_service = ProceduralMemoryService(memory_service, mcp_service)


class ChatRequest(BaseModel):
    message: str
    user_id: str
    mode: str = "basic"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    execution_trace: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

@app.get("/")
async def root():
    return {
        "message": "Agentic AI Platform API - WORKING!", 
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Agentic AI Backend - WORKING VERSION"
    }



async def get_tool_plan_from_llm(user_message, available_tools):
    """
    LLM에게 질의와 tool 목록을 주고, 사용할 tool plan을 JSON으로 받는다.
    """
    available_tools = await mcp_connector.get_available_tools()
    print("available_tools:", available_tools)

    if not isinstance(available_tools, list):
        available_tools = []

    tool_names = [tool['name'] for tool in available_tools if isinstance(tool, dict) and 'name' in tool]
    tool_descs = "\n".join([f"- {tool['name']}: {tool.get('description','')}" for tool in available_tools if isinstance(tool, dict) and 'name' in tool])

    
    prompt = f"""
너는 사용자의 요청을 MCP tool을 조합해 해결하는 AI 플래너야.
아래는 사용 가능한 tool 목록이야:
{tool_descs}

사용자 요청:
\"\"\"{user_message}\"\"\"

아래 형식의 JSON으로, 순차적으로 실행할 plan을 만들어줘.
[
  {{"tool": "tool_name", "parameters": {{...}} }},
  ...
]
반드시 tool_name은 위 목록에서만 선택하고, parameters는 각 tool에 맞게 예시로 채워줘.
"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512
    )
    # LLM이 반환한 JSON 부분만 추출
    import json, re
    content = response.choices[0].message.content
    # JSON 추출 (가장 먼저 나오는 대괄호 블록)
    if not isinstance(content, str):
        content = str(content)
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if match:
        plan_json = match.group(0)
        try:
            plan = json.loads(plan_json)
            return plan
        except Exception as e:
            print("LLM JSON 파싱 오류:", e)
    # fallback: analyze_text만 실행
    return [{"tool": "analyze_text", "parameters": {"text": user_message, "analysis_type": "general"}}]


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    logger.info(f"Chat request received: {request.message[:50]}...")
    session_id = request.session_id or str(uuid.uuid4())

    # 1. MCP에서 사용 가능한 툴 목록 조회
    raw_tools = await mcp_connector.get_available_tools()
    logger.info(f"Raw tools: {raw_tools}")

    # 문자열 리스트라면 dict로 변환
    if isinstance(raw_tools, list):
        if all(isinstance(t, str) for t in raw_tools):
            available_tools = [{"name": t} for t in raw_tools]
        elif all(isinstance(t, dict) and "name" in t for t in raw_tools):
            available_tools = raw_tools
        else:
            raise HTTPException(status_code=500, detail="MCP에서 반환된 도구 형식이 올바르지 않습니다.")
    else:
        raise HTTPException(status_code=500, detail="도구 목록 응답 형식 오류")

    tool_names = [tool["name"] for tool in available_tools]

    # 2. LLM에게 플랜 생성 요청
    plan = await get_tool_plan_from_llm(request.message, available_tools)

    # 3. 플랜 실행
    execution_trace = []
    for idx, step in enumerate(plan, 1):
        tool_name = step["tool"]
        parameters = step.get("parameters", {})
        if tool_name not in tool_names:
            execution_trace.append({
                "step_id": idx,
                "tool": tool_name,
                "parameters": parameters,
                "success": False,
                "output": f"Tool '{tool_name}' is not available.",
                "timestamp": datetime.utcnow().isoformat()
            })
            continue
        result = await mcp_connector.call_tool(tool_name, parameters)
        if result is None or not isinstance(result, dict):
            result = {"success": False, "error": "도구 실행 오류 또는 응답 없음"}
        execution_trace.append({
            "step_id": idx,
            "tool": tool_name,
            "parameters": parameters,
            "success": result.get("success", False),
            "output": result.get("output", result.get("error", "")),
            "timestamp": datetime.utcnow().isoformat()
        })

    # 4. 응답 생성
    response_text = f"총 {len(execution_trace)}개의 도구를 순차적으로 실행했습니다.\n"
    for step in execution_trace:
        response_text += f"- {step['tool']}: {step['output']}\n"

    return ChatResponse(
        response=response_text,
        session_id=session_id,
        execution_trace=execution_trace,
        metadata={
            "mode": request.mode,
            "tools_used": len(execution_trace),
            "success_rate": sum(1 for s in execution_trace if s['success']) / len(execution_trace) if execution_trace else 0.0,
            "processing_time": f"{len(execution_trace) * 1.2:.1f}초 (예상)",
            "workflow_type": "llm_dynamic_plan"
        }
    )



@app.post("/feedback")
async def submit_feedback(session_id: str, rating: int, comments: str = ""):
    logger.info(f"Feedback received: session={session_id}, rating={rating}")
    return {
        "status": "feedback_received", 
        "message": "피드백이 성공적으로 수집되었습니다.",
        "session_id": session_id,
        "rating": rating,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Enhanced Agentic AI Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")