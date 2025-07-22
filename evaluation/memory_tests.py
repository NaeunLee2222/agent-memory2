import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.memory import (
    MemoryService, WorkingMemory, EpisodicMemory, SemanticMemory, ProceduralMemory,
    MemoryType, MemoryPriority
)
from ..models.database import Agent, AgentExecution, MemoryRecord
from ..core.config import settings
from ..utils.exceptions import MemoryError

@pytest.fixture
def mock_db_session():
    """Mock 데이터베이스 세션"""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def mock_vector_store():
    """Mock 벡터 저장소"""
    return AsyncMock()

@pytest.fixture
def memory_service(mock_db_session, mock_vector_store):
    """메모리 서비스 테스트 픽스처"""
    service = MemoryService(mock_db_session)
    service.vector_store = mock_vector_store
    return service

@pytest.fixture
def sample_agent():
    """샘플 에이전트 데이터"""
    return {
        "id": "agent_123",
        "name": "테스트 에이전트",
        "mode": "flow",
        "config": {"max_memory": 1000}
    }

@pytest.fixture
def sample_execution():
    """샘플 실행 데이터"""
    return {
        "id": "exec_123",
        "agent_id": "agent_123",
        "status": "completed",
        "started_at": datetime.utcnow(),
        "completed_at": datetime.utcnow()
    }

class TestWorkingMemory:
    """작업 메모리 테스트"""
    
    @pytest.mark.asyncio
    async def test_store_working_memory(self, memory_service, mock_db_session):
        """작업 메모리 저장 테스트"""
        # Given
        agent_id = "agent_123"
        execution_id = "exec_123"
        context_data = {
            "current_step": "데이터 분석",
            "variables": {"user_input": "분석 요청", "progress": 50},
            "next_actions": ["결과 정리", "리포트 생성"]
        }
        
        # When
        memory_id = await memory_service.store_working_memory(
            agent_id, execution_id, context_data
        )
        
        # Then
        assert memory_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        # 저장된 메모리 데이터 검증
        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.agent_id == agent_id
        assert call_args.memory_type == MemoryType.WORKING.value
        assert call_args.content == context_data
    
    @pytest.mark.asyncio
    async def test_retrieve_working_memory(self, memory_service, mock_db_session):
        """작업 메모리 조회 테스트"""
        # Given
        execution_id = "exec_123"
        mock_memory = MagicMock(spec=MemoryRecord)
        mock_memory.content = {
            "current_step": "데이터 분석",
            "variables": {"progress": 75}
        }
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_memory
        mock_db_session.execute.return_value = mock_result
        
        # When
        context = await memory_service.get_working_memory(execution_id)
        
        # Then
        assert context is not None
        assert context["current_step"] == "데이터 분석"
        assert context["variables"]["progress"] == 75
    
    @pytest.mark.asyncio
    async def test_update_working_memory(self, memory_service, mock_db_session):
        """작업 메모리 업데이트 테스트"""
        # Given
        execution_id = "exec_123"
        updates = {"variables": {"progress": 100}, "status": "completed"}
        
        mock_memory = MagicMock(spec=MemoryRecord)
        mock_memory.content = {"current_step": "데이터 분석", "variables": {"progress": 50}}
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_memory
        mock_db_session.execute.return_value = mock_result
        
        # When
        await memory_service.update_working_memory(execution_id, updates)
        
        # Then
        assert mock_memory.content["variables"]["progress"] == 100
        assert mock_memory.content["status"] == "completed"
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_working_memory_cleanup(self, memory_service, mock_db_session):
        """작업 메모리 정리 테스트"""
        # Given
        cutoff_date = datetime.utcnow() - timedelta(hours=24)
        
        # When
        cleanup_count = await memory_service.cleanup_working_memory(cutoff_date)
        
        # Then
        mock_db_session.execute.assert_called()
        mock_db_session.commit.assert_called_once()
        assert isinstance(cleanup_count, int)

