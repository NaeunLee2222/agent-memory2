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
from backend.services.pattern_learning_service import PatternLearningService
from backend.services.tool_analytics_service import ToolAnalyticsService
from backend.services.verification_service import VerificationService
from backend.services.scenario_test_service import ScenarioTestService
from backend.memory.procedural_memory import ProceduralMemoryManager
from backend.database.memory_database import MemoryDatabase
from backend.models.verification_models import ScenarioType

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

# Enhanced services
memory_database = MemoryDatabase()
pattern_learning_service = PatternLearningService(memory_database)
tool_analytics_service = ToolAnalyticsService(memory_database)
verification_service = VerificationService(memory_database)
scenario_test_service = ScenarioTestService(verification_service, mcp_connector)
procedural_memory = ProceduralMemoryManager(
    pattern_learning_service=pattern_learning_service,
    tool_analytics_service=tool_analytics_service
)

@app.on_event("startup")
async def startup_event():
    global pattern_learning_service, tool_analytics_service, verification_service, scenario_test_service, procedural_memory
    await memory_database.initialize()
    await pattern_learning_service.initialize()
    await tool_analytics_service.initialize()
    await verification_service.initialize()
    logger.info("Enhanced Agentic AI Platform initialized with pattern learning, verification, and scenario testing")


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

    # 2.5. Check for pattern suggestions if in flow mode
    pattern_suggestion = None
    if request.mode == "flow":
        pattern_suggestion = await procedural_memory.suggest_workflow_optimization(
            user_input=request.message,
            user_id=request.user_id,
            context={"mode": request.mode, "session_id": session_id}
        )

    # 3. 플랜 실행
    start_time = datetime.now()
    execution_trace = []
    for idx, step in enumerate(plan, 1):
        tool_name = step["tool"]
        parameters = step.get("parameters", {})
        step_start = datetime.now()
        
        if tool_name not in tool_names:
            execution_trace.append({
                "step_id": idx,
                "tool": tool_name,
                "parameters": parameters,
                "success": False,
                "output": f"Tool '{tool_name}' is not available.",
                "execution_time": 0.0,
                "timestamp": datetime.now().isoformat()
            })
            continue
            
        result = await mcp_connector.call_tool(tool_name, parameters)
        if result is None or not isinstance(result, dict):
            result = {"success": False, "error": "도구 실행 오류 또는 응답 없음"}
            
        step_time = (datetime.now() - step_start).total_seconds()
        execution_trace.append({
            "step_id": idx,
            "tool": tool_name,
            "parameters": parameters,
            "success": result.get("success", False),
            "output": result.get("output", result.get("error", "")),
            "execution_time": step_time,
            "timestamp": datetime.now().isoformat()
        })

    total_execution_time = (datetime.now() - start_time).total_seconds()
    overall_success = all(step.get('success', False) for step in execution_trace)

    # 3.5. Track execution for pattern learning
    if request.mode == "flow":
        pattern_id = await procedural_memory.track_workflow_execution(
            session_id=session_id,
            user_id=request.user_id,
            execution_trace=execution_trace,
            success=overall_success,
            total_execution_time=total_execution_time,
            context={"mode": request.mode, "user_input": request.message}
        )
    
    # 3.6. Track verification metrics
    scenario_type = ScenarioType.FLOW_MODE_PATTERN_LEARNING if request.mode == "flow" else ScenarioType.BASIC_MODE_TOOL_SELECTION
    success_rate = sum(1 for s in execution_trace if s['success']) / len(execution_trace) if execution_trace else 0.0
    
    await verification_service.track_execution(
        session_id=session_id,
        user_id=request.user_id,
        scenario_type=scenario_type,
        execution_trace=execution_trace,
        total_execution_time=total_execution_time,
        success_rate=success_rate,
        context={"mode": request.mode, "user_input": request.message, "tools_available": tool_names},
        pattern_suggestion=pattern_suggestion
    )

    # 4. 응답 생성
    response_text = f"총 {len(execution_trace)}개의 도구를 순차적으로 실행했습니다.\n"
    for step in execution_trace:
        response_text += f"- {step['tool']}: {step['output']}\n"
    
    if pattern_suggestion:
        response_text += f"\n💡 학습된 패턴 제안: {pattern_suggestion['pattern_name']} (신뢰도: {pattern_suggestion['confidence_score']:.1%})"

    return ChatResponse(
        response=response_text,
        session_id=session_id,
        execution_trace=execution_trace,
        metadata={
            "mode": request.mode,
            "tools_used": len(execution_trace),
            "success_rate": sum(1 for s in execution_trace if s['success']) / len(execution_trace) if execution_trace else 0.0,
            "processing_time": f"{total_execution_time:.1f}초",
            "workflow_type": "enhanced_pattern_learning",
            "pattern_suggestion": pattern_suggestion,
            "overall_success": overall_success
        }
    )



