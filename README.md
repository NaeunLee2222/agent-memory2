"""
# 🤖 Enhanced Agentic AI PoC - 실행 가이드

## 🚀 빠른 시작

### 1. 환경 설정
```bash
git clone <repository>
cd enhanced-agentic-ai-poc
cp .env.example .env
# .env 파일에 API 키 설정
```

### 2. 시스템 시작
```bash
docker-compose up --build
```

### 3. 접속 정보
- Frontend: http://localhost:8501
- Backend API: http://localhost:8100
- API 문서: http://localhost:8100/docs
- Prometheus: http://localhost:9090

## 🧪 평가 실행

### 종합 평가
```bash
cd evaluation
pip install requests pandas
python poc_evaluator.py
```

### 개별 테스트
- 절차적 메모리 테스트
- 에피소드 메모리 테스트
- 5초 이내 피드백 테스트
- 크로스 에이전트 학습 테스트
- MCP 도구 성능 테스트

## 📊 검증 시나리오

### 1. 절차적 메모리 (플로우 모드)
**목적**: Step-Action-Tool 워크플로우 패턴 학습 검증
**테스트**: 동일 작업 3회 반복 → 자동 패턴 학습 확인
**성공 기준**: 패턴 학습률 50% 이상, 처리 시간 20% 단축

### 2. 에피소드 메모리 (개인화)
**목적**: 사용자별 상호작용 학습 및 개인화 서비스 검증
**테스트**: 선호도 학습 → 새 세션에서 적용 확인
**성공 기준**: 개인화 적용 성공률 75% 이상

### 3. 5초 이내 즉시 피드백
**목적**: 실시간 피드백 처리 및 시스템 개선 검증
**테스트**: 다양한 피드백 유형별 처리 시간 측정
**성공 기준**: 95% 이상 5초 이내 처리

### 4. 크로스 에이전트 학습
**목적**: 에이전트 간 학습 공유 및 집단 지능 검증
**테스트**: A 에이전트 학습 → B 에이전트 활용 확인
**성공 기준**: 학습 전이 성공률 80% 이상

### 5. MCP 도구 성능 최적화
**목적**: MCP 기반 도구 체인의 성능 및 안정성 검증
**테스트**: 복합 워크플로우 실행 → 성능 최적화 확인
**성공 기준**: 도구 성공률 85% 이상, 처리 시간 5초 이내

## 🎯 성공 기준

### 필수 달성 목표
- ✅ 워크플로우 패턴 학습: 80% 이상
- ✅ 5초 이내 피드백 처리: 95% 이상
- ✅ 개인화 학습 정확도: 75% 이상
- ✅ 크로스 에이전트 학습: 80% 이상
- ✅ MCP 도구 성능: 85% 이상

### 성능 목표
- 평균 응답 시간: 3초 이내
- 메모리 검색 시간: 200ms 이내
- 시스템 가용성: 99% 이상
- 동시 사용자: 100명 이상 지원

## 🔧 문제 해결

### 일반적인 문제
1. **컨테이너 시작 실패**: Docker 메모리 부족 → 4GB 이상 할당
2. **API 연결 오류**: 백엔드 완전 시작 대기 (30-60초)
3. **메모리 시스템 오류**: Redis/ChromaDB/Neo4j 헬스 체크
4. **느린 응답**: OpenAI API 키 및 요청 제한 확인

### 성능 최적화
- Redis 메모리 설정 조정
- ChromaDB 인덱스 최적화
- Neo4j 관계형 쿼리 최적화
- Docker 리소스 할당 증가

## 📈 모니터링

### Prometheus 메트릭
- request_duration_seconds: 요청 처리 시간
- memory_operations_total: 메모리 작업 수
- requests_total: 총 요청 수

### 주요 로그 위치
- Backend: docker logs enhanced-agentic-ai-poc-backend-1
- Frontend: docker logs enhanced-agentic-ai-poc-frontend-1

## 🎓 사용 가이드

### 기본 사용법
1. 웹 인터페이스 접속
2. 사용자 ID 설정
3. 모드 선택 (Flow/Basic)
4. 메시지 입력 및 대화
5. 피드백 제공으로 시스템 개선

### 고급 기능
- 실시간 성능 대시보드 모니터링
- 메모리 시스템 상태 분석
- 피드백 이력 및 최적화 추적
- 크로스 에이전트 학습 효과 확인

이 Enhanced PoC를 통해 차세대 지능형 에이전트 시스템의 핵심 기능들을 실증하고 검증할 수 있습니다.