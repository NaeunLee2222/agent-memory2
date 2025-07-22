import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.feedback_service import (
    FeedbackService, FeedbackCollector, FeedbackAnalyzer, FeedbackProcessor,
    FeedbackType, FeedbackPriority, FeedbackData
)
from ..models.database import Feedback, FeedbackAnalysis
from ..models.memory import MemoryService
from ..utils.exceptions import FeedbackProcessingError

@pytest.fixture
def mock_db_session():
    """Mock 데이터베이스 세션"""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def mock_memory_service():
    """Mock 메모리 서비스"""
    return AsyncMock(spec=MemoryService)

@pytest.fixture
def feedback_collector(mock_db_session, mock_memory_service):
    """피드백 수집기 테스트 픽스처"""
    return FeedbackCollector(mock_db_session, mock_memory_service)

@pytest.fixture
def feedback_analyzer(mock_db_session):
    """피드백 분석기 테스트 픽스처"""
    return FeedbackAnalyzer(mock_db_session)

@pytest.fixture
def feedback_processor(mock_db_session, mock_memory_service):
    """피드백 처리기 테스트 픽스처"""
    return FeedbackProcessor(mock_db_session, mock_memory_service)

@pytest.fixture
def feedback_service(mock_db_session, mock_memory_service):
    """피드백 서비스 테스트 픽스처"""
    return FeedbackService(mock_db_session, mock_memory_service)

