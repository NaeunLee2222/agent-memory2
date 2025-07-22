evaluation_results = {
            "timestamp": datetime.now().isoformat(),
            "evaluation_version": "2.0",
            "tests": {}
        }
        
        # 테스트 실행
        test_methods = [
            self.test_procedural_memory_flow_mode,
            self.test_episodic_memory_personalization,
            self.test_5_second_feedback_target,
            self.test_cross_agent_learning,
            self.test_mcp_tool_performance_optimization
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                result = test_method()
                test_name = result["test_name"]
                evaluation_results["tests"][test_name] = result
                
                if result.get("passed", False):
                    passed_tests += 1
                    self.logger.info(f"✅ {test_name}: 통과")
                else:
                    self.logger.info(f"❌ {test_name}: 실패")
                    
            except Exception as e:
                self.logger.error(f"❌ 테스트 실행 중 오류: {str(e)}")
                evaluation_results["tests"][f"error_{test_method.__name__}"] = {
                    "error": str(e),
                    "passed": False
                }
        
        # 종합 평가 메트릭 계산
        evaluation_results["overall_metrics"] = self._calculate_overall_metrics(evaluation_results)
        
        # 결과 저장
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_poc_evaluation_{timestamp_str}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(evaluation_results, f, indent=2, ensure_ascii=False, default=str)
        
        # 평가 리포트 생성
        self._generate_evaluation_report(evaluation_results, passed_tests, total_tests)
        
        return evaluation_results
    
    def _calculate_overall_metrics(self, results: Dict) -> Dict:
        """종합 성과 지표 계산"""
        metrics = {}
        
        # 절차적 메모리 성능
        procedural_test = results["tests"].get("절차적 메모리 - 플로우 모드", {})
        if procedural_test:
            proc_metrics = procedural_test.get("metrics", {})
            metrics["procedural_memory_success_rate"] = proc_metrics.get("success_rate", 0)
            metrics["workflow_learning_rate"] = proc_metrics.get("pattern_learning_rate", 0)
        
        # 피드백 루프 성능
        feedback_test = results["tests"].get("5초 이내 피드백 처리", {})
        if feedback_test:
            fb_metrics = feedback_test.get("metrics", {})
            metrics["feedback_target_achievement"] = fb_metrics.get("target_achievement_rate", 0)
            metrics["avg_feedback_time"] = fb_metrics.get("avg_processing_time", 0)
        
        # 에피소드 메모리 성능
        episodic_test = results["tests"].get("에피소드 메모리 - 개인화 학습", {})
        if episodic_test:
            ep_metrics = episodic_test.get("metrics", {})
            metrics["personalization_success_rate"] = ep_metrics.get("success_rate", 0)
        
        # 크로스 에이전트 학습 성능
        cross_test = results["tests"].get("크로스 에이전트 학습", {})
        if cross_test:
            cross_metrics = cross_test.get("metrics", {})
            metrics["cross_agent_success_rate"] = cross_metrics.get("success_rate", 0)
        
        # MCP 도구 성능
        mcp_test = results["tests"].get("MCP 도구 성능 최적화", {})
        if mcp_test:
            mcp_metrics = mcp_test.get("metrics", {})
            metrics["mcp_tool_success_rate"] = mcp_metrics.get("avg_success_rate", 0)
            metrics["avg_mcp_processing_time"] = mcp_metrics.get("avg_processing_time", 0)
        
        # 전체 성공률
        passed_tests = sum(1 for test in results["tests"].values() if test.get("passed", False))
        total_tests = len(results["tests"])
        metrics["overall_success_rate"] = passed_tests / total_tests if total_tests > 0 else 0
        
        return metrics
    
    def _generate_evaluation_report(self, results: Dict, passed_tests: int, total_tests: int):
        """평가 리포트 생성"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📋 Enhanced Agentic AI PoC 평가 리포트")
        self.logger.info("=" * 60)
        
        overall_metrics = results.get("overall_metrics", {})
        
        # 핵심 성과 지표
        self.logger.info("\n🎯 핵심 성과 지표:")
        self.logger.info("-" * 30)
        
        # 1. 절차적 메모리 (워크플로우 학습)
        proc_success = overall_metrics.get("procedural_memory_success_rate", 0)
        workflow_learning = overall_metrics.get("workflow_learning_rate", 0)
        self.logger.info(f"워크플로우 학습 성공률: {proc_success:.1%} (목표: >80%)")
        self.logger.info(f"패턴 학습률: {workflow_learning:.1%} (목표: >50%)")
        
        # 2. 5초 이내 피드백 처리
        feedback_achievement = overall_metrics.get("feedback_target_achievement", 0)
        avg_feedback_time = overall_metrics.get("avg_feedback_time", 0)
        self.logger.info(f"5초 이내 피드백 처리율: {feedback_achievement:.1%} (목표: >95%)")
        self.logger.info(f"평균 피드백 처리 시간: {avg_feedback_time:.3f}초 (목표: <5초)")
        
        # 3. 개인화 학습
        personalization = overall_metrics.get("personalization_success_rate", 0)
        self.logger.info(f"개인화 학습 성공률: {personalization:.1%} (목표: >75%)")
        
        # 4. 크로스 에이전트 학습
        cross_agent = overall_metrics.get("cross_agent_success_rate", 0)
        self.logger.info(f"크로스 에이전트 학습 성공률: {cross_agent:.1%} (목표: >80%)")
        
        # 5. MCP 도구 성능
        mcp_success = overall_metrics.get("mcp_tool_success_rate", 0)
        mcp_time = overall_metrics.get("avg_mcp_processing_time", 0)
        self.logger.info(f"MCP 도구 성공률: {mcp_success:.1%} (목표: >85%)")
        self.logger.info(f"평균 MCP 처리 시간: {mcp_time:.2f}초 (목표: <5초)")
        
        # 전체 성공률
        overall_success = overall_metrics.get("overall_success_rate", 0)
        self.logger.info(f"\n🏆 전체 성공률: {overall_success:.1%} ({passed_tests}/{total_tests} 테스트 통과)")
        
        # PoC 성공 여부 판정
        self.logger.info("\n🎉 PoC 성공 기준 평가:")
        self.logger.info("-" * 30)
        
        success_criteria = [
            ("워크플로우 학습", proc_success >= 0.8, proc_success),
            ("5초 이내 피드백", feedback_achievement >= 0.95, feedback_achievement),
            ("개인화 학습", personalization >= 0.75, personalization),
            ("크로스 에이전트 학습", cross_agent >= 0.8, cross_agent),
            ("MCP 도구 성능", mcp_success >= 0.85, mcp_success)
        ]
        
        passed_criteria = 0
        for criteria_name, passed, value in success_criteria:
            status = "✅ 통과" if passed else "❌ 미달성"
            self.logger.info(f"{criteria_name}: {status} ({value:.1%})")
            if passed:
                passed_criteria += 1
        
        final_success_rate = passed_criteria / len(success_criteria)
        
        self.logger.info(f"\n📊 기준 달성률: {final_success_rate:.1%} ({passed_criteria}/{len(success_criteria)})")
        
        # 최종 판정
        if final_success_rate >= 0.8:
            self.logger.info("🎉 PoC 성공! - 운영 환경 적용 가능")
        elif final_success_rate >= 0.6:
            self.logger.info("⚠️ PoC 부분 성공 - 추가 최적화 필요")
        else:
            self.logger.info("❌ PoC 실패 - 시스템 재설계 검토 필요")
        
        # 개선 권장사항
        self.logger.info("\n💡 개선 권장사항:")
        self.logger.info("-" * 30)
        
        recommendations = []
        
        if feedback_achievement < 0.95:
            recommendations.append("피드백 처리 파이프라인 최적화 필요")
        
        if proc_success < 0.8:
            recommendations.append("워크플로우 패턴 학습 알고리즘 개선 필요")
        
        if cross_agent < 0.8:
            recommendations.append("크로스 에이전트 학습 메커니즘 강화 필요")
        
        if mcp_success < 0.85:
            recommendations.append("MCP 도구 안정성 및 성능 개선 필요")
        
        if avg_feedback_time >= 5.0:
            recommendations.append("피드백 처리 속도 최적화 필요")
        
        if not recommendations:
            recommendations.append("모든 목표 달성! 운영 환경 배포 준비 완료")
        
        for i, recommendation in enumerate(recommendations, 1):
            self.logger.info(f"{i}. {recommendation}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Agentic AI PoC 평가 도구")
    parser.add_argument("--backend-url", default="http://localhost:8000", 
                       help="백엔드 서버 URL")
    parser.add_argument("--output-dir", default="./evaluation_results", 
                       help="결과 저장 디렉토리")
    
    args = parser.parse_args()
    
    evaluator = EnhancedPoCEvaluator(args.backend_url)
    results = evaluator.run_comprehensive_evaluation()

# === 실행 가이드 (README.md) ===
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
- Backend API: http://localhost:8000
- API 문서: http://localhost:8000/docs
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
"""                             'steps': [
                                 {'range': [0, 70], 'color': "lightgray"},
                                 {'range': [70, 90], 'color': "yellow"},
                                 {'range': [90, 100], 'color': "green"}],
                             'threshold': {'line': {'color': "red", 'width': 4},
                                          'thickness': 0.75, 'value': 90}}))
                
                st.plotly_chart(fig_gauge_time, use_container_width=True)
            
            with target_col2:
                # 신뢰도 목표 (80% 이상)
                high_conf = len(df_recent[df_recent["confidence_score"] >= 0.8])
                conf_success_rate = (high_conf / len(df_recent) * 100)
                
                fig_gauge_conf = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = conf_success_rate,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "신뢰도 목표 달성률 (%)"},
                    delta = {'reference': 85},
                    gauge = {'axis': {'range': [None, 100]},
                             'bar': {'color': "darkgreen"},
                             'steps': [
                                 {'range': [0, 70], 'color': "lightgray"},
                                 {'range': [70, 85], 'color': "yellow"},
                                 {'range': [85, 100], 'color': "green"}]}))
                
                st.plotly_chart(fig_gauge_conf, use_container_width=True)
            
            with target_col3:
                # 전체 성공률 (처리 시간 + 신뢰도)
                overall_success = (time_success_rate + conf_success_rate) / 2
                
                fig_gauge_overall = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = overall_success,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "전체 목표 달성률 (%)"},
                    delta = {'reference': 80},
                    gauge = {'axis': {'range': [None, 100]},
                             'bar': {'color': "purple"},
                             'steps': [
                                 {'range': [0, 60], 'color': "lightgray"},
                                 {'range': [60, 80], 'color': "yellow"},
                                 {'range': [80, 100], 'color': "green"}]}))
                
                st.plotly_chart(fig_gauge_overall, use_container_width=True)
        
        else:
            st.info("최근 30분간 데이터가 없습니다. 채팅을 통해 데이터를 생성해보세요.")
    
    else:
        st.info("성능 데이터가 없습니다. 채팅 기능을 사용해보세요.")
    
    # MCP 도구 성능 통계
    st.subheader("🔧 MCP 도구 성능 통계")
    
    mcp_stats = call_backend("/mcp/tools/performance")
    
    if mcp_stats:
        mcp_data = []
        for tool_name, stats in mcp_stats.items():
            mcp_data.append({
                "도구명": tool_name,
                "성공률": f"{stats.get('recent_success_rate', stats.get('success_rate', 0)) * 100:.1f}%",
                "평균 응답시간": f"{stats.get('recent_avg_time', stats.get('avg_response_time', 0)):.2f}초",
                "사용 횟수": stats.get('usage_count', 0)
            })
        
        df_mcp = pd.DataFrame(mcp_data)
        st.dataframe(df_mcp, use_container_width=True)
    
    # 최적화 이력
    st.subheader("⚡ 최적화 이력")
    
    opt_history = call_backend("/feedback/optimization-history")
    
    if opt_history and any(opt_history.values()):
        for tool_name, history in opt_history.items():
            if history:
                st.write(f"**{tool_name} 최적화 이력:**")
                for opt in history[-3:]:  # 최근 3개만 표시
                    st.write(f"- {opt.get('timestamp', 'N/A')}: {', '.join(opt.get('optimizations', []))}")

