# 6. backend/database/memory_database.py - 기본 구현

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import uuid

from backend.models.memory import MemoryType, MemoryData
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class MemoryDatabase:
    """메모리 데이터베이스 (기본 구현)"""
    
    def __init__(self):
        # 인메모리 저장소 (실제로는 Redis, MongoDB 등 사용)
        self._memories: Dict[str, MemoryData] = {}
        self._agent_memories: Dict[str, List[str]] = {}  # agent_id -> memory_ids
        
    async def initialize(self):
        """데이터베이스 초기화"""
        logger.info("Memory database initialized (in-memory)")
        
    async def store_memory(self, memory_data: MemoryData) -> str:
        """메모리 저장"""
        if not memory_data.memory_id:
            memory_data.memory_id = str(uuid.uuid4())
            
        self._memories[memory_data.memory_id] = memory_data
        
        # 에이전트별 인덱스 추가
        if memory_data.agent_id not in self._agent_memories:
            self._agent_memories[memory_data.agent_id] = []
        self._agent_memories[memory_data.agent_id].append(memory_data.memory_id)
        
        return memory_data.memory_id
    
    async def retrieve_memories(
        self,
        agent_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[MemoryData]:
        """메모리 검색"""
        
        memories = []
        
        if agent_id:
            memory_ids = self._agent_memories.get(agent_id, [])
            memories = [self._memories[mid] for mid in memory_ids if mid in self._memories]
        else:
            memories = list(self._memories.values())
        
        # 필터 적용
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]
            
        if filters:
            for key, value in filters.items():
                if key == 'memory_id':
                    memories = [m for m in memories if m.memory_id == value]
                # 다른 필터들도 필요에 따라 추가
        
        # 정렬
        if order_by == '-timestamp':
            memories.sort(key=lambda x: x.timestamp, reverse=True)
        elif order_by == 'timestamp':
            memories.sort(key=lambda x: x.timestamp)
            
        # 제한
        if limit:
            memories = memories[:limit]
            
        return memories
    
    async def search_memories(
        self,
        agent_id: str,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        limit: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[MemoryData]:
        """메모리 검색 (텍스트 기반)"""
        
        memories = await self.retrieve_memories(agent_id=agent_id)
        
        if memory_types:
            memories = [m for m in memories if m.memory_type in memory_types]
        
        # 간단한 텍스트 검색 (실제로는 벡터 검색 사용)
        query_lower = query.lower()
        matched_memories = []
        
        for memory in memories:
            content_str = json.dumps(memory.content, default=str).lower()
            if query_lower in content_str:
                matched_memories.append(memory)
        
        if limit:
            matched_memories = matched_memories[:limit]
            
        return matched_memories
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """메모리 업데이트"""
        
        if memory_id not in self._memories:
            return False
            
        memory = self._memories[memory_id]
        
        if content is not None:
            memory.content = content
        if metadata is not None:
            memory.metadata = metadata
        if context is not None:
            memory.context = context
            
        memory.updated_at = datetime.utcnow()
        
        return True
    
    async def delete_memory(self, memory_id: str) -> bool:
        """메모리 삭제"""
        
        if memory_id not in self._memories:
            return False
            
        memory = self._memories[memory_id]
        
        # 에이전트 인덱스에서 제거
        if memory.agent_id in self._agent_memories:
            if memory_id in self._agent_memories[memory.agent_id]:
                self._agent_memories[memory.agent_id].remove(memory_id)
        
        # 메모리 삭제
        del self._memories[memory_id]
        
        return True
    
    async def get_memory_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """메모리 통계"""
        
        if agent_id:
            memory_ids = self._agent_memories.get(agent_id, [])
            memories = [self._memories[mid] for mid in memory_ids if mid in self._memories]
        else:
            memories = list(self._memories.values())
        
        stats = {
            'total_memories': len(memories),
            'by_type': {},
            'total_storage_used': 0
        }
        
        for memory in memories:
            memory_type = memory.memory_type.value
            if memory_type not in stats['by_type']:
                stats['by_type'][memory_type] = 0
            stats['by_type'][memory_type] += 1
            
            # 대략적인 크기 계산
            content_size = len(json.dumps(memory.content, default=str))
            stats['total_storage_used'] += content_size
        
        return stats
    
    async def cleanup_expired_memories(self) -> int:
        """만료된 메모리 정리"""
        
        now = datetime.utcnow()
        expired_ids = []
        
        for memory_id, memory in self._memories.items():
            if memory.expires_at and memory.expires_at < now:
                expired_ids.append(memory_id)
        
        for memory_id in expired_ids:
            await self.delete_memory(memory_id)
        
        return len(expired_ids)