from pymongo import MongoClient
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging

from backend.services.pattern_learning_service import PatternLearningService
from backend.services.tool_analytics_service import ToolAnalyticsService
from backend.models.pattern_models import WorkflowPattern, PatternType, ExecutionStep

logger = logging.getLogger(__name__)

class ProceduralMemoryManager:
    def __init__(self, 
                 connection_string="mongodb://localhost:27017/", 
                 db_name="procedural_memory",
                 pattern_learning_service: Optional[PatternLearningService] = None,
                 tool_analytics_service: Optional[ToolAnalyticsService] = None):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.procedures = self.db.procedures
        self.pattern_learning_service = pattern_learning_service
        self.tool_analytics_service = tool_analytics_service
        
        # Enhanced pattern storage
        self.workflow_patterns = self.db.workflow_patterns
        self.pattern_executions = self.db.pattern_executions
    
    async def find_similar_procedures(self, intent: str, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """유사한 절차 패턴 검색 - Enhanced with pattern learning"""
        try:
            # Use pattern learning service if available
            if self.pattern_learning_service:
                user_id = "system"  # Default for system-wide patterns
                pattern_suggestion = await self.pattern_learning_service.suggest_pattern(
                    intent, user_id, "procedural_search"
                )
                
                if pattern_suggestion:
                    pattern = await self.pattern_learning_service.get_pattern_by_id(
                        pattern_suggestion.pattern_id
                    )
                    if pattern:
                        return [self._convert_pattern_to_procedure(pattern)]
            
            # Fallback to traditional text matching
            procedures = list(self.procedures.find({
                "intent": {"$regex": intent, "$options": "i"}
            }).limit(5))
            
            return procedures
        except Exception as e:
            logger.error(f"Error finding similar procedures: {e}")
            return []
    
    async def store_procedure(self, procedure_data: Dict[str, Any]) -> str:
        """절차 패턴 저장"""
        try:
            procedure_data["created_at"] = datetime.utcnow()
            procedure_data["usage_count"] = 0
            procedure_data["success_rate"] = 1.0
            
            result = self.procedures.insert_one(procedure_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing procedure: {e}")
            return ""
    
    async def update_procedure_performance(self, procedure_id: str, success: bool) -> bool:
        """절차 성능 업데이트 - Enhanced with pattern learning"""
        try:
            procedure = self.procedures.find_one({"_id": procedure_id})
            if procedure:
                current_rate = procedure.get("success_rate", 1.0)
                usage_count = procedure.get("usage_count", 0)
                
                # 성공률 업데이트
                new_rate = (current_rate * usage_count + (1.0 if success else 0.0)) / (usage_count + 1)
                
                self.procedures.update_one(
                    {"_id": procedure_id},
                    {
                        "$set": {"success_rate": new_rate},
                        "$inc": {"usage_count": 1}
                    }
                )
                
                # Update pattern learning service if available
                if self.pattern_learning_service and "pattern_id" in procedure:
                    await self.pattern_learning_service.submit_pattern_feedback(
                        suggestion_id="",
                        pattern_id=procedure["pattern_id"],
                        accepted=success,
                        rating=5 if success else 1
                    )
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating procedure performance: {e}")
            return False
    
    async def track_workflow_execution(
        self,
        session_id: str,
        user_id: str,
        execution_trace: List[Dict[str, Any]],
        success: bool,
        total_execution_time: float,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track workflow execution for enhanced pattern learning"""
        
        if not self.pattern_learning_service:
            logger.warning("Pattern learning service not available")
            return ""
        
        try:
            # Track execution in pattern learning service
            pattern_id = await self.pattern_learning_service.track_execution(
                session_id=session_id,
                user_id=user_id,
                execution_trace=execution_trace,
                success=success,
                total_execution_time=total_execution_time,
                context=context or {}
            )
            
            # Track individual tool usage in analytics service
            if self.tool_analytics_service:
                tools_used = []
                for trace in execution_trace:
                    tool_name = trace.get('tool', '')
                    if tool_name:
                        tools_used.append(tool_name)
                        await self.tool_analytics_service.track_tool_usage(
                            tool_name=tool_name,
                            user_id=user_id,
                            session_id=session_id,
                            execution_time=trace.get('execution_time', 0.0),
                            success=trace.get('success', False),
                            context=context or {},
                            parameters=trace.get('parameters', {})
                        )
                
                # Track tool combination
                if len(tools_used) > 1:
                    await self.tool_analytics_service.track_tool_combination(
                        tools=tools_used,
                        user_id=user_id,
                        session_id=session_id,
                        total_execution_time=total_execution_time,
                        success=success,
                        context=context or {}
                    )
            
            logger.info(f"Tracked workflow execution with pattern ID: {pattern_id}")
            return pattern_id
            
        except Exception as e:
            logger.error(f"Error tracking workflow execution: {e}")
            return ""
    
    async def suggest_workflow_optimization(
        self,
        user_input: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Suggest workflow optimization based on learned patterns"""
        
        if not self.pattern_learning_service:
            return None
        
        try:
            # Get pattern suggestion
            suggestion = await self.pattern_learning_service.suggest_pattern(
                user_input=user_input,
                user_id=user_id,
                session_id="optimization_request",
                context=context or {}
            )
            
            if not suggestion:
                return None
            
            pattern = await self.pattern_learning_service.get_pattern_by_id(
                suggestion.pattern_id
            )
            
            if not pattern:
                return None
            
            # Get tool recommendations if analytics service available
            tool_recommendations = []
            if self.tool_analytics_service:
                available_tools = [step.tool_name for step in pattern.steps]
                recommendations = await self.tool_analytics_service.get_tool_recommendations(
                    user_input=user_input,
                    user_id=user_id,
                    context=context or {},
                    available_tools=available_tools
                )
                tool_recommendations = recommendations[:3]  # Top 3 recommendations
            
            return {
                "suggestion_id": suggestion.suggestion_id,
                "pattern_id": pattern.pattern_id,
                "pattern_name": pattern.name,
                "confidence_score": suggestion.confidence_score,
                "estimated_execution_time": pattern.average_execution_time,
                "success_rate": pattern.success_rate,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "tool_name": step.tool_name,
                        "parameters": step.parameters,
                        "estimated_time": step.execution_time
                    }
                    for step in pattern.steps
                ],
                "tool_recommendations": tool_recommendations,
                "optimization_benefits": {
                    "time_savings": f"{max(0, 10 - pattern.average_execution_time):.1f}s",
                    "success_improvement": f"{(pattern.success_rate - 0.7) * 100:.1f}%",
                    "learning_confidence": f"{pattern.confidence_score * 100:.1f}%"
                }
            }
            
        except Exception as e:
            logger.error(f"Error suggesting workflow optimization: {e}")
            return None
    
    async def get_procedural_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get procedural memory analytics"""
        
        analytics = {
            "traditional_procedures": 0,
            "learned_patterns": 0,
            "total_executions": 0,
            "average_success_rate": 0.0,
            "pattern_learning_metrics": {}
        }
        
        try:
            # Traditional procedure counts
            procedure_count = self.procedures.count_documents({})
            analytics["traditional_procedures"] = procedure_count
            
            # Get pattern learning metrics if service available
            if self.pattern_learning_service:
                pattern_metrics = await self.pattern_learning_service.get_learning_metrics(user_id)
                analytics["learned_patterns"] = pattern_metrics.get("total_patterns_learned", 0)
                analytics["pattern_learning_metrics"] = pattern_metrics
            
            # Get tool analytics if service available
            if self.tool_analytics_service:
                if user_id:
                    tool_insights = await self.tool_analytics_service.get_user_tool_insights(user_id)
                    analytics["user_tool_insights"] = tool_insights
                else:
                    system_analytics = await self.tool_analytics_service.get_system_analytics()
                    analytics["system_tool_analytics"] = system_analytics
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting procedural analytics: {e}")
            return analytics
    
    def _convert_pattern_to_procedure(self, pattern: WorkflowPattern) -> Dict[str, Any]:
        """Convert a WorkflowPattern to legacy procedure format"""
        
        return {
            "_id": pattern.pattern_id,
            "pattern_id": pattern.pattern_id,
            "intent": pattern.name,
            "description": pattern.description,
            "steps": [
                {
                    "step_id": step.step_id,
                    "tool": step.tool_name,
                    "parameters": step.parameters,
                    "expected_time": step.execution_time
                }
                for step in pattern.steps
            ],
            "success_rate": pattern.success_rate,
            "usage_count": pattern.total_executions,
            "confidence_score": pattern.confidence_score,
            "created_at": pattern.created_at,
            "updated_at": pattern.updated_at
        }