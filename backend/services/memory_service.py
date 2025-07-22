# 1. backend/services/memory_service.py - 상대 임포트를 절대 임포트로 수정

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
from dataclasses import asdict

# 상대 임포트를 절대 임포트로 변경
from models.memory import MemoryType, MemoryData, MemoryMetrics
from database.memory_database import MemoryDatabase
from utils.logger import get_logger
# from utils.config import config  # 이 라인이 문제를 일으킬 수 있으므로 제거하거나 수정

logger = get_logger(__name__)

# 설정을 직접 정의하거나 환경변수에서 가져오기
import os

class MemoryConfig:
    MAX_MEMORIES_PER_AGENT = int(os.getenv("MAX_MEMORIES_PER_AGENT", 10000))
    MAX_STORAGE_PER_AGENT = int(os.getenv("MAX_STORAGE_PER_AGENT", 1000000000))  # 1GB
    DEFAULT_TTL = int(os.getenv("DEFAULT_TTL", 3600))  # 1시간
    CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", 300))  # 5분

config = MemoryConfig()

class MemoryService:
    def __init__(self, database: MemoryDatabase):
        self.database = database
        self.max_memories_per_agent = config.MAX_MEMORIES_PER_AGENT
        self.max_storage_per_agent = config.MAX_STORAGE_PER_AGENT
        self.default_ttl = config.DEFAULT_TTL
        self.cleanup_interval = config.CLEANUP_INTERVAL
        
        # 캐시 및 통계
        self.memory_cache = {}
        self.access_stats = {
            'total_stores': 0,
            'total_retrievals': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 백그라운드 정리 작업
        self._cleanup_task = None
        
    async def initialize(self):
        """메모리 서비스 초기화"""
        try:
            logger.info("Initializing memory service...")
            
            # 백그라운드 정리 작업 시작
            self._cleanup_task = asyncio.create_task(self._background_cleanup())
            
            logger.info("Memory service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory service: {str(e)}")
            raise

    async def _background_cleanup(self):
        """백그라운드 정리 작업"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_memories()
            except Exception as e:
                logger.error(f"Error in background cleanup: {str(e)}")
                await asyncio.sleep(60)  # 에러 시 1분 대기

    async def store_memory(self, memory_data: MemoryData) -> str:
        """메모리 저장"""
        try:
            # 용량 확인
            await self._check_capacity(memory_data.agent_id)
            
            # TTL 설정
            if memory_data.ttl and not memory_data.expires_at:
                memory_data.expires_at = datetime.utcnow() + timedelta(seconds=memory_data.ttl)
            
            # 데이터베이스에 저장
            memory_id = await self.database.store_memory(memory_data)
            
            # 통계 업데이트
            self.access_stats['total_stores'] += 1
            
            logger.info(f"Stored memory {memory_id} for agent {memory_data.agent_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise

    async def retrieve_memories(
        self, 
        agent_id: str, 
        memory_type: Optional[MemoryType] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[MemoryData]:
        """메모리 검색"""
        try:
            memories = await self.database.retrieve_memories(
                agent_id=agent_id,
                memory_type=memory_type,
                filters=filters,
                limit=limit,
                order_by=order_by
            )
            
            # 통계 업데이트
            self.access_stats['total_retrievals'] += 1
            
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            raise

    async def search_memories(
        self,
        agent_id: str,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[MemoryData]:
        """메모리 검색"""
        try:
            results = await self.database.search_memories(
                agent_id=agent_id,
                query=query,
                memory_types=memory_types,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            return results
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            raise

    async def update_memory(
        self, 
        memory_id: str,
        content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """메모리 업데이트"""
        try:
            success = await self.database.update_memory(
                memory_id=memory_id,
                content=content,
                metadata=metadata,
                context=context
            )
            return success
            
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")
            raise

    async def delete_memory(self, memory_id: str) -> bool:
        """메모리 삭제"""
        try:
            success = await self.database.delete_memory(memory_id)
            return success
            
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            raise

    async def get_memory_by_id(self, memory_id: str) -> Optional[MemoryData]:
        """ID로 메모리 조회"""
        try:
            memories = await self.database.retrieve_memories(
                filters={'memory_id': memory_id},
                limit=1
            )
            return memories[0] if memories else None
            
        except Exception as e:
            logger.error(f"Error getting memory by ID: {str(e)}")
            raise

    async def get_memory_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """메모리 통계 조회"""
        try:
            stats = await self.database.get_memory_stats(agent_id=agent_id)
            
            # 서비스 레벨 통계 추가
            stats.update(self.access_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            raise

    async def get_memory_metrics(self, agent_id: str) -> MemoryMetrics:
        """메모리 메트릭 계산"""
        try:
            memories = await self.retrieve_memories(agent_id=agent_id, limit=1000)
            
            total_memories = len(memories)
            memory_distribution = {}
            total_size = 0
            
            for memory in memories:
                memory_type = memory.memory_type
                if memory_type not in memory_distribution:
                    memory_distribution[memory_type] = 0
                memory_distribution[memory_type] += 1
                
                # 대략적인 크기 계산
                content_size = len(json.dumps(memory.content, default=str))
                total_size += content_size
            
            avg_size = total_size / total_memories if total_memories > 0 else 0
            
            return MemoryMetrics(
                total_memories=total_memories,
                memory_distribution=memory_distribution,
                total_size_bytes=total_size,
                average_size_bytes=avg_size,
                oldest_memory=min((m.timestamp for m in memories), default=None),
                newest_memory=max((m.timestamp for m in memories), default=None)
            )
            
        except Exception as e:
            logger.error(f"Error calculating memory metrics: {str(e)}")
            raise

    async def cleanup_expired_memories(self) -> int:
        """만료된 메모리 정리"""
        try:
            deleted_count = await self.database.cleanup_expired_memories()
            logger.info(f"Cleaned up {deleted_count} expired memories")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired memories: {str(e)}")
            raise

    async def cleanup_old_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        cutoff_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """오래된 메모리 정리"""
        try:
            if hasattr(self.database, 'cleanup_old_memories'):
                deleted_count = await self.database.cleanup_old_memories(
                    memory_type=memory_type,
                    cutoff_date=cutoff_date,
                    filters=filters
                )
            else:
                # 대체 구현
                cutoff_date = cutoff_date or (datetime.utcnow() - timedelta(days=30))
                filters = filters or {}
                filters['timestamp__lt'] = cutoff_date
                
                old_memories = await self.retrieve_memories(
                    agent_id=filters.get('agent_id', ''),
                    memory_type=memory_type,
                    filters=filters
                )
                
                deleted_count = 0
                for memory in old_memories:
                    if await self.delete_memory(memory.memory_id):
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old memories")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old memories: {str(e)}")
            raise

    async def _check_capacity(self, agent_id: str):
        """용량 확인"""
        try:
            stats = await self.get_memory_stats(agent_id=agent_id)
            
            total_memories = stats.get('total_memories', 0)
            total_storage = stats.get('total_storage_used', 0)
            
            if total_memories >= self.max_memories_per_agent:
                await self.auto_cleanup_memories(agent_id)
            
            if total_storage >= self.max_storage_per_agent:
                await self.auto_cleanup_memories(agent_id)
                
        except Exception as e:
            logger.error(f"Error checking capacity: {str(e)}")
            # 용량 확인 실패 시에도 저장은 계속 진행

    async def check_memory_capacity(self, agent_id: str) -> Dict[str, Any]:
        """메모리 용량 확인"""
        try:
            stats = await self.get_memory_stats(agent_id=agent_id)
            
            total_memories = stats.get('total_memories', 0)
            total_storage = stats.get('total_storage_used', 0)
            
            memory_usage = total_memories / self.max_memories_per_agent
            storage_usage = total_storage / self.max_storage_per_agent
            
            return {
                'memory_count_usage': memory_usage,
                'storage_usage': storage_usage,
                'needs_cleanup': memory_usage > 0.9 or storage_usage > 0.9,
                'total_memories': total_memories,
                'total_storage_used': total_storage,
                'max_memories': self.max_memories_per_agent,
                'max_storage': self.max_storage_per_agent
            }
            
        except Exception as e:
            logger.error(f"Error checking memory capacity: {str(e)}")
            return {
                'memory_count_usage': 0,
                'storage_usage': 0,
                'needs_cleanup': False,
                'error': str(e)
            }

    async def auto_cleanup_memories(self, agent_id: str) -> Dict[str, Any]:
        """자동 메모리 정리"""
        try:
            # 만료된 메모리 먼저 정리
            expired_cleaned = await self.cleanup_expired_memories()
            
            # 오래된 메모리 정리
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            old_cleaned = await self.cleanup_old_memories(
                cutoff_date=cutoff_date,
                filters={'agent_id': agent_id}
            )
            
            return {
                'expired_cleaned': expired_cleaned,
                'old_cleaned': old_cleaned,
                'total_cleaned': expired_cleaned + old_cleaned
            }
            
        except Exception as e:
            logger.error(f"Error in auto cleanup: {str(e)}")
            return {
                'expired_cleaned': 0,
                'old_cleaned': 0,
                'total_cleaned': 0,
                'error': str(e)
            }

    async def shutdown(self):
        """메모리 서비스 종료"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                
            logger.info("Memory service shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during memory service shutdown: {str(e)}")