class TestEpisodicMemory:
    """에피소드 메모리 테스트"""
    
    @pytest.mark.asyncio
    async def test_store_episodic_memory(self, memory_service, mock_db_session, mock_vector_store):
        """에피소드 메모리 저장 테스트"""
        # Given
        agent_id = "agent_123"
        episode_data = {
            "task": "문서 요약",
            "input": "긴 문서 내용...",
            "output": "요약된 내용",
            "result": "success",
            "duration": 120.5,
            "tools_used": ["text_processor", "summarizer"]
        }
        
        mock_vector_store.add_document.return_value = "vector_123"
        
        # When
        memory_id = await memory_service.store_episodic_memory(
            agent_id, episode_data
        )
        
        # Then
        assert memory_id is not None
        mock_db_session.add.assert_called_once()
        mock_vector_store.add_document.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar_episodes(self, memory_service, mock_vector_store):
        """유사 에피소드 검색 테스트"""
        # Given
        agent_id = "agent_123"
        query = "문서 요약 작업"
        
        mock_vector_store.search_similar.return_value = [
            {"id": "vector_1", "score": 0.95, "metadata": {"memory_id": "mem_1"}},
            {"id": "vector_2", "score": 0.87, "metadata": {"memory_id": "mem_2"}}
        ]
        
        # When
        similar_episodes = await memory_service.search_similar_episodes(
            agent_id, query, limit=5
        )
        
        # Then
        assert len(similar_episodes) == 2
        assert similar_episodes[0]["score"] == 0.95
        mock_vector_store.search_similar.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_episodes(self, memory_service, mock_db_session):
        """최근 에피소드 조회 테스트"""
        # Given
        agent_id = "agent_123"
        days = 7
        
        mock_episodes = [
            MagicMock(spec=MemoryRecord),
            MagicMock(spec=MemoryRecord),
            MagicMock(spec=MemoryRecord)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_episodes
        mock_db_session.execute.return_value = mock_result
        
        # When
        recent_episodes = await memory_service.get_recent_episodes(agent_id, days)
        
        # Then
        assert len(recent_episodes) == 3
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_episode_patterns(self, memory_service, mock_db_session):
        """에피소드 패턴 분석 테스트"""
        # Given
        agent_id = "agent_123"
        
        mock_episodes = []
        for i in range(10):
            episode = MagicMock(spec=MemoryRecord)
            episode.content = {
                "task": "문서 요약" if i % 2 == 0 else "데이터 분석",
                "result": "success" if i < 8 else "failure",
                "duration": 100 + i * 10
            }
            mock_episodes.append(episode)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_episodes
        mock_db_session.execute.return_value = mock_result
        
        # When
        patterns = await memory_service.analyze_episode_patterns(agent_id)
        
        # Then
        assert "task_frequency" in patterns
        assert "success_rate" in patterns
        assert "average_duration" in patterns
        assert patterns["success_rate"] == 0.8  # 8/10 성공

class TestSemanticMemory:
    """시맨틱 메모리 테스트"""
    
    @pytest.mark.asyncio
    async def test_store_semantic_memory(self, memory_service, mock_db_session, mock_vector_store):
        """시맨틱 메모리 저장 테스트"""
        # Given
        agent_id = "agent_123"
        concept = "문서_요약_모범사례"
        knowledge = {
            "규칙": ["중요한 내용 우선", "간결하게 작성", "핵심 키워드 포함"],
            "예시": {"입력": "긴 문서", "출력": "요약본"},
            "주의사항": ["정확성 확보", "원문 의미 보존"]
        }
        
        mock_vector_store.add_document.return_value = "vector_123"
        
        # When
        memory_id = await memory_service.store_semantic_memory(
            agent_id, concept, knowledge
        )
        
        # Then
        assert memory_id is not None
        mock_db_session.add.assert_called_once()
        mock_vector_store.add_document.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_semantic_memory(self, memory_service, mock_db_session):
        """시맨틱 메모리 조회 테스트"""
        # Given
        agent_id = "agent_123"
        concept = "문서_요약_모범사례"
        
        mock_memory = MagicMock(spec=MemoryRecord)
        mock_memory.content = {
            "규칙": ["중요한 내용 우선", "간결하게 작성"],
            "예시": {"입력": "긴 문서", "출력": "요약본"}
        }
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_memory
        mock_db_session.execute.return_value = mock_result
        
        # When
        knowledge = await memory_service.get_semantic_memory(agent_id, concept)
        
        # Then
        assert knowledge is not None
        assert "규칙" in knowledge
        assert len(knowledge["규칙"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_related_concepts(self, memory_service, mock_vector_store):
        """관련 개념 검색 테스트"""
        # Given
        agent_id = "agent_123"
        query = "문서 처리 방법"
        
        mock_vector_store.search_similar.return_value = [
            {"id": "vector_1", "score": 0.92, "metadata": {"concept": "문서_요약_모범사례"}},
            {"id": "vector_2", "score": 0.85, "metadata": {"concept": "문서_분석_기법"}}
        ]
        
        # When
        related_concepts = await memory_service.search_related_concepts(
            agent_id, query, limit=5
        )
        
        # Then
        assert len(related_concepts) == 2
        assert related_concepts[0]["concept"] == "문서_요약_모범사례"
        mock_vector_store.search_similar.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_semantic_memory(self, memory_service, mock_db_session):
        """시맨틱 메모리 업데이트 테스트"""
        # Given
        agent_id = "agent_123"
        concept = "문서_요약_모범사례"
        new_knowledge = {
            "새로운_규칙": ["사용자 의도 파악", "적절한 길이 조절"]
        }
        
        mock_memory = MagicMock(spec=MemoryRecord)
        mock_memory.content = {"규칙": ["기존 규칙"]}
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_memory
        mock_db_session.execute.return_value = mock_result
        
        # When
        await memory_service.update_semantic_memory(agent_id, concept, new_knowledge)
        
        # Then
        assert "새로운_규칙" in mock_memory.content
        mock_db_session.commit.assert_called_once()

class TestProceduralMemory:
    """절차 메모리 테스트"""
    
    @pytest.mark.asyncio
    async def test_store_procedural_memory(self, memory_service, mock_db_session):
        """절차 메모리 저장 테스트"""
        # Given
        agent_id = "agent_123"
        process_name = "문서_요약_프로세스"
        steps = {
            "1": "문서 읽기 및 이해",
            "2": "핵심 내용 식별",
            "3": "요약본 작성",
            "4": "검토 및 수정"
        }
        metadata = {"complexity": "medium", "success_rate": 0.9}
        
        # When
        memory_id = await memory_service.store_procedural_memory(
            agent_id, process_name, steps, metadata
        )
        
        # Then
        assert memory_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_procedural_memory(self, memory_service, mock_db_session):
        """절차 메모리 조회 테스트"""
        # Given
        agent_id = "agent_123"
        process_name = "문서_요약_프로세스"
        
        mock_memory = MagicMock(spec=MemoryRecord)
        mock_memory.content = {
            "steps": {
                "1": "문서 읽기 및 이해",
                "2": "핵심 내용 식별"
            },
            "metadata": {"complexity": "medium"}
        }
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_memory
        mock_db_session.execute.return_value = mock_result
        
        # When
        process = await memory_service.get_procedural_memory(agent_id, process_name)
        
        # Then
        assert process is not None
        assert "steps" in process
        assert len(process["steps"]) == 2
    
    @pytest.mark.asyncio
    async def test_optimize_procedural_memory(self, memory_service, mock_db_session):
        """절차 메모리 최적화 테스트"""
        # Given
        agent_id = "agent_123"
        process_name = "문서_요약_프로세스"
        performance_data = {
            "execution_time": 120.0,
            "success_rate": 0.95,
            "user_satisfaction": 4.2
        }
        
        mock_memory = MagicMock(spec=MemoryRecord)
        mock_memory.content = {
            "steps": {"1": "기존 단계"},
            "performance_history": []
        }
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_memory
        mock_db_session.execute.return_value = mock_result
        
        # When
        await memory_service.optimize_procedural_memory(
            agent_id, process_name, performance_data
        )
        
        # Then
        assert len(mock_memory.content["performance_history"]) == 1
        assert mock_memory.content["performance_history"][0] == performance_data
        mock_db_session.commit.assert_called_once()

class TestMemoryIntegration:
    """메모리 시스템 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_cross_memory_search(self, memory_service, mock_vector_store):
        """메모리 간 교차 검색 테스트"""
        # Given
        agent_id = "agent_123"
        query = "문서 요약 최적화"
        
        # 에피소드 메모리 결과
        mock_vector_store.search_similar.side_effect = [
            [{"id": "ep1", "score": 0.9, "metadata": {"memory_id": "mem1"}}],
            [{"id": "sem1", "score": 0.85, "metadata": {"concept": "요약_기법"}}]
        ]
        
        # When
        results = await memory_service.search_across_memories(agent_id, query)
        
        # Then
        assert "episodic" in results
        assert "semantic" in results
        assert len(results["episodic"]) == 1
        assert len(results["semantic"]) == 1
    
    @pytest.mark.asyncio
    async def test_memory_consolidation(self, memory_service, mock_db_session):
        """메모리 통합 처리 테스트"""
        # Given
        agent_id = "agent_123"
        
        # Mock 최근 에피소드들
        mock_episodes = []
        for i in range(5):
            episode = MagicMock(spec=MemoryRecord)
            episode.content = {
                "task": "문서 요약",
                "result": "success",
                "patterns": ["패턴A", "패턴B"]
            }
            mock_episodes.append(episode)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_episodes
        mock_db_session.execute.return_value = mock_result
        
        # When
        consolidation_result = await memory_service.consolidate_memories(agent_id)
        
        # Then
        assert "patterns_identified" in consolidation_result
        assert "knowledge_extracted" in consolidation_result
        assert consolidation_result["episodes_processed"] == 5
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_for_execution(self, memory_service, mock_db_session, mock_vector_store):
        """실행을 위한 메모리 조회 테스트"""
        # Given
        agent_id = "agent_123"
        task_description = "긴 기술 문서를 요약해주세요"
        context = {"user_preference": "간결한 스타일"}
        
        # Mock 관련 메모리들
        mock_vector_store.search_similar.return_value = [
            {"id": "ep1", "score": 0.9, "metadata": {"memory_id": "mem1"}}
        ]
        
        mock_episodic = MagicMock(spec=MemoryRecord)
        mock_episodic.content = {
            "task": "기술 문서 요약",
            "successful_approach": "단계별 요약"
        }
        
        mock_semantic = MagicMock(spec=MemoryRecord)
        mock_semantic.content = {
            "기술문서_요약규칙": ["전문용어 설명", "구조화된 정리"]
        }
        
        mock_procedural = MagicMock(spec=MemoryRecord)
        mock_procedural.content = {
            "steps": {
                "1": "문서 구조 파악",
                "2": "핵심 내용 추출",
                "3": "요약본 작성"
            }
        }
        
        mock_db_session.get.side_effect = [mock_episodic, mock_semantic, mock_procedural]
        
        # When
        relevant_memories = await memory_service.get_relevant_memories_for_task(
            agent_id, task_description, context
        )
        
        # Then
        assert "episodic" in relevant_memories
        assert "semantic" in relevant_memories
        assert "procedural" in relevant_memories

class TestMemoryPerformance:
    """메모리 시스템 성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_memory_storage_performance(self, memory_service, mock_db_session):
        """메모리 저장 성능 테스트"""
        import time
        
        # Given
        agent_id = "agent_123"
        large_data = {"content": "x" * 10000}  # 10KB 데이터
        
        # When
        start_time = time.time()
        tasks = []
        for i in range(100):
            task = memory_service.store_episodic_memory(
                agent_id, {**large_data, "id": i}
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Then
        processing_time = end_time - start_time
        assert processing_time < 5.0  # 5초 이내 목표
        assert mock_db_session.add.call_count == 100
    
    @pytest.mark.asyncio
    async def test_memory_search_performance(self, memory_service, mock_vector_store):
        """메모리 검색 성능 테스트"""
        import time
        
        # Given
        agent_id = "agent_123"
        query = "문서 요약 작업"
        
        mock_vector_store.search_similar.return_value = [
            {"id": f"result_{i}", "score": 0.9 - i*0.01} 
            for i in range(10)
        ]
        
        # When
        start_time = time.time()
        tasks = []
        for i in range(50):
            task = memory_service.search_similar_episodes(agent_id, f"{query} {i}")
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Then
        processing_time = end_time - start_time
        assert processing_time < 3.0  # 3초 이내 목표
        assert mock_vector_store.search_similar.call_count == 50
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_performance(self, memory_service, mock_db_session):
        """메모리 정리 성능 테스트"""
        import time
        
        # Given
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # When
        start_time = time.time()
        cleanup_result = await memory_service.cleanup_old_memories(cutoff_date)
        end_time = time.time()
        
        # Then
        processing_time = end_time - start_time
        assert processing_time < 2.0  # 2초 이내 목표
        assert "cleaned_count" in cleanup_result

class TestMemoryErrorHandling:
    """메모리 시스템 오류 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, memory_service, mock_db_session):
        """데이터베이스 연결 오류 처리 테스트"""
        # Given
        mock_db_session.add.side_effect = Exception("DB 연결 실패")
        
        # When & Then
        with pytest.raises(MemoryError):
            await memory_service.store_working_memory(
                "agent_123", "exec_123", {"test": "data"}
            )
    
    @pytest.mark.asyncio
    async def test_vector_store_error(self, memory_service, mock_vector_store):
        """벡터 저장소 오류 처리 테스트"""
        # Given
        mock_vector_store.add_document.side_effect = Exception("벡터 저장 실패")
        
        # When & Then
        with pytest.raises(MemoryError):
            await memory_service.store_episodic_memory(
                "agent_123", {"test": "episode"}
            )
    
    @pytest.mark.asyncio
    async def test_memory_size_limit_error(self, memory_service):
        """메모리 크기 제한 오류 처리 테스트"""
        # Given
        agent_id = "agent_123"
        large_content = {"data": "x" * 1000000}  # 1MB 데이터
        
        # When & Then
        with pytest.raises(MemoryError, match="메모리 크기 제한"):
            await memory_service.store_working_memory(
                agent_id, "exec_123", large_content
            )

@pytest.mark.load
class TestMemoryLoad:
    """메모리 시스템 부하 테스트"""
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, memory_service, mock_db_session):
        """동시 메모리 작업 테스트"""
        # Given
        agent_id = "agent_123"
        
        # When
        tasks = []
        
        # 다양한 메모리 작업 동시 실행
        for i in range(20):
            if i % 4 == 0:
                task = memory_service.store_working_memory(
                    agent_id, f"exec_{i}", {"step": i}
                )
            elif i % 4 == 1:
                task = memory_service.store_episodic_memory(
                    agent_id, {"episode": i}
                )
            elif i % 4 == 2:
                task = memory_service.store_semantic_memory(
                    agent_id, f"concept_{i}", {"knowledge": i}
                )
            else:
                task = memory_service.store_procedural_memory(
                    agent_id, f"process_{i}", {"steps": {1: f"step_{i}"}}
                )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Then
        successful_operations = [r for r in results if not isinstance(r, Exception)]
        failure_rate = (len(tasks) - len(successful_operations)) / len(tasks)
        assert failure_rate < 0.05  # 5% 미만 실패율 목표