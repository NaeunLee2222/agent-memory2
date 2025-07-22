from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime

class AgenticPlanner:
    def __init__(self, semantic_memory, procedural_memory):
        self.semantic_memory = semantic_memory
        self.procedural_memory = procedural_memory
        
    async def create_execution_plan(self, intent: str, entities: List[Dict], requirements: List[str]) -> Dict:
        """복합 작업을 단계별 실행 계획으로 분해"""
        
        # 1. 과거 유사한 패턴 검색
        similar_procedures = await self.procedural_memory.find_similar_procedures(
            intent, similarity_threshold=0.7
        )
        
        if similar_procedures:
            # 기존 패턴 활용
            base_plan = similar_procedures[0]
            execution_plan = await self._adapt_existing_plan(base_plan, entities, requirements)
        else:
            # 새로운 계획 생성
            execution_plan = await self._create_new_plan(intent, entities, requirements)
        
        return execution_plan
    
    async def _create_new_plan(self, intent: str, entities: List[Dict], requirements: List[str]) -> Dict:
        """새로운 실행 계획 생성"""
        
        # 의도 분석에 따른 목표 타입 결정
        goal_type = self._determine_goal_type(intent)
        
        # 목표 타입별 단계 생성
        if goal_type == "document_generation":
            steps = await self._create_document_generation_steps(entities, requirements)
        elif goal_type == "data_processing":
            steps = await self._create_data_processing_steps(entities, requirements)
        elif goal_type == "communication":
            steps = await self._create_communication_steps(entities, requirements)
        else:
            steps = await self._create_generic_steps(intent, entities, requirements)
        
        return {
            "plan_id": f"plan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "goal_type": goal_type,
            "intent": intent,
            "steps": steps,
            "estimated_duration": sum(step.get("estimated_time", 5) for step in steps),
            "dependencies": self._calculate_dependencies(steps),
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _determine_goal_type(self, intent: str) -> str:
        """의도로부터 목표 타입 결정"""
        intent_lower = intent.lower()
        
        if any(keyword in intent_lower for keyword in ["문서", "생성", "작성", "rfq", "document"]):
            return "document_generation"
        elif any(keyword in intent_lower for keyword in ["검색", "조회", "찾기", "search", "query"]):
            return "data_processing"
        elif any(keyword in intent_lower for keyword in ["메시지", "전송", "슬랙", "알림", "message", "send"]):
            return "communication"
        else:
            return "generic"
    
    async def _create_document_generation_steps(self, entities: List[Dict], requirements: List[str]) -> List[Dict]:
        """문서 생성 작업 단계 생성"""
        steps = []
        
        # 단계 1: 요구사항 분석
        steps.append({
            "step_id": 1,
            "name": "analyze_requirements",
            "tool": "analyze_text",
            "parameters": {
                "text": " ".join(requirements),
                "analysis_type": "document_requirements"
            },
            "estimated_time": 3,
            "dependencies": []
        })
        
        # 단계 2: 문서 타입별 처리
        doc_type = self._extract_document_type(entities)
        if doc_type == "rfq":
            # RFQ 커버 생성
            steps.append({
                "step_id": 2,
                "name": "create_rfq_cover",
                "tool": "create_rfq_cover",
                "parameters": self._extract_rfq_parameters(entities),
                "estimated_time": 5,
                "dependencies": [1]
            })
            
            # RFQ 콘텐츠 생성 (병렬 실행 가능)
            steps.append({
                "step_id": 3,
                "name": "generate_rfq_content", 
                "tool": "generate_content",
                "parameters": {
                    "template": "rfq_template",
                    "data": entities
                },
                "estimated_time": 7,
                "dependencies": [1]  # 단계 2와 병렬 실행 가능
            })
            
            # 문서 결합
            steps.append({
                "step_id": 4,
                "name": "combine_documents",
                "tool": "combine_rfq_cover",
                "parameters": {
                    "documents": ["cover", "content"],
                    "output_format": "pdf"
                },
                "estimated_time": 3,
                "dependencies": [2, 3]
            })
        
        return steps
    
    async def _create_communication_steps(self, entities: List[Dict], requirements: List[str]) -> List[Dict]:
        """커뮤니케이션 작업 단계 생성"""
        steps = []
        
        # 메시지 내용 생성
        steps.append({
            "step_id": 1,
            "name": "generate_message",
            "tool": "generate_message",
            "parameters": {
                "content_type": "slack_message",
                "context": entities,
                "tone": "professional"
            },
            "estimated_time": 2,
            "dependencies": []
        })
        
        # 슬랙 전송
        steps.append({
            "step_id": 2,
            "name": "send_slack",
            "tool": "send_slack_message",
            "parameters": self._extract_slack_parameters(entities),
            "estimated_time": 1,
            "dependencies": [1]
        })
        
        return steps
    
    def _extract_document_type(self, entities: List[Dict]) -> str:
        """엔티티에서 문서 타입 추출"""
        for entity in entities:
            if entity.get("type") == "document_type":
                return entity.get("value", "").lower()
        return "generic"
    
    def _extract_rfq_parameters(self, entities: List[Dict]) -> Dict:
        """RFQ 파라미터 추출"""
        params = {}
        for entity in entities:
            if entity.get("type") == "company":
                params["company_name"] = entity.get("value")
            elif entity.get("type") == "project":
                params["project_title"] = entity.get("value")
            elif entity.get("type") == "deadline":
                params["deadline"] = entity.get("value")
        return params
    
    def _calculate_dependencies(self, steps: List[Dict]) -> Dict:
        """단계 간 의존관계 계산"""
        dependencies = {}
        for step in steps:
            step_id = step["step_id"]
            deps = step.get("dependencies", [])
            dependencies[step_id] = deps
        return dependencies
    
    async def find_alternative_step(self, failed_step: Dict, error: str) -> Optional[Dict]:
        """실패한 단계의 대안 찾기"""
        
        # 도구 대체 가능성 확인
        alternative_tools = await self.semantic_memory.find_alternative_tools(
            failed_step["tool"], failed_step.get("parameters", {})
        )
        
        if alternative_tools:
            alternative_step = failed_step.copy()
            alternative_step["step_id"] = f"{failed_step['step_id']}_alt"
            alternative_step["tool"] = alternative_tools[0]["name"]
            alternative_step["parameters"] = self._adapt_parameters(
                failed_step["parameters"], alternative_tools[0]
            )
            return alternative_step
        
        return None
    
    def _adapt_parameters(self, original_params: Dict, alternative_tool: Dict) -> Dict:
        """대안 도구에 맞게 파라미터 조정"""
        # 도구별 파라미터 매핑 로직
        adapted_params = original_params.copy()
        
        # 공통 파라미터 매핑 규칙 적용
        tool_mappings = {
            "create_rfq_cover": {"company_name": "company", "project_title": "title"},
            "generate_content": {"template": "content_type", "data": "input_data"}
        }
        
        if alternative_tool["name"] in tool_mappings:
            mapping = tool_mappings[alternative_tool["name"]]
            for old_key, new_key in mapping.items():
                if old_key in adapted_params:
                    adapted_params[new_key] = adapted_params.pop(old_key)
        
        return adapted_params