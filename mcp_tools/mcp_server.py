from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
import logging
import uvicorn

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

# Mock 도구 함수들
async def create_rfq_cover(**kwargs):
    company_name = kwargs.get('company_name', 'Unknown Company')
    project_title = kwargs.get('project_title', 'Untitled Project')
    deadline = kwargs.get('deadline', 'TBD')
    
    content = f"""
=== RFQ 커버 페이지 ===
회사명: {company_name}
프로젝트: {project_title}
마감일: {deadline}

생성일: 2025-01-20
"""
    return {"content": content, "format": "text", "status": "completed"}

async def combine_rfq_cover(**kwargs):
    documents = kwargs.get('documents', ['cover', 'content'])
    output_format = kwargs.get('output_format', 'pdf')
    
    combined_content = f"결합된 RFQ 문서 ({output_format})\n"
    for doc in documents:
        combined_content += f"- {doc} 섹션 포함\n"
    
    return {"content": combined_content, "format": output_format, "sections": documents, "status": "completed"}

async def modify_tbe_content(**kwargs):
    content = kwargs.get('content', '')
    modifications = kwargs.get('modifications', ['기본 수정사항 적용'])
    
    modified_content = f"수정된 콘텐츠:\n{content}\n\n적용된 수정사항:\n"
    for mod in modifications:
        modified_content += f"- {mod}\n"
    
    return {"original_content": content, "modified_content": modified_content, "modifications_applied": modifications, "status": "completed"}

async def send_slack_message(**kwargs):
    channel = kwargs.get('channel', '#general')
    message = kwargs.get('message', '')
    mentions = kwargs.get('mentions', [])
    
    formatted_message = message
    if mentions:
        mention_str = " ".join([f"@{user}" for user in mentions])
        formatted_message = f"{mention_str} {message}"
    
    return {"channel": channel, "message": formatted_message, "mentions": mentions, "status": "sent"}

async def search_database(**kwargs):
    query = kwargs.get('query', '')
    filters = kwargs.get('filters', {})
    limit = kwargs.get('limit', 10)
    
    results = [
        {"id": i, "title": f"검색 결과 {i}", "content": f"'{query}' 관련 내용 {i}"}
        for i in range(1, min(limit + 1, 6))
    ]
    
    return {"query": query, "filters": filters, "results": results, "total_count": len(results), "status": "completed"}

async def analyze_text(**kwargs):
    text = kwargs.get('text', '')
    analysis_type = kwargs.get('analysis_type', 'general')
    
    analysis_result = {
        "text_length": len(text),
        "word_count": len(text.split()) if text else 0,
        "analysis_type": analysis_type,
        "sentiment": "neutral",
        "key_topics": ["분석", "텍스트", "처리"],
        "confidence": 0.85
    }
    
    if analysis_type == "document_requirements":
        analysis_result.update({
            "document_type": "RFQ" if "rfq" in text.lower() else "general",
            "required_sections": ["제목", "내용", "마감일"],
            "complexity": "medium"
        })
    
    return analysis_result

async def generate_content(**kwargs):
    template = kwargs.get('template', '')
    data = kwargs.get('data', {})
    
    if template == "rfq_template":
        content = f"""
=== RFQ 본문 ===
프로젝트 개요: {data.get('project', '프로젝트 설명')}
요구사항: {data.get('requirements', '상세 요구사항')}
제출 기한: {data.get('deadline', 'TBD')}

자동 생성된 콘텐츠입니다.
"""
    else:
        content = f"템플릿 '{template}'을 사용하여 생성된 콘텐츠"
    
    return {"template": template, "generated_content": content, "data_used": data, "status": "completed"}

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
            execution_time=1.0,
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
    uvicorn.run(app, host="0.0.0.0", port=3000)