class FeedbackRequest(BaseModel):
    session_id: str
    rating: int
    comments: str = ""
    pattern_id: Optional[str] = None
    suggestion_accepted: Optional[bool] = None
    user_id: Optional[str] = None

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    logger.info(f"Feedback received: session={request.session_id}, rating={request.rating}")
    
    # Enhanced feedback processing
    if request.pattern_id and request.suggestion_accepted is not None:
        await pattern_learning_service.submit_pattern_feedback(
            suggestion_id="",
            pattern_id=request.pattern_id,
            accepted=request.suggestion_accepted,
            rating=request.rating
        )
    
    # Track verification feedback if user_id provided
    if request.user_id:
        # Find matching execution for this session to update with feedback
        user_feedback = {
            "rating": request.rating,
            "comments": request.comments,
            "suggestion_accepted": request.suggestion_accepted,
            "pattern_id": request.pattern_id
        }
        # Note: In a real implementation, we'd find and update the matching execution record
    
    return {
        "status": "feedback_received", 
        "message": "피드백이 성공적으로 수집되었습니다.",
        "session_id": request.session_id,
        "rating": request.rating,
        "timestamp": datetime.now().isoformat(),
        "pattern_learning_applied": request.pattern_id is not None
    }

# === New Pattern Learning & Analytics API Endpoints ===

@app.get("/patterns/learned")
async def get_learned_patterns(user_id: Optional[str] = None):
    """Get learned patterns for user or system-wide"""
    try:
        if user_id:
            patterns = await pattern_learning_service.get_user_patterns(user_id)
        else:
            patterns = list(pattern_learning_service.patterns.values())
        
        return {
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "name": p.name,
                    "description": p.description,
                    "success_rate": p.success_rate,
                    "confidence_score": p.confidence_score,
                    "total_executions": p.total_executions,
                    "average_execution_time": p.average_execution_time,
                    "steps": len(p.steps),
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat()
                }
                for p in patterns
            ],
            "total_patterns": len(patterns)
        }
    except Exception as e:
        logger.error(f"Error getting learned patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patterns/{pattern_id}")
