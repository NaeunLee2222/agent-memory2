# 🔧 Backend 연결 문제 해결

## 문제 원인
# Frontend가 backend:8100으로 접근하려 하지만, 
# Backend는 컨테이너 내부에서 포트 8000으로 실행 중

## 해결 방법 1: Docker Compose 환경변수 수정
echo "📝 Docker Compose 환경변수 수정..."

# docker-compose.yml의 frontend 섹션을 다음과 같이 수정:
cat << 'EOF' > docker-compose-fix.yml
services:
  frontend:
    # ... 기존 설정 ...
    environment:
      - BACKEND_URL=http://backend:8000  # 8100 → 8000으로 변경
EOF

## 해결 방법 2: 즉시 적용 (재시작 없이)
echo "⚡ 즉시 환경변수 수정 적용..."

# Frontend 컨테이너에서 환경변수 임시 변경
docker-compose exec frontend sh -c 'export BACKEND_URL=http://backend:8000'

## 해결 방법 3: Frontend 컨테이너 재시작
echo "🔄 Frontend 재시작으로 환경변수 적용..."

# 1. docker-compose.yml 수정 (frontend 환경변수)
# 2. Frontend만 재시작
docker-compose down frontend
docker-compose up -d frontend

## 검증 명령어
echo "✅ 연결 테스트..."

# Frontend 컨테이너에서 올바른 URL로 Backend 접근 테스트
docker-compose exec frontend curl -v http://backend:8000/health

# 성공하면 다음과 같은 응답이 나와야 함:
# HTTP/1.1 200 OK
# {"status": "healthy", ...}