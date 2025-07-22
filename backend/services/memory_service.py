import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
from mem0 import Memory
from chromadb import Client
from neo4j import GraphDatabase
from ..utils.config import config
from ..models.schemas import (
    MemoryType,
    ProceduralMemory,
    EpisodicMemory,
    SemanticMemory,
    WorkflowPattern,
    MCPToolType,
)


class EnhancedMemoryService:
    def __init__(self):
        self.redis_client = None
        self.mem0 = Memory()
        self.chroma_client = None
        self.neo4j_driver = None
        self.performance_metrics = []

    async def initialize(self):
        """메모리 시스템 초기화"""
        # Redis - Working Memory
        self.redis_client = redis.from_url(config.REDIS_URL)

        # ChromaDB - Episodic Memory
        self.chroma_client = Client(
            host=config.CHROMA_HOST, port=int(config.CHROMA_PORT)
        )
        try:
            self.episodes_collection = self.chroma_client.create_collection("episodes")
            self.procedures_collection = self.chroma_client.create_collection(
                "procedures"
            )
        except:
            self.episodes_collection = self.chroma_client.get_collection("episodes")
            self.procedures_collection = self.chroma_client.get_collection("procedures")

        # Neo4j - Semantic Memory
        self.neo4j_driver = GraphDatabase.driver(
            config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )

    # === Working Memory (작업 기억) ===
    async def store_working_memory(
        self, session_id: str, key: str, value: Any, ttl: int = 3600
    ):
        """세션별 작업 메모리 저장"""
        start_time = time.time()

        memory_key = f"working:{session_id}:{key}"
        await self.redis_client.setex(memory_key, ttl, json.dumps(value, default=str))

        return time.time() - start_time

    async def get_working_memory(
        self, session_id: str, key: str = None
    ) -> Dict[str, Any]:
        """세션별 작업 메모리 조회"""
        start_time = time.time()

        if key:
            memory_key = f"working:{session_id}:{key}"
            result = await self.redis_client.get(memory_key)
            if result:
                return {key: json.loads(result)}, time.time() - start_time
            return {}, time.time() - start_time
        else:
            # 세션의 모든 작업 메모리 조회
            pattern = f"working:{session_id}:*"
            keys = await self.redis_client.keys(pattern)

            result = {}
            for full_key in keys:
                key_name = full_key.decode().split(":")[-1]
                value = await self.redis_client.get(full_key)
                if value:
                    result[key_name] = json.loads(value)

            return result, time.time() - start_time

    # === Procedural Memory (절차적 기억) ===
    async def store_procedural_memory(
        self, workflow_pattern: WorkflowPattern, user_id: str
    ):
        """성공한 워크플로우 패턴 저장"""
        start_time = time.time()

        # Mem0에 절차 패턴 저장
        procedure_data = {
            "pattern_id": workflow_pattern.pattern_id,
            "pattern_name": workflow_pattern.pattern_name,
            "steps": [step.dict() for step in workflow_pattern.steps],
            "success_rate": workflow_pattern.success_rate,
            "avg_execution_time": workflow_pattern.avg_execution_time,
            "usage_count": workflow_pattern.usage_count,
        }

        self.mem0.add(
            f"Workflow pattern: {workflow_pattern.pattern_name} with {len(workflow_pattern.steps)} steps, "
            f"success rate: {workflow_pattern.success_rate:.1%}",
            user_id=user_id,
            metadata={
                "type": "procedural",
                "pattern_id": workflow_pattern.pattern_id,
                "domain": "workflow",
            },
        )

        # ChromaDB에도 상세 정보 저장
        self.procedures_collection.add(
            documents=[json.dumps(procedure_data, default=str)],
            metadatas=[
                {
                    "pattern_id": workflow_pattern.pattern_id,
                    "user_id": user_id,
                    "success_rate": workflow_pattern.success_rate,
                    "created_at": datetime.now().isoformat(),
                }
            ],
            ids=[f"{user_id}_{workflow_pattern.pattern_id}"],
        )

        return time.time() - start_time

    async def retrieve_similar_procedures(
        self, task_description: str, user_id: str, limit: int = 3
    ):
        """유사한 절차 패턴 검색"""
        start_time = time.time()

        # Mem0에서 관련 절차 검색
        memories = self.mem0.search(
            query=f"workflow procedure for: {task_description}",
            user_id=user_id,
            limit=limit,
        )

        procedures = []
        if memories and "results" in memories:
            for memory in memories["results"]:
                metadata = memory.get("metadata", {})
                if metadata.get("type") == "procedural":
                    procedures.append(
                        {
                            "content": memory.get("memory", ""),
                            "pattern_id": metadata.get("pattern_id"),
                            "relevance_score": memory.get("score", 0),
                        }
                    )

        return procedures, time.time() - start_time

    # === Episodic Memory (일화적 기억) ===
    async def store_episodic_memory(self, episode: EpisodicMemory):
        """사용자 상호작용 에피소드 저장"""
        start_time = time.time()

        # Mem0에 에피소드 정보 저장
        episode_content = (
            f"User {episode.user_id} interaction: {episode.interaction_type}. "
            f"Context: {episode.context}. "
            f"Satisfaction: {episode.user_satisfaction}"
        )

        self.mem0.add(
            episode_content,
            user_id=episode.user_id,
            metadata={
                "type": "episodic",
                "episode_id": episode.episode_id,
                "interaction_type": episode.interaction_type,
                "timestamp": episode.timestamp.isoformat(),
            },
        )

        # ChromaDB에 상세 에피소드 저장
        episode_data = episode.dict()
        self.episodes_collection.add(
            documents=[json.dumps(episode_data, default=str)],
            metadatas=[
                {
                    "user_id": episode.user_id,
                    "episode_id": episode.episode_id,
                    "interaction_type": episode.interaction_type,
                    "timestamp": episode.timestamp.isoformat(),
                    "satisfaction": episode.user_satisfaction or 0,
                }
            ],
            ids=[episode.episode_id],
        )

        return time.time() - start_time

    async def retrieve_user_episodes(
        self, user_id: str, interaction_type: str = None, limit: int = 5
    ):
        """사용자의 과거 에피소드 검색"""
        start_time = time.time()

        query = f"user {user_id} interactions"
        if interaction_type:
            query += f" related to {interaction_type}"

        memories = self.mem0.search(query=query, user_id=user_id, limit=limit)

        episodes = []
        if memories and "results" in memories:
            for memory in memories["results"]:
                metadata = memory.get("metadata", {})
                if metadata.get("type") == "episodic":
                    episodes.append(
                        {
                            "content": memory.get("memory", ""),
                            "episode_id": metadata.get("episode_id"),
                            "interaction_type": metadata.get("interaction_type"),
                            "timestamp": metadata.get("timestamp"),
                            "relevance_score": memory.get("score", 0),
                        }
                    )

        return episodes, time.time() - start_time

    # === Semantic Memory (의미적 기억) ===
    async def store_semantic_knowledge(self, knowledge: SemanticMemory):
        """도메인 지식 저장"""
        start_time = time.time()

        # Neo4j에 지식 그래프로 저장
        with self.neo4j_driver.session() as session:
            query = """
            MERGE (e:Entity {name: $entity, domain: $domain})
            MERGE (o:Entity {name: $object, domain: $domain})
            MERGE (e)-[r:RELATION {
                type: $relation,
                confidence: $confidence,
                source: $source,
                created_at: $created_at,
                knowledge_id: $knowledge_id
            }]->(o)
            SET r.usage_count = COALESCE(r.usage_count, 0) + 1
            """

            session.run(
                query,
                {
                    "entity": knowledge.entity,
                    "object": knowledge.object,
                    "relation": knowledge.relation,
                    "domain": knowledge.domain,
                    "confidence": knowledge.confidence,
                    "source": knowledge.source,
                    "created_at": knowledge.created_at.isoformat(),
                    "knowledge_id": knowledge.knowledge_id,
                },
            )

        # Mem0에도 텍스트로 저장
        knowledge_text = f"{knowledge.entity} {knowledge.relation} {knowledge.object} in {knowledge.domain} domain"
        self.mem0.add(
            knowledge_text,
            user_id="system",  # 시스템 레벨 지식
            metadata={
                "type": "semantic",
                "domain": knowledge.domain,
                "knowledge_id": knowledge.knowledge_id,
                "confidence": knowledge.confidence,
            },
        )

        return time.time() - start_time

    async def query_semantic_knowledge(
        self, entity: str, domain: str = None, limit: int = 10
    ):
        """의미적 지식 쿼리"""
        start_time = time.time()

        with self.neo4j_driver.session() as session:
            if domain:
                query = """
                MATCH (e:Entity {name: $entity, domain: $domain})-[r:RELATION]->(o:Entity)
                RETURN e.name as entity, r.type as relation, o.name as object, 
                       r.confidence as confidence, r.usage_count as usage_count
                ORDER BY r.confidence DESC, r.usage_count DESC
                LIMIT $limit
                """
                result = session.run(
                    query, {"entity": entity, "domain": domain, "limit": limit}
                )
            else:
                query = """
                MATCH (e:Entity {name: $entity})-[r:RELATION]->(o:Entity)
                RETURN e.name as entity, r.type as relation, o.name as object, 
                       r.confidence as confidence, r.usage_count as usage_count, e.domain as domain
                ORDER BY r.confidence DESC, r.usage_count DESC
                LIMIT $limit
                """
                result = session.run(query, {"entity": entity, "limit": limit})

            knowledge_items = []
            for record in result:
                knowledge_items.append(
                    {
                        "entity": record["entity"],
                        "relation": record["relation"],
                        "object": record["object"],
                        "confidence": record["confidence"],
                        "usage_count": record["usage_count"],
                        "domain": record.get("domain", domain),
                    }
                )

        return knowledge_items, time.time() - start_time

    # === 통합 검색 메소드 ===
    async def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        memory_types: List[MemoryType] = None,
        limit: int = 5,
    ):
        """관련 메모리 통합 검색"""
        start_time = time.time()
        all_memories = {
            MemoryType.WORKING: [],
            MemoryType.EPISODIC: [],
            MemoryType.SEMANTIC: [],
            MemoryType.PROCEDURAL: [],
        }

        # 요청된 메모리 타입만 검색 (기본은 모든 타입)
        if memory_types is None:
            memory_types = list(MemoryType)

        # Mem0 통합 검색
        memories = self.mem0.search(
            query=query, user_id=user_id, limit=limit * len(memory_types)
        )

        if memories and "results" in memories:
            for memory in memories["results"]:
                metadata = memory.get("metadata", {})
                memory_type = metadata.get("type", "")

                memory_item = {
                    "content": memory.get("memory", ""),
                    "score": memory.get("score", 0),
                    "metadata": metadata,
                }

                if memory_type == "working" and MemoryType.WORKING in memory_types:
                    all_memories[MemoryType.WORKING].append(memory_item)
                elif memory_type == "episodic" and MemoryType.EPISODIC in memory_types:
                    all_memories[MemoryType.EPISODIC].append(memory_item)
                elif memory_type == "semantic" and MemoryType.SEMANTIC in memory_types:
                    all_memories[MemoryType.SEMANTIC].append(memory_item)
                elif (
                    memory_type == "procedural"
                    and MemoryType.PROCEDURAL in memory_types
                ):
                    all_memories[MemoryType.PROCEDURAL].append(memory_item)

        # 각 타입별로 최고 점수 항목들만 유지
        for memory_type in all_memories:
            all_memories[memory_type] = sorted(
                all_memories[memory_type], key=lambda x: x["score"], reverse=True
            )[:limit]

        return all_memories, time.time() - start_time

    async def get_memory_statistics(self):
        """메모리 시스템 통계"""
        stats = {}

        try:
            # Redis 통계
            redis_info = await self.redis_client.info()
            working_keys = await self.redis_client.keys("working:*")
            stats["working_memory"] = {
                "total_keys": len(working_keys),
                "memory_usage": redis_info.get("used_memory_human", "0"),
                "connected_clients": redis_info.get("connected_clients", 0),
            }

            # ChromaDB 통계
            stats["episodic_memory"] = {
                "episodes_count": self.episodes_collection.count(),
                "procedures_count": self.procedures_collection.count(),
            }

            # Neo4j 통계
            with self.neo4j_driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = result.single()["node_count"]

                result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = result.single()["rel_count"]

                stats["semantic_memory"] = {
                    "nodes_count": node_count,
                    "relationships_count": rel_count,
                }

            # 성능 메트릭
            if self.performance_metrics:
                recent_metrics = self.performance_metrics[-10:]
                avg_time = sum(m.memory_retrieval_time for m in recent_metrics) / len(
                    recent_metrics
                )
                stats["performance"] = {
                    "avg_retrieval_time": avg_time,
                    "total_operations": len(self.performance_metrics),
                }

        except Exception as e:
            stats["error"] = str(e)

        return stats
