# 메모리 API 테스트 스크립트

#!/bin/bash

echo "🧠 메모리 API 테스트 시작..."
echo "=============================="

BASE_URL="http://localhost:8100"
AGENT_ID="test_agent_001"

# 1. 테스트 메모리 데이터 추가
echo "1️⃣ 테스트 메모리 데이터 생성..."

# Working Memory 추가
curl -X POST "$BASE_URL/api/v1/memory/store" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_type": "working",
    "content": {
      "task": "user_interaction",
      "status": "active",
      "data": {"user_input": "Hello, how are you?"}
    },
    "agent_id": "'$AGENT_ID'",
    "context": {"session_id": "session_123"},
    "metadata": {"priority": "high"}
  }'
echo ""

# Episodic Memory 추가
curl -X POST "$BASE_URL/api/v1/memory/store" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_type": "episodic",
    "content": {
      "event": "successful_task_completion",
      "outcome": "positive",
      "duration": 2.5,
      "user_satisfaction": "high"
    },
    "agent_id": "'$AGENT_ID'",
    "context": {"task_type": "question_answering"},
    "metadata": {"confidence": 0.95}
  }'
echo ""

# Semantic Memory 추가
curl -X POST "$BASE_URL/api/v1/memory/store" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_type": "semantic",
    "content": {
      "knowledge_type": "user_preference",
      "rule": "user_prefers_detailed_explanations",
      "domain": "communication_style",
      "confidence": 0.8
    },
    "agent_id": "'$AGENT_ID'",
    "context": {"learned_from": "user_feedback"},
    "metadata": {"validation_count": 3}
  }'
echo ""

# 2. 메모리 통계 조회 테스트
echo "2️⃣ 메모리 통계 조회 테스트..."
curl -s "$BASE_URL/api/v1/memory/$AGENT_ID/stats" | jq . 2>/dev/null || curl -s "$BASE_URL/api/v1/memory/$AGENT_ID/stats"
echo ""

# 3. 메모리 검색 테스트
echo "3️⃣ 메모리 검색 테스트..."
curl -s "$BASE_URL/api/v1/memory/$AGENT_ID" | jq . 2>/dev/null || curl -s "$BASE_URL/api/v1/memory/$AGENT_ID"
echo ""

# 4. 피드백 데이터 추가
echo "4️⃣ 테스트 피드백 데이터 생성..."

# Success Feedback
curl -X POST "$BASE_URL/api/v1/feedback/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "'$AGENT_ID'",
    "feedback_type": "success",
    "content": "Great response, very helpful!",
    "metadata": {"rating": 5, "session_id": "session_123"},
    "context": {"response_time": 1.2}
  }'
echo ""

# Error Feedback
curl -X POST "$BASE_URL/api/v1/feedback/collect" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "'$AGENT_ID'",
    "feedback_type": "error",
    "content": "Response was not accurate",
    "metadata": {"error_category": "factual", "session_id": "session_123"},
    "context": {"correction_needed": true}
  }'
echo ""

# 5. 피드백 인사이트 조회 테스트
echo "5️⃣ 피드백 인사이트 조회 테스트..."
curl -s "$BASE_URL/api/v1/feedback/$AGENT_ID/insights" | jq . 2>/dev/null || curl -s "$BASE_URL/api/v1/feedback/$AGENT_ID/insights"
echo ""

# 6. 시스템 성능 조회 테스트
echo "6️⃣ 시스템 성능 조회 테스트..."
curl -s "$BASE_URL/api/v1/performance/system" | jq . 2>/dev/null || curl -s "$BASE_URL/api/v1/performance/system"
echo ""

# 7. 메트릭 엔드포인트 테스트
echo "7️⃣ 메트릭 엔드포인트 테스트..."
echo "Memory Metrics:"
curl -s "$BASE_URL/api/v1/memory/metrics"
echo ""
echo "Feedback Metrics:"
curl -s "$BASE_URL/api/v1/feedback/metrics"
echo ""

# 8. Prometheus 메트릭 테스트
echo "8️⃣ Prometheus 메트릭 테스트..."
curl -s "$BASE_URL/metrics"
echo ""

echo "✅ 모든 API 테스트 완료!"
echo ""
echo "🌐 이제 Frontend에서 다음 URL을 통해 확인하세요:"
echo "- http://localhost:8501 (Streamlit Frontend)"
echo "- http://localhost:8100/docs (FastAPI 문서)"