from typing import Dict, List, Any, Optional
import re
import json
from datetime import datetime

class AgenticReasoner:
    def __init__(self, episodic_memory, semantic_memory):
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory
        
    async def analyze_request(self, message: str, context: Dict) -> Dict:
        """사용자 요청 분석"""
        
        # 1. 의도 추출
        intent = self._extract_intent(message)
        
        # 2. 엔티티 추출
        entities = self._extract_entities(message)
        
        # 3. 요구사항 분석
        requirements = self._extract_requirements(message)
        
        # 4. 복잡도 평가
        complexity = self._assess_complexity(intent, entities, requirements)
        
        return {
            "intent": intent,
            "entities": entities,
            "requirements": requirements,
            "complexity": complexity,
            "original_message": message,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _extract_intent(self, message: str) -> str:
        """메시지에서 의도 추출"""
        message_lower = message.lower()
        
        # 의도 패턴 매칭
        intent_patterns = {
            "document_generation": [
                r".*문서.*생성.*", r".*rfq.*만들.*", r".*작성.*",
                r".*create.*document.*", r".*generate.*rfq.*"
            ],
            "data_search": [
                r".*검색.*", r".*찾.*", r".*조회.*",
                r".*search.*", r".*find.*", r".*query.*"
            ],
            "communication": [
                r".*메시지.*보내.*", r".*슬랙.*전송.*", r".*알림.*",
                r".*send.*message.*", r".*notify.*"
            ],
            "data_modification": [
                r".*수정.*", r".*변경.*", r".*업데이트.*",
                r".*modify.*", r".*update.*", r".*edit.*"
            ],
            "file_processing": [
                r".*결합.*", r".*합치.*", r".*병합.*",
                r".*combine.*", r".*merge.*"
            ]
        }
        
        for intent_type, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent_type
        
        return "general_assistance"
    
    def _extract_entities(self, message: str) -> List[Dict]:
        """메시지에서 엔티티 추출"""
        entities = []
        
        # 회사명 추출
        company_pattern = r"(?:회사|company)[\s:]*([A-Za-z가-힣\s]+)"
        company_match = re.search(company_pattern, message, re.IGNORECASE)
        if company_match:
            entities.append({
                "type": "company",
                "value": company_match.group(1).strip(),
                "confidence": 0.8
            })
        
        # 프로젝트명 추출
        project_patterns = [
            r"(?:프로젝트|project)[\s:]*([A-Za-z가-힣\s]+)",
            r"(?:제목|title)[\s:]*([A-Za-z가-힣\s]+)"
        ]
        for pattern in project_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities.append({
                    "type": "project",
                    "value": match.group(1).strip(),
                    "confidence": 0.7
                })
                break
        
        # 날짜 추출
        date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{2}/\d{2}/\d{4})",
            r"(?:마감|deadline)[\s:]*(\d{4}-\d{2}-\d{2})"
        ]
        for pattern in date_patterns:
            match = re.search(pattern, message)
            if match:
                entities.append({
                    "type": "deadline",
                    "value": match.group(1),
                    "confidence": 0.9
                })
                break
        
        # 문서 타입 추출
        doc_types = ["rfq", "proposal", "contract", "report"]
        for doc_type in doc_types:
            if doc_type.lower() in message.lower():
                entities.append({
                    "type": "document_type",
                    "value": doc_type,
                    "confidence": 0.8
                })
                break
        
        # 채널 추출 (슬랙)
        channel_pattern = r"#([a-zA-Z0-9_-]+)"
        channel_matches = re.findall(channel_pattern, message)
        for channel in channel_matches:
            entities.append({
                "type": "channel",
                "value": f"#{channel}",
                "confidence": 0.9
            })
        
        return entities
    
    def _extract_requirements(self, message: str) -> List[str]:
        """요구사항 추출"""
        requirements = []
        
        # 명시적 요구사항 패턴
        requirement_indicators = [
            "필요한", "요구되는", "포함해야", "반드시",
            "required", "needed", "must", "should"
        ]
        
        sentences = re.split(r'[.!?]', message)
        for sentence in sentences:
            for indicator in requirement_indicators:
                if indicator in sentence.lower():
                    requirements.append(sentence.strip())
                    break
        
        # 기본 요구사항이 없으면 메시지 전체를 요구사항으로 처리
        if not requirements:
            requirements.append(message)
        
        return requirements
    
    def _assess_complexity(self, intent: str, entities: List[Dict], requirements: List[str]) -> Dict:
        """작업 복잡도 평가"""
        complexity_score = 0
        
        # 의도별 기본 복잡도
        intent_complexity = {
            "document_generation": 3,
            "data_search": 2,
            "communication": 1,
            "data_modification": 2,
            "file_processing": 2,
            "general_assistance": 1
        }
        
        complexity_score += intent_complexity.get(intent, 1)
        
        # 엔티티 수에 따른 복잡도 증가
        complexity_score += len(entities) * 0.5
        
        # 요구사항 수에 따른 복잡도 증가
        complexity_score += len(requirements) * 0.3
        
        # 복잡도 레벨 결정
        if complexity_score <= 2:
            level = "simple"
        elif complexity_score <= 4:
            level = "medium"
        else:
            level = "complex"
        
        return {
            "score": complexity_score,
            "level": level,
            "estimated_steps": min(int(complexity_score), 5),
            "recommended_mode": "flow" if level == "complex" else "basic"
        }
    
    async def select_optimal_tools(self, intent: str, entities: List[Dict], 
                                  similar_episodes: List[Dict], available_tools: List[Dict]) -> List[Dict]:
        """최적 도구 선택"""
        
        # 1. 의도 기반 도구 필터링
        relevant_tools = await self._filter_tools_by_intent(intent, available_tools)
        
        # 2. 과거 성공 경험 반영
        if similar_episodes:
            success_tools = self._extract_successful_tools(similar_episodes)
            relevant_tools = self._prioritize_by_success(relevant_tools, success_tools)
        
        # 3. 엔티티 정보로 파라미터 생성
        selected_tools = []
        for tool in relevant_tools[:3]:  # 최대 3개 도구 선택
            parameters = await self._generate_parameters(tool, entities, intent)
            selected_tools.append({
                "name": tool["name"],
                "parameters": parameters,
                "confidence": tool.get("confidence", 0.5)
            })
        
        return selected_tools
    
    async def _filter_tools_by_intent(self, intent: str, available_tools: List[Dict]) -> List[Dict]:
        """의도에 따른 도구 필터링"""
        
        intent_tool_mapping = {
            "document_generation": ["create_rfq_cover", "generate_content", "combine_rfq_cover"],
            "data_search": ["search_database", "query_api"],
            "communication": ["send_slack_message", "send_email"],
            "data_modification": ["modify_tbe_content", "update_database"],
            "file_processing": ["combine_rfq_cover", "merge_files"]
        }
        
        preferred_tools = intent_tool_mapping.get(intent, [])
        
        filtered_tools = []
        for tool in available_tools:
            if tool["name"] in preferred_tools:
                tool["confidence"] = 0.9
                filtered_tools.append(tool)
            elif tool["category"] in intent:
                tool["confidence"] = 0.6
                filtered_tools.append(tool)
        
        return sorted(filtered_tools, key=lambda x: x.get("confidence", 0), reverse=True)
    
    def _extract_successful_tools(self, episodes: List[Dict]) -> List[str]:
        """성공한 에피소드에서 도구 추출"""
        successful_tools = []
        
        for episode in episodes:
            if episode.get("success", False):
                tools = episode.get("tools_used", [])
                successful_tools.extend(tools)
        
        # 빈도순으로 정렬
        from collections import Counter
        tool_counts = Counter(successful_tools)
        return [tool for tool, count in tool_counts.most_common()]
    
    async def _generate_parameters(self, tool: Dict, entities: List[Dict], intent: str) -> Dict:
        """도구별 파라미터 생성"""
        parameters = {}
        
        tool_name = tool["name"]
        
        if tool_name == "create_rfq_cover":
            for entity in entities:
                if entity["type"] == "company":
                    parameters["company_name"] = entity["value"]
                elif entity["type"] == "project":
                    parameters["project_title"] = entity["value"]
                elif entity["type"] == "deadline":
                    parameters["deadline"] = entity["value"]
                    
        elif tool_name == "send_slack_message":
            message_content = f"자동 생성된 메시지: {intent} 작업이 완료되었습니다."
            parameters["message"] = message_content
            
            for entity in entities:
                if entity["type"] == "channel":
                    parameters["channel"] = entity["value"]
                    
        elif tool_name == "search_database":
            # 검색 쿼리 생성
            search_terms = []
            for entity in entities:
                if entity["type"] in ["company", "project"]:
                    search_terms.append(entity["value"])
            
            parameters["query"] = " ".join(search_terms) if search_terms else intent
            
        elif tool_name == "modify_tbe_content":
            parameters["content"] = "기존 콘텐츠"  # 실제로는 컨텍스트에서 가져와야 함
            parameters["modifications"] = ["업데이트 요청됨"]
        
        return parameters