class TestFeedbackCollector:
    """피드백 수집기 테스트"""
    
    @pytest.mark.asyncio
    async def test_collect_explicit_positive_feedback(self, feedback_collector, mock_db_session):
        """긍정적 명시적 피드백 수집 테스트"""
        # Given
        execution_id = "exec_123"
        rating = 4
        comment = "정말 유용했습니다!"
        user_id = "user_456"
        
        # When
        feedback_id = await feedback_collector.collect_explicit_feedback(
            execution_id, rating, comment, user_id
        )
        
        # Then
        assert feedback_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        # 저장된 피드백 검증
        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.execution_id == execution_id
        assert call_args.feedback_type == FeedbackType.EXPLICIT_POSITIVE.value
        assert call_args.content["rating"] == rating
        assert call_args.content["comment"] == comment
        assert call_args.content["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_collect_explicit_negative_feedback(self, feedback_collector, mock_db_session):
        """부정적 명시적 피드백 수집 테스트"""
        # Given
        execution_id = "exec_123"
        rating = 2
        comment = "응답이 부정확했습니다."
        user_id = "user_456"
        
        # When
        feedback_id = await feedback_collector.collect_explicit_feedback(
            execution_id, rating, comment, user_id
        )
        
        # Then
        assert feedback_id is not None
        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.feedback_type == FeedbackType.EXPLICIT_NEGATIVE.value
    
    @pytest.mark.asyncio
    async def test_collect_implicit_success_feedback(self, feedback_collector, mock_db_session):
        """암시적 성공 피드백 수집 테스트"""
        # Given
        execution_id = "exec_123"
        performance_metrics = {
            "execution_time": 15.5,
            "error_count": 0,
            "completion_rate": 0.95
        }
        
        # When
        feedback_id = await feedback_collector.collect_implicit_feedback(
            execution_id, performance_metrics
        )
        
        # Then
        assert feedback_id is not None
        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.feedback_type == FeedbackType.IMPLICIT_SUCCESS.value
        assert call_args.content == performance_metrics
    
    @pytest.mark.asyncio
    async def test_collect_implicit_failure_feedback(self, feedback_collector, mock_db_session):
        """암시적 실패 피드백 수집 테스트"""
        # Given
        execution_id = "exec_123"
        performance_metrics = {
            "execution_time": 45.0,
            "error_count": 3,
            "completion_rate": 0.2
        }
        
        # When
        feedback_id = await feedback_collector.collect_implicit_feedback(
            execution_id, performance_metrics
        )
        
        # Then
        assert feedback_id is not None
        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.feedback_type == FeedbackType.IMPLICIT_FAILURE.value
    
    @pytest.mark.asyncio
    async def test_collect_performance_feedback(self, feedback_collector, mock_db_session):
        """성능 피드백 수집 테스트"""
        # Given
        execution_id = "exec_123"
        metrics = {
            "cpu_usage": 75.5,
            "memory_usage": 60.2,
            "response_time": 2.3
        }
        
        # When
        feedback_id = await feedback_collector.collect_performance_feedback(
            execution_id, metrics
        )
        
        # Then
        assert feedback_id is not None
        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.feedback_type == FeedbackType.PERFORMANCE_METRIC.value
        assert call_args.content == metrics

class TestFeedbackAnalyzer:
    """피드백 분석기 테스트"""
    
    @pytest.mark.asyncio
    async def test_analyze_explicit_positive_feedback(self, feedback_analyzer):
        """긍정적 명시적 피드백 분석 테스트"""
        # Given
        feedback = MagicMock(spec=Feedback)
        feedback.id = "feedback_123"
        feedback.feedback_type = "explicit_positive"
        feedback.content = {
            "rating": 5,
            "comment": "매우 만족스러운 결과였습니다!"
        }
        
        # When
        result = await feedback_analyzer._analyze_explicit_feedback(feedback)
        
        # Then
        assert result["sentiment_score"] == 1.0  # 최고 점수
        assert result["confidence_level"] == 0.8
        assert "사용자 만족도 높음" in result["key_insights"]
        assert len(result["recommended_actions"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_explicit_negative_feedback(self, feedback_analyzer):
        """부정적 명시적 피드백 분석 테스트"""
        # Given
        feedback = MagicMock(spec=Feedback)
        feedback.id = "feedback_123"
        feedback.feedback_type = "explicit_negative"
        feedback.content = {
            "rating": 1,
            "comment": "응답이 느리고 부정확했습니다."
        }
        
        # When
        result = await feedback_analyzer._analyze_explicit_feedback(feedback)
        
        # Then
        assert result["sentiment_score"] == -1.0  # 최저 점수
        assert "사용자 불만족 - 개선 필요" in result["key_insights"]
        assert "응답 속도 최적화" in result["recommended_actions"]
    
    @pytest.mark.asyncio
    async def test_analyze_implicit_feedback(self, feedback_analyzer):
        """암시적 피드백 분석 테스트"""
        # Given
        feedback = MagicMock(spec=Feedback)
        feedback.id = "feedback_123"
        feedback.feedback_type = "implicit_success"
        feedback.content = {
            "execution_time": 10.0,
            "error_count": 0,
            "completion_rate": 1.0
        }
        
        # When
        result = await feedback_analyzer._analyze_implicit_feedback(feedback)
        
        # Then
        assert result["sentiment_score"] > 0  # 긍정적 점수
        assert result["confidence_level"] == 0.6
        assert "전체 성능 점수" in result["key_insights"][0]
    
    @pytest.mark.asyncio
    async def test_analyze_performance_feedback(self, feedback_analyzer):
        """성능 피드백 분석 테스트"""
        # Given
        feedback = MagicMock(spec=Feedback)
        feedback.id = "feedback_123"
        feedback.feedback_type = "performance_metric"
        feedback.content = {
            "cpu_usage": 85.0,
            "memory_usage": 70.0,
            "response_time": 3.5
        }
        
        # When
        result = await feedback_analyzer._analyze_performance_feedback(feedback)
        
        # Then
        assert "성능 등급: C" in result["key_insights"]
        assert "CPU 사용량 최적화" in result["recommended_actions"]
        assert result["confidence_level"] == 0.9

class TestFeedbackProcessor:
    """피드백 처리기 테스트"""
    
    @pytest.mark.asyncio
    async def test_identify_common_issues(self, feedback_processor):
        """공통 이슈 식별 테스트"""
        # Given
        mock_feedbacks = []
        for i in range(5):
            feedback = MagicMock(spec=Feedback)
            feedback.id = f"feedback_{i}"
            feedback.analysis = [MagicMock()]
            feedback.analysis[0].analysis_result = {
                "key_insights": ["응답 속도 느림", "정확도 부족"]
            }
            mock_feedbacks.append(feedback)
        
        # When
        issues = await feedback_processor._identify_common_issues(mock_feedbacks)
        
        # Then
        assert len(issues) == 2
        assert issues[0]["issue"] in ["응답 속도 느림", "정확도 부족"]
        assert issues[0]["frequency"] == 5
        assert issues[0]["impact"] == "high"
    
    @pytest.mark.asyncio
    async def test_identify_success_patterns(self, feedback_processor):
        """성공 패턴 식별 테스트"""
        # Given
        mock_feedbacks = []
        for i in range(3):
            feedback = MagicMock(spec=Feedback)
            feedback.id = f"feedback_{i}"
            feedback.analysis = [MagicMock()]
            feedback.analysis[0].analysis_result = {
                "key_insights": ["정확한 답변", "빠른 응답"]
            }
            mock_feedbacks.append(feedback)
        
        # When
        patterns = await feedback_processor._identify_success_patterns(mock_feedbacks)
        
        # Then
        assert len(patterns) == 2
        assert patterns[0]["pattern"] in ["정확한 답변", "빠른 응답"]
        assert patterns[0]["frequency"] == 3
    
    @pytest.mark.asyncio
    async def test_prioritize_improvements(self, feedback_processor):
        """개선사항 우선순위 결정 테스트"""
        # Given
        issues = [
            {"issue": "응답 속도 느림", "frequency": 10, "impact": "high"},
            {"issue": "정확도 부족", "frequency": 5, "impact": "medium"}
        ]
        patterns = [
            {"pattern": "정확한 답변", "frequency": 8, "reliability": "high"}
        ]
        
        # When
        improvements = await feedback_processor._prioritize_improvements(issues, patterns)
        
        # Then
        assert len(improvements) == 3  # 2개 이슈 + 1개 패턴
        assert improvements[0]["type"] == "issue_resolution"
        assert improvements[0]["priority"] == "high"
        assert improvements[2]["type"] == "pattern_reinforcement"

class TestFeedbackService:
    """피드백 서비스 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_submit_user_feedback_positive(self, feedback_service, mock_db_session):
        """긍정적 사용자 피드백 제출 테스트"""
        # Given
        execution_id = "exec_123"
        rating = 4
        comment = "좋은 결과였습니다."
        user_id = "user_456"
        
        # When
        result = await feedback_service.submit_user_feedback(
            execution_id, rating, comment, user_id
        )
        
        # Then
        assert result["status"] == "submitted"
        assert "feedback_id" in result
        assert result["message"] == "피드백이 성공적으로 제출되었습니다."
        mock_db_session.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_user_feedback_negative_immediate_analysis(self, feedback_service, mock_db_session):
        """부정적 사용자 피드백 즉시 분석 테스트"""
        # Given
        execution_id = "exec_123"
        rating = 1
        comment = "매우 불만족스럽습니다."
        user_id = "user_456"
        
        # Mock get 메서드
        mock_feedback = MagicMock(spec=Feedback)
        mock_feedback.id = "feedback_123"
        mock_feedback.feedback_type = "explicit_negative"
        mock_feedback.content = {"rating": 1, "comment": comment}
        mock_db_session.get.return_value = mock_feedback
        
        # When
        result = await feedback_service.submit_user_feedback(
            execution_id, rating, comment, user_id
        )
        
        # Then
        assert result["status"] == "submitted"
        mock_db_session.get.assert_called_once()  # 즉시 분석을 위한 조회
        assert mock_db_session.commit.call_count == 2  # 저장 + 분석 결과 저장
    
    @pytest.mark.asyncio
    async def test_process_system_feedback(self, feedback_service, mock_db_session):
        """시스템 피드백 처리 테스트"""
        # Given
        execution_id = "exec_123"
        performance_metrics = {
            "execution_time": 25.0,
            "error_count": 0,
            "completion_rate": 0.9,
            "cpu_usage": 65.0,
            "memory_usage": 45.0,
            "response_time": 2.1
        }
        
        # When
        result = await feedback_service.process_system_feedback(
            execution_id, performance_metrics
        )
        
        # Then
        assert result["status"] == "processed"
        assert len(result["feedback_ids"]) == 1
        assert result["message"] == "시스템 피드백이 처리되었습니다."
    
    @pytest.mark.asyncio
    async def test_get_feedback_summary(self, feedback_service, mock_db_session):
        """피드백 요약 조회 테스트"""
        # Given
        agent_id = "agent_123"
        days = 30
        
        # Mock 쿼리 결과
        mock_result = MagicMock()
        mock_stats = MagicMock()
        mock_stats.total_count = 100
        mock_stats.positive_ratio = 0.75
        mock_result.first.return_value = mock_stats
        mock_db_session.execute.return_value = mock_result
        
        # When
        summary = await feedback_service.get_feedback_summary(agent_id, days)
        
        # Then
        assert summary["period_days"] == days
        assert summary["total_feedback_count"] == 100
        assert summary["positive_feedback_ratio"] == 0.75
        assert summary["analysis_coverage"] == "100%"
        assert "last_updated" in summary

class TestFeedbackIntegration:
    """피드백 시스템 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_complete_feedback_workflow(self, feedback_service, mock_db_session, mock_memory_service):
        """완전한 피드백 워크플로우 테스트"""
        # Given
        execution_id = "exec_123"
        agent_id = "agent_456"
        
        # 1. 사용자 피드백 제출
        await feedback_service.submit_user_feedback(
            execution_id, 4, "좋은 결과였습니다.", "user_123"
        )
        
        # 2. 시스템 피드백 처리
        await feedback_service.process_system_feedback(
            execution_id, {
                "execution_time": 15.0,
                "error_count": 0,
                "completion_rate": 1.0
            }
        )
        
        # 3. 배치 분석 실행
        batch_result = await feedback_service.run_feedback_analysis_batch()
        
        # 4. 에이전트 개선 트리거
        improvement_result = await feedback_service.trigger_agent_improvement(agent_id)
        
        # Then
        assert batch_result["status"] == "completed"
        assert improvement_result["status"] == "completed"
        assert improvement_result["agent_id"] == agent_id
    
    @pytest.mark.asyncio
    async def test_feedback_error_handling(self, feedback_service):
        """피드백 오류 처리 테스트"""
        # Given - 잘못된 데이터
        execution_id = "invalid_exec"
        rating = 10  # 범위 초과
        comment = ""
        user_id = ""
        
        # When & Then
        with pytest.raises(FeedbackProcessingError):
            await feedback_service.submit_user_feedback(
                execution_id, rating, comment, user_id
            )
    
    @pytest.mark.asyncio
    async def test_concurrent_feedback_processing(self, feedback_service):
        """동시 피드백 처리 테스트"""
        # Given
        tasks = []
        for i in range(10):
            task = feedback_service.submit_user_feedback(
                f"exec_{i}", 4, f"피드백 {i}", f"user_{i}"
            )
            tasks.append(task)
        
        # When
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Then
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 10

@pytest.mark.performance
class TestFeedbackPerformance:
    """피드백 시스템 성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_batch_analysis_performance(self, feedback_analyzer, mock_db_session):
        """배치 분석 성능 테스트"""
        import time
        
        # Given
        mock_feedbacks = []
        for i in range(100):
            feedback = MagicMock(spec=Feedback)
            feedback.id = f"feedback_{i}"
            feedback.feedback_type = "explicit_positive"
            feedback.content = {"rating": 4, "comment": f"테스트 {i}"}
            feedback.analyzed_at = None
            mock_feedbacks.append(feedback)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_feedbacks
        mock_db_session.execute.return_value = mock_result
        
        # When
        start_time = time.time()
        await feedback_analyzer.analyze_feedback_batch(limit=100)
        end_time = time.time()
        
        # Then
        processing_time = end_time - start_time
        assert processing_time < 10.0  # 10초 이내 처리 목표
        assert len(mock_feedbacks) == 100

@pytest.mark.load
class TestFeedbackLoad:
    """피드백 시스템 부하 테스트"""
    
    @pytest.mark.asyncio
    async def test_high_volume_feedback_collection(self, feedback_collector, mock_db_session):
        """대용량 피드백 수집 테스트"""
        # Given
        tasks = []
        for i in range(1000):
            task = feedback_collector.collect_explicit_feedback(
                f"exec_{i}", 4, f"피드백 {i}", f"user_{i % 100}"
            )
            tasks.append(task)
        
        # When
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Then
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failure_rate = (len(tasks) - len(successful_results)) / len(tasks)
        assert failure_rate < 0.01  # 1% 미만 실패율 목표
