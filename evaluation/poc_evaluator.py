import asyncio
import time
import json
import requests
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
import logging


class EnhancedPoCEvaluator:
    def __init__(self, backend_url: str = "http://localhost:8100"):
        self.backend_url = backend_url
        self.test_results = {}
        self.performance_data = []

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def call_api(self, endpoint: str, data: Dict = None) -> Dict:
        """API 호출 with timeout and retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if data:
                    response = requests.post(
                        f"{self.backend_url}{endpoint}", json=data, timeout=30
                    )
                else:
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=30)

                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.error(f"HTTP {response.status_code}: {response.text}")
                    return {"error": f"HTTP {response.status_code}"}

            except Exception as e:
                if attempt == max_retries - 1:
                    return {"error": str(e)}
                time.sleep(2**attempt)  # 지수 백오프

        return {"error": "Max retries exceeded"}

    def test_procedural_memory_flow_mode(self):
        """절차적 메모리 - 플로우 모드 검증"""
        self.logger.info("🧠 절차적 메모리 (플로우 모드) 테스트 시작...")

        test_case = {
            "message": "데이터베이스에서 SHE 비상 정보 조회하고 Slack으로 알림해주세요",
            "user_id": "test_procedural_user",
            "mode": "flow",
            "expected_tools": ["SEARCH_DB", "GENERATE_MSG", "SEND_SLACK"],
        }

        results = []

        # 3번 반복 실행으로 패턴 학습 확인
        for iteration in range(3):
            session_id = f"procedural_flow_test_{iteration}"

            start_time = time.time()
            response = self.call_api(
                "/chat",
                {
                    "message": test_case["message"],
                    "user_id": test_case["user_id"],
                    "session_id": session_id,
                    "mode": test_case["mode"],
                },
            )
            end_time = time.time()

            if "error" not in response:
                used_tools = [
                    tool["tool_type"] for tool in response.get("tools_used", [])
                ]
                workflow_executed = response.get("workflow_executed")

                result = {
                    "iteration": iteration + 1,
                    "processing_time": end_time - start_time,
                    "tools_used": used_tools,
                    "workflow_pattern": workflow_executed is not None,
                    "success": len(used_tools) >= 2,  # 최소 2개 도구 사용
                    "pattern_reuse": iteration > 0 and workflow_executed is not None,
                }

                results.append(result)
                self.logger.info(
                    f"  반복 {iteration + 1}: {result['processing_time']:.2f}초 - {'✅' if result['success'] else '❌'}"
                )
            else:
                results.append(
                    {
                        "iteration": iteration + 1,
                        "error": response["error"],
                        "success": False,
                    }
                )

        # 성능 개선 확인 (시간 단축)
        if len(results) >= 3:
            time_improvement = (
                results[0]["processing_time"] - results[-1]["processing_time"]
            )
            pattern_learning = sum(
                1 for r in results[1:] if r.get("pattern_reuse", False)
            )

            success_metrics = {
                "total_tests": len(results),
                "successful_tests": sum(1 for r in results if r.get("success", False)),
                "success_rate": sum(1 for r in results if r.get("success", False))
                / len(results),
                "time_improvement": time_improvement,
                "pattern_learning_rate": (
                    pattern_learning / (len(results) - 1) if len(results) > 1 else 0
                ),
                "avg_processing_time": sum(r.get("processing_time", 0) for r in results)
                / len(results),
            }

            return {
                "test_name": "절차적 메모리 - 플로우 모드",
                "results": results,
                "metrics": success_metrics,
                "passed": success_metrics["success_rate"] >= 0.8
                and success_metrics["pattern_learning_rate"] >= 0.5,
            }

        return {
            "test_name": "절차적 메모리 - 플로우 모드",
            "results": results,
            "passed": False,
        }

    def test_episodic_memory_personalization(self):
        """에피소드 메모리 - 개인화 학습 검증"""
        self.logger.info("📚 에피소드 메모리 개인화 테스트 시작...")

        user_id = "test_episodic_user"

        # 1단계: 선호도 학습
        preference_session = f"episodic_pref_{int(time.time())}"
        preference_response = self.call_api(
            "/chat",
            {
                "message": "저는 기술적인 설명을 선호하고, 간결한 메시지를 좋아합니다",
                "user_id": user_id,
                "session_id": preference_session,
                "mode": "basic",
            },
        )

        # 피드백으로 선호도 강화
        feedback_response = self.call_api(
            "/feedback",
            {
                "session_id": preference_session,
                "user_id": user_id,
                "feedback_type": "style_preference",
                "content": "기술적이고 간결한 스타일을 선호합니다",
                "rating": 5.0,
            },
        )

        time.sleep(2)  # 메모리 처리 시간 대기

        # 2단계: 새 세션에서 개인화 적용 확인
        test_session = f"episodic_test_{int(time.time())}"
        test_response = self.call_api(
            "/chat",
            {
                "message": "머신러닝에 대해 설명해주세요",
                "user_id": user_id,
                "session_id": test_session,
                "mode": "basic",
            },
        )

        # 3단계: 선호도 조회로 학습 확인
        preferences_response = self.call_api(f"/user/{user_id}/preferences")

        results = {
            "preference_learning": "error" not in preference_response,
            "feedback_processing": "error" not in feedback_response
            and feedback_response.get("applied", False),
            "personalization_applied": "error" not in test_response
            and len(test_response.get("memory_used", {}).get("EPISODIC", [])) > 0,
            "preferences_stored": "error" not in preferences_response
            and len(preferences_response) > 0,
            "processing_times": {
                "preference": preference_response.get("processing_time", 0),
                "feedback": feedback_response.get("processing_time", 0),
                "personalized": test_response.get("processing_time", 0),
            },
        }

        success_rate = (
            sum(1 for k, v in results.items() if k != "processing_times" and v) / 4
        )

        return {
            "test_name": "에피소드 메모리 - 개인화 학습",
            "results": results,
            "metrics": {
                "success_rate": success_rate,
                "preference_recall": results["personalization_applied"],
                "feedback_responsiveness": results["feedback_processing"],
            },
            "passed": success_rate >= 0.75,
        }

    def test_5_second_feedback_target(self):
        """5초 이내 피드백 처리 목표 검증"""
        self.logger.info("⚡ 5초 이내 피드백 처리 테스트 시작...")

        feedback_tests = [
            {"type": "style_preference", "content": "더 친근한 톤으로 대화해주세요"},
            {
                "type": "response_quality",
                "content": "응답이 너무 길어요",
                "rating": 2.0,
            },
            {"type": "tool_performance", "content": "데이터 조회가 느려요"},
            {"type": "workflow_efficiency", "content": "단계를 줄여주세요"},
            {"type": "user_experience", "content": "더 직관적이었으면 좋겠어요"},
        ]

        results = []

        for i, test in enumerate(feedback_tests):
            session_id = f"feedback_speed_test_{i}"

            start_time = time.time()
            response = self.call_api(
                "/feedback",
                {
                    "session_id": session_id,
                    "user_id": "feedback_speed_tester",
                    "feedback_type": test["type"],
                    "content": test["content"],
                    "rating": test.get("rating"),
                },
            )
            end_time = time.time()

            processing_time = end_time - start_time
            meets_target = processing_time < 5.0

            result = {
                "test_case": i + 1,
                "feedback_type": test["type"],
                "processing_time": processing_time,
                "meets_5s_target": meets_target,
                "applied": response.get("applied", False),
                "optimizations_count": len(response.get("optimizations", [])),
            }

            results.append(result)

            status = "✅" if meets_target else "❌"
            self.logger.info(f"  테스트 {i+1}: {processing_time:.3f}초 - {status}")

        # 성과 지표 계산
        target_achievement_rate = sum(1 for r in results if r["meets_5s_target"]) / len(
            results
        )
        avg_processing_time = sum(r["processing_time"] for r in results) / len(results)
        application_rate = sum(1 for r in results if r["applied"]) / len(results)

        return {
            "test_name": "5초 이내 피드백 처리",
            "results": results,
            "metrics": {
                "target_achievement_rate": target_achievement_rate,
                "avg_processing_time": avg_processing_time,
                "application_rate": application_rate,
                "total_tests": len(results),
            },
            "passed": target_achievement_rate >= 0.95,  # 95% 목표
        }

    def test_cross_agent_learning(self):
        """크로스 에이전트 학습 검증"""
        self.logger.info("🤝 크로스 에이전트 학습 테스트 시작...")

        user_id = "cross_agent_test_user"

        # Agent 1에서 학습
        agent1_session = f"cross_agent_1_{int(time.time())}"

        # 선호도 설정
        learning_response = self.call_api(
            "/chat",
            {
                "message": "저는 항상 Slack 알림을 선호하고, 상세한 로그 정보를 원합니다",
                "user_id": user_id,
                "session_id": agent1_session,
                "mode": "basic",
            },
        )

        # 피드백으로 학습 강화
        feedback_response = self.call_api(
            "/feedback",
            {
                "session_id": agent1_session,
                "user_id": user_id,
                "feedback_type": "style_preference",
                "content": "상세한 기술 정보를 포함해서 Slack으로 알림해주세요",
                "rating": 5.0,
            },
        )

        time.sleep(3)  # 크로스 에이전트 학습 전파 시간

        # Agent 2에서 학습 내용 활용 확인
        agent2_session = f"cross_agent_2_{int(time.time())}"

        application_response = self.call_api(
            "/chat",
            {
                "message": "시스템 상태를 확인해주세요",
                "user_id": user_id,  # 동일한 사용자
                "session_id": agent2_session,  # 다른 세션 (다른 에이전트 시뮬레이션)
                "mode": "basic",
            },
        )

        # 선호도 데이터 확인
        preferences_response = self.call_api(f"/user/{user_id}/preferences")

        results = {
            "initial_learning": "error" not in learning_response,
            "feedback_applied": feedback_response.get("applied", False),
            "cross_agent_memory_used": len(
                application_response.get("memory_used", {}).get("EPISODIC", [])
            )
            > 0,
            "preferences_shared": len(preferences_response) > 0,
            "processing_times": {
                "learning": learning_response.get("processing_time", 0),
                "feedback": feedback_response.get("processing_time", 0),
                "application": application_response.get("processing_time", 0),
            },
            "tools_optimization": any(
                "slack" in tool.get("tool_type", "").lower()
                for tool in application_response.get("tools_used", [])
            ),
        }

        # 성공률 계산
        success_indicators = [
            "initial_learning",
            "feedback_applied",
            "cross_agent_memory_used",
            "preferences_shared",
        ]
        success_rate = sum(
            1 for indicator in success_indicators if results[indicator]
        ) / len(success_indicators)

        return {
            "test_name": "크로스 에이전트 학습",
            "results": results,
            "metrics": {
                "success_rate": success_rate,
                "learning_transfer_success": results["cross_agent_memory_used"],
                "preference_sharing_success": results["preferences_shared"],
            },
            "passed": success_rate >= 0.8,  # 80% 목표
        }

    def test_mcp_tool_performance_optimization(self):
        """MCP 도구 성능 최적화 검증"""
        self.logger.info("🔧 MCP 도구 성능 최적화 테스트 시작...")

        # 초기 성능 측정
        initial_stats = self.call_api("/mcp/tools/performance")

        # 여러 도구를 사용하는 워크플로우 실행
        test_workflows = [
            {
                "message": "데이터베이스에서 사용자 정보를 조회하고 결과를 Slack으로 전송해주세요",
                "expected_tools": ["SEARCH_DB", "SEND_SLACK"],
            },
            {
                "message": "비상 상황 알림을 생성하고 이메일과 Slack으로 동시 발송해주세요",
                "expected_tools": ["EMERGENCY_MAIL", "SEND_SLACK"],
            },
            {
                "message": "시스템 상태 메시지를 생성해서 관리자에게 전달해주세요",
                "expected_tools": ["GENERATE_MSG", "SEND_SLACK"],
            },
        ]

        performance_results = []

        for i, workflow in enumerate(test_workflows):
            session_id = f"mcp_perf_test_{i}"

            start_time = time.time()
            response = self.call_api(
                "/chat",
                {
                    "message": workflow["message"],
                    "user_id": "mcp_performance_tester",
                    "session_id": session_id,
                    "mode": "flow",
                },
            )
            end_time = time.time()

            if "error" not in response:
                tools_used = response.get("tools_used", [])
                successful_tools = [t for t in tools_used if t.get("success")]

                result = {
                    "workflow": i + 1,
                    "total_time": end_time - start_time,
                    "tools_used": len(tools_used),
                    "successful_tools": len(successful_tools),
                    "success_rate": (
                        len(successful_tools) / len(tools_used) if tools_used else 0
                    ),
                    "avg_tool_time": (
                        sum(t.get("execution_time", 0) for t in tools_used)
                        / len(tools_used)
                        if tools_used
                        else 0
                    ),
                }

                performance_results.append(result)
                self.logger.info(
                    f"  워크플로우 {i+1}: {result['total_time']:.2f}초, 성공률 {result['success_rate']:.1%}"
                )

        # 최종 성능 측정
        final_stats = self.call_api("/mcp/tools/performance")

        # 성능 개선 확인
        improvements = {}
        if initial_stats and final_stats:
            for tool_name in initial_stats.keys():
                if tool_name in final_stats:
                    initial_time = initial_stats[tool_name].get(
                        "recent_avg_time",
                        initial_stats[tool_name].get("avg_response_time", 0),
                    )
                    final_time = final_stats[tool_name].get(
                        "recent_avg_time",
                        final_stats[tool_name].get("avg_response_time", 0),
                    )

                    if initial_time > 0:
                        improvements[tool_name] = {
                            "time_improvement": initial_time - final_time,
                            "improvement_rate": (
                                (initial_time - final_time) / initial_time
                                if initial_time > 0
                                else 0
                            ),
                        }

        metrics = {
            "total_workflows": len(performance_results),
            "avg_success_rate": (
                sum(r["success_rate"] for r in performance_results)
                / len(performance_results)
                if performance_results
                else 0
            ),
            "avg_processing_time": (
                sum(r["total_time"] for r in performance_results)
                / len(performance_results)
                if performance_results
                else 0
            ),
            "performance_improvements": improvements,
        }

        return {
            "test_name": "MCP 도구 성능 최적화",
            "results": performance_results,
            "metrics": metrics,
            "passed": metrics["avg_success_rate"] >= 0.85
            and metrics["avg_processing_time"] <= 5.0,
        }

    def run_comprehensive_evaluation(self):
        """종합 평가 실행"""
        self.logger.info("🚀 Enhanced Agentic AI PoC 종합 평가 시작...")
        self.logger.info("=" * 60)

        evaluation_results @ app.get("/feedback/optimization-history")


async def optimization_history_endpoint():
    """최적화 이력 조회"""
    try:
        history = await feedback_service.get_optimization_history()
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최적화 이력 조회 오류: {str(e)}")


@app.get("/user/{user_id}/preferences")
async def user_preferences_endpoint(user_id: str):
    """사용자 선호도 조회"""
    try:
        preferences = await feedback_service.get_user_preferences(user_id)
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"선호도 조회 오류: {str(e)}")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "memory": memory_service is not None,
            "mcp": mcp_service is not None,
            "feedback": feedback_service is not None,
            "agent": agent_service is not None,
        },
        "version": "2.0.0",
    }


@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
