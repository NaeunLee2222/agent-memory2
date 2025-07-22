from pymongo import MongoClient
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class ProceduralMemoryManager:
    def __init__(self, connection_string="mongodb://localhost:27017/", db_name="procedural_memory"):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.procedures = self.db.procedures
    
    async def find_similar_procedures(self, intent: str, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """유사한 절차 패턴 검색"""
        try:
            # 간단한 텍스트 매칭으로 구현 (실제로는 임베딩 기반 검색)
            procedures = list(self.procedures.find({
                "intent": {"$regex": intent, "$options": "i"}
            }).limit(5))
            
            return procedures
        except Exception as e:
            print(f"Error finding similar procedures: {e}")
            return []
    
    async def store_procedure(self, procedure_data: Dict[str, Any]) -> str:
        """절차 패턴 저장"""
        try:
            procedure_data["created_at"] = datetime.utcnow()
            procedure_data["usage_count"] = 0
            procedure_data["success_rate"] = 1.0
            
            result = self.procedures.insert_one(procedure_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing procedure: {e}")
            return ""
    
    async def update_procedure_performance(self, procedure_id: str, success: bool) -> bool:
        """절차 성능 업데이트"""
        try:
            procedure = self.procedures.find_one({"_id": procedure_id})
            if procedure:
                current_rate = procedure.get("success_rate", 1.0)
                usage_count = procedure.get("usage_count", 0)
                
                # 성공률 업데이트
                new_rate = (current_rate * usage_count + (1.0 if success else 0.0)) / (usage_count + 1)
                
                self.procedures.update_one(
                    {"_id": procedure_id},
                    {
                        "$set": {"success_rate": new_rate},
                        "$inc": {"usage_count": 1}
                    }
                )
                return True
            return False
        except Exception as e:
            print(f"Error updating procedure performance: {e}")
            return False