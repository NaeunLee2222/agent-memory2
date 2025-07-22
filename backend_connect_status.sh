#!/bin/bash
# Backend 연결 상태 진단 스크립트

echo "🔍 Backend 연결 상태 진단 시작..."
echo "=================================="

# 1. Docker 컨테이너 상태 확인
echo "1️⃣ Docker 컨테이너 상태:"
docker-compose ps | grep -E "(backend|frontend)"
echo ""

# 2. Backend 포트 확인
echo "2️⃣ Backend 포트 상태:"
netstat -tlnp | grep 8100 || echo "포트 8100이 열려있지 않습니다."
echo ""

# 3. Backend 직접 접근 테스트
echo "3️⃣ Backend 직접 접근 테스트:"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8100/health 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "✅ Backend 직접 접근 성공 (HTTP $response)"
    curl -s http://localhost:8100/health | jq . 2>/dev/null || curl -s http://localhost:8100/health
else
    echo "❌ Backend 직접 접근 실패 (HTTP $response)"
fi
echo ""

# 4. 컨테이너 간 네트워크 테스트
echo "4️⃣ 컨테이너 간 네트워크 테스트:"
network_test=$(docker-compose exec -T frontend curl -s -o /dev/null -w "%{http_code}" http://backend:8000/health 2>/dev/null)
if [ "$network_test" = "200" ]; then
    echo "✅ 컨테이너 간 네트워크 연결 성공"
else
    echo "❌ 컨테이너 간 네트워크 연결 실패"
fi
echo ""

# 5. Backend 로그 마지막 10줄
echo "5️⃣ Backend 로그 (최근 10줄):"
docker-compose logs --tail=10 backend
echo ""

# 6. Frontend 환경변수 확인
echo "6️⃣ Frontend 환경변수:"
docker-compose exec -T frontend printenv | grep -i backend || echo "BACKEND 환경변수가 설정되지 않았습니다."
echo ""

# 7. 권장 해결책 제시
echo "🔧 권장 해결책:"
if [ "$response" != "200" ]; then
    echo "- Backend 컨테이너를 재시작하세요: docker-compose restart backend"
    echo "- Backend 로그를 확인하세요: docker-compose logs backend"
fi

if [ "$network_test" != "200" ]; then
    echo "- Docker 네트워크를 재생성하세요: docker-compose down && docker-compose up -d"
    echo "- 모든 서비스가 같은 네트워크에 있는지 확인하세요"
fi

echo ""
echo "🏁 진단 완료"