from typing import Dict, List, Optional, Any, Tuple
import asyncio
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import difflib

from backend.models.pattern_models import (
    WorkflowPattern, PatternExecution, PatternType, ExecutionStep,
    PatternSuggestion, FeedbackMetrics
)
from backend.database.memory_database import MemoryDatabase

logger = logging.getLogger(__name__)

class PatternLearningService:
    """Pattern learning service for workflow and tool selection optimization"""
    
    def __init__(self, memory_database: MemoryDatabase):
        self.memory_database = memory_database
        self.patterns: Dict[str, WorkflowPattern] = {}
        self.pattern_executions: List[PatternExecution] = []
        self.learning_threshold = 3  # Minimum executions to learn a pattern
        self.confidence_threshold = 0.8  # Minimum confidence to suggest pattern
        
    async def initialize(self):
        """Initialize the pattern learning service"""
        logger.info("Initializing Pattern Learning Service")
        # Load existing patterns from database
        await self._load_patterns()
        
    async def track_execution(
        self,
        session_id: str,
        user_id: str,
        execution_trace: List[Dict[str, Any]],
        success: bool,
        total_execution_time: float,
        context: Dict[str, Any] = None
    ) -> str:
        """Track a workflow execution for pattern learning"""
        
        # Convert execution trace to steps
        steps = []
        for i, trace in enumerate(execution_trace):
            step = ExecutionStep(
                step_id=i + 1,
                tool_name=trace.get('tool', ''),
                parameters=trace.get('parameters', {}),
                execution_time=trace.get('execution_time', 0.0),
                success=trace.get('success', False),
                output_summary=str(trace.get('output', ''))[:200]  # Truncate output
            )
            steps.append(step)
        
        # Create execution record
        execution = PatternExecution(
            session_id=session_id,
            user_id=user_id,
            pattern_id="",  # Will be set if pattern is found/created
            execution_time=total_execution_time,
            success=success,
            context=context or {}
        )
        
        # Try to match existing pattern or create new one
        pattern_id = await self._match_or_create_pattern(
            steps, user_id, execution, context
        )
        execution.pattern_id = pattern_id
        
        # Store execution
        self.pattern_executions.append(execution)
        
        # Update pattern statistics
        await self._update_pattern_stats(pattern_id, execution)
        
        logger.info(f"Tracked execution for pattern {pattern_id}")
        return pattern_id
    
    async def suggest_pattern(
        self,
        user_input: str,
        user_id: str,
        session_id: str,
        context: Dict[str, Any] = None
    ) -> Optional[PatternSuggestion]:
        """Suggest a learned pattern for the given input"""
        
        # Find matching patterns
        matching_patterns = await self._find_matching_patterns(
            user_input, user_id, context
        )
        
        if not matching_patterns:
            return None
        
        # Get best pattern with highest confidence
        best_pattern, confidence = matching_patterns[0]
        
        if confidence < self.confidence_threshold:
            return None
        
        suggestion = PatternSuggestion(
            pattern_id=best_pattern.pattern_id,
            user_id=user_id,
            session_id=session_id,
            confidence_score=confidence
        )
        
        logger.info(f"Suggested pattern {best_pattern.pattern_id} with confidence {confidence}")
        return suggestion
    
    async def get_pattern_by_id(self, pattern_id: str) -> Optional[WorkflowPattern]:
        """Get a pattern by its ID"""
        return self.patterns.get(pattern_id)
    
    async def get_user_patterns(self, user_id: str) -> List[WorkflowPattern]:
        """Get all patterns for a user"""
        return [p for p in self.patterns.values() if p.user_id == user_id]
    
    async def submit_pattern_feedback(
        self,
        suggestion_id: str,
        pattern_id: str,
        accepted: bool,
        rating: Optional[int] = None,
        execution_result: Optional[Dict[str, Any]] = None
    ):
        """Submit feedback for a pattern suggestion"""
        
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return
        
        # Update pattern confidence based on feedback
        if accepted and rating:
            # Positive feedback increases confidence
            pattern.confidence_score = min(1.0, pattern.confidence_score + 0.1)
            if execution_result and execution_result.get('success'):
                pattern.successful_executions += 1
                pattern.total_executions += 1
        else:
            # Negative feedback decreases confidence
            pattern.confidence_score = max(0.0, pattern.confidence_score - 0.05)
        
        pattern.updated_at = datetime.utcnow()
        
        logger.info(f"Updated pattern {pattern_id} confidence to {pattern.confidence_score}")
    
    async def get_learning_metrics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get pattern learning metrics"""
        
        patterns = list(self.patterns.values())
        if user_id:
            patterns = [p for p in patterns if p.user_id == user_id]
        
        total_patterns = len(patterns)
        confident_patterns = len([p for p in patterns if p.confidence_score >= self.confidence_threshold])
        
        # Calculate average metrics
        avg_success_rate = sum(p.success_rate for p in patterns) / max(1, total_patterns)
        avg_execution_time = sum(p.average_execution_time for p in patterns) / max(1, total_patterns)
        
        # Recent performance (last 7 days)
        recent_executions = [
            e for e in self.pattern_executions 
            if e.executed_at >= datetime.utcnow() - timedelta(days=7)
        ]
        
        if user_id:
            recent_executions = [e for e in recent_executions if e.user_id == user_id]
        
        recent_success_rate = (
            sum(1 for e in recent_executions if e.success) / max(1, len(recent_executions))
        )
        
        return {
            "total_patterns_learned": total_patterns,
            "confident_patterns": confident_patterns,
            "learning_effectiveness": confident_patterns / max(1, total_patterns),
            "average_success_rate": avg_success_rate,
            "average_execution_time": avg_execution_time,
            "recent_success_rate": recent_success_rate,
            "total_executions": len(self.pattern_executions),
            "patterns_by_type": self._get_patterns_by_type()
        }
    
    async def _match_or_create_pattern(
        self,
        steps: List[ExecutionStep],
        user_id: str,
        execution: PatternExecution,
        context: Dict[str, Any]
    ) -> str:
        """Match execution to existing pattern or create new one"""
        
        # Try to find similar pattern
        for pattern in self.patterns.values():
            if await self._is_similar_pattern(pattern.steps, steps, user_id):
                return pattern.pattern_id
        
        # Create new pattern if no match found
        pattern = WorkflowPattern(
            pattern_type=PatternType.WORKFLOW,
            name=f"Pattern_{len(self.patterns) + 1}",
            description=f"Auto-learned pattern with {len(steps)} steps",
            steps=steps,
            user_id=user_id,
            context_tags=self._extract_context_tags(context),
            total_executions=1,
            successful_executions=1 if execution.success else 0,
            confidence_score=0.3  # Initial low confidence
        )
        
        self.patterns[pattern.pattern_id] = pattern
        logger.info(f"Created new pattern {pattern.pattern_id}")
        return pattern.pattern_id
    
    async def _is_similar_pattern(
        self,
        pattern_steps: List[ExecutionStep],
        new_steps: List[ExecutionStep],
        user_id: str
    ) -> bool:
        """Check if two step sequences are similar enough to be the same pattern"""
        
        if len(pattern_steps) != len(new_steps):
            return False
        
        # Check tool sequence similarity
        pattern_tools = [step.tool_name for step in pattern_steps]
        new_tools = [step.tool_name for step in new_steps]
        
        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, pattern_tools, new_tools).ratio()
        
        return similarity >= 0.8  # 80% similarity threshold
    
    async def _find_matching_patterns(
        self,
        user_input: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> List[Tuple[WorkflowPattern, float]]:
        """Find patterns that match the user input"""
        
        matches = []
        
        for pattern in self.patterns.values():
            # Skip patterns with low confidence
            if pattern.confidence_score < 0.5:
                continue
            
            # Calculate match score
            score = await self._calculate_pattern_match_score(
                pattern, user_input, user_id, context
            )
            
            if score > 0.5:
                matches.append((pattern, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    async def _calculate_pattern_match_score(
        self,
        pattern: WorkflowPattern,
        user_input: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> float:
        """Calculate how well a pattern matches the current request"""
        
        score = 0.0
        
        # User match bonus
        if pattern.user_id == user_id:
            score += 0.3
        
        # Context similarity
        if context:
            context_tags = self._extract_context_tags(context)
            common_tags = set(pattern.context_tags) & set(context_tags)
            if common_tags:
                score += 0.3 * (len(common_tags) / max(len(pattern.context_tags), 1))
        
        # Pattern confidence
        score += 0.4 * pattern.confidence_score
        
        # Success rate bonus
        score *= pattern.success_rate
        
        return min(1.0, score)
    
    async def _update_pattern_stats(self, pattern_id: str, execution: PatternExecution):
        """Update pattern statistics after execution"""
        
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return
        
        pattern.total_executions += 1
        if execution.success:
            pattern.successful_executions += 1
        
        # Recalculate success rate
        pattern.success_rate = pattern.successful_executions / pattern.total_executions
        
        # Update average execution time
        total_time = pattern.average_execution_time * (pattern.total_executions - 1)
        pattern.average_execution_time = (total_time + execution.execution_time) / pattern.total_executions
        
        # Update confidence based on recent performance
        if pattern.total_executions >= self.learning_threshold:
            pattern.confidence_score = min(1.0, pattern.success_rate * 1.2)
        
        pattern.updated_at = datetime.utcnow()
    
    def _extract_context_tags(self, context: Dict[str, Any]) -> List[str]:
        """Extract tags from context for pattern matching"""
        
        tags = []
        
        if not context:
            return tags
        
        # Extract common context elements
        if 'mode' in context:
            tags.append(f"mode_{context['mode']}")
        
        if 'time_of_day' in context:
            tags.append(f"time_{context['time_of_day']}")
        
        if 'user_role' in context:
            tags.append(f"role_{context['user_role']}")
        
        return tags
    
    def _get_patterns_by_type(self) -> Dict[str, int]:
        """Get count of patterns by type"""
        
        type_counts = defaultdict(int)
        for pattern in self.patterns.values():
            type_counts[pattern.pattern_type.value] += 1
        
        return dict(type_counts)
    
    async def _load_patterns(self):
        """Load existing patterns from database"""
        # This would typically load from persistent storage
        # For now, initialize empty
        logger.info("Loaded 0 existing patterns from database")