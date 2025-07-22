from neo4j import GraphDatabase
from typing import Dict, Any, List, Optional
import json

class SemanticMemoryManager:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    async def find_alternative_tools(self, failed_tool: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """실패한 도구의 대안 찾기"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (t1:Tool {name: $tool_name})-[:SIMILAR_TO]-(t2:Tool)
                    WHERE t2.success_rate > 0.7
                    RETURN t2.name as name, t2.category as category, t2.success_rate as success_rate
                    ORDER BY t2.success_rate DESC
                    LIMIT 3
                """, tool_name=failed_tool)
                
                alternatives = []
                for record in result:
                    alternatives.append({
                        "name": record["name"],
                        "category": record["category"],
                        "success_rate": record["success_rate"]
                    })
                
                return alternatives
        except Exception as e:
            print(f"Error finding alternative tools: {e}")
            return []
    
    async def optimize_tool_sequence(self, tools: List[str]) -> List[str]:
        """도구 실행 순서 최적화"""
        try:
            with self.driver.session() as session:
                # 도구 간 의존관계 조회
                result = session.run("""
                    MATCH (t1:Tool)-[r:PRECEDES]->(t2:Tool)
                    WHERE t1.name IN $tools AND t2.name IN $tools
                    RETURN t1.name as from_tool, t2.name as to_tool, r.weight as weight
                """, tools=tools)
                
                dependencies = {}
                for record in result:
                    from_tool = record["from_tool"]
                    to_tool = record["to_tool"]
                    if from_tool not in dependencies:
                        dependencies[from_tool] = []
                    dependencies[from_tool].append(to_tool)
                
                # 토폴로지 정렬
                optimized_order = self._topological_sort(tools, dependencies)
                return optimized_order if optimized_order else tools
                
        except Exception as e:
            print(f"Error optimizing tool sequence: {e}")
            return tools
    
    def _topological_sort(self, tools: List[str], dependencies: Dict[str, List[str]]) -> List[str]:
        """토폴로지 정렬"""
        in_degree = {tool: 0 for tool in tools}
        
        # 진입 차수 계산
        for tool in tools:
            for dep in dependencies.get(tool, []):
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # 진입 차수가 0인 노드부터 시작
        queue = [tool for tool in tools if in_degree[tool] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in dependencies.get(current, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        return result if len(result) == len(tools) else []
    
    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
                return {"status": "healthy", "component": "semantic_memory"}
        except Exception as e:
            return {"status": "unhealthy", "component": "semantic_memory", "error": str(e)}
    
    def close(self):
        """연결 종료"""
        self.driver.close()