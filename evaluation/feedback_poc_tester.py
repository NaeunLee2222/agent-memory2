"""
Automated PoC Scenario Tester for Feedback Loop Validation
Tests scenarios 1.1 (Flow Mode Pattern Learning) and 1.2 (Basic Mode Tool Selection)
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeedbackPoCTester:
    def __init__(self, backend_url: str = "http://localhost:8100"):
        self.backend_url = backend_url
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """Make HTTP request to backend"""
        try:
            url = f"{self.backend_url}{endpoint}"
            
            if method == "POST":
                async with self.session.post(url, json=data) as response:
                    return await response.json()
            else:
                async with self.session.get(url) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return None
    
    async def wait_for_backend(self, max_attempts: int = 10):
        """Wait for backend to be ready"""
        for attempt in range(max_attempts):
            try:
                response = await self.make_request("/health")
                if response and response.get("status") == "healthy":
                    logger.info("Backend is ready!")
                    return True
            except Exception:
                pass
            
            logger.info(f"Waiting for backend... (attempt {attempt + 1}/{max_attempts})")
            await asyncio.sleep(2)
        
        logger.error("Backend not available")
        return False
    
    async def test_flow_mode_pattern_learning(self) -> Dict[str, Any]:
        """
        Test Scenario 1.1: Flow Mode - Step-Action-Tool Pattern Learning
        
        Tests:
        1. Execute same workflow 3 times
        2. Verify pattern learning occurs
        3. Check 4th execution uses learned pattern
        4. Measure performance improvements
        """
        logger.info("🧪 Testing Flow Mode Pattern Learning (Scenario 1.1)")
        
        test_request = {
            "message": "데이터베이스에서 SHE 비상 정보 조회하고 Slack으로 알림",
            "user_id": "test_user_flow",
            "mode": "flow"
        }
        
        execution_times = []
        success_rates = []
        patterns_learned = []
        
        # Execute workflow 4 times
        for execution in range(1, 5):
            logger.info(f"📋 Execution {execution}/4")
            start_time = time.time()
            
            response = await self.make_request("/chat", "POST", test_request)
            execution_time = time.time() - start_time
            
            if not response:
                logger.error(f"Execution {execution} failed - no response")
                continue
            
            # Extract metrics
            metadata = response.get("metadata", {})
            execution_times.append(execution_time)
            success_rates.append(metadata.get("success_rate", 0))
            
            # Check for pattern suggestions (should appear from 4th execution)
            pattern_suggestion = metadata.get("pattern_suggestion")
            if pattern_suggestion:
                patterns_learned.append({
                    "execution": execution,
                    "pattern_id": pattern_suggestion.get("pattern_id"),
                    "confidence": pattern_suggestion.get("confidence_score", 0)
                })
                logger.info(f"✨ Pattern suggested at execution {execution}: confidence {pattern_suggestion.get('confidence_score', 0):.1%}")
            
            # Submit positive feedback to improve pattern learning
            if response.get("session_id"):
                feedback_data = {
                    "session_id": response["session_id"],
                    "rating": 5 if metadata.get("overall_success", False) else 3,
                    "comments": f"Test execution {execution}"
                }
                
                if pattern_suggestion:
                    feedback_data["pattern_id"] = pattern_suggestion.get("pattern_id")
                    feedback_data["suggestion_accepted"] = True
                
                await self.make_request("/feedback", "POST", feedback_data)
            
            # Wait between executions to allow processing
            await asyncio.sleep(1)
        
        # Analyze results
        results = {
            "scenario": "1.1_flow_mode_pattern_learning",
            "total_executions": len(execution_times),
            "patterns_learned_count": len(patterns_learned),
            "execution_times": execution_times,
            "avg_execution_time": statistics.mean(execution_times) if execution_times else 0,
            "success_rates": success_rates,
            "avg_success_rate": statistics.mean(success_rates) if success_rates else 0,
            "patterns_learned": patterns_learned,
            "performance_improvement": self._calculate_performance_improvement(execution_times),
            "pattern_learning_success": len(patterns_learned) > 0,
            "success_criteria": {
                "pattern_learned": len(patterns_learned) > 0,
                "performance_improved": self._calculate_performance_improvement(execution_times) > 0,
                "success_rate_maintained": statistics.mean(success_rates) >= 0.95 if success_rates else False
            }
        }
        
        # Check success criteria
        success_criteria = results["success_criteria"]
        overall_success = all(success_criteria.values())
        results["overall_success"] = overall_success
        
        logger.info(f"📊 Flow Mode Pattern Learning Results:")
        logger.info(f"   - Patterns Learned: {len(patterns_learned)}")
        logger.info(f"   - Performance Improvement: {results['performance_improvement']:.1%}")
        logger.info(f"   - Average Success Rate: {results['avg_success_rate']:.1%}")
        logger.info(f"   - Overall Success: {'✅' if overall_success else '❌'}")
        
        return results
    
    async def test_basic_mode_tool_selection(self) -> Dict[str, Any]:
        """
        Test Scenario 1.2: Basic Mode - Tool Selection Pattern Learning
        
        Tests:
        1. Natural language to tool mapping learning
        2. Tool efficiency learning over multiple uses
        3. Context-aware tool selection improvement
        """
        logger.info("🧪 Testing Basic Mode Tool Selection Learning (Scenario 1.2)")
        
        test_scenarios = [
            {
                "message": "긴급 상황을 팀에 알려줘",
                "user_id": "test_user_basic",
                "mode": "basic",
                "expected_tools": ["emergency_mail", "send_slack"]
            },
            {
                "message": "프로젝트 데이터를 검색하고 팀에 공유해줘",
                "user_id": "test_user_basic", 
                "mode": "basic",
                "expected_tools": ["search_db", "send_slack"]
            },
            {
                "message": "데이터베이스 조회 결과를 메일로 보내줘",
                "user_id": "test_user_basic",
                "mode": "basic", 
                "expected_tools": ["search_db", "emergency_mail"]
            }
        ]
        
        scenario_results = []
        
        for scenario_idx, scenario in enumerate(test_scenarios, 1):
            logger.info(f"📋 Testing scenario {scenario_idx}: {scenario['message'][:50]}...")
            
            # Execute each scenario multiple times to track learning
            execution_results = []
            
            for execution in range(1, 4):  # 3 executions per scenario
                start_time = time.time()
                
                response = await self.make_request("/chat", "POST", {
                    "message": scenario["message"],
                    "user_id": scenario["user_id"],
                    "mode": scenario["mode"]
                })
                
                execution_time = time.time() - start_time
                
                if not response:
                    continue
                
                # Analyze tool selection
                execution_trace = response.get("execution_trace", [])
                tools_used = [step.get("tool", "") for step in execution_trace]
                
                metadata = response.get("metadata", {})
                success_rate = metadata.get("success_rate", 0)
                
                execution_result = {
                    "execution": execution,
                    "tools_used": tools_used,
                    "execution_time": execution_time,
                    "success_rate": success_rate,
                    "tools_expected": scenario["expected_tools"],
                    "tool_accuracy": self._calculate_tool_accuracy(tools_used, scenario["expected_tools"])
                }
                
                execution_results.append(execution_result)
                
                # Submit feedback
                if response.get("session_id"):
                    rating = 5 if success_rate >= 0.8 else 3
                    await self.make_request("/feedback", "POST", {
                        "session_id": response["session_id"],
                        "rating": rating,
                        "comments": f"Scenario {scenario_idx} execution {execution}"
                    })
                
                await asyncio.sleep(0.5)
            
            # Analyze scenario results
            if execution_results:
                scenario_result = {
                    "scenario_id": scenario_idx,
                    "message": scenario["message"],
                    "executions": execution_results,
                    "tool_accuracy_improvement": self._calculate_learning_improvement(
                        [r["tool_accuracy"] for r in execution_results]
                    ),
                    "performance_improvement": self._calculate_performance_improvement(
                        [r["execution_time"] for r in execution_results]
                    ),
                    "success_rate_improvement": self._calculate_learning_improvement(
                        [r["success_rate"] for r in execution_results]
                    )
                }
                scenario_results.append(scenario_result)
        
        # Overall analysis
        results = {
            "scenario": "1.2_basic_mode_tool_selection",
            "scenarios_tested": len(scenario_results),
            "scenario_results": scenario_results,
            "avg_tool_accuracy_improvement": statistics.mean([
                s["tool_accuracy_improvement"] for s in scenario_results
            ]) if scenario_results else 0,
            "avg_performance_improvement": statistics.mean([
                s["performance_improvement"] for s in scenario_results
            ]) if scenario_results else 0,
            "success_criteria": {
                "tool_accuracy_improved": statistics.mean([
                    s["tool_accuracy_improvement"] for s in scenario_results
                ]) >= 0.1 if scenario_results else False,  # 10% improvement threshold
                "performance_maintained": statistics.mean([
                    s["performance_improvement"] for s in scenario_results
                ]) >= -0.1 if scenario_results else False,  # Allow 10% performance degradation
                "scenarios_successful": len([
                    s for s in scenario_results if s["tool_accuracy_improvement"] > 0
                ]) >= 2  # At least 2 scenarios should show improvement
            }
        }
        
        # Check success criteria
        success_criteria = results["success_criteria"]
        overall_success = all(success_criteria.values())
        results["overall_success"] = overall_success
        
        logger.info(f"📊 Basic Mode Tool Selection Results:")
        logger.info(f"   - Scenarios Tested: {len(scenario_results)}")
        logger.info(f"   - Avg Tool Accuracy Improvement: {results['avg_tool_accuracy_improvement']:.1%}")
        logger.info(f"   - Avg Performance Change: {results['avg_performance_improvement']:.1%}")
        logger.info(f"   - Overall Success: {'✅' if overall_success else '❌'}")
        
        return results
    
    async def get_analytics_snapshot(self) -> Dict[str, Any]:
        """Get analytics snapshot for validation"""
        logger.info("📊 Collecting analytics snapshot")
        
        analytics = {}
        
        # Pattern analytics
        pattern_analytics = await self.make_request("/analytics/patterns")
        if pattern_analytics:
            analytics["patterns"] = pattern_analytics.get("analytics", {})
        
        # Tool analytics
        tool_analytics = await self.make_request("/analytics/tools")
        if tool_analytics:
            analytics["tools"] = tool_analytics.get("analytics", {})
        
        # Procedural analytics
        procedural_analytics = await self.make_request("/analytics/procedural")
        if procedural_analytics:
            analytics["procedural"] = procedural_analytics.get("analytics", {})
        
        return analytics
    
    async def run_full_poc_test(self) -> Dict[str, Any]:
        """Run complete PoC test suite"""
        logger.info("🚀 Starting Full PoC Test Suite")
        
        # Wait for backend
        if not await self.wait_for_backend():
            return {"error": "Backend not available"}
        
        start_time = time.time()
        
        # Get baseline analytics
        baseline_analytics = await self.get_analytics_snapshot()
        
        # Run scenario tests
        flow_results = await self.test_flow_mode_pattern_learning()
        basic_results = await self.test_basic_mode_tool_selection()
        
        # Get final analytics
        final_analytics = await self.get_analytics_snapshot()
        
        total_time = time.time() - start_time
        
        # Compile comprehensive results
        results = {
            "test_suite": "feedback_loop_poc",
            "timestamp": datetime.now().isoformat(),
            "total_test_time": total_time,
            "baseline_analytics": baseline_analytics,
            "final_analytics": final_analytics,
            "scenario_results": {
                "flow_mode_pattern_learning": flow_results,
                "basic_mode_tool_selection": basic_results
            },
            "overall_success": flow_results.get("overall_success", False) and basic_results.get("overall_success", False),
            "summary": {
                "patterns_learned": flow_results.get("patterns_learned_count", 0),
                "tool_accuracy_improvement": basic_results.get("avg_tool_accuracy_improvement", 0),
                "performance_improvements": {
                    "flow_mode": flow_results.get("performance_improvement", 0),
                    "basic_mode": basic_results.get("avg_performance_improvement", 0)
                }
            }
        }
        
        logger.info("🎯 PoC Test Suite Complete!")
        logger.info(f"   - Overall Success: {'✅' if results['overall_success'] else '❌'}")
        logger.info(f"   - Total Test Time: {total_time:.1f}s")
        logger.info(f"   - Patterns Learned: {results['summary']['patterns_learned']}")
        logger.info(f"   - Tool Accuracy Improvement: {results['summary']['tool_accuracy_improvement']:.1%}")
        
        return results
    
    def _calculate_performance_improvement(self, execution_times: List[float]) -> float:
        """Calculate performance improvement percentage"""
        if len(execution_times) < 2:
            return 0.0
        
        initial_avg = statistics.mean(execution_times[:2])
        final_avg = statistics.mean(execution_times[-2:])
        
        if initial_avg == 0:
            return 0.0
        
        return (initial_avg - final_avg) / initial_avg
    
    def _calculate_learning_improvement(self, values: List[float]) -> float:
        """Calculate learning improvement from first to last value"""
        if len(values) < 2:
            return 0.0
        
        initial = values[0]
        final = values[-1]
        
        if initial == 0:
            return final  # If starting from 0, return final value
        
        return (final - initial) / initial
    
    def _calculate_tool_accuracy(self, tools_used: List[str], expected_tools: List[str]) -> float:
        """Calculate accuracy of tool selection"""
        if not expected_tools:
            return 1.0 if not tools_used else 0.0
        
        # Calculate intersection over union
        used_set = set(tools_used)
        expected_set = set(expected_tools)
        
        intersection = used_set & expected_set
        union = used_set | expected_set
        
        if not union:
            return 1.0
        
        return len(intersection) / len(union)
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"poc_test_results_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Results saved to {filename}")

async def main():
    """Main test execution"""
    async with FeedbackPoCTester() as tester:
        results = await tester.run_full_poc_test()
        tester.save_results(results)
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 FEEDBACK LOOP PoC TEST RESULTS")
        print("="*60)
        print(f"Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}")
        print(f"Test Duration: {results['total_test_time']:.1f} seconds")
        print(f"Patterns Learned: {results['summary']['patterns_learned']}")
        print(f"Tool Accuracy Improvement: {results['summary']['tool_accuracy_improvement']:.1%}")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())