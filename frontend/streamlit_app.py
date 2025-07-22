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
BACKEND_URL = "http://backend:8100"

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