async def get_pattern_details(pattern_id: str):
    """Get detailed information about a specific pattern"""
    try:
        pattern = await pattern_learning_service.get_pattern_by_id(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        return {
            "pattern_id": pattern.pattern_id,
            "name": pattern.name,
            "description": pattern.description,
            "pattern_type": pattern.pattern_type.value,
            "success_rate": pattern.success_rate,
            "confidence_score": pattern.confidence_score, 
            "total_executions": pattern.total_executions,
            "successful_executions": pattern.successful_executions,
            "average_execution_time": pattern.average_execution_time,
            "steps": [
                {
                    "step_id": step.step_id,
                    "tool_name": step.tool_name,
                    "parameters": step.parameters,
                    "execution_time": step.execution_time,
                    "success": step.success,
                    "output_summary": step.output_summary
                }
                for step in pattern.steps
            ],
            "context_tags": pattern.context_tags,
            "created_at": pattern.created_at.isoformat(),
            "updated_at": pattern.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting pattern details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/patterns")
async def get_pattern_analytics(user_id: Optional[str] = None):
    """Get pattern learning analytics"""
    try:
        metrics = await pattern_learning_service.get_learning_metrics(user_id)
        return {
            "analytics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting pattern analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/tools")
async def get_tool_analytics(user_id: Optional[str] = None):
    """Get tool usage analytics"""
    try:
        if user_id:
            analytics = await tool_analytics_service.get_user_tool_insights(user_id)
        else:
            analytics = await tool_analytics_service.get_system_analytics()
        
        return {
            "analytics": analytics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting tool analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/tools/{tool_name}")
async def get_tool_performance(tool_name: str, days: int = 7):
    """Get performance analytics for a specific tool"""
    try:
        performance = await tool_analytics_service.analyze_tool_performance(tool_name, days)
        return {
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting tool performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations/tools")
async def get_tool_recommendations(
    user_input: str,
    user_id: str,
    available_tools: str = "",  # Comma-separated tool names
    context: str = "{}"  # JSON string
):
    """Get tool recommendations based on user input and context"""
    try:
        import json
        context_dict = json.loads(context) if context != "{}" else {}
        tools_list = available_tools.split(",") if available_tools else []
        
        recommendations = await tool_analytics_service.get_tool_recommendations(
            user_input=user_input,
            user_id=user_id,
            context=context_dict,
            available_tools=tools_list
        )
        
        return {
            "recommendations": [
                {"tool_name": tool, "score": score}
                for tool, score in recommendations
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting tool recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/procedural")
async def get_procedural_analytics(user_id: Optional[str] = None):
    """Get procedural memory analytics"""
    try:
        analytics = await procedural_memory.get_procedural_analytics(user_id)
        return {
            "analytics": analytics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting procedural analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class PatternSuggestionRequest(BaseModel):
    user_input: str
    user_id: str
    context: Dict[str, Any] = {}

@app.post("/patterns/suggest")
async def suggest_pattern(request: PatternSuggestionRequest):
    """Get pattern suggestions for user input"""
    try:
        suggestion = await pattern_learning_service.suggest_pattern(
            user_input=request.user_input,
            user_id=request.user_id,
            session_id=str(uuid.uuid4()),
            context=request.context
        )
        
        if not suggestion:
            return {"suggestion": None, "message": "No suitable pattern found"}
        
        pattern = await pattern_learning_service.get_pattern_by_id(suggestion.pattern_id)
        
        return {
            "suggestion": {
                "suggestion_id": suggestion.suggestion_id,
                "pattern_id": suggestion.pattern_id,
                "confidence_score": suggestion.confidence_score,
                "pattern_details": {
                    "name": pattern.name if pattern else "Unknown",
                    "description": pattern.description if pattern else "",
                    "success_rate": pattern.success_rate if pattern else 0.0,
                    "steps": len(pattern.steps) if pattern else 0
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error suggesting pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Verification API Endpoints ===

@app.get("/verification/pattern-metrics/{user_id}")
async def get_pattern_verification_metrics(user_id: str):
    """Get pattern verification metrics for specific user"""
    try:
        metrics = await verification_service.get_pattern_verification_metrics(user_id)
        if not metrics:
            return {"metrics": None, "message": "No verification data found for user"}
        
        return {
            "metrics": {
                "scenario_id": metrics.scenario_id,
                "user_id": metrics.user_id,
                "total_executions": metrics.total_executions,
                "patterns_learned": metrics.patterns_learned,
                "pattern_learning_success_rate": metrics.pattern_learning_success_rate,
                "pattern_suggestion_accuracy": metrics.pattern_suggestion_accuracy,
                "baseline_avg_time": metrics.baseline_avg_time,
                "optimized_avg_time": metrics.optimized_avg_time,
                "time_improvement_percentage": metrics.time_improvement_percentage,
                "avg_pattern_confidence": metrics.avg_pattern_confidence,
                "pattern_adaptation_rate": metrics.pattern_adaptation_rate,
                "last_updated": metrics.last_updated.isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting pattern verification metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verification/tool-metrics/{user_id}")
async def get_tool_verification_metrics(user_id: str):
    """Get tool selection verification metrics for specific user"""
    try:
        metrics = await verification_service.get_tool_selection_verification_metrics(user_id)
        if not metrics:
            return {"metrics": None, "message": "No verification data found for user"}
        
        return {
            "metrics": {
                "scenario_id": metrics.scenario_id,
                "user_id": metrics.user_id,
                "total_requests": metrics.total_requests,
                "correct_tool_selections": metrics.correct_tool_selections,
                "intent_recognition_accuracy": metrics.intent_recognition_accuracy,
                "initial_accuracy": metrics.initial_accuracy,
                "current_accuracy": metrics.current_accuracy,
                "accuracy_improvement": metrics.accuracy_improvement,
                "initial_satisfaction": metrics.initial_satisfaction,
                "current_satisfaction": metrics.current_satisfaction,
                "satisfaction_improvement": metrics.satisfaction_improvement,
                "optimal_tool_selection_rate": metrics.optimal_tool_selection_rate,
                "last_updated": metrics.last_updated.isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting tool verification metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verification/comprehensive-report/{user_id}")
async def get_comprehensive_verification_report(user_id: str):
    """Get comprehensive verification report for specific user"""
    try:
        report = await verification_service.generate_comprehensive_report(user_id)
        
        return {
            "report": {
                "report_id": report.report_id,
                "user_id": report.user_id,
                "test_period": {
                    "start": report.test_period_start.isoformat(),
                    "end": report.test_period_end.isoformat()
                },
                "flow_mode_results": {
                    "patterns_learned": report.flow_mode_results.patterns_learned,
                    "pattern_suggestion_accuracy": report.flow_mode_results.pattern_suggestion_accuracy,
                    "time_improvement_percentage": report.flow_mode_results.time_improvement_percentage,
                    "avg_pattern_confidence": report.flow_mode_results.avg_pattern_confidence,
                    "pattern_adaptation_rate": report.flow_mode_results.pattern_adaptation_rate
                },
                "basic_mode_results": {
                    "intent_recognition_accuracy": report.basic_mode_results.intent_recognition_accuracy,
                    "accuracy_improvement": report.basic_mode_results.accuracy_improvement,
                    "satisfaction_improvement": report.basic_mode_results.satisfaction_improvement,
                    "optimal_tool_selection_rate": report.basic_mode_results.optimal_tool_selection_rate
                },
                "overall_metrics": {
                    "success_criteria_met": report.overall_success_criteria_met,
                    "total_success_criteria": report.total_success_criteria,
                    "overall_pass_rate": report.overall_pass_rate,
                    "total_executions": report.total_executions
                },
                "success_criteria": report.success_criteria,
                "key_insights": report.key_insights,
                "recommendations": report.recommendations,
                "generated_at": report.generated_at.isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verification/phase-analysis/{user_id}")
async def get_phase_based_analysis(user_id: str, scenario_type: str):
    """Get phase-based analysis for specific user and scenario"""
    try:
        if scenario_type not in ["1.1_flow_mode_pattern_learning", "1.2_basic_mode_tool_selection"]:
            raise HTTPException(status_code=400, detail="Invalid scenario type")
        
        scenario_enum = ScenarioType(scenario_type)
        analysis = await verification_service.get_phase_based_analysis(user_id, scenario_enum)
        
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting phase-based analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verification/dashboard")
async def get_verification_dashboard():
    """Get real-time verification dashboard data"""
    try:
        dashboard_data = await verification_service.get_real_time_dashboard_data()
        
        return {
            "dashboard": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting verification dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === Scenario Test API Endpoints ===

@app.get("/scenarios/list")
async def get_all_scenarios():
    """Get all available test scenarios"""
    try:
        scenarios = scenario_test_service.get_all_scenarios()
        return {
            "scenarios": scenarios,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scenarios/1.1/execute")
async def execute_scenario_11(user_id: str):
    """Execute Scenario 1.1: Flow Mode Pattern Learning"""
    try:
        result = await scenario_test_service.execute_scenario_11(user_id)
        return {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing scenario 1.1: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scenarios/1.2/execute")
async def execute_scenario_12(user_id: str):
    """Execute Scenario 1.2: Basic Mode Tool Selection"""
    try:
        result = await scenario_test_service.execute_scenario_12(user_id)
        return {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing scenario 1.2: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scenarios/{scenario_id}/status")
async def get_scenario_status(scenario_id: str, user_id: str):
    """Get scenario execution status"""
    try:
        if scenario_id not in ["1.1", "1.2"]:
            raise HTTPException(status_code=400, detail="Invalid scenario_id. Use '1.1' or '1.2'")
        
        status = await scenario_test_service.get_scenario_status(scenario_id, user_id)
        return {
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scenario status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ScenarioFeedbackRequest(BaseModel):
    scenario_id: str
    user_id: str
    rating: int
    comments: str = ""
    specific_feedback: Dict[str, Any] = {}

@app.post("/scenarios/feedback")
async def submit_scenario_feedback(request: ScenarioFeedbackRequest):
    """Submit feedback for scenario execution"""
    try:
        if request.scenario_id not in ["1.1", "1.2"]:
            raise HTTPException(status_code=400, detail="Invalid scenario_id. Use '1.1' or '1.2'")
        
        if not (1 <= request.rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        result = await scenario_test_service.process_scenario_feedback(
            scenario_id=request.scenario_id,
            user_id=request.user_id,
            feedback={
                "rating": request.rating,
                "comments": request.comments,
                "specific_feedback": request.specific_feedback
            }
        )
        
        return {
            "result": result,
            "message": "피드백이 성공적으로 처리되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing scenario feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scenarios/{scenario_id}/comparison")
async def get_scenario_comparison(scenario_id: str, user_id: str):
    """Get before/after comparison for scenario"""
    try:
        if scenario_id not in ["1.1", "1.2"]:
            raise HTTPException(status_code=400, detail="Invalid scenario_id. Use '1.1' or '1.2'")
        
        # Get current metrics
        if scenario_id == "1.1":
            current_metrics = await verification_service.get_pattern_verification_metrics(user_id)
            if current_metrics:
                comparison_data = {
                    "scenario_id": scenario_id,
                    "user_id": user_id,
                    "metrics_type": "pattern_learning",
                    "current_metrics": {
                        "pattern_suggestion_accuracy": current_metrics.pattern_suggestion_accuracy,
                        "time_improvement_percentage": current_metrics.time_improvement_percentage,
                        "avg_pattern_confidence": current_metrics.avg_pattern_confidence,
                        "total_executions": current_metrics.total_executions
                    },
                    "baseline_metrics": {
                        "pattern_suggestion_accuracy": 0.0,
                        "time_improvement_percentage": 0.0,
                        "avg_pattern_confidence": 0.0,
                        "total_executions": 0
                    },
                    "improvement": {
                        "accuracy_improvement": current_metrics.pattern_suggestion_accuracy,
                        "time_improvement": current_metrics.time_improvement_percentage,
                        "confidence_improvement": current_metrics.avg_pattern_confidence
                    }
                }
            else:
                comparison_data = {"message": "No metrics data available yet"}
        
        elif scenario_id == "1.2":
            current_metrics = await verification_service.get_tool_selection_verification_metrics(user_id)
            if current_metrics:
                comparison_data = {
                    "scenario_id": scenario_id,
                    "user_id": user_id,
                    "metrics_type": "tool_selection",
                    "current_metrics": {
                        "intent_recognition_accuracy": current_metrics.intent_recognition_accuracy,
                        "accuracy_improvement": current_metrics.accuracy_improvement,
                        "satisfaction_improvement": current_metrics.satisfaction_improvement,
                        "total_requests": current_metrics.total_requests
                    },
                    "baseline_metrics": {
                        "intent_recognition_accuracy": current_metrics.initial_accuracy,
                        "accuracy_improvement": 0.0,
                        "satisfaction_improvement": 0.0,
                        "total_requests": 0
                    },
                    "improvement": {
                        "accuracy_improvement": current_metrics.accuracy_improvement,
                        "satisfaction_improvement": current_metrics.satisfaction_improvement,
                        "recognition_improvement": current_metrics.current_accuracy - current_metrics.initial_accuracy if current_metrics.initial_accuracy > 0 else 0
                    }
                }
            else:
                comparison_data = {"message": "No metrics data available yet"}
        
        return {
            "comparison": comparison_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scenario comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Enhanced Agentic AI Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")