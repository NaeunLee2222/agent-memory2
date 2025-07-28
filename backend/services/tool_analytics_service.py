from typing import Dict, List, Optional, Any, Tuple
import asyncio
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from backend.models.pattern_models import (
    ToolUsageAnalytics, ToolCombination, UserToolPreference, FeedbackMetrics
)
from backend.database.memory_database import MemoryDatabase

logger = logging.getLogger(__name__)

class ToolAnalyticsService:
    """Service for analyzing tool usage patterns and recommendations"""
    
    def __init__(self, memory_database: MemoryDatabase):
        self.memory_database = memory_database
        self.tool_analytics: List[ToolUsageAnalytics] = []
        self.tool_combinations: Dict[str, ToolCombination] = {}
        self.user_preferences: Dict[str, Dict[str, UserToolPreference]] = defaultdict(dict)
        self.feedback_metrics: List[FeedbackMetrics] = []
        
    async def initialize(self):
        """Initialize the tool analytics service"""
        logger.info("Initializing Tool Analytics Service")
        await self._load_analytics_data()
        
    async def track_tool_usage(
        self,
        tool_name: str,
        user_id: str,
        session_id: str,
        execution_time: float,
        success: bool,
        context: Dict[str, Any],
        parameters: Dict[str, Any]
    ):
        """Track individual tool usage"""
        
        analytics = ToolUsageAnalytics(
            tool_name=tool_name,
            user_id=user_id,
            session_id=session_id,
            execution_time=execution_time,
            success=success,
            context=context,
            parameters_used=parameters
        )
        
        self.tool_analytics.append(analytics)
        
        # Update user preferences
        await self._update_user_preferences(user_id, tool_name, success, execution_time)
        
        logger.debug(f"Tracked tool usage: {tool_name} for user {user_id}")
    
    async def track_tool_combination(
        self,
        tools: List[str],
        user_id: str,
        session_id: str,
        total_execution_time: float,
        success: bool,
        context: Dict[str, Any]
    ):
        """Track tool combination usage"""
        
        combination_key = "_".join(sorted(tools))
        
        if combination_key in self.tool_combinations:
            combination = self.tool_combinations[combination_key]
            
            # Update statistics
            combination.usage_count += 1
            old_total_time = combination.average_execution_time * (combination.usage_count - 1)
            combination.average_execution_time = (old_total_time + total_execution_time) / combination.usage_count
            
            # Update success rate
            old_successes = combination.success_rate * (combination.usage_count - 1)
            new_successes = old_successes + (1 if success else 0)
            combination.success_rate = new_successes / combination.usage_count
            
            combination.updated_at = datetime.utcnow()
        else:
            # Create new combination
            combination = ToolCombination(
                tools=tools,
                success_rate=1.0 if success else 0.0,
                average_execution_time=total_execution_time,
                usage_count=1,
                context_pattern=self._extract_context_pattern(context)
            )
            self.tool_combinations[combination_key] = combination
        
        logger.debug(f"Tracked tool combination: {combination_key}")
    
    async def get_tool_recommendations(
        self,
        user_input: str,
        user_id: str,
        context: Dict[str, Any],
        available_tools: List[str]
    ) -> List[Tuple[str, float]]:
        """Get recommended tools based on context and user preferences"""
        
        recommendations = []
        
        # Get user preferences
        user_prefs = self.user_preferences.get(user_id, {})
        
        # Analyze context for tool selection
        context_score = self._calculate_context_relevance(context)
        
        for tool_name in available_tools:
            score = 0.0
            
            # User preference score
            if tool_name in user_prefs:
                pref = user_prefs[tool_name]
                score += 0.4 * pref.preference_score
                
                # Context matching bonus
                context_tags = self._extract_context_tags(context)
                common_tags = set(pref.context_tags) & set(context_tags)
                if common_tags:
                    score += 0.2 * (len(common_tags) / max(len(pref.context_tags), 1))
            
            # Historical success rate
            tool_analytics = [a for a in self.tool_analytics if a.tool_name == tool_name]
            if tool_analytics:
                success_rate = sum(1 for a in tool_analytics if a.success) / len(tool_analytics)
                score += 0.3 * success_rate
            
            # Recent performance bonus
            recent_analytics = [
                a for a in tool_analytics 
                if a.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ]
            if recent_analytics:
                recent_success_rate = sum(1 for a in recent_analytics if a.success) / len(recent_analytics)
                score += 0.1 * recent_success_rate
            
            if score > 0.1:  # Minimum threshold
                recommendations.append((tool_name, score))
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations
    
    async def get_optimal_tool_combination(
        self,
        required_capabilities: List[str],
        context: Dict[str, Any],
        max_tools: int = 5
    ) -> Optional[List[str]]:
        """Get optimal tool combination for required capabilities"""
        
        # Find combinations that match context
        context_pattern = self._extract_context_pattern(context)
        
        matching_combinations = []
        for combination in self.tool_combinations.values():
            if combination.context_pattern == context_pattern and len(combination.tools) <= max_tools:
                score = (
                    combination.success_rate * 0.6 +
                    (1.0 / max(combination.average_execution_time, 0.1)) * 0.2 +
                    min(combination.usage_count / 10.0, 1.0) * 0.2
                )
                matching_combinations.append((combination.tools, score))
        
        if matching_combinations:
            matching_combinations.sort(key=lambda x: x[1], reverse=True)
            return matching_combinations[0][0]
        
        return None
    
    async def analyze_tool_performance(
        self,
        tool_name: str,
        time_period_days: int = 7
    ) -> Dict[str, Any]:
        """Analyze performance metrics for a specific tool"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        recent_analytics = [
            a for a in self.tool_analytics 
            if a.tool_name == tool_name and a.timestamp >= cutoff_date
        ]
        
        if not recent_analytics:
            return {"error": "No recent data available"}
        
        # Calculate metrics
        total_uses = len(recent_analytics)
        successful_uses = sum(1 for a in recent_analytics if a.success)
        success_rate = successful_uses / total_uses
        
        execution_times = [a.execution_time for a in recent_analytics]
        avg_execution_time = statistics.mean(execution_times)
        
        # Performance trends
        daily_performance = defaultdict(list)
        for analytics in recent_analytics:
            day = analytics.timestamp.date()
            daily_performance[day].append(analytics.success)
        
        daily_success_rates = {
            str(day): sum(successes) / len(successes)
            for day, successes in daily_performance.items()
        }
        
        # User adoption
        unique_users = len(set(a.user_id for a in recent_analytics))
        
        # Context analysis
        context_performance = defaultdict(list)
        for analytics in recent_analytics:
            context_key = self._extract_context_pattern(analytics.context)
            context_performance[context_key].append(analytics.success)
        
        context_success_rates = {
            context: sum(successes) / len(successes)
            for context, successes in context_performance.items()
        }
        
        return {
            "tool_name": tool_name,
            "period_days": time_period_days,
            "total_uses": total_uses,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "unique_users": unique_users,
            "daily_success_rates": daily_success_rates,
            "context_performance": context_success_rates,
            "performance_trend": self._calculate_trend(list(daily_success_rates.values()))
        }
    
    async def get_user_tool_insights(self, user_id: str) -> Dict[str, Any]:
        """Get personalized tool usage insights for a user"""
        
        user_analytics = [a for a in self.tool_analytics if a.user_id == user_id]
        if not user_analytics:
            return {"error": "No usage data available"}
        
        # Most used tools
        tool_usage = Counter(a.tool_name for a in user_analytics)
        most_used = tool_usage.most_common(5)
        
        # Best performing tools
        tool_performance = defaultdict(list)
        for analytics in user_analytics:
            tool_performance[analytics.tool_name].append(analytics.success)
        
        best_performing = []
        for tool, successes in tool_performance.items():
            if len(successes) >= 3:  # Minimum usage for reliability
                success_rate = sum(successes) / len(successes)
                best_performing.append((tool, success_rate))
        
        best_performing.sort(key=lambda x: x[1], reverse=True)
        best_performing = best_performing[:5]
        
        # Time patterns
        usage_by_hour = defaultdict(int)
        for analytics in user_analytics:
            hour = analytics.timestamp.hour
            usage_by_hour[hour] += 1
        
        peak_hours = sorted(usage_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Recent improvement metrics
        recent_metrics = [
            m for m in self.feedback_metrics 
            if m.user_id == user_id and m.timestamp >= datetime.utcnow() - timedelta(days=30)
        ]
        
        improvements = {}
        for metric in recent_metrics:
            if metric.metric_type not in improvements:
                improvements[metric.metric_type] = []
            improvements[metric.metric_type].append(metric.improvement_percentage)
        
        avg_improvements = {
            metric_type: statistics.mean(values)
            for metric_type, values in improvements.items()
        }
        
        return {
            "user_id": user_id,
            "total_tool_uses": len(user_analytics),
            "most_used_tools": most_used,
            "best_performing_tools": best_performing,
            "peak_usage_hours": [hour for hour, _ in peak_hours],
            "overall_success_rate": sum(1 for a in user_analytics if a.success) / len(user_analytics),
            "recent_improvements": avg_improvements,
            "preferences": {
                tool: pref.preference_score 
                for tool, pref in self.user_preferences.get(user_id, {}).items()
            }
        }
    
    async def record_feedback_improvement(
        self,
        session_id: str,
        user_id: str,
        metric_type: str,
        before_value: float,
        after_value: float
    ):
        """Record improvement metrics from feedback"""
        
        improvement_percentage = ((after_value - before_value) / max(before_value, 0.001)) * 100
        
        metric = FeedbackMetrics(
            session_id=session_id,
            user_id=user_id,
            metric_type=metric_type,
            before_value=before_value,
            after_value=after_value,
            improvement_percentage=improvement_percentage
        )
        
        self.feedback_metrics.append(metric)
        logger.info(f"Recorded {improvement_percentage:.1f}% improvement in {metric_type}")
    
    async def get_system_analytics(self) -> Dict[str, Any]:
        """Get overall system analytics"""
        
        total_analytics = len(self.tool_analytics)
        if total_analytics == 0:
            return {"error": "No analytics data available"}
        
        # Overall success rate
        overall_success_rate = sum(1 for a in self.tool_analytics if a.success) / total_analytics
        
        # Tool popularity
        tool_usage = Counter(a.tool_name for a in self.tool_analytics)
        popular_tools = tool_usage.most_common(10)
        
        # User engagement
        unique_users = len(set(a.user_id for a in self.tool_analytics))
        avg_tools_per_user = total_analytics / unique_users if unique_users > 0 else 0
        
        # Performance trends
        recent_analytics = [
            a for a in self.tool_analytics 
            if a.timestamp >= datetime.utcnow() - timedelta(days=7)
        ]
        recent_success_rate = (
            sum(1 for a in recent_analytics if a.success) / len(recent_analytics)
            if recent_analytics else 0
        )
        
        # Combination effectiveness
        best_combinations = sorted(
            [(combo.tools, combo.success_rate, combo.usage_count) 
             for combo in self.tool_combinations.values()],
            key=lambda x: x[1] * x[2],  # success_rate * usage_count
            reverse=True
        )[:5]
        
        return {
            "total_tool_uses": total_analytics,
            "overall_success_rate": overall_success_rate,
            "recent_success_rate": recent_success_rate,
            "unique_users": unique_users,
            "avg_tools_per_user": avg_tools_per_user,
            "popular_tools": popular_tools,
            "best_combinations": best_combinations,
            "total_combinations": len(self.tool_combinations),
            "improvement_trend": recent_success_rate - overall_success_rate
        }
    
    async def _update_user_preferences(
        self,
        user_id: str,
        tool_name: str,
        success: bool,
        execution_time: float
    ):
        """Update user preferences based on tool usage"""
        
        if tool_name not in self.user_preferences[user_id]:
            # Create new preference
            self.user_preferences[user_id][tool_name] = UserToolPreference(
                user_id=user_id,
                tool_name=tool_name,
                preference_score=0.5,
                context_tags=[],
                usage_frequency=1,
                last_used=datetime.utcnow(),
                satisfaction_scores=[1.0 if success else 0.0]
            )
        else:
            # Update existing preference
            pref = self.user_preferences[user_id][tool_name]
            pref.usage_frequency += 1
            pref.last_used = datetime.utcnow()
            pref.satisfaction_scores.append(1.0 if success else 0.0)
            
            # Update preference score based on recent performance
            recent_scores = pref.satisfaction_scores[-10:]  # Last 10 uses
            pref.preference_score = sum(recent_scores) / len(recent_scores)
            
            # Factor in execution time (faster is better)
            time_bonus = max(0, (5.0 - execution_time) / 5.0) * 0.1
            pref.preference_score = min(1.0, pref.preference_score + time_bonus)
            
            pref.updated_at = datetime.utcnow()
    
    def _extract_context_pattern(self, context: Dict[str, Any]) -> str:
        """Extract a pattern string from context for grouping"""
        
        if not context:
            return "default"
        
        # Create a simplified pattern key
        pattern_parts = []
        
        if 'mode' in context:
            pattern_parts.append(f"mode_{context['mode']}")
        
        if 'user_role' in context:
            pattern_parts.append(f"role_{context['user_role']}")
        
        if 'time_of_day' in context:
            pattern_parts.append(f"time_{context['time_of_day']}")
        
        return "_".join(pattern_parts) if pattern_parts else "default"
    
    def _extract_context_tags(self, context: Dict[str, Any]) -> List[str]:
        """Extract context tags for matching"""
        
        tags = []
        if not context:
            return tags
        
        for key, value in context.items():
            if isinstance(value, (str, int, float)):
                tags.append(f"{key}_{value}")
        
        return tags
    
    def _calculate_context_relevance(self, context: Dict[str, Any]) -> float:
        """Calculate relevance score based on context"""
        
        # Simple scoring based on context richness
        if not context:
            return 0.1
        
        score = 0.5  # Base score
        
        # Bonus for rich context
        score += min(0.3, len(context) * 0.1)
        
        # Bonus for specific context types
        if 'mode' in context:
            score += 0.1
        if 'user_role' in context:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values"""
        
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear trend
        x = list(range(len(values)))
        n = len(values)
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(xi * yi for xi, yi in zip(x, values))
        sum_x2 = sum(xi * xi for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.05:
            return "improving"
        elif slope < -0.05:
            return "declining"
        else:
            return "stable"
    
    async def _load_analytics_data(self):
        """Load existing analytics data from database"""
        # This would typically load from persistent storage
        logger.info("Loaded 0 existing analytics records from database")