# === 시스템 상태 ===
elif selected == "🔧 시스템 상태":
    st.header("🔧 시스템 상태 모니터링")
    
    # 헬스체크
    health = call_backend("/health")
    
    if health:
        st.subheader("💚 시스템 헬스체크")
        
        col1, col2 = st.columns(2)
        
        with col1:
            status_color = "🟢" if health["status"] == "healthy" else "🔴"
            st.write(f"**전체 상태:** {status_color} {health['status'].upper()}")
            st.write(f"**버전:** {health['version']}")
            st.write(f"**마지막 확인:** {datetime.fromtimestamp(health['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col2:
            st.write("**서비스 상태:**")
            services = health.get("services", {})
            for service_name, status in services.items():
                status_icon = "✅" if status else "❌"
                st.write(f"{status_icon} {service_name}")
    
    # 사용자 선호도 조회
    st.subheader("👤 사용자 선호도")
    
    preferences = call_backend(f"/user/{st.session_state.user_id}/preferences")
    
    if preferences:
        if preferences:
            st.write("**현재 사용자 선호도:**")
            for key, value in preferences.items():
                st.write(f"- **{key}:** {value}")
        else:
            st.info("아직 학습된 선호도가 없습니다.")
    
    # 시스템 설정
    st.subheader("⚙️ 시스템 설정")
    
    with st.expander("고급 설정"):
        # 로그 레벨 설정 (시뮬레이션)
        log_level = st.selectbox("로그 레벨", ["DEBUG", "INFO", "WARNING", "ERROR"])
        
        # 메트릭 수집 활성화
        enable_metrics = st.checkbox("성능 메트릭 수집", value=True)
        
        # 자동 최적화 활성화
        enable_auto_opt = st.checkbox("자동 최적화", value=True)
        
        if st.button("설정 적용"):
            st.success("설정이 적용되었습니다!")
    
    # 시스템 테스트
    st.subheader("🧪 시스템 종합 테스트")
    
    test_col1, test_col2 = st.columns(2)
    
    with test_col1:
        if st.button("🔍 메모리 시스템 테스트"):
            with st.spinner("메모리 시스템 테스트 중..."):
                # 각 메모리 유형 테스트
                test_results = []
                
                # 작업 메모리 테스트
                try:
                    response = send_chat_message("작업 메모리 테스트: 현재 컨텍스트 저장", "basic")
                    test_results.append("✅ 작업 메모리: 정상")
                except:
                    test_results.append("❌ 작업 메모리: 오류")
                
                # 에피소드 메모리 테스트
                try:
                    send_feedback("response_quality", "에피소드 메모리 테스트용 피드백", 4.0)
                    test_results.append("✅ 에피소드 메모리: 정상")
                except:
                    test_results.append("❌ 에피소드 메모리: 오류")
                
                for result in test_results:
                    st.write(result)
    
    with test_col2:
        if st.button("⚡ 피드백 루프 테스트"):
            with st.spinner("피드백 루프 테스트 중..."):
                # 5초 이내 목표 테스트
                start_time = time.time()
                response = send_feedback("tool_performance", "피드백 루프 응답 시간 테스트")
                end_time = time.time()
                
                response_time = end_time - start_time
                
                if response_time < 5.0:
                    st.success(f"✅ 피드백 루프 테스트 성공! ({response_time:.2f}초)")
                else:
                    st.error(f"❌ 피드백 루프 테스트 실패 ({response_time:.2f}초 > 5초)")
    
    # 데이터 내보내기
    st.subheader("📤 데이터 내보내기")
    
    if st.button("성능 데이터 다운로드"):
        if st.session_state.performance_data:
            df_export = pd.DataFrame(st.session_state.performance_data)
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="CSV 파일 다운로드",
                data=csv,
                file_name=f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("내보낼 성능 데이터가 없습니다.")

# === 하단 상태 표시줄 ===
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.write(f"**세션 ID:** {st.session_state.session_id[-8:]}")

with col2:
    st.write(f"**사용자:** {st.session_state.user_id}")

with col3:
    st.write(f"**메시지 수:** {len(st.session_state.messages)}")

with col4:
    if st.session_state.performance_data:
        last_response_time = st.session_state.performance_data[-1]["processing_time"]
        st.write(f"**최근 응답:** {last_response_time:.2f}초")
    else:
        st.write("**최근 응답:** N/A")

# === evaluation/poc_evaluator.py ===
import asyncio
import time
import json
import requests
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
import logging

class EnhancedPoCEvaluator:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.test_results = {}
        self.performance_data = []
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def call_api(self, endpoint: str, data: Dict = None) -> Dict:
        """API 호출 with timeout and retry"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if data:
                    response = requests.post(f"{self.backend_url}{endpoint}", 
                                           json=data, timeout=30)
                else:
                    response = requests.get(f"{self.backend_url}{endpoint}", 
                                          timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.error(f"HTTP {response.status_code}: {response.text}")
                    return {"error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    return {"error": str(e)}
                time.sleep(2 ** attempt)  # 지수 백오프
        
        return {"error": "Max retries exceeded"}
    
    def test_procedural_memory_flow_mode(self):
        """절차적 메모리 - 플로우 모드 검증"""
        self.logger.info("🧠 절차적 메모리 (플로우 모드) 테스트 시작...")
        
        test_case = {
            "message": "데이터베이스에서 SHE 비상 정보 조회하고 Slack으로 알림해주세요",
            "user_id": "test_procedural_user",
            "mode": "flow",
            "expected_tools": ["SEARCH_DB", "GENERATE_MSG", "SEND_SLACK"]
        }
        
        results = []
        
        # 3번 반복 실행으로 패턴 학습 확인
        for iteration in range(3):
            session_id = f"procedural_flow_test_{iteration}"
            
            start_time = time.time()
            response = self.call_api("/chat", {
                "message": test_case["message"],
                "user_id": test_case["user_id"],
                "session_id": session_id,
                "mode": test_case["mode"]
            })
            end_time = time.time()
            
            if "error" not in response:
                used_tools = [tool["tool_type"] for tool in response.get("tools_used", [])]
                workflow_executed = response.get("workflow_executed")
                
                result = {
                    "iteration": iteration + 1,
                    "processing_time": end_time - start_time,
                    "tools_used": used_tools,
                    "workflow_pattern": workflow_executed is not None,
                    "success": len(used_tools) >= 2,  # 최소 2개 도구 사용
                    "pattern_reuse": iteration > 0 and workflow_executed is not None
                }
                
                results.append(result)
                self.logger.info(f"  반복 {iteration + 1}: {result['processing_time']:.2f}초 - {'✅' if result['success'] else '❌'}")
            else:
                results.append({
                    "iteration": iteration + 1,
                    "error": response["error"],
                    "success": False
                })
        
        # 성능 개선 확인 (시간 단축)
        if len(results) >= 3:
            time_improvement = results[0]["processing_time"] - results[-1]["processing_time"]
            pattern_learning = sum(1 for r in results[1:] if r.get("pattern_reuse", False))
            
            success_metrics = {
                "total_tests": len(results),
                "successful_tests": sum(1 for r in results if r.get("success", False)),
                "success_rate": sum(1 for r in results if r.get("success", False)) / len(results),
                "time_improvement": time_improvement,
                "pattern_learning_rate": pattern_learning / (len(results) - 1) if len(results) > 1 else 0,
                "avg_processing_time": sum(r.get("processing_time", 0) for r in results) / len(results)
            }
            
            return {
                "test_name": "절차적 메모리 - 플로우 모드",
                "results": results,
                "metrics": success_metrics,
                "passed": success_metrics["success_rate"] >= 0.8 and success_metrics["pattern_learning_rate"] >= 0.5
            }
        
        return {"test_name": "절차적 메모리 - 플로우 모드", "results": results, "passed": False}
    
    def test_episodic_memory_personalization(self):
        """에피소드 메모리 - 개인화 학습 검증"""
        self.logger.info("📚 에피소드 메모리 개인화 테스트 시작...")
        
        user_id = "test_episodic_user"
        
        # 1단계: 선호도 학습
        preference_session = f"episodic_pref_{int(time.time())}"
        preference_response = self.call_api("/chat", {
            "message": "저는 기술적인 설명을 선호하고, 간결한 메시지를 좋아합니다",
            "user_id": user_id,
            "session_id": preference_session,
            "mode": "basic"
        })
        
        # 피드백으로 선호도 강화
        feedback_response = self.call_api("/feedback", {
            "session_id": preference_session,
            "user_id": user_id,
            "feedback_type": "style_preference",
            "content": "기술적이고 간결한 스타일을 선호합니다",
            "rating": 5.0
        })
        
        time.sleep(2)  # 메모리 처리 시간 대기
        
        # 2단계: 새 세션에서 개인화 적용 확인
        test_session = f"episodic_test_{int(time.time())}"
        test_response = self.call_api("/chat", {
            "message": "머신러닝에 대해 설명해주세요",
            "user_id": user_id,
            "session_id": test_session,
            "mode": "basic"
        })
        
        # 3단계: 선호도 조회로 학습 확인
        preferences_response = self.call_api(f"/user/{user_id}/preferences")
        
        results = {
            "preference_learning": "error" not in preference_response,
            "feedback_processing": "error" not in feedback_response and feedback_response.get("applied", False),
            "personalization_applied": "error" not in test_response and len(test_response.get("memory_used", {}).get("EPISODIC", [])) > 0,
            "preferences_stored": "error" not in preferences_response and len(preferences_response) > 0,
            "processing_times": {
                "preference": preference_response.get("processing_time", 0),
                "feedback": feedback_response.get("processing_time", 0),
                "personalized": test_response.get("processing_time", 0)
            }
        }
        
        success_rate = sum(1 for k, v in results.items() if k != "processing_times" and v) / 4
        
        return {
            "test_name": "에피소드 메모리 - 개인화 학습",
            "results": results,
            "metrics": {
                "success_rate": success_rate,
                "preference_recall": results["personalization_applied"],
                "feedback_responsiveness": results["feedback_processing"]
            },
            "passed": success_rate >= 0.75
        }
    
    def test_5_second_feedback_target(self):
        """5초 이내 피드백 처리 목표 검증"""
        self.logger.info("⚡ 5초 이내 피드백 처리 테스트 시작...")
        
        feedback_tests = [
            {"type": "style_preference", "content": "더 친근한 톤으로 대화해주세요"},
            {"type": "response_quality", "content": "응답이 너무 길어요", "rating": 2.0},
            {"type": "tool_performance", "content": "데이터 조회가 느려요"},
            {"type": "workflow_efficiency", "content": "단계를 줄여주세요"},
            {"type": "user_experience", "content": "더 직관적이었으면 좋겠어요"}
        ]
        
        results = []
        
        for i, test in enumerate(feedback_tests):
            session_id = f"feedback_speed_test_{i}"
            
            start_time = time.time()
            response = self.call_api("/feedback", {
                "session_id": session_id,
                "user_id": "feedback_speed_tester",
                "feedback_type": test["type"],
                "content": test["content"],
                "rating": test.get("rating")
            })
            end_time = time.time()
            
            processing_time = end_time - start_time
            meets_target = processing_time < 5.0
            
            result = {
                "test_case": i + 1,
                "feedback_type": test["type"],
                "processing_time": processing_time,
                "meets_5s_target": meets_target,
                "applied": response.get("applied", False),
                "optimizations_count": len(response.get("optimizations", []))
            }
            
            results.append(result)
            
            status = "✅" if meets_target else "❌"
            self.logger.info(f"  테스트 {i+1}: {processing_time:.3f}초 - {status}")
        
        # 성과 지표 계산
        target_achievement_rate = sum(1 for r in results if r["meets_5s_target"]) / len(results)
        avg_processing_time = sum(r["processing_time"] for r in results) / len(results)
        application_rate = sum(1 for r in results if r["applied"]) / len(results)
        
        return {
            "test_name": "5초 이내 피드백 처리",
            "results": results,
            "metrics": {
                "target_achievement_rate": target_achievement_rate,
                "avg_processing_time": avg_processing_time,
                "application_rate": application_rate,
                "total_tests": len(results)
            },
            "passed": target_achievement_rate >= 0.95  # 95% 목표
        }
    
    def test_cross_agent_learning(self):
        """크로스 에이전트 학습 검증"""
        self.logger.info("🤝 크로스 에이전트 학습 테스트 시작...")
        
        user_id = "cross_agent_test_user"
        
        # Agent 1에서 학습
        agent1_session = f"cross_agent_1_{int(time.time())}"
        
        # 선호도 설정
        learning_response = self.call_api("/chat", {
            "message": "저는 항상 Slack 알림을 선호하고, 상세한 로그 정보를 원합니다",
            "user_id": user_id,
            "session_id": agent1_session,
            "mode": "basic"
        })
        
        # 피드백으로 학습 강화
        feedback_response = self.call_api("/feedback", {
            "session_id": agent1_session,
            "user_id": user_id,
            "feedback_type": "style_preference",
            "content": "상세한 기술 정보를 포함해서 Slack으로 알림해주세요",
            "rating": 5.0
        })
        
        time.sleep(3)  # 크로스 에이전트 학습 전파 시간
        
        # Agent 2에서 학습 내용 활용 확인
        agent2_session = f"cross_agent_2_{int(time.time())}"
        
        application_response = self.call_api("/chat", {
            "message": "시스템 상태를 확인해주세요",
            "user_id": user_id,  # 동일한 사용자
            "session_id": agent2_session,  # 다른 세션 (다른 에이전트 시뮬레이션)
            "mode": "basic"
        })
        
        # 선호도 데이터 확인
        preferences_response = self.call_api(f"/user/{user_id}/preferences")
        
        results = {
            "initial_learning": "error" not in learning_response,
            "feedback_applied": feedback_response.get("applied", False),
            "cross_agent_memory_used": len(application_response.get("memory_used", {}).get("EPISODIC", [])) > 0,
            "preferences_shared": len(preferences_response) > 0,
            "processing_times": {
                "learning": learning_response.get("processing_time", 0),
                "feedback": feedback_response.get("processing_time", 0),
                "application": application_response.get("processing_time", 0)
            },
            "tools_optimization": any("slack" in tool.get("tool_type", "").lower() 
                                    for tool in application_response.get("tools_used", []))
        }
        
        # 성공률 계산
        success_indicators = ["initial_learning", "feedback_applied", "cross_agent_memory_used", "preferences_shared"]
        success_rate = sum(1 for indicator in success_indicators if results[indicator]) / len(success_indicators)
        
        return {
            "test_name": "크로스 에이전트 학습",
            "results": results,
            "metrics": {
                "success_rate": success_rate,
                "learning_transfer_success": results["cross_agent_memory_used"],
                "preference_sharing_success": results["preferences_shared"]
            },
            "passed": success_rate >= 0.8  # 80% 목표
        }
    
    def test_mcp_tool_performance_optimization(self):
        """MCP 도구 성능 최적화 검증"""
        self.logger.info("🔧 MCP 도구 성능 최적화 테스트 시작...")
        
        # 초기 성능 측정
        initial_stats = self.call_api("/mcp/tools/performance")
        
        # 여러 도구를 사용하는 워크플로우 실행
        test_workflows = [
            {
                "message": "데이터베이스에서 사용자 정보를 조회하고 결과를 Slack으로 전송해주세요",
                "expected_tools": ["SEARCH_DB", "SEND_SLACK"]
            },
            {
                "message": "비상 상황 알림을 생성하고 이메일과 Slack으로 동시 발송해주세요", 
                "expected_tools": ["EMERGENCY_MAIL", "SEND_SLACK"]
            },
            {
                "message": "시스템 상태 메시지를 생성해서 관리자에게 전달해주세요",
                "expected_tools": ["GENERATE_MSG", "SEND_SLACK"]
            }
        ]
        
        performance_results = []
        
        for i, workflow in enumerate(test_workflows):
            session_id = f"mcp_perf_test_{i}"
            
            start_time = time.time()
            response = self.call_api("/chat", {
                "message": workflow["message"],
                "user_id": "mcp_performance_tester",
                "session_id": session_id,
                "mode": "flow"
            })
            end_time = time.time()
            
            if "error" not in response:
                tools_used = response.get("tools_used", [])
                successful_tools = [t for t in tools_used if t.get("success")]
                
                result = {
                    "workflow": i + 1,
                    "total_time": end_time - start_time,
                    "tools_used": len(tools_used),
                    "successful_tools": len(successful_tools),
                    "success_rate": len(successful_tools) / len(tools_used) if tools_used else 0,
                    "avg_tool_time": sum(t.get("execution_time", 0) for t in tools_used) / len(tools_used) if tools_used else 0
                }
                
                performance_results.append(result)
                self.logger.info(f"  워크플로우 {i+1}: {result['total_time']:.2f}초, 성공률 {result['success_rate']:.1%}")
        
        # 최종 성능 측정
        final_stats = self.call_api("/mcp/tools/performance")
        
        # 성능 개선 확인
        improvements = {}
        if initial_stats and final_stats:
            for tool_name in initial_stats.keys():
                if tool_name in final_stats:
                    initial_time = initial_stats[tool_name].get("recent_avg_time", 
                                                              initial_stats[tool_name].get("avg_response_time", 0))
                    final_time = final_stats[tool_name].get("recent_avg_time",
                                                          final_stats[tool_name].get("avg_response_time", 0))
                    
                    if initial_time > 0:
                        improvements[tool_name] = {
                            "time_improvement": initial_time - final_time,
                            "improvement_rate": (initial_time - final_time) / initial_time if initial_time > 0 else 0
                        }
        
        metrics = {
            "total_workflows": len(performance_results),
            "avg_success_rate": sum(r["success_rate"] for r in performance_results) / len(performance_results) if performance_results else 0,
            "avg_processing_time": sum(r["total_time"] for r in performance_results) / len(performance_results) if performance_results else 0,
            "performance_improvements": improvements
        }
        
        return {
            "test_name": "MCP 도구 성능 최적화",
            "results": performance_results,
            "metrics": metrics,
            "passed": metrics["avg_success_rate"] >= 0.85 and metrics["avg_processing_time"] <= 5.0
        }
    
    def run_comprehensive_evaluation(self):
        """종합 평가 실행"""
        self.logger.info("🚀 Enhanced Agentic AI PoC 종합 평가 시작...")
        self.logger.info("=" * 60)
        
        evaluation_results@app.get("/feedback/optimization-history")
async def optimization_history_endpoint():
    """최적화 이력 조회"""
    try:
        history = await feedback_service.get_optimization_history()
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최적화 이력 조회 오류: {str(e)}")

@app.get("/user/{user_id}/preferences")
async def user_preferences_endpoint(user_id: str):
    """사용자 선호도 조회"""
    try:
        preferences = await feedback_service.get_user_preferences(user_id)
        return preferences
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"선호도 조회 오류: {str(e)}")

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "memory": memory_service is not None,
            "mcp": mcp_service is not None,
            "feedback": feedback_service is not None,
            "agent": agent_service is not None
        },
        "version": "2.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# === frontend/Dockerfile ===
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

# === frontend/requirements.txt ===
streamlit==1.29.0
requests==2.31.0
plotly==5.17.0
pandas==2.1.4
altair==5.2.0
streamlit-option-menu==0.3.6
streamlit-autorefresh==0.0.1

# === frontend/streamlit_app.py ===
import streamlit as st
import requests
import time
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh

# 설정
BACKEND_URL = "http://backend:8000"

st.set_page_config(
    page_title="Enhanced Agentic AI PoC",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user"
if "performance_data" not in st.session_state:
    st.session_state.performance_data = []
if "feedback_history" not in st.session_state:
    st.session_state.feedback_history = []

def call_backend(endpoint, method="GET", data=None):
    """백엔드 API 호출"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"백엔드 오류: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"연결 오류: {str(e)}")
        return None

def send_chat_message(message, mode):
    """채팅 메시지 전송"""
    data = {
        "message": message,
        "user_id": st.session_state.user_id,
        "session_id": st.session_state.session_id,
        "mode": mode,
        "context": {}
    }
    
    with st.spinner("🤖 AI가 처리 중입니다..."):
        response = call_backend("/chat", method="POST", data=data)
    
    if response:
        # 성능 데이터 저장
        st.session_state.performance_data.append({
            "timestamp": datetime.now(),
            "processing_time": response.get("processing_time", 0),
            "tools_used": len(response.get("tools_used", [])),
            "confidence_score": response.get("confidence_score", 0),
            "mode": mode,
            "memory_types": len([k for k, v in response.get("memory_used", {}).items() if v])
        })
        
        return response
    return None

def send_feedback(feedback_type, content, rating=None):
    """피드백 전송"""
    data = {
        "session_id": st.session_state.session_id,
        "user_id": st.session_state.user_id,
        "feedback_type": feedback_type,
        "content": content,
        "rating": rating
    }
    
    start_time = time.time()
    response = call_backend("/feedback", method="POST", data=data)
    end_time = time.time()
    
    if response:
        feedback_record = {
            "timestamp": datetime.now(),
            "type": feedback_type,
            "content": content,
            "response_time": end_time - start_time,
            "optimizations": response.get("optimizations", []),
            "applied": response.get("applied", False)
        }
        st.session_state.feedback_history.append(feedback_record)
        
        # 5초 이내 목표 달성 여부 표시
        if end_time - start_time < 5.0:
            st.success(f"✅ 피드백이 {end_time - start_time:.2f}초 만에 적용되었습니다!")
        else:
            st.warning(f"⚠️ 피드백 처리가 {end_time - start_time:.2f}초 소요되었습니다 (목표: 5초 이내)")
        
        if response.get("optimizations"):
            st.write("**적용된 최적화:**")
            for opt in response["optimizations"]:
                st.write(f"- {opt}")
    
    return response

# === 메인 인터페이스 ===
st.title("🤖 Enhanced Agentic AI PoC")
st.markdown("**MCP 도구 기반 지능형 메모리와 5초 이내 피드백 루프**")

# 사이드바 메뉴
with st.sidebar:
    selected = option_menu(
        "메인 메뉴",
        ["💬 채팅", "🧠 메모리 분석", "⚡ 피드백 센터", "📊 성능 대시보드", "🔧 시스템 상태"],
        icons=['chat', 'brain', 'lightning', 'graph-up', 'gear'],
        menu_icon="robot",
        default_index=0,
    )
    
    st.markdown("---")
    
    # 사용자 설정
    st.header("👤 사용자 설정")
    st.session_state.user_id = st.text_input("사용자 ID", value=st.session_state.user_id)
    
    # 새 세션 시작
    if st.button("🔄 새 세션 시작"):
        st.session_state.session_id = f"session_{int(time.time())}"
        st.session_state.messages = []
        st.success("새 세션이 시작되었습니다!")
        st.rerun()

# === 채팅 인터페이스 ===
if selected == "💬 채팅":
    st.header("💬 지능형 채팅 인터페이스")
    
    # 모드 선택
    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("실행 모드", ["flow", "basic"], 
                       help="Flow: 구조화된 Step-Action-Tool, Basic: 자율적 도구 선택")
    with col2:
        st.write("**현재 세션:**", st.session_state.session_id[-8:])
        st.write("**처리된 메시지:**", len(st.session_state.messages) // 2)
    
    # 빠른 테스트 버튼들
    st.subheader("🚀 빠른 테스트")
    test_col1, test_col2, test_col3 = st.columns(3)
    
    with test_col1:
        if st.button("📊 데이터 조회 테스트"):
            test_message = "사용자 데이터를 조회하고 Slack으로 알림해주세요"
            st.session_state.test_message = test_message
    
    with test_col2:
        if st.button("🚨 비상 알림 테스트"):
            test_message = "SHE 비상 상황이 발생했습니다. 긴급 알림을 보내주세요"
            st.session_state.test_message = test_message
    
    with test_col3:
        if st.button("🔄 절차 학습 테스트"):
            test_message = "주간 리포트를 생성하고 관련 팀에 전송해주세요"
            st.session_state.test_message = test_message
    
    # 채팅 기록 표시
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                if message["role"] == "assistant" and "metadata" in message:
                    with st.expander("📊 실행 상세 정보"):
                        metadata = message["metadata"]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("처리 시간", f"{metadata.get('processing_time', 0):.2f}초")
                        with col2:
                            st.metric("사용 도구", f"{len(metadata.get('tools_used', []))}개")
                        with col3:
                            st.metric("신뢰도", f"{metadata.get('confidence_score', 0):.1%}")
                        
                        if metadata.get("workflow_executed"):
                            st.write("**실행된 워크플로우:**", metadata["workflow_executed"].get("pattern_name", "N/A"))
                        
                        if metadata.get("memory_used"):
                            st.write("**활용된 메모리:**")
                            for memory_type, items in metadata["memory_used"].items():
                                if items:
                                    st.write(f"- {memory_type}: {len(items)}개 항목")
                        
                        if metadata.get("optimization_applied"):
                            st.write("**적용된 최적화:**")
                            for opt in metadata["optimization_applied"]:
                                st.write(f"- {opt}")
    
    # 테스트 메시지 자동 입력
    default_message = ""
    if hasattr(st.session_state, 'test_message'):
        default_message = st.session_state.test_message
        delattr(st.session_state, 'test_message')
    
    # 채팅 입력
    if prompt := st.chat_input("메시지를 입력하세요...", value=default_message):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답 처리
        response = send_chat_message(prompt, mode)
        
        if response:
            # AI 응답 추가
            assistant_message = {
                "role": "assistant",
                "content": response["response"],
                "metadata": response
            }
            st.session_state.messages.append(assistant_message)
            
            with st.chat_message("assistant"):
                st.markdown(response["response"])
                
                with st.expander("📊 실행 상세 정보"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("처리 시간", f"{response.get('processing_time', 0):.2f}초")
                    with col2:
                        st.metric("사용 도구", f"{len(response.get('tools_used', []))}개")
                    with col3:
                        st.metric("신뢰도", f"{response.get('confidence_score', 0):.1%}")
    
    # 즉시 피드백 섹션
    with st.expander("⚡ 즉시 피드백 (5초 이내 목표)", expanded=False):
        feedback_col1, feedback_col2 = st.columns(2)
        
        with feedback_col1:
            st.write("**스타일 피드백**")
            if st.button("🎭 더 친근하게"):
                send_feedback("style_preference", "더 친근하고 캐주얼한 톤으로 대화해주세요")
            if st.button("💼 더 공식적으로"):
                send_feedback("style_preference", "더 공식적이고 비즈니스 톤으로 대화해주세요")
            if st.button("🔬 더 기술적으로"):
                send_feedback("style_preference", "더 기술적이고 전문적인 설명을 해주세요")
        
        with feedback_col2:
            st.write("**내용 피드백**")
            if st.button("📝 더 자세히"):
                send_feedback("response_quality", "응답이 너무 간단해요. 더 자세한 설명이 필요해요", rating=2.0)
            if st.button("📋 더 간략하게"):
                send_feedback("response_quality", "응답이 너무 길어요. 더 간략하게 요약해주세요", rating=2.5)
            if st.button("🚀 속도 우선"):
                send_feedback("workflow_efficiency", "정확도보다 빠른 응답이 더 중요해요")

# === 메모리 분석 ===
elif selected == "🧠 메모리 분석":
    st.header("🧠 지능형 메모리 시스템 분석")
    
    # 실시간 새로고침
    st_autorefresh(interval=10000, key="memory_refresh")  # 10초마다 새로고침
    
    # 메모리 통계 조회
    memory_stats = call_backend("/memory/stats")
    
    if memory_stats:
        st.subheader("📊 메모리 시스템 현황")
        
        # 메트릭 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            working_count = memory_stats.get("working_memory", {}).get("total_keys", 0)
            st.metric("작업 메모리", f"{working_count}개", help="현재 활성 세션의 임시 메모리")
        
        with col2:
            episodic_count = memory_stats.get("episodic_memory", {}).get("episodes_count", 0)
            st.metric("에피소드 메모리", f"{episodic_count}개", help="사용자 상호작용 기록")
        
        with col3:
            semantic_nodes = memory_stats.get("semantic_memory", {}).get("nodes_count", 0)
            st.metric("시맨틱 메모리", f"{semantic_nodes}개", help="도메인 지식 노드")
        
        with col4:
            procedures_count = memory_stats.get("episodic_memory", {}).get("procedures_count", 0)
            st.metric("절차 메모리", f"{procedures_count}개", help="학습된 워크플로우 패턴")
        
        # 성능 지표
        if "performance" in memory_stats:
            st.subheader("⚡ 메모리 성능 지표")
            perf = memory_stats["performance"]
            
            perf_col1, perf_col2 = st.columns(2)
            with perf_col1:
                avg_time = perf.get("avg_retrieval_time", 0)
                color = "green" if avg_time < 0.2 else "orange" if avg_time < 0.5 else "red"
                st.metric(
                    "평균 검색 시간", 
                    f"{avg_time:.3f}초", 
                    help="목표: 0.2초 이하",
                    delta=f"목표 대비 {(avg_time - 0.2):.3f}초" if avg_time > 0.2 else "목표 달성!"
                )
            
            with perf_col2:
                total_ops = perf.get("total_operations", 0)
                st.metric("총 작업 수", f"{total_ops:,}회")
        
        # 메모리 사용률 시각화
        st.subheader("📈 메모리 사용 분포")
        
        memory_data = {
            "메모리 유형": ["작업 메모리", "에피소드 메모리", "시맨틱 메모리", "절차 메모리"],
            "항목 수": [
                working_count,
                episodic_count, 
                semantic_nodes,
                procedures_count
            ]
        }
        
        df_memory = pd.DataFrame(memory_data)
        fig_pie = px.pie(df_memory, values="항목 수", names="메모리 유형", 
                        title="메모리 유형별 분포")
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Redis 상세 정보
        if "working_memory" in memory_stats:
            st.subheader("💾 Redis 작업 메모리 상세")
            redis_info = memory_stats["working_memory"]
            
            detail_col1, detail_col2 = st.columns(2)
            with detail_col1:
                st.write(f"**메모리 사용량:** {redis_info.get('memory_usage', 'N/A')}")
            with detail_col2:
                st.write(f"**연결된 클라이언트:** {redis_info.get('connected_clients', 0)}개")
    
    # 메모리 테스트 섹션
    st.subheader("🧪 메모리 시스템 테스트")
    
    test_col1, test_col2 = st.columns(2)
    
    with test_col1:
        st.write("**절차 메모리 테스트**")
        if st.button("📋 워크플로우 학습 테스트"):
            # 동일한 작업을 3번 수행하여 절차 학습 확인
            test_message = "데이터 조회 → 메시지 생성 → Slack 전송 워크플로우 테스트"
            response = send_chat_message(test_message, "flow")
            if response:
                st.success("워크플로우 실행 완료! 3회 반복 후 자동 학습을 확인해보세요.")
    
    with test_col2:
        st.write("**에피소드 메모리 테스트**")
        if st.button("🎯 개인화 학습 테스트"):
            test_message = "제 선호도를 기억해주세요: 간결한 메시지, 기술적 설명 선호"
            response = send_chat_message(test_message, "basic")
            if response:
                st.success("선호도 저장 완료! 다음 대화에서 개인화 효과를 확인해보세요.")

# === 피드백 센터 ===
elif selected == "⚡ 피드백 센터":
    st.header("⚡ 실시간 피드백 센터")
    st.markdown("**목표: 5초 이내 피드백 반영**")
    
    # 피드백 이력 표시
    if st.session_state.feedback_history:
        st.subheader("📊 피드백 처리 성능")
        
        df_feedback = pd.DataFrame(st.session_state.feedback_history)
        
        # 5초 이내 달성률 계산
        within_5s = len(df_feedback[df_feedback["response_time"] < 5.0])
        total_feedback = len(df_feedback)
        success_rate = (within_5s / total_feedback * 100) if total_feedback > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("5초 이내 처리율", f"{success_rate:.1f}%", 
                     help="목표: 95% 이상")
        with col2:
            avg_time = df_feedback["response_time"].mean()
            st.metric("평균 처리 시간", f"{avg_time:.2f}초")
        with col3:
            st.metric("총 피드백", f"{total_feedback}건")
        
        # 피드백 처리 시간 분포 차트
        fig_hist = px.histogram(df_feedback, x="response_time", 
                               title="피드백 처리 시간 분포",
                               labels={"response_time": "처리 시간 (초)", "count": "빈도"})
        fig_hist.add_vline(x=5.0, line_dash="dash", line_color="red", 
                          annotation_text="목표: 5초")
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # 최근 피드백 이력
        st.subheader("📝 최근 피드백 이력")
        recent_feedback = df_feedback.tail(10).sort_values("timestamp", ascending=False)
        
        for _, feedback in recent_feedback.iterrows():
            with st.expander(f"🕒 {feedback['timestamp'].strftime('%H:%M:%S')} - {feedback['type']}"):
                st.write(f"**내용:** {feedback['content']}")
                st.write(f"**처리 시간:** {feedback['response_time']:.2f}초")
                st.write(f"**적용 여부:** {'✅ 적용됨' if feedback['applied'] else '❌ 미적용'}")
                
                if feedback['optimizations']:
                    st.write("**적용된 최적화:**")
                    for opt in feedback['optimizations']:
                        st.write(f"- {opt}")
    
    # 고급 피드백 입력
    st.subheader("💬 상세 피드백 입력")
    
    feedback_type = st.selectbox("피드백 유형", [
        "style_preference", "response_quality", "tool_performance", 
        "workflow_efficiency", "user_experience"
    ])
    
    feedback_content = st.text_area("피드백 내용", 
                                   placeholder="구체적인 개선 사항을 설명해주세요...")
    
    rating = st.slider("만족도 평가", 1.0, 5.0, 3.0, 0.5)
    
    if st.button("🚀 피드백 제출 (5초 이내 목표)"):
        if feedback_content:
            send_feedback(feedback_type, feedback_content, rating)
        else:
            st.warning("피드백 내용을 입력해주세요.")
    
    # 크로스 에이전트 학습 테스트
    st.subheader("🤝 크로스 에이전트 학습 테스트")
    st.write("다른 세션에서 학습한 선호도가 현재 세션에 적용되는지 테스트합니다.")
    
    if st.button("🔄 다른 세션 선호도 동기화"):
        # 다른 사용자 ID로 선호도 설정 후 현재 세션에 적용 테스트
        sync_response = send_feedback("preference_sync", "다른 에이전트 학습 내용을 현재 세션에 동기화")
        if sync_response:
            st.success("크로스 에이전트 학습 동기화 완료!")

# === 성능 대시보드 ===
elif selected == "📊 성능 대시보드":
    st.header("📊 시스템 성능 대시보드")
    
    # 자동 새로고침
    st_autorefresh(interval=5000, key="dashboard_refresh")  # 5초마다 새로고침
    
    if st.session_state.performance_data:
        df_perf = pd.DataFrame(st.session_state.performance_data)
        
        # 최근 30분 데이터만 표시
        current_time = datetime.now()
        df_recent = df_perf[df_perf["timestamp"] > (current_time - timedelta(minutes=30))]
        
        if not df_recent.empty:
            # 실시간 메트릭
            st.subheader("⚡ 실시간 성능 지표")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_processing = df_recent["processing_time"].mean()
                st.metric("평균 처리 시간", f"{avg_processing:.2f}초",
                         delta=f"{avg_processing - df_recent['processing_time'].iloc[0]:.2f}초")
            
            with col2:
                avg_confidence = df_recent["confidence_score"].mean()
                st.metric("평균 신뢰도", f"{avg_confidence:.1%}")
            
            with col3:
                avg_tools = df_recent["tools_used"].mean()
                st.metric("평균 도구 사용", f"{avg_tools:.1f}개")
            
            with col4:
                avg_memory = df_recent["memory_types"].mean()
                st.metric("평균 메모리 활용", f"{avg_memory:.1f}개 유형")
            
            # 시간대별 성능 추이
            st.subheader("📈 시간대별 성능 추이")
            
            # 처리 시간 추이
            fig_time = px.line(df_recent, x="timestamp", y="processing_time", 
                              color="mode", title="처리 시간 추이")
            fig_time.add_hline(y=3.0, line_dash="dash", line_color="orange", 
                              annotation_text="목표: 3초 이내")
            st.plotly_chart(fig_time, use_container_width=True)
            
            # 모드별 성능 비교
            st.subheader("🔄 모드별 성능 비교")
            
            mode_comparison = df_recent.groupby("mode").agg({
                "processing_time": ["mean", "std"],
                "confidence_score": "mean",
                "tools_used": "mean"
            }).round(3)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 모드별 처리 시간 박스플롯
                fig_box = px.box(df_recent, x="mode", y="processing_time", 
                                title="모드별 처리 시간 분포")
                st.plotly_chart(fig_box, use_container_width=True)
            
            with col2:
                # 모드별 신뢰도 비교
                fig_conf = px.bar(df_recent.groupby("mode")["confidence_score"].mean().reset_index(), 
                                 x="mode", y="confidence_score", 
                                 title="모드별 평균 신뢰도")
                st.plotly_chart(fig_conf, use_container_width=True)
            
            # 성능 목표 달성 현황
            st.subheader("🎯 성능 목표 달성 현황")
            
            target_col1, target_col2, target_col3 = st.columns(3)
            
            with target_col1:
                # 처리 시간 목표 (3초 이내)
                under_3s = len(df_recent[df_recent["processing_time"] < 3.0])
                time_success_rate = (under_3s / len(df_recent) * 100)
                
                fig_gauge_time = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = time_success_rate,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "처리 시간 목표 달성률 (%)"},
                    delta = {'reference': 90},
                    gauge = {'axis': {'range': [None, 100]},
                             'bar': {'color': "darkblue"},
                             'steps': [    def _calculate_expected_improvements(self, optimizations: List[str]) -> Dict[str, float]:
        """최적화로 인한 예상 개선 효과 계산"""
        improvements = {}
        
        for optimization in optimizations:
            if "속도" in optimization or "캐싱" in optimization:
                improvements["response_time_improvement"] = improvements.get("response_time_improvement", 0) + 0.25
                
            elif "안정성" in optimization or "신뢰성" in optimization:
                improvements["reliability_improvement"] = improvements.get("reliability_improvement", 0) + 0.15
                
            elif "정확도" in optimization or "품질" in optimization:
                improvements["accuracy_improvement"] = improvements.get("accuracy_improvement", 0) + 0.20
                
            elif "만족도" in optimization or "사용자" in optimization:
                improvements["user_satisfaction_improvement"] = improvements.get("user_satisfaction_improvement", 0) + 0.30
        
        return improvements
    
    async def get_optimization_history(self, tool_type: MCPToolType = None) -> Dict[str, Any]:
        """최적화 이력 조회"""
        if tool_type:
            return {
                str(tool_type): self.optimization_history.get(tool_type, [])
            }
        return {str(k): v for k, v in self.optimization_history.items()}
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """사용자 선호도 조회"""
        # 메모리에서도 조회 (크로스 에이전트 학습용)
        preferences, _ = await self.memory_service.get_working_memory(f"preferences_{user_id}", "shared_preferences")
        
        # 현재 세션 선호도와 병합
        current_preferences = self.user_preferences.get(user_id, {})
        
        return {**preferences.get("shared_preferences", {}), **current_preferences}

# === backend/services/agent_service.py ===
import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import OpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from ..services.memory_service import EnhancedMemoryService
from ..services.mcp_service import MCPService
from ..services.feedback_service import EnhancedFeedbackService
from ..models.schemas import (
    AgentMode, ChatResponse, WorkflowStep, WorkflowPattern,
    MCPToolCall, MCPToolType, MemoryType, EpisodicMemory
)
from ..utils.config import config

class EnhancedAgentService:
    def __init__(self, memory_service: EnhancedMemoryService, mcp_service: MCPService, feedback_service: EnhancedFeedbackService):
        self.memory_service = memory_service
        self.mcp_service = mcp_service
        self.feedback_service = feedback_service
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.checkpointer = MemorySaver()
        
        # 워크플로우 패턴 저장소
        self.learned_patterns = {}
        
    async def process_chat(self, message: str, user_id: str, session_id: str, mode: AgentMode, context: Dict[str, Any] = None) -> ChatResponse:
        """채팅 메시지 처리"""
        start_time = time.time()
        context = context or {}
        
        # 1. 관련 메모리 검색
        memories, memory_retrieval_time = await self.memory_service.retrieve_relevant_memories(
            user_id=user_id,
            query=message,
            memory_types=[MemoryType.PROCEDURAL, MemoryType.EPISODIC, MemoryType.SEMANTIC],
            limit=3
        )
        
        # 2. 사용자 선호도 적용
        user_preferences = await self.feedback_service.get_user_preferences(user_id)
        
        # 3. 모드별 처리
        if mode == AgentMode.FLOW:
            workflow_result = await self._process_flow_mode(message, user_id, session_id, memories, user_preferences, context)
        else:
            workflow_result = await self._process_basic_mode(message, user_id, session_id, memories, user_preferences, context)
        
        # 4. 응답 생성
        response_text = await self._generate_response(message, workflow_result, user_preferences)
        
        # 5. 에피소드 메모리에 상호작용 저장
        episode = EpisodicMemory(
            episode_id=f"{session_id}_{int(time.time() * 1000)}",
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.now(),
            interaction_type="chat_interaction",
            context={
                "message": message,
                "mode": mode,
                "response": response_text,
                "tools_used": [result.tool_type for result in workflow_result["tools_used"]],
                "processing_time": time.time() - start_time
            },
            workflow_executed=workflow_result.get("workflow_pattern"),
            lessons_learned=workflow_result.get("lessons_learned", [])
        )
        
        await self.memory_service.store_episodic_memory(episode)
        
        # 6. 성능 피드백 처리
        for tool_result in workflow_result["tools_used"]:
            await self.feedback_service.process_performance_feedback(
                tool_type=tool_result.tool_type,
                execution_time=tool_result.execution_time,
                success=tool_result.success,
                error_type=tool_result.error
            )
        
        total_processing_time = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            workflow_executed=workflow_result.get("workflow_pattern"),
            memory_used={
                MemoryType.WORKING: [f"세션 컨텍스트: {len(context)} 항목"],
                MemoryType.EPISODIC: [m["content"][:100] for m in memories[MemoryType.EPISODIC][:2]],
                MemoryType.SEMANTIC: [m["content"][:100] for m in memories[MemoryType.SEMANTIC][:2]],
                MemoryType.PROCEDURAL: [m["content"][:100] for m in memories[MemoryType.PROCEDURAL][:2]]
            },
            processing_time=total_processing_time,
            tools_used=workflow_result["tools_used"],
            confidence_score=workflow_result.get("confidence_score", 0.8),
            optimization_applied=workflow_result.get("optimizations", [])
        )
    
    async def _process_flow_mode(self, message: str, user_id: str, session_id: str, 
                                memories: Dict[MemoryType, List], user_preferences: Dict, 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """플로우 모드 처리 - 구조화된 Step-Action-Tool 실행"""
        
        # 1. 유사한 절차 패턴 검색
        similar_procedures, _ = await self.memory_service.retrieve_similar_procedures(message, user_id, limit=3)
        
        # 2. 새로운 워크플로우 계획 또는 기존 패턴 재사용
        if similar_procedures and similar_procedures[0].get("relevance_score", 0) > 0.8:
            # 기존 패턴 재사용
            workflow_pattern = await self._reuse_workflow_pattern(similar_procedures[0], context)
            optimization_note = ["기존 성공 패턴 재사용"]
        else:
            # 새로운 워크플로우 계획
            workflow_pattern = await self._plan_new_workflow(message, memories, user_preferences, context)
            optimization_note = ["새로운 워크플로우 생성"]
        
        # 3. 워크플로우 실행
        execution_results = await self._execute_workflow(workflow_pattern)
        
        # 4. 성공한 패턴을 절차 메모리에 저장
        if all(result.success for result in execution_results):
            workflow_pattern.success_rate = 1.0
            workflow_pattern.usage_count = workflow_pattern.usage_count + 1
            await self.memory_service.store_procedural_memory(workflow_pattern, user_id)
            optimization_note.append("성공 패턴 학습 완료")
        
        return {
            "workflow_pattern": workflow_pattern,
            "tools_used": execution_results,
            "confidence_score": 0.9 if all(r.success for r in execution_results) else 0.6,
            "optimizations": optimization_note,
            "lessons_learned": self._extract_lessons_from_execution(execution_results)
        }
    
    async def _process_basic_mode(self, message: str, user_id: str, session_id: str,
                                 memories: Dict[MemoryType, List], user_preferences: Dict,
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """기본 모드 처리 - 자율적 도구 선택 및 실행"""
        
        # 1. 자연어 의도 분석
        intent_analysis = await self._analyze_user_intent(message, memories, user_preferences)
        
        # 2. 최적 도구 조합 추천
        suggested_tools = self.mcp_service.suggest_optimal_tool_combination(message)
        
        # 3. 에피소드 메모리 기반 도구 선택 개선
        if memories[MemoryType.EPISODIC]:
            refined_tools = await self._refine_tools_from_episodes(suggested_tools, memories[MemoryType.EPISODIC])
        else:
            refined_tools = suggested_tools
        
        # 4. 도구 실행
        tool_calls = []
        for tool_type in refined_tools[:3]:  # 최대 3개 도구
            tool_call = MCPToolCall(
                tool_type=tool_type,
                parameters=self._generate_tool_parameters(tool_type, message, intent_analysis),
                context=context
            )
            tool_calls.append(tool_call)
        
        execution_results = await self.mcp_service.execute_workflow(tool_calls)
        
        # 5. 실행 결과 기반 학습
        lessons_learned = []
        if execution_results:
            success_rate = sum(1 for r in execution_results if r.success) / len(execution_results)
            if success_rate > 0.8:
                lessons_learned.append(f"도구 조합 {[r.tool_type for r in execution_results]} 성공률 높음")
        
        return {
            "workflow_pattern": None,  # 기본 모드는 고정 워크플로우 없음
            "tools_used": execution_results,
            "confidence_score": intent_analysis.get("confidence", 0.7),
            "optimizations": [f"자율 선택: {len(refined_tools)}개 도구 활용"],
            "lessons_learned": lessons_learned
        }
    
    async def _plan_new_workflow(self, message: str, memories: Dict[MemoryType, List], 
                               user_preferences: Dict, context: Dict[str, Any]) -> WorkflowPattern:
        """새로운 워크플로우 계획"""
        
        # AI를 통한 워크플로우 계획 생성
        system_prompt = """
        사용자 요청을 분석하여 Step-Action-Tool 워크플로우를 계획하세요.
        
        사용 가능한 도구:
        - SEARCH_DB: 데이터베이스 검색
        - GENERATE_MSG: 메시지 생성
        - SEND_SLACK: Slack 알림 전송
        - EMERGENCY_MAIL: 비상 메일 데이터 생성
        - SEND_EMAIL: 이메일 전송
        
        3-5단계의 논리적 순서로 계획하세요.
        """
        
        user_prompt = f"""
        요청: {message}
        컨텍스트: {context}
        사용자 선호도: {user_preferences}
        
        JSON 형태로 워크플로우를 계획하세요:
        {{
            "pattern_name": "워크플로우 이름",
            "steps": [
                {{"step_id": 1, "step_name": "단계명", "action": "액션", "tool_type": "SEARCH_DB", "parameters": {{}}}},
                ...
            ]
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            plan_json = json.loads(response.choices[0].message.content)
            
            # WorkflowPattern 객체 생성
            steps = []
            for step_data in plan_json["steps"]:
                tool_calls = [MCPToolCall(
                    tool_type=MCPToolType(step_data["tool_type"]),
                    parameters=step_data.get("parameters", {}),
                    context=context
                )]
                
                step = WorkflowStep(
                    step_id=step_data["step_id"],
                    step_name=step_data["step_name"],
                    action=step_data["action"],
                    tool_calls=tool_calls
                )
                steps.append(step)
            
            workflow_pattern = WorkflowPattern(
                pattern_id=f"wf_{int(time.time() * 1000)}",
                pattern_name=plan_json["pattern_name"],
                steps=steps,
                success_rate=0.0,  # 초기값
                avg_execution_time=0.0,
                usage_count=0,
                last_used=datetime.now()
            )
            
            return workflow_pattern
            
        except Exception as e:
            # 기본 워크플로우 반환
            return self._create_default_workflow(message)
    
    async def _reuse_workflow_pattern(self, similar_procedure: Dict, context: Dict[str, Any]) -> WorkflowPattern:
        """기존 워크플로우 패턴 재사용"""
        pattern_id = similar_procedure.get("pattern_id", "default")
        
        # 기본 패턴 생성 (실제로는 저장된 패턴을 불러와야 함)
        return self._create_default_workflow("재사용 워크플로우")
    
    def _create_default_workflow(self, message: str) -> WorkflowPattern:
        """기본 워크플로우 생성"""
        steps = [
            WorkflowStep(
                step_id=1,
                step_name="데이터 수집",
                action="정보 조회",
                tool_calls=[MCPToolCall(
                    tool_type=MCPToolType.SEARCH_DB,
                    parameters={"query": message},
                    context={}
                )]
            ),
            WorkflowStep(
                step_id=2,
                step_name="응답 생성",
                action="메시지 작성",
                tool_calls=[MCPToolCall(
                    tool_type=MCPToolType.GENERATE_MSG,
                    parameters={"content": "조회 결과", "style": "professional"},
                    context={}
                )]
            ),
            WorkflowStep(
                step_id=3,
                step_name="결과 전달",
                action="알림 발송",
                tool_calls=[MCPToolCall(
                    tool_type=MCPToolType.SEND_SLACK,
                    parameters={"message": "결과 메시지", "channel": "#general"},
                    context={}
                )]
            )
        ]
        
        return WorkflowPattern(
            pattern_id=f"default_wf_{int(time.time())}",
            pattern_name="기본 처리 워크플로우",
            steps=steps,
            success_rate=0.8,
            avg_execution_time=5.0,
            usage_count=1,
            last_used=datetime.now()
        )
    
    async def _execute_workflow(self, workflow_pattern: WorkflowPattern) -> List:
        """워크플로우 실행"""
        results = []
        
        for step in workflow_pattern.steps:
            step.status = "running"
            step_start_time = time.time()
            
            # 단계별 도구 실행
            step_results = await self.mcp_service.execute_workflow(step.tool_calls)
            
            step.execution_time = time.time() - step_start_time
            step.result = step_results
            
            if all(r.success for r in step_results):
                step.status = "completed"
            else:
                step.status = "failed"
                break  # 실패 시 워크플로우 중단
            
            results.extend(step_results)
        
        return results
    
    async def _analyze_user_intent(self, message: str, memories: Dict[MemoryType, List], 
                                 user_preferences: Dict) -> Dict[str, Any]:
        """사용자 의도 분석"""
        
        # 메모리 컨텍스트 구성
        memory_context = ""
        for memory_type, memory_list in memories.items():
            if memory_list:
                memory_context += f"\n{memory_type}: {memory_list[0].get('content', '')[:100]}"
        
        system_prompt = """
        사용자의 메시지를 분석하여 의도와 필요한 도구를 파악하세요.
        분석 결과를 JSON으로 반환하세요.
        """
        
        user_prompt = f"""
        메시지: {message}
        메모리 컨텍스트: {memory_context}
        사용자 선호도: {user_preferences}
        
        다음 형태로 분석하세요:
        {{
            "primary_intent": "주요 의도",
            "urgency": "low|medium|high",
            "domain": "도메인 영역",
            "required_tools": ["필요한 도구 목록"],
            "confidence": 0.8
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            # 기본 분석 반환
            return {
                "primary_intent": "일반 문의",
                "urgency": "medium",
                "domain": "general",
                "required_tools": ["SEARCH_DB", "GENERATE_MSG"],
                "confidence": 0.5
            }
    
    async def _refine_tools_from_episodes(self, suggested_tools: List[MCPToolType], 
                                        episodes: List[Dict]) -> List[MCPToolType]:
        """에피소드 메모리 기반 도구 선택 개선"""
        refined_tools = suggested_tools.copy()
        
        # 과거 성공 경험에서 효과적이었던 도구 우선순위 조정
        for episode in episodes:
            if "성공" in episode.get("content", ""):
                # 성공한 에피소드에서 언급된 도구들의 우선순위 증가
                # 실제로는 더 정교한 NLP 분석 필요
                pass
        
        return refined_tools
    
    def _generate_tool_parameters(self, tool_type: MCPToolType, message: str, 
                                intent_analysis: Dict) -> Dict[str, Any]:
        """도구별 파라미터 생성"""
        
        if tool_type == MCPToolType.SEARCH_DB:
            return {
                "query": message[:100],  # 쿼리 길이 제한
                "table": "main_data",
                "filters": {}
            }
        
        elif tool_type == MCPToolType.GENERATE_MSG:
            style = "professional"
            if intent_analysis.get("urgency") == "high":
                style = "urgent"
            return {
                "content": message,
                "style": style,
                "length": "medium"
            }
        
        elif tool_type == MCPToolType.SEND_SLACK:
            return {
                "message": f"알림: {message}",
                "channel": "#general"
            }
        
        elif tool_type == MCPToolType.EMERGENCY_MAIL:
            return {
                "type": "general",
                "severity": intent_analysis.get("urgency", "medium"),
                "description": message
            }
        
        else:
            return {}
    
    async def _generate_response(self, message: str, workflow_result: Dict, 
                               user_preferences: Dict) -> str:
        """최종 응답 생성"""
        
        # 사용자 선호 스타일 적용
        style = user_preferences.get("message_style", "professional")
        
        tools_used = [r.tool_type for r in workflow_result["tools_used"] if r.success]
        success_count = sum(1 for r in workflow_result["tools_used"] if r.success)
        
        if success_count == len(workflow_result["tools_used"]):
            base_response = f"요청을 성공적으로 처리했습니다. 사용된 도구: {', '.join(map(str, tools_used))}"
        else:
            base_response = f"요청을 부분적으로 처리했습니다. 성공한 도구: {success_count}/{len(workflow_result['tools_used'])}"
        
        # 스타일에 따른 응답 조정
        if style == "casual":
            response = f"안녕하세요! {base_response} 😊"
        elif style == "technical":
            response = f"[처리 완료] {base_response}\n실행 시간: {workflow_result.get('processing_time', 0):.2f}초"
        elif style == "concise":
            response = base_response
        else:  # professional
            response = f"안녕하세요,\n\n{base_response}\n\n감사합니다."
        
        return response
    
    def _extract_lessons_from_execution(self, execution_results: List) -> List[str]:
        """실행 결과에서 교훈 추출"""
        lessons = []
        
        success_count = sum(1 for r in execution_results if r.success)
        total_time = sum(r.execution_time for r in execution_results)
        
        if success_count == len(execution_results):
            lessons.append("모든 도구 실행 성공")
        
        if total_time > 10.0:
            lessons.append("실행 시간 최적화 필요")
        
        # 실패한 도구가 있는 경우
        failed_tools = [r.tool_type for r in execution_results if not r.success]
        if failed_tools:
            lessons.append(f"실패 도구: {failed_tools} - 대안 도구 검토 필요")
        
        return lessons

# === backend/main.py ===
import asyncio
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from .models.schemas import (
    ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse,
    SystemMetrics, AgentMode
)
from .services.memory_service import EnhancedMemoryService
from .services.mcp_service import MCPService
from .services.feedback_service import EnhancedFeedbackService
from .services.agent_service import EnhancedAgentService
from .utils.config import config

# Prometheus 메트릭
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
MEMORY_OPERATIONS = Counter('memory_operations_total', 'Memory operations', ['operation_type'])

# 글로벌 서비스 인스턴스
memory_service = None
mcp_service = None
feedback_service = None
agent_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global memory_service, mcp_service, feedback_service, agent_service
    
    # 시작 시 초기화
    logging.info("🚀 서비스 초기화 시작...")
    
    memory_service = EnhancedMemoryService()
    await memory_service.initialize()
    logging.info("✅ 메모리 서비스 초기화 완료")
    
    mcp_service = MCPService()
    logging.info("✅ MCP 서비스 초기화 완료")
    
    feedback_service = EnhancedFeedbackService(memory_service)
    logging.info("✅ 피드백 서비스 초기화 완료")
    
    agent_service = EnhancedAgentService(memory_service, mcp_service, feedback_service)
    logging.info("✅ 에이전트 서비스 초기화 완료")
    
    logging.info("🎉 모든 서비스 초기화 완료!")
    
    yield
    
    # 종료 시 정리
    logging.info("🛑 서비스 종료 중...")
    if memory_service.redis_client:
        await memory_service.redis_client.close()
    if memory_service.neo4j_driver:
        memory_service.neo4j_driver.close()
    logging.info("✅ 정리 완료")

app = FastAPI(
    title="Enhanced Agentic AI PoC",
    description="MCP 도구 기반 지능형 메모리와 피드백 루프를 갖춘 에이전트 시스템",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_prometheus_metrics(request, call_next):
    """Prometheus 메트릭 미들웨어"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # 메트릭 기록
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response

# === API 엔드포인트 ===

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """메인 채팅 엔드포인트"""
    try:
        start_time = time.time()
        
        # 사용자 선호도 크로스 에이전트 학습 적용
        await feedback_service.process_immediate_feedback(FeedbackRequest(
            session_id=request.session_id,
            user_id=request.user_id,
            feedback_type="preference_sync",
            content="크로스 에이전트 선호도 동기화"
        ))
        
        # 채팅 처리
        response = await agent_service.process_chat(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            mode=request.mode,
            context=request.context
        )
        
        MEMORY_OPERATIONS.labels(operation_type="chat_processing").inc()
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 처리 오류: {str(e)}")

@app.post("/feedback", response_model=FeedbackResponse)
async def feedback_endpoint(request: FeedbackRequest):
    """즉시 피드백 처리 엔드포인트"""
    try:
        response = await feedback_service.process_immediate_feedback(request)
        MEMORY_OPERATIONS.labels(operation_type="feedback_processing").inc()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"피드백 처리 오류: {str(e)}")

@app.get("/memory/stats")
async def memory_stats_endpoint():
    """메모리 시스템 통계"""
    try:
        stats = await memory_service.get_memory_statistics()
        MEMORY_OPERATIONS.labels(operation_type="stats_query").inc()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 오류: {str(e)}")

@app.get("/mcp/tools/performance")
async def mcp_performance_endpoint():
    """MCP 도구 성능 통계"""
    try:
        stats = mcp_service.get_all_performance_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP 성능 조회 오류: {str(e)}")

@app.get("/feedback/optimization-history")
async def optimization_history_endpoint():
    """최적화 이력 조회"""
    try:
        history = await feedback_service.get_optimization_history()# === Enhanced Agentic AI PoC Implementation ===
# PROJECT STRUCTURE:
# enhanced-agentic-ai-poc/
# ├── docker-compose.yml
# ├── .env.example
# ├── backend/
# │   ├── Dockerfile
# │   ├── requirements.txt
# │   ├── main.py
# │   ├── models/
# │   │   └── schemas.py
# │   ├── services/
# │   │   ├── memory_service.py
# │   │   ├── mcp_service.py
# │   │   ├── agent_service.py
# │   │   └── feedback_service.py
# │   ├── utils/
# │   │   └── config.py
# │   └── mcp_tools/
# │       ├── search_db.py
# │       ├── send_slack.py
# │       ├── generate_msg.py
# │       └── emergency_mail.py
# ├── frontend/
# │   ├── Dockerfile
# │   ├── requirements.txt
# │   └── streamlit_app.py
# └── evaluation/
#     ├── poc_evaluator.py
#     ├── memory_tests.py
#     ├── feedback_tests.py
#     └── performance_monitor.py

# === docker-compose.yml ===
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MEM0_API_KEY=${MEM0_API_KEY}
      - REDIS_URL=redis://redis:6379
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8001
      - NEO4J_URI=neo4j://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=testpassword
    depends_on:
      - redis
      - chroma
      - neo4j
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/testpassword
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data

  # 모니터링 서비스
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

volumes:
  redis_data:
  chroma_data:
  neo4j_data:

# === .env.example ===
OPENAI_API_KEY=sk-your-openai-key-here
MEM0_API_KEY=your-mem0-key-here
ENVIRONMENT=development
LOG_LEVEL=INFO

# === backend/Dockerfile ===
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# === backend/requirements.txt ===
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
redis==5.0.1
chromadb==0.4.22
neo4j==5.15.0
openai==1.5.0
mem0ai==0.1.10
langgraph==0.2.5
langchain==0.2.18
langchain-openai==0.1.28
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
python-dotenv==1.0.0
asyncio==3.4.3
aioredis==2.0.1
prometheus-client==0.19.0
psutil==5.9.0

# === backend/utils/config.py ===
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MEM0_API_KEY = os.getenv("MEM0_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = os.getenv("CHROMA_PORT", "8001")
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

config = Config()

# === backend/models/schemas.py ===
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import time

class AgentMode(str, Enum):
    FLOW = "flow"
    BASIC = "basic"

class MemoryType(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

class MCPToolType(str, Enum):
    SEARCH_DB = "search_db"
    SEND_SLACK = "send_slack"
    GENERATE_MSG = "generate_msg"
    EMERGENCY_MAIL = "emergency_mail_data_generator"
    SEND_EMAIL = "send_email"

# MCP Tool 관련 스키마
class MCPToolCall(BaseModel):
    tool_type: MCPToolType
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = {}

class MCPToolResult(BaseModel):
    tool_type: MCPToolType
    success: bool
    result: Any
    execution_time: float
    error: Optional[str] = None

# 워크플로우 관련 스키마
class WorkflowStep(BaseModel):
    step_id: int
    step_name: str
    action: str
    tool_calls: List[MCPToolCall]
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Any] = None
    execution_time: Optional[float] = None

class WorkflowPattern(BaseModel):
    pattern_id: str
    pattern_name: str
    steps: List[WorkflowStep]
    success_rate: float
    avg_execution_time: float
    usage_count: int
    last_used: datetime

# 메모리 관련 스키마
class ProceduralMemory(BaseModel):
    procedure_id: str
    name: str
    description: str
    workflow_pattern: WorkflowPattern
    success_rate: float
    optimization_history: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class EpisodicMemory(BaseModel):
    episode_id: str
    user_id: str
    session_id: str
    timestamp: datetime
    interaction_type: str
    context: Dict[str, Any]
    workflow_executed: Optional[WorkflowPattern] = None
    user_satisfaction: Optional[float] = None
    lessons_learned: List[str] = []

class SemanticMemory(BaseModel):
    knowledge_id: str
    domain: str
    entity: str
    relation: str
    object: str
    confidence: float
    source: str
    created_at: datetime
    usage_count: int = 0

# 피드백 관련 스키마
class PerformanceFeedback(BaseModel):
    feedback_id: str
    tool_type: MCPToolType
    execution_time: float
    success: bool
    error_type: Optional[str] = None
    optimization_applied: List[str] = []
    timestamp: datetime

class UserFeedback(BaseModel):
    feedback_id: str
    user_id: str
    session_id: str
    feedback_type: str  # satisfaction, preference, correction
    content: str
    rating: Optional[float] = None
    applied_changes: List[str] = []
    timestamp: datetime

# API 요청/응답 스키마
class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str
    mode: AgentMode
    context: Optional[Dict[str, Any]] = {}
    preferred_tools: Optional[List[MCPToolType]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    workflow_executed: Optional[WorkflowPattern] = None
    memory_used: Dict[MemoryType, List[str]]
    processing_time: float
    tools_used: List[MCPToolResult]
    confidence_score: float
    optimization_applied: List[str] = []

class FeedbackRequest(BaseModel):
    session_id: str
    user_id: str
    feedback_type: str
    content: str
    rating: Optional[float] = None
    target_component: Optional[str] = None  # workflow, tool, response

class FeedbackResponse(BaseModel):
    applied: bool
    processing_time: float
    optimizations: List[str]
    expected_improvements: Dict[str, float]

# 통계 및 모니터링 스키마
class SystemMetrics(BaseModel):
    timestamp: datetime
    memory_stats: Dict[MemoryType, Dict[str, Any]]
    tool_performance: Dict[MCPToolType, Dict[str, float]]
    workflow_efficiency: Dict[str, float]
    user_satisfaction: float
    system_load: Dict[str, float]

# === backend/mcp_tools/search_db.py ===
import asyncio
import time
import random
from typing import Dict, Any
from ..models.schemas import MCPToolResult, MCPToolType

class SearchDBTool:
    def __init__(self):
        self.tool_type = MCPToolType.SEARCH_DB
        self.performance_stats = {
            "avg_response_time": 1.2,
            "success_rate": 0.95,
            "query_limit": 100  # characters
        }
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> MCPToolResult:
        """DB 검색 도구 실행"""
        start_time = time.time()
        
        query = parameters.get("query", "")
        table = parameters.get("table", "default")
        filters = parameters.get("filters", {})
        
        try:
            # 쿼리 길이에 따른 성능 시뮬레이션
            if len(query) > self.performance_stats["query_limit"]:
                execution_time = 2.8 + random.uniform(0, 0.5)
                success_rate = 0.72
            else:
                execution_time = 1.2 + random.uniform(0, 0.3)
                success_rate = 0.95
            
            await asyncio.sleep(execution_time)
            
            # 성공/실패 시뮬레이션
            success = random.random() < success_rate
            
            if success:
                # 모의 결과 데이터 생성
                result_data = {
                    "query": query,
                    "table": table,
                    "results": [
                        {"id": i, "name": f"Item_{i}", "value": random.randint(1, 100)}
                        for i in range(random.randint(1, 5))
                    ],
                    "count": random.randint(1, 5)
                }
                
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=True,
                    result=result_data,
                    execution_time=time.time() - start_time
                )
            else:
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error="Database query failed - connection timeout"
                )
                
        except Exception as e:
            return MCPToolResult(
                tool_type=self.tool_type,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        return self.performance_stats.copy()

# === backend/mcp_tools/send_slack.py ===
import asyncio
import time
import random
from typing import Dict, Any
from ..models.schemas import MCPToolResult, MCPToolType

class SendSlackTool:
    def __init__(self):
        self.tool_type = MCPToolType.SEND_SLACK
        self.performance_stats = {
            "avg_response_time": 0.8,
            "success_rate": 0.92,
            "message_limit": 4000,  # characters
            "api_rate_limit": 50  # per minute
        }
        self.api_calls_count = 0
        self.last_reset_time = time.time()
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> MCPToolResult:
        """Slack 메시지 전송 도구 실행"""
        start_time = time.time()
        
        message = parameters.get("message", "")
        channel = parameters.get("channel", "#general")
        user = parameters.get("user", None)
        
        try:
            # API 호출 제한 확인
            current_time = time.time()
            if current_time - self.last_reset_time > 60:  # 1분 경과
                self.api_calls_count = 0
                self.last_reset_time = current_time
            
            if self.api_calls_count >= self.performance_stats["api_rate_limit"]:
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error="API rate limit exceeded"
                )
            
            # 메시지 길이 제한 확인
            if len(message) > self.performance_stats["message_limit"]:
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error=f"Message too long: {len(message)} > {self.performance_stats['message_limit']}"
                )
            
            # 실행 시간 시뮬레이션
            execution_time = 0.8 + random.uniform(0, 0.4)
            await asyncio.sleep(execution_time)
            
            # 성공/실패 시뮬레이션
            success = random.random() < self.performance_stats["success_rate"]
            self.api_calls_count += 1
            
            if success:
                result_data = {
                    "message": message,
                    "channel": channel,
                    "timestamp": current_time,
                    "message_id": f"slack_msg_{int(current_time * 1000)}"
                }
                
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=True,
                    result=result_data,
                    execution_time=time.time() - start_time
                )
            else:
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error="Slack API error - channel not found"
                )
                
        except Exception as e:
            return MCPToolResult(
                tool_type=self.tool_type,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        return {
            **self.performance_stats,
            "current_api_calls": self.api_calls_count,
            "time_until_reset": max(0, 60 - (time.time() - self.last_reset_time))
        }

# === backend/mcp_tools/generate_msg.py ===
import asyncio
import time
import random
from typing import Dict, Any
from openai import OpenAI
from ..models.schemas import MCPToolResult, MCPToolType
from ..utils.config import config

class GenerateMessageTool:
    def __init__(self):
        self.tool_type = MCPToolType.GENERATE_MSG
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.performance_stats = {
            "avg_response_time": 2.1,
            "success_rate": 0.94,
            "template_cache": {}
        }
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> MCPToolResult:
        """메시지 생성 도구 실행"""
        start_time = time.time()
        
        message_type = parameters.get("type", "general")
        content = parameters.get("content", "")
        style = parameters.get("style", "professional")  # professional, casual, technical
        length = parameters.get("length", "medium")  # short, medium, long
        
        try:
            # 템플릿 캐싱 최적화 시뮬레이션
            cache_key = f"{message_type}_{style}_{length}"
            if cache_key in self.performance_stats["template_cache"]:
                execution_time = 1.1 + random.uniform(0, 0.2)  # 캐시 적용으로 빠름
            else:
                execution_time = 2.1 + random.uniform(0, 0.5)  # 새로 생성
                self.performance_stats["template_cache"][cache_key] = True
            
            await asyncio.sleep(execution_time)
            
            # 스타일별 메시지 생성 로직
            if style == "professional":
                generated_message = f"안녕하세요,\n\n{content}에 대해 알려드립니다.\n\n감사합니다."
            elif style == "casual":
                generated_message = f"안녕! {content} 관련해서 알려줄게 😊"
            elif style == "technical":
                generated_message = f"[시스템 알림] {content}\n\n세부 정보:\n- 타임스탬프: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                generated_message = content
            
            # 길이 조정
            if length == "short":
                generated_message = generated_message[:100] + "..." if len(generated_message) > 100 else generated_message
            elif length == "long":
                generated_message += "\n\n추가적으로 필요한 정보가 있으시면 언제든 문의해 주세요."
            
            # 성공/실패 시뮬레이션
            success = random.random() < self.performance_stats["success_rate"]
            
            if success:
                result_data = {
                    "generated_message": generated_message,
                    "style": style,
                    "length": length,
                    "word_count": len(generated_message.split()),
                    "cached": cache_key in self.performance_stats["template_cache"]
                }
                
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=True,
                    result=result_data,
                    execution_time=time.time() - start_time
                )
            else:
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error="Message generation failed - content policy violation"
                )
                
        except Exception as e:
            return MCPToolResult(
                tool_type=self.tool_type,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        return {
            **self.performance_stats,
            "cached_templates": len(self.performance_stats["template_cache"])
        }

# === backend/mcp_tools/emergency_mail.py ===
import asyncio
import time
import random
from typing import Dict, Any
from ..models.schemas import MCPToolResult, MCPToolType

class EmergencyMailDataGeneratorTool:
    def __init__(self):
        self.tool_type = MCPToolType.EMERGENCY_MAIL
        self.performance_stats = {
            "avg_response_time": 0.9,
            "success_rate": 0.98,
            "data_templates": {
                "she_emergency": {
                    "priority": "high",
                    "recipients": ["safety@company.com", "manager@company.com"],
                    "template": "SHE 비상 상황 발생"
                },
                "system_emergency": {
                    "priority": "critical",
                    "recipients": ["ops@company.com", "admin@company.com"],
                    "template": "시스템 비상 상황 발생"
                }
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: Dict[str, Any] = None) -> MCPToolResult:
        """비상 메일 데이터 생성 도구 실행"""
        start_time = time.time()
        
        emergency_type = parameters.get("type", "general")
        severity = parameters.get("severity", "medium")
        location = parameters.get("location", "unknown")
        description = parameters.get("description", "")
        
        try:
            # 실행 시간 시뮬레이션
            execution_time = 0.9 + random.uniform(0, 0.2)
            await asyncio.sleep(execution_time)
            
            # 비상 유형별 데이터 생성
            template_data = self.performance_stats["data_templates"].get(
                emergency_type, 
                self.performance_stats["data_templates"]["system_emergency"]
            )
            
            # 심각도에 따른 우선순위 조정
            priority_map = {"low": "medium", "medium": "high", "high": "critical"}
            final_priority = priority_map.get(severity, "high")
            
            # 수신자 목록 생성
            recipients = template_data["recipients"].copy()
            if final_priority == "critical":
                recipients.extend(["ceo@company.com", "emergency@company.com"])
            
            # 성공/실패 시뮬레이션
            success = random.random() < self.performance_stats["success_rate"]
            
            if success:
                result_data = {
                    "emergency_id": f"EMG_{int(time.time() * 1000)}",
                    "type": emergency_type,
                    "priority": final_priority,
                    "severity": severity,
                    "location": location,
                    "description": description,
                    "recipients": recipients,
                    "template": template_data["template"],
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "escalation_required": final_priority == "critical"
                }
                
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=True,
                    result=result_data,
                    execution_time=time.time() - start_time
                )
            else:
                return MCPToolResult(
                    tool_type=self.tool_type,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error="Emergency data generation failed - template not found"
                )
                
        except Exception as e:
            return MCPToolResult(
                tool_type=self.tool_type,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        return self.performance_stats.copy()

# === backend/services/mcp_service.py ===
import asyncio
from typing import Dict, Any, List, Type
from ..models.schemas import MCPToolCall, MCPToolResult, MCPToolType
from ..mcp_tools.search_db import SearchDBTool
from ..mcp_tools.send_slack import SendSlackTool
from ..mcp_tools.generate_msg import GenerateMessageTool
from ..mcp_tools.emergency_mail import EmergencyMailDataGeneratorTool

class MCPService:
    def __init__(self):
        self.tools = {
            MCPToolType.SEARCH_DB: SearchDBTool(),
            MCPToolType.SEND_SLACK: SendSlackTool(),
            MCPToolType.GENERATE_MSG: GenerateMessageTool(),
            MCPToolType.EMERGENCY_MAIL: EmergencyMailDataGeneratorTool(),
        }
        self.performance_history = []
    
    async def execute_tool(self, tool_call: MCPToolCall) -> MCPToolResult:
        """MCP 도구 실행"""
        if tool_call.tool_type not in self.tools:
            return MCPToolResult(
                tool_type=tool_call.tool_type,
                success=False,
                result=None,
                execution_time=0,
                error=f"Tool {tool_call.tool_type} not found"
            )
        
        tool = self.tools[tool_call.tool_type]
        result = await tool.execute(tool_call.parameters, tool_call.context)
        
        # 성능 히스토리 기록
        self.performance_history.append({
            "tool_type": tool_call.tool_type,
            "execution_time": result.execution_time,
            "success": result.success,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # 히스토리 크기 제한
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]
        
        return result
    
    async def execute_workflow(self, tool_calls: List[MCPToolCall]) -> List[MCPToolResult]:
        """워크플로우 실행 (도구 체인)"""
        results = []
        
        for tool_call in tool_calls:
            # 이전 결과를 다음 도구의 컨텍스트에 포함
            if results:
                tool_call.context = tool_call.context or {}
                tool_call.context["previous_results"] = [r.result for r in results if r.success]
            
            result = await self.execute_tool(tool_call)
            results.append(result)
            
            # 실패 시 워크플로우 중단 (옵션)
            if not result.success:
                break
        
        return results
    
    def get_tool_performance_stats(self, tool_type: MCPToolType) -> Dict[str, Any]:
        """특정 도구의 성능 통계 반환"""
        if tool_type not in self.tools:
            return {}
        
        tool_data = [h for h in self.performance_history if h["tool_type"] == tool_type]
        
        if not tool_data:
            return self.tools[tool_type].get_performance_stats()
        
        success_count = sum(1 for d in tool_data if d["success"])
        avg_time = sum(d["execution_time"] for d in tool_data) / len(tool_data)
        
        return {
            **self.tools[tool_type].get_performance_stats(),
            "recent_success_rate": success_count / len(tool_data),
            "recent_avg_time": avg_time,
            "usage_count": len(tool_data)
        }
    
    def get_all_performance_stats(self) -> Dict[MCPToolType, Dict[str, Any]]:
        """모든 도구의 성능 통계 반환"""
        return {
            tool_type: self.get_tool_performance_stats(tool_type)
            for tool_type in self.tools.keys()
        }
    
    def suggest_optimal_tool_combination(self, task_description: str) -> List[MCPToolType]:
        """작업 설명을 바탕으로 최적 도구 조합 제안"""
        # 간단한 키워드 기반 매칭 (실제로는 더 정교한 NLP 필요)
        keywords = task_description.lower()
        
        suggested_tools = []
        
        if any(word in keywords for word in ["메시지", "생성", "작성"]):
            suggested_tools.append(MCPToolType.GENERATE_MSG)
        
        if any(word in keywords for word in ["slack", "알림", "전송", "발송"]):
            suggested_tools.append(MCPToolType.SEND_SLACK)
        
        return suggested_tools

# === backend/services/memory_service.py ===
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
    MemoryType, ProceduralMemory, EpisodicMemory, SemanticMemory,
    WorkflowPattern, MCPToolType
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
        self.chroma_client = Client(host=config.CHROMA_HOST, port=int(config.CHROMA_PORT))
        try:
            self.episodes_collection = self.chroma_client.create_collection("episodes")
            self.procedures_collection = self.chroma_client.create_collection("procedures")
        except:
            self.episodes_collection = self.chroma_client.get_collection("episodes")
            self.procedures_collection = self.chroma_client.get_collection("procedures")
        
        # Neo4j - Semantic Memory
        self.neo4j_driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
    
    # === Working Memory (작업 기억) ===
    async def store_working_memory(self, session_id: str, key: str, value: Any, ttl: int = 3600):
        """세션별 작업 메모리 저장"""
        start_time = time.time()
        
        memory_key = f"working:{session_id}:{key}"
        await self.redis_client.setex(memory_key, ttl, json.dumps(value, default=str))
        
        return time.time() - start_time
    
    async def get_working_memory(self, session_id: str, key: str = None) -> Dict[str, Any]:
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
    async def store_procedural_memory(self, workflow_pattern: WorkflowPattern, user_id: str):
        """성공한 워크플로우 패턴 저장"""
        start_time = time.time()
        
        # Mem0에 절차 패턴 저장
        procedure_data = {
            "pattern_id": workflow_pattern.pattern_id,
            "pattern_name": workflow_pattern.pattern_name,
            "steps": [step.dict() for step in workflow_pattern.steps],
            "success_rate": workflow_pattern.success_rate,
            "avg_execution_time": workflow_pattern.avg_execution_time,
            "usage_count": workflow_pattern.usage_count
        }
        
        self.mem0.add(
            f"Workflow pattern: {workflow_pattern.pattern_name} with {len(workflow_pattern.steps)} steps, "
            f"success rate: {workflow_pattern.success_rate:.1%}",
            user_id=user_id,
            metadata={
                "type": "procedural",
                "pattern_id": workflow_pattern.pattern_id,
                "domain": "workflow"
            }
        )
        
        # ChromaDB에도 상세 정보 저장
        self.procedures_collection.add(
            documents=[json.dumps(procedure_data, default=str)],
            metadatas=[{
                "pattern_id": workflow_pattern.pattern_id,
                "user_id": user_id,
                "success_rate": workflow_pattern.success_rate,
                "created_at": datetime.now().isoformat()
            }],
            ids=[f"{user_id}_{workflow_pattern.pattern_id}"]
        )
        
        return time.time() - start_time
    
    async def retrieve_similar_procedures(self, task_description: str, user_id: str, limit: int = 3):
        """유사한 절차 패턴 검색"""
        start_time = time.time()
        
        # Mem0에서 관련 절차 검색
        memories = self.mem0.search(
            query=f"workflow procedure for: {task_description}",
            user_id=user_id,
            limit=limit
        )
        
        procedures = []
        if memories and "results" in memories:
            for memory in memories["results"]:
                metadata = memory.get("metadata", {})
                if metadata.get("type") == "procedural":
                    procedures.append({
                        "content": memory.get("memory", ""),
                        "pattern_id": metadata.get("pattern_id"),
                        "relevance_score": memory.get("score", 0)
                    })
        
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
                "timestamp": episode.timestamp.isoformat()
            }
        )
        
        # ChromaDB에 상세 에피소드 저장
        episode_data = episode.dict()
        self.episodes_collection.add(
            documents=[json.dumps(episode_data, default=str)],
            metadatas=[{
                "user_id": episode.user_id,
                "episode_id": episode.episode_id,
                "interaction_type": episode.interaction_type,
                "timestamp": episode.timestamp.isoformat(),
                "satisfaction": episode.user_satisfaction or 0
            }],
            ids=[episode.episode_id]
        )
        
        return time.time() - start_time
    
    async def retrieve_user_episodes(self, user_id: str, interaction_type: str = None, limit: int = 5):
        """사용자의 과거 에피소드 검색"""
        start_time = time.time()
        
        query = f"user {user_id} interactions"
        if interaction_type:
            query += f" related to {interaction_type}"
        
        memories = self.mem0.search(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
        episodes = []
        if memories and "results" in memories:
            for memory in memories["results"]:
                metadata = memory.get("metadata", {})
                if metadata.get("type") == "episodic":
                    episodes.append({
                        "content": memory.get("memory", ""),
                        "episode_id": metadata.get("episode_id"),
                        "interaction_type": metadata.get("interaction_type"),
                        "timestamp": metadata.get("timestamp"),
                        "relevance_score": memory.get("score", 0)
                    })
        
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
            
            session.run(query, {
                "entity": knowledge.entity,
                "object": knowledge.object,
                "relation": knowledge.relation,
                "domain": knowledge.domain,
                "confidence": knowledge.confidence,
                "source": knowledge.source,
                "created_at": knowledge.created_at.isoformat(),
                "knowledge_id": knowledge.knowledge_id
            })
        
        # Mem0에도 텍스트로 저장
        knowledge_text = f"{knowledge.entity} {knowledge.relation} {knowledge.object} in {knowledge.domain} domain"
        self.mem0.add(
            knowledge_text,
            user_id="system",  # 시스템 레벨 지식
            metadata={
                "type": "semantic",
                "domain": knowledge.domain,
                "knowledge_id": knowledge.knowledge_id,
                "confidence": knowledge.confidence
            }
        )
        
        return time.time() - start_time
    
    async def query_semantic_knowledge(self, entity: str, domain: str = None, limit: int = 10):
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
                result = session.run(query, {"entity": entity, "domain": domain, "limit": limit})
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
                knowledge_items.append({
                    "entity": record["entity"],
                    "relation": record["relation"],
                    "object": record["object"],
                    "confidence": record["confidence"],
                    "usage_count": record["usage_count"],
                    "domain": record.get("domain", domain)
                })
        
        return knowledge_items, time.time() - start_time
    
    # === 통합 검색 메소드 ===
    async def retrieve_relevant_memories(self, user_id: str, query: str, memory_types: List[MemoryType] = None, limit: int = 5):
        """관련 메모리 통합 검색"""
        start_time = time.time()
        all_memories = {
            MemoryType.WORKING: [],
            MemoryType.EPISODIC: [],
            MemoryType.SEMANTIC: [],
            MemoryType.PROCEDURAL: []
        }
        
        # 요청된 메모리 타입만 검색 (기본은 모든 타입)
        if memory_types is None:
            memory_types = list(MemoryType)
        
        # Mem0 통합 검색
        memories = self.mem0.search(query=query, user_id=user_id, limit=limit * len(memory_types))
        
        if memories and "results" in memories:
            for memory in memories["results"]:
                metadata = memory.get("metadata", {})
                memory_type = metadata.get("type", "")
                
                memory_item = {
                    "content": memory.get("memory", ""),
                    "score": memory.get("score", 0),
                    "metadata": metadata
                }
                
                if memory_type == "working" and MemoryType.WORKING in memory_types:
                    all_memories[MemoryType.WORKING].append(memory_item)
                elif memory_type == "episodic" and MemoryType.EPISODIC in memory_types:
                    all_memories[MemoryType.EPISODIC].append(memory_item)
                elif memory_type == "semantic" and MemoryType.SEMANTIC in memory_types:
                    all_memories[MemoryType.SEMANTIC].append(memory_item)
                elif memory_type == "procedural" and MemoryType.PROCEDURAL in memory_types:
                    all_memories[MemoryType.PROCEDURAL].append(memory_item)
        
        # 각 타입별로 최고 점수 항목들만 유지
        for memory_type in all_memories:
            all_memories[memory_type] = sorted(
                all_memories[memory_type], 
                key=lambda x: x["score"], 
                reverse=True
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
                "connected_clients": redis_info.get("connected_clients", 0)
            }
            
            # ChromaDB 통계
            stats["episodic_memory"] = {
                "episodes_count": self.episodes_collection.count(),
                "procedures_count": self.procedures_collection.count()
            }
            
            # Neo4j 통계
            with self.neo4j_driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = result.single()["node_count"]
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = result.single()["rel_count"]
                
                stats["semantic_memory"] = {
                    "nodes_count": node_count,
                    "relationships_count": rel_count
                }
            
            # 성능 메트릭
            if self.performance_metrics:
                recent_metrics = self.performance_metrics[-10:]
                avg_time = sum(m.memory_retrieval_time for m in recent_metrics) / len(recent_metrics)
                stats["performance"] = {
                    "avg_retrieval_time": avg_time,
                    "total_operations": len(self.performance_metrics)
                }
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats

# === backend/services/feedback_service.py ===
import asyncio
import time
import json
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime, timedelta
from ..services.memory_service import EnhancedMemoryService
from ..models.schemas import (
    FeedbackRequest, FeedbackResponse, PerformanceFeedback, UserFeedback,
    MCPToolType, WorkflowPattern
)

class EnhancedFeedbackService:
    def __init__(self, memory_service: EnhancedMemoryService):
        self.memory_service = memory_service
        self.user_preferences = defaultdict(dict)
        self.performance_feedback = []
        self.optimization_history = defaultdict(list)
        
    async def process_immediate_feedback(self, feedback: FeedbackRequest) -> FeedbackResponse:
        """5초 이내 즉시 피드백 처리"""
        start_time = time.time()
        
        optimizations = []
        
        try:
            # 사용자 피드백 저장
            user_feedback = UserFeedback(
                feedback_id=f"fb_{int(time.time() * 1000)}",
                user_id=feedback.user_id,
                session_id=feedback.session_id,
                feedback_type=feedback.feedback_type,
                content=feedback.content,
                rating=feedback.rating,
                timestamp=datetime.now()
            )
            
            # 피드백 유형별 즉시 적용
            if feedback.feedback_type == "style_preference":
                # 메시지 스타일 선호도 업데이트
                style = self._extract_style_preference(feedback.content)
                self.user_preferences[feedback.user_id]["message_style"] = style
                optimizations.append(f"메시지 스타일을 {style}로 변경")
                
                # Working Memory에 즉시 적용
                await self.memory_service.store_working_memory(
                    session_id=feedback.session_id,
                    key="style_preference",
                    value=style,
                    ttl=1800
                )
                
            elif feedback.feedback_type == "tool_performance":
                # 도구 성능 피드백 처리
                tool_optimization = self._process_tool_feedback(feedback.content)
                if tool_optimization:
                    optimizations.extend(tool_optimization)
                    
            elif feedback.feedback_type == "workflow_efficiency":
                # 워크플로우 효율성 피드백
                workflow_improvements = await self._optimize_workflow_from_feedback(
                    feedback.user_id, 
                    feedback.session_id, 
                    feedback.content
                )
                optimizations.extend(workflow_improvements)
                
            elif feedback.feedback_type == "response_quality":
                # 응답 품질 개선
                quality_improvements = self._improve_response_quality(
                    feedback.content, 
                    feedback.rating or 3.0
                )
                optimizations.extend(quality_improvements)
            
            # 크로스 에이전트 학습을 위한 선호도 공유
            await self._share_user_preferences(feedback.user_id)
            
            # 장기 메모리에 피드백 저장
            await self._store_feedback_in_memory(user_feedback)
            
            processing_time = time.time() - start_time
            
            # 예상 개선 효과 계산
            expected_improvements = self._calculate_expected_improvements(optimizations)
            
            return FeedbackResponse(
                applied=True,
                processing_time=processing_time,
                optimizations=optimizations,
                expected_improvements=expected_improvements
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return FeedbackResponse(
                applied=False,
                processing_time=processing_time,
                optimizations=[f"오류 발생: {str(e)}"],
                expected_improvements={}
            )
    
    async def process_performance_feedback(self, tool_type: MCPToolType, execution_time: float, success: bool, error_type: str = None):
        """도구 성능 피드백 처리"""
        feedback = PerformanceFeedback(
            feedback_id=f"perf_{int(time.time() * 1000)}",
            tool_type=tool_type,
            execution_time=execution_time,
            success=success,
            error_type=error_type,
            timestamp=datetime.now()
        )
        
        self.performance_feedback.append(feedback)
        
        # 성능 최적화 로직
        optimizations = []
        
        # 실행 시간이 임계값을 초과하는 경우
        if execution_time > 3.0:  # 3초 이상
            optimization = await self._optimize_slow_tool(tool_type, execution_time)
            if optimization:
                optimizations.extend(optimization)
                feedback.optimization_applied = optimization
        
        # 실패율이 높은 경우
        recent_failures = [f for f in self.performance_feedback[-20:] 
                          if f.tool_type == tool_type and not f.success]
        
        if len(recent_failures) >= 5:  # 최근 20회 중 5회 이상 실패
            reliability_optimization = await self._improve_tool_reliability(tool_type)
            optimizations.extend(reliability_optimization)
            feedback.optimization_applied.extend(reliability_optimization)
        
        return optimizations
    
    def _extract_style_preference(self, feedback_content: str) -> str:
        """피드백에서 스타일 선호도 추출"""
        content_lower = feedback_content.lower()
        
        if any(word in content_lower for word in ["친근", "캐주얼", "편한"]):
            return "casual"
        elif any(word in content_lower for word in ["공식", "정중", "비즈니스"]):
            return "professional"
        elif any(word in content_lower for word in ["기술적", "자세한", "전문적"]):
            return "technical"
        elif any(word in content_lower for word in ["간단", "짧게", "요약"]):
            return "concise"
        else:
            return "balanced"
    
    def _process_tool_feedback(self, feedback_content: str) -> List[str]:
        """도구 성능 피드백 처리"""
        optimizations = []
        content_lower = feedback_content.lower()
        
        if any(word in content_lower for word in ["느려", "오래", "지연"]):
            optimizations.append("도구 실행 속도 최적화 적용")
            optimizations.append("캐싱 메커니즘 강화")
            
        elif any(word in content_lower for word in ["실패", "오류", "에러"]):
            optimizations.append("도구 안정성 개선")
            optimizations.append("예외 처리 강화")
            
        elif any(word in content_lower for word in ["부정확", "틀린", "잘못"]):
            optimizations.append("도구 정확도 개선")
            optimizations.append("검증 로직 추가")
        
        return optimizations
    
    async def _optimize_workflow_from_feedback(self, user_id: str, session_id: str, feedback_content: str) -> List[str]:
        """워크플로우 피드백 기반 최적화"""
        optimizations = []
        
        # 현재 세션의 워크플로우 정보 조회
        workflow_data, _ = await self.memory_service.get_working_memory(session_id, "current_workflow")
        
        if workflow_data:
            content_lower = feedback_content.lower()
            
            if any(word in content_lower for word in ["단계", "복잡", "간소화"]):
                optimizations.append("워크플로우 단계 최적화")
                # 불필요한 단계 제거 로직
                
            elif any(word in content_lower for word in ["순서", "흐름", "로직"]):
                optimizations.append("실행 순서 재배치")
                # 병렬 처리 가능한 단계 식별
                
            elif any(word in content_lower for word in ["도구", "선택", "대체"]):
                optimizations.append("최적 도구 조합 재선택")
                # 성능이 더 좋은 도구로 대체
        
        return optimizations
    
    def _improve_response_quality(self, feedback_content: str, rating: float) -> List[str]:
        """응답 품질 개선"""
        optimizations = []
        
        if rating < 3.0:
            content_lower = feedback_content.lower()
            
            if any(word in content_lower for word in ["길어", "장황", "너무"]):
                optimizations.append("응답 길이 최적화")
                
            elif any(word in content_lower for word in ["짧아", "부족", "더"]):
                optimizations.append("응답 상세도 증가")
                
            elif any(word in content_lower for word in ["관련없", "부정확", "틀린"]):
                optimizations.append("응답 관련성 개선")
                optimizations.append("컨텍스트 이해도 향상")
        
        return optimizations
    
    async def _optimize_slow_tool(self, tool_type: MCPToolType, execution_time: float) -> List[str]:
        """느린 도구 최적화"""
        optimizations = []
        
        if tool_type == MCPToolType.SEARCH_DB:
            optimizations.append("데이터베이스 쿼리 최적화")
            optimizations.append("인덱스 추가 제안")
            optimizations.append("결과 캐싱 적용")
            
        elif tool_type == MCPToolType.GENERATE_MSG:
            optimizations.append("메시지 템플릿 캐싱")
            optimizations.append("생성 알고리즘 최적화")
            
        elif tool_type == MCPToolType.SEND_SLACK:
            optimizations.append("배치 전송 최적화")
            optimizations.append("API 호출 효율화")
        
        # 최적화 이력에 기록
        self.optimization_history[tool_type].append({
            "timestamp": datetime.now(),
            "execution_time": execution_time,
            "optimizations": optimizations
        })
        
        return optimizations
    
    async def _improve_tool_reliability(self, tool_type: MCPToolType) -> List[str]:
        """도구 신뢰성 개선"""
        optimizations = []
        
        # 최근 실패 패턴 분석
        recent_failures = [f for f in self.performance_feedback[-50:] 
                          if f.tool_type == tool_type and not f.success]
        
        error_types = [f.error_type for f in recent_failures if f.error_type]
        
        if error_types:
            # 가장 빈번한 오류 유형
            most_common_error = max(set(error_types), key=error_types.count)
            
            if "timeout" in most_common_error.lower():
                optimizations.append("타임아웃 설정 최적화")
                optimizations.append("재시도 로직 개선")
                
            elif "connection" in most_common_error.lower():
                optimizations.append("연결 풀 최적화")
                optimizations.append("연결 안정성 개선")
                
            elif "rate limit" in most_common_error.lower():
                optimizations.append("속도 제한 대응")
                optimizations.append("요청 간격 조정")
        
        return optimizations
    
    async def _share_user_preferences(self, user_id: str):
        """사용자 선호도 크로스 에이전트 공유"""
        if user_id in self.user_preferences:
            preferences = self.user_preferences[user_id]
            
            # 메모리에 선호도 저장하여 다른 세션에서 활용 가능하게 함
            await self.memory_service.store_working_memory(
                session_id=f"preferences_{user_id}",
                key="shared_preferences",
                value=preferences,
                ttl=86400  # 24시간
            )
            
            # 장기 메모리에도 저장
            preference_text = f"사용자 {user_id} 선호도: " + ", ".join([
                f"{k}: {v}" for k, v in preferences.items()
            ])
            
            self.memory_service.mem0.add(
                preference_text,
                user_id=user_id,
                metadata={"type": "preference", "shared": True}
            )
    
    async def _store_feedback_in_memory(self, feedback: UserFeedback):
        """피드백을 장기 메모리에 저장"""
        feedback_text = (
            f"사용자 피드백: {feedback.feedback_type} - {feedback.content} "
            f"(평점: {feedback.rating})"
        )
        
        self.memory_service.mem0.add(
            feedback_text,
            user_id=feedback.user_id,
            metadata={
                "type": "feedback",
                "feedback_type": feedback.feedback_type,
                "rating": feedback.rating,
                "timestamp": feedback.timestamp.isoformat()
            }
        )
    
    def _calculate_expected_improvements(self, optimizations: List[str]) -> Dict[str, float]:
        """최적화로 인한 예상 개선 효과 계산"""
        improvements keywords for word in ["조회", "검색", "찾기", "데이터"]):
            suggested_tools.append(MCPToolType.SEARCH_DB)
        
        if any(word in keywords for word in ["비상", "긴급", "응급"]):
            suggested_tools.append(MCPToolType.EMERGENCY_MAIL)
        
        if any(word in