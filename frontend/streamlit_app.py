import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import time
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any, Optional
import os

# 페이지 설정
st.set_page_config(
    page_title="Agentic AI Platform",
    page_icon="🤖",
    layout="wide"
)

# API 기본 URL (수정된 백엔드 URL)
API_BASE_URL = os.getenv("BACKEND_URL", "http://backend:8000")

class AgenticAIApp:
    def __init__(self):
        self.session_state_init()
    
    def session_state_init(self):
        """세션 상태 초기화"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'user_id' not in st.session_state:
            st.session_state.user_id = "user_001"
        if 'session_id' not in st.session_state:
            st.session_state.session_id = f"session_{int(time.time())}"
        if 'mode' not in st.session_state:
            st.session_state.mode = "basic"
        if 'selected_example' not in st.session_state:
            st.session_state.selected_example = ""
        if 'pending_message' not in st.session_state:
            st.session_state.pending_message = ""
    
    def make_api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """API 요청 수행"""
        try:
            url = f"{API_BASE_URL}{endpoint}"
            
            if method == "POST":
                response = requests.post(url, json=data, timeout=30)
            elif method == "GET":
                response = requests.get(url, timeout=30)
            else:
                st.error(f"지원하지 않는 HTTP 메서드: {method}")
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API 요청 실패: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error("🔌 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None
        except requests.exceptions.Timeout:
            st.error("⏰ 요청 시간이 초과되었습니다.")
            return None
        except Exception as e:
            st.error(f"❌ 예상치 못한 오류: {str(e)}")
            return None
    
    def chat_with_agent(self, message: str, user_id: str, mode: str) -> Optional[Dict]:
        """에이전트와 채팅 - 새로운 API 형식"""
        data = {
            "message": message,
            "user_id": user_id,
            "mode": mode,
            "session_id": st.session_state.session_id
        }
        
        return self.make_api_request("/chat", "POST", data)
    
    def collect_feedback(self, session_id: str, rating: int, comments: str = "") -> bool:
        """피드백 수집 - 기존 방식"""
        try:
            url = f"{API_BASE_URL}/feedback"
            response = requests.post(
                url,
                params={
                    "session_id": session_id,
                    "rating": rating,
                    "comments": comments
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            st.error(f"피드백 수집 실패: {str(e)}")
            return False
    
    def collect_enhanced_feedback(
        self, 
        session_id: str, 
        rating: int, 
        comments: str = "", 
        pattern_feedback: Optional[Dict[str, Any]] = None
    ) -> bool:
        """향상된 피드백 수집 (패턴 학습 포함)"""
        try:
            feedback_data = {
                "session_id": session_id,
                "rating": rating,
                "comments": comments
            }
            
            # Add pattern feedback if provided
            if pattern_feedback and pattern_feedback.get("pattern_id"):
                feedback_data["pattern_id"] = pattern_feedback["pattern_id"]
                feedback_data["suggestion_accepted"] = pattern_feedback["suggestion_accepted"]
            
            response = self.make_api_request("/feedback", "POST", feedback_data)
            return response is not None
        except Exception as e:
            st.error(f"향상된 피드백 전송 실패: {e}")
            return False
    
    def get_system_health(self) -> Optional[Dict]:
        """시스템 건강 상태 조회"""
        return self.make_api_request("/health")

    def process_user_message(self, message: str):
        """사용자 메시지 처리"""
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 에이전트 응답 요청
        with st.spinner("🤔 에이전트가 작업을 수행 중입니다..."):
            response_data = self.chat_with_agent(message, st.session_state.user_id, st.session_state.mode)
        
        if response_data:
            # 어시스턴트 응답 추가
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_data.get("response", "응답을 받지 못했습니다."),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "execution_trace": response_data.get("execution_trace", []),
                "metadata": response_data.get("metadata", {})
            })
        else:
            st.error("응답을 받을 수 없습니다. 다시 시도해주세요.")

    def render_chat_interface(self):
        """채팅 인터페이스 렌더링"""
        st.header("🤖 Agentic AI Chat")
        
        # 설정 사이드바
        with st.sidebar:
            st.subheader("⚙️ 설정")
            
            # 사용자 ID 설정
            user_id = st.text_input("User ID", value=st.session_state.user_id)
            if user_id != st.session_state.user_id:
                st.session_state.user_id = user_id
            
            # 모드 선택
            mode = st.selectbox(
                "실행 모드",
                options=["basic", "flow"],
                index=0 if st.session_state.mode == "basic" else 1,
                help="basic: 자율 실행, flow: 단계별 계획 실행"
            )
            if mode != st.session_state.mode:
                st.session_state.mode = mode
            
            # 테스트 명령어 예시
            st.markdown("### 📝 테스트 명령어")
            
            test_commands = [
                "AI 프로젝트로 데이터베이스를 검색하고, 검색 결과를 바탕으로 기존 TBE 콘텐츠를 수정한 다음 결과를 슬랙으로 공유해줘",
                "프로젝트명이 'AI 챗봇 개발'이고 회사명이 '테크이노베이션'인 RFQ 문서를 생성하고, 내용을 분석한 후 #general 채널에 완료 메시지를 전송해줘",
                "'블록체인 개발' 프로젝트의 RFQ 문서를 생성하고, 데이터베이스에서 관련 정보를 검색해서 내용을 보완한 후, 최종 문서를 결합하고 @developer에게 검토 요청 메시지를 보내줘"
            ]
            
            for i, cmd in enumerate(test_commands, 1):
                if st.button(f"예시 {i}", key=f"example_{i}"):
                    st.session_state.pending_message = cmd
                    st.rerun()
            
            # 새 세션 시작
            if st.button("🔄 새 세션 시작"):
                st.session_state.messages = []
                st.session_state.session_id = f"session_{int(time.time())}"
                st.session_state.selected_example = ""
                st.session_state.pending_message = ""
                st.rerun()
        
        # 대기 중인 메시지가 있으면 처리
        if st.session_state.pending_message:
            st.info(f"📝 선택된 예시: {st.session_state.pending_message}")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✅ 전송"):
                    message = st.session_state.pending_message
                    st.session_state.pending_message = ""
                    self.process_user_message(message)
                    st.rerun()
            
            with col2:
                if st.button("❌ 취소"):
                    st.session_state.pending_message = ""
                    st.rerun()
        
        # 채팅 히스토리 표시
        chat_container = st.container()
        
        with chat_container:
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.write(message["content"])
                    
                    # 응답 시간 표시
                    if "timestamp" in message:
                        st.caption(f"📅 {message['timestamp']}")
                    
                    # 실행 트레이스 표시 (어시스턴트 메시지에만)
                    if message["role"] == "assistant" and "execution_trace" in message:
                        if message["execution_trace"]:
                            with st.expander("🔍 실행 세부사항"):
                                for j, trace in enumerate(message["execution_trace"], 1):
                                    status = "✅" if trace.get("success", False) else "❌"
                                    st.markdown(f"**{status} 단계 {j}**: {trace.get('tool', 'Unknown')}")
                                    st.markdown(f"   📝 {trace.get('output', 'No output')}")
                                    if trace.get("parameters"):
                                        st.json(trace["parameters"])
                    
                    # 메타데이터 표시
                    if message["role"] == "assistant" and "metadata" in message:
                        metadata = message["metadata"]
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("도구 사용", metadata.get("tools_used", 0))
                        with col2:
                            st.metric("성공률", f"{metadata.get('success_rate', 0):.1%}")
                        with col3:
                            st.metric("처리 시간", metadata.get("processing_time", "N/A"))
                    
                    # 피드백 버튼 (어시스턴트 메시지에만)
                    if message["role"] == "assistant":
                        col1, col2, col3 = st.columns([1, 1, 2])
                        
                        message_key = f"msg_{i}_{message.get('timestamp', str(time.time())).replace(' ', '_').replace(':', '_')}"
                        
                        with col1:
                            if st.button("👍 좋음", key=f"good_{message_key}"):
                                success = self.collect_feedback(
                                    session_id=st.session_state.session_id,
                                    rating=5,
                                    comments="사용자 만족"
                                )
                                if success:
                                    st.success("✅ 피드백 전송 완료!")
                        
                        with col2:
                            if st.button("👎 나쁨", key=f"bad_{message_key}"):
                                success = self.collect_feedback(
                                    session_id=st.session_state.session_id,
                                    rating=1,
                                    comments="사용자 불만족"
                                )
                                if success:
                                    st.success("✅ 피드백 전송 완료!")
                        
                        with col3:
                            # 상세 피드백 - Enhanced for pattern learning
                            with st.expander("💬 상세 피드백"):
                                rating = st.selectbox("만족도", [5, 4, 3, 2, 1], key=f"rating_{message_key}")
                                comment = st.text_area("의견", key=f"comment_{message_key}")
                                
                                # Pattern feedback section
                                metadata = message.get("metadata", {})
                                pattern_suggestion = metadata.get("pattern_suggestion")
                                
                                if pattern_suggestion:
                                    st.write("**패턴 제안에 대한 피드백:**")
                                    pattern_accepted = st.radio(
                                        "제안된 패턴이 도움이 되었나요?",
                                        ["예", "아니오", "부분적으로"],
                                        key=f"pattern_{message_key}"
                                    )
                                    
                                    pattern_feedback = {
                                        "pattern_id": pattern_suggestion.get("pattern_id"),
                                        "suggestion_accepted": pattern_accepted == "예"
                                    }
                                else:
                                    pattern_feedback = {}
                                
                                if st.button("제출", key=f"submit_{message_key}"):
                                    if self.collect_enhanced_feedback(
                                        st.session_state.session_id, 
                                        rating, 
                                        comment, 
                                        pattern_feedback
                                    ):
                                        st.success("피드백 제출 완료!")
        
        # 채팅 입력 - value 매개변수 완전히 제거
        prompt = st.chat_input("메시지를 입력하세요...")
        
        if prompt:
            self.process_user_message(prompt)
            st.rerun()

    def render_system_monitoring(self):
        """시스템 모니터링 렌더링"""
        st.header("⚡ System Monitoring")
        
        # 시스템 건강 상태 가져오기
        health = self.get_system_health()
        
        if health:
            # 상태 표시
            status = health.get("status", "unknown")
            if status == "healthy":
                st.success(f"✅ 시스템 상태: {status}")
            else:
                st.error(f"❌ 시스템 상태: {status}")
            
            # 상세 정보
            st.json(health)
        else:
            st.warning("시스템 상태를 가져올 수 없습니다.")
        
        # 실시간 업데이트
        if st.button("🔄 상태 새로고침"):
            st.rerun()
    
    def render_pattern_analytics(self):
        """패턴 학습 분석 대시보드"""
        st.header("🧠 Pattern Learning Analytics")
        
        # 사용자 선택
        col1, col2 = st.columns([1, 3])
        with col1:
            user_filter = st.selectbox(
                "사용자 필터",
                ["전체", "개별 사용자"],
                key="pattern_user_filter"
            )
        
        with col2:
            if user_filter == "개별 사용자":
                selected_user = st.text_input("User ID", value=st.session_state.user_id)
            else:
                selected_user = None
        
        # 패턴 학습 메트릭 가져오기
        analytics_endpoint = "/analytics/patterns"
        if selected_user:
            analytics_endpoint += f"?user_id={selected_user}"
        
        analytics_data = self.make_api_request(analytics_endpoint)
        
        if analytics_data and "analytics" in analytics_data:
            metrics = analytics_data["analytics"]
            
            # 주요 메트릭 표시
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "학습된 패턴 수",
                    metrics.get("total_patterns_learned", 0),
                    delta=None
                )
            
            with col2:
                st.metric(
                    "신뢰 패턴 수",
                    metrics.get("confident_patterns", 0),
                    delta=None
                )
            
            with col3:
                learning_effectiveness = metrics.get("learning_effectiveness", 0) * 100
                st.metric(
                    "학습 효과성",
                    f"{learning_effectiveness:.1f}%",
                    delta=None
                )
            
            with col4:
                avg_success_rate = metrics.get("average_success_rate", 0) * 100
                st.metric(
                    "평균 성공률",
                    f"{avg_success_rate:.1f}%",
                    delta=None
                )
            
            st.divider()
            
            # 패턴 타입별 분포
            if "patterns_by_type" in metrics:
                st.subheader("📊 패턴 타입별 분포")
                
                pattern_types = metrics["patterns_by_type"]
                if pattern_types:
                    df_types = pd.DataFrame(
                        list(pattern_types.items()),
                        columns=["Pattern Type", "Count"]
                    )
                    
                    fig = px.pie(
                        df_types,
                        values="Count",
                        names="Pattern Type",
                        title="학습된 패턴 타입 분포"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("아직 학습된 패턴이 없습니다.")
            
            st.divider()
            
        else:
            st.warning("패턴 분석 데이터를 가져올 수 없습니다.")
        
        # 학습된 패턴 목록
        st.subheader("📋 학습된 패턴 목록")
        
        patterns_endpoint = "/patterns/learned"
        if selected_user:
            patterns_endpoint += f"?user_id={selected_user}"
        
        patterns_data = self.make_api_request(patterns_endpoint)
        
        if patterns_data and "patterns" in patterns_data:
            patterns = patterns_data["patterns"]
            
            if patterns:
                # 패턴 정렬 옵션
                sort_by = st.selectbox(
                    "정렬 기준",
                    ["created_at", "success_rate", "confidence_score", "total_executions"],
                    key="pattern_sort"
                )
                
                # 패턴 정렬
                if sort_by in ["success_rate", "confidence_score", "total_executions"]:
                    patterns.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
                else:
                    patterns.sort(key=lambda x: x.get(sort_by, ""), reverse=True)
                
                # 패턴 카드 표시
                for pattern in patterns[:10]:  # 최대 10개만 표시
                    with st.expander(
                        f"🔄 {pattern['name']} (신뢰도: {pattern['confidence_score']:.1%})"
                    ):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**설명:** {pattern['description']}")
                            st.write(f"**성공률:** {pattern['success_rate']:.1%}")
                            st.write(f"**실행 횟수:** {pattern['total_executions']}")
                            
                        with col2:
                            st.write(f"**평균 실행 시간:** {pattern['average_execution_time']:.1f}s")
                            st.write(f"**단계 수:** {pattern['steps']}")
                            st.write(f"**생성일:** {pattern['created_at'][:10]}")
                        
                        # 패턴 상세 정보 버튼
                        if st.button(f"상세 보기", key=f"detail_{pattern['pattern_id']}"):
                            self.show_pattern_details(pattern['pattern_id'])
            else:
                st.info("학습된 패턴이 없습니다.")
        else:
            st.warning("패턴 목록을 가져올 수 없습니다.")
        
        # 새로고침 버튼
        if st.button("🔄 데이터 새로고침", key="pattern_refresh"):
            st.rerun()
    
    def show_pattern_details(self, pattern_id: str):
        """패턴 상세 정보 표시"""
        pattern_data = self.make_api_request(f"/patterns/{pattern_id}")
        
        if pattern_data:
            st.subheader(f"📋 패턴 상세: {pattern_data['name']}")
            
            # 기본 정보
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ID:** {pattern_data['pattern_id']}")
                st.write(f"**타입:** {pattern_data['pattern_type']}")
                st.write(f"**성공률:** {pattern_data['success_rate']:.1%}")
                
            with col2:
                st.write(f"**신뢰도:** {pattern_data['confidence_score']:.1%}")
                st.write(f"**실행 횟수:** {pattern_data['total_executions']}")
                st.write(f"**평균 시간:** {pattern_data['average_execution_time']:.1f}s")
            
            # 단계별 정보
            if "steps" in pattern_data and pattern_data["steps"]:
                st.subheader("🔧 실행 단계")
                
                for step in pattern_data["steps"]:
                    with st.expander(f"Step {step['step_id']}: {step['tool_name']}"):
                        st.write(f"**도구:** {step['tool_name']}")
                        st.write(f"**실행 시간:** {step['execution_time']:.2f}s")
                        st.write(f"**성공 여부:** {'✅' if step['success'] else '❌'}")
                        
                        if step['parameters']:
                            st.write("**파라미터:**")
                            st.json(step['parameters'])
                        
                        if step['output_summary']:
                            st.write(f"**출력 요약:** {step['output_summary']}")
        else:
            st.error("패턴 상세 정보를 가져올 수 없습니다.")
    
    def render_tool_analytics(self):
        """도구 분석 대시보드"""
        st.header("🔧 Tool Usage Analytics")
        
        # 사용자 선택
        col1, col2 = st.columns([1, 3])
        with col1:
            user_filter = st.selectbox(
                "사용자 필터",
                ["전체", "개별 사용자"],
                key="tool_user_filter"
            )
        
        with col2:
            if user_filter == "개별 사용자":
                selected_user = st.text_input("User ID", value=st.session_state.user_id, key="tool_user_input")
            else:
                selected_user = None
        
        # 도구 분석 데이터 가져오기
        analytics_endpoint = "/analytics/tools"
        if selected_user:
            analytics_endpoint += f"?user_id={selected_user}"
        
        analytics_data = self.make_api_request(analytics_endpoint)
        
        if analytics_data and "analytics" in analytics_data:
            metrics = analytics_data["analytics"]
            
            if selected_user:
                # 개별 사용자 분석
                self.render_user_tool_analytics(metrics, selected_user)
            else:
                # 시스템 전체 분석
                self.render_system_tool_analytics(metrics)
        else:
            st.warning("도구 분석 데이터를 가져올 수 없습니다.")
        
        # 새로고침 버튼
        if st.button("🔄 데이터 새로고침", key="tool_refresh"):
            st.rerun()
    
    def render_user_tool_analytics(self, metrics: Dict, user_id: str):
        """개별 사용자 도구 분석"""
        st.subheader(f"👤 {user_id} 사용자 분석")
        
        if "error" in metrics:
            st.warning(metrics["error"])
            return
        
        # 주요 메트릭
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "총 도구 사용",
                metrics.get("total_tool_uses", 0)
            )
        
        with col2:
            success_rate = metrics.get("overall_success_rate", 0) * 100
            st.metric(
                "전체 성공률",
                f"{success_rate:.1f}%"
            )
        
        with col3:
            st.metric(
                "최고 사용 시간대",
                ", ".join(map(str, metrics.get("peak_usage_hours", [])[:3]))
            )
        
        with col4:
            improvement_avg = 0
            if "recent_improvements" in metrics:
                improvements = metrics["recent_improvements"]
                if improvements:
                    improvement_avg = sum(improvements.values()) / len(improvements)
            st.metric(
                "평균 개선율",
                f"{improvement_avg:.1f}%"
            )
        
        st.divider()
        
        # 가장 많이 사용한 도구
        if "most_used_tools" in metrics:
            st.subheader("📊 가장 많이 사용한 도구")
            most_used = metrics["most_used_tools"]
            
            if most_used:
                df_tools = pd.DataFrame(most_used, columns=["Tool", "Usage Count"])
                
                fig = px.bar(
                    df_tools,
                    x="Tool",
                    y="Usage Count",
                    title="도구별 사용 빈도"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # 최고 성능 도구
        if "best_performing_tools" in metrics:
            st.subheader("🏆 최고 성능 도구")
            best_performing = metrics["best_performing_tools"]
            
            if best_performing:
                for tool, success_rate in best_performing[:5]:
                    st.write(f"**{tool}**: {success_rate:.1%} 성공률")
        
        # 개인화 선호도
        if "preferences" in metrics:
            st.subheader("⭐ 개인화 선호도")
            preferences = metrics["preferences"]
            
            if preferences:
                df_prefs = pd.DataFrame(
                    list(preferences.items()),
                    columns=["Tool", "Preference Score"]
                )
                df_prefs["Preference Score"] = df_prefs["Preference Score"].apply(lambda x: x * 100)
                
                fig = px.horizontal_bar(
                    df_prefs,
                    x="Preference Score",
                    y="Tool",
                    title="도구별 개인화 선호도 (%)"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def render_system_tool_analytics(self, metrics: Dict):
        """시스템 전체 도구 분석"""
        st.subheader("🌐 시스템 전체 분석")
        
        if "error" in metrics:
            st.warning(metrics["error"])
            return
        
        # 주요 메트릭
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "총 도구 사용",
                metrics.get("total_tool_uses", 0)
            )
        
        with col2:
            success_rate = metrics.get("overall_success_rate", 0) * 100
            st.metric(
                "전체 성공률",
                f"{success_rate:.1f}%"
            )
        
        with col3:
            st.metric(
                "활성 사용자",
                metrics.get("unique_users", 0)
            )
        
        with col4:
            avg_tools = metrics.get("avg_tools_per_user", 0)
            st.metric(
                "사용자당 평균 도구",
                f"{avg_tools:.1f}"
            )
        
        st.divider()
        
        # 인기 도구
        if "popular_tools" in metrics:
            st.subheader("🔥 인기 도구 순위")
            popular_tools = metrics["popular_tools"]
            
            if popular_tools:
                df_popular = pd.DataFrame(popular_tools, columns=["Tool", "Usage Count"])
                
                fig = px.bar(
                    df_popular,
                    x="Tool",
                    y="Usage Count",
                    title="도구별 전체 사용 빈도"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # 최고 조합
        if "best_combinations" in metrics:
            st.subheader("🤝 최고 도구 조합")
            best_combinations = metrics["best_combinations"]
            
            if best_combinations:
                for i, (tools, success_rate, usage_count) in enumerate(best_combinations[:5], 1):
                    tools_str = " → ".join(tools)
                    st.write(f"**{i}.** {tools_str}")
                    st.write(f"   성공률: {success_rate:.1%}, 사용 횟수: {usage_count}")
        
        # 성능 트렌드
        improvement_trend = metrics.get("improvement_trend", 0)
        if improvement_trend != 0:
            st.subheader("📈 성능 트렌드")
            if improvement_trend > 0:
                st.success(f"📈 성능이 {improvement_trend:.1%} 향상되었습니다!")
            else:
                st.warning(f"📉 성능이 {abs(improvement_trend):.1%} 감소했습니다.")
    
    def render_verification_dashboard(self):
        """PoC 검증 대시보드 렌더링"""
        st.header("🔍 인터랙티브 PoC 검증 대시보드")
        st.markdown("**원클릭으로 시나리오를 실행하고 피드백을 통해 학습 효과를 확인하세요!**")
        
        # 사용자 선택
        col1, col2 = st.columns([2, 1])
        with col1:
            user_id = st.selectbox(
                "테스트 사용자 선택",
                ["user_001", "user_002", "test_user"],
                key="verification_user_id",
                help="시나리오 실행에 사용할 사용자 ID를 선택하세요"
            )
        
        with col2:
            if st.button("🔄 대시보드 새로고침", key="refresh_dashboard"):
                st.rerun()
        
        st.divider()
        
        # 시나리오 선택 탭
        scenario_tab1, scenario_tab2, comparison_tab = st.tabs([
            "📈 Scenario 1.1: Flow Mode",
            "🎯 Scenario 1.2: Basic Mode", 
            "📊 비교 분석"
        ])
        
        with scenario_tab1:
            self.render_scenario_11_interface(user_id)
        
        with scenario_tab2:
            self.render_scenario_12_interface(user_id)
        
        with comparison_tab:
            self.render_comparison_interface(user_id)
    
    def render_scenario_11_interface(self, user_id: str):
        """Scenario 1.1 인터페이스 렌더링"""
        st.subheader("📈 Flow Mode 패턴 학습 테스트")
        
        # 시나리오 설명
        with st.expander("🎯 시나리오 1.1 상세 정보", expanded=False):
            st.markdown("""
            **검증 목적**: 성공한 워크플로우 패턴의 자동 학습과 재사용 능력 확인
            
            **테스트 시나리오**:
            - 동일한 요청을 4회 실행하여 패턴 학습 유도
            - 4번째 실행부터 자동 패턴 제안 확인
            - 실행 시간 최적화 효과 측정
            
            **성공 기준**:
            - 패턴 제안 정확도: 95% 이상
            - 실행 시간 단축: 25% 이상  
            - 평균 패턴 신뢰도: 80% 이상
            """)
        
        # 실행 버튼과 진행 상태
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🚀 Scenario 1.1 자동 실행 시작", key="execute_scenario_11", type="primary"):
                st.session_state.scenario_11_executing = True
                st.session_state.scenario_11_results = None
        
        with col2:
            # 현재 상태 조회
            status_response = self.make_api_request(f"/scenarios/1.1/status?user_id={user_id}")
            if status_response and status_response.get("status"):
                status = status_response["status"]
                progress = status.get("progress", 0.0)
                st.metric("진행률", f"{progress:.1%}")
        
        # 실행 중 상태 표시
        if st.session_state.get("scenario_11_executing", False):
            with st.spinner("시나리오 1.1 실행 중... 잠시만 기다려주세요"):
                # API 호출로 시나리오 실행
                execution_response = self.make_api_request(
                    f"/scenarios/1.1/execute?user_id={user_id}", 
                    method="POST"
                )
                
                if execution_response and execution_response.get("result"):
                    st.session_state.scenario_11_results = execution_response["result"]
                    st.session_state.scenario_11_executing = False
                    st.success("✅ Scenario 1.1 실행 완료!")
                    st.rerun()
                else:
                    st.error("❌ 시나리오 실행에 실패했습니다.")
                    st.session_state.scenario_11_executing = False
        
        # 실행 결과 표시
        if st.session_state.get("scenario_11_results"):
            results = st.session_state.scenario_11_results
            
            if results.get("status") == "completed":
                st.success("🎉 시나리오 1.1 실행 완료!")
                
                # 실행 요약
                execution_results = results.get("execution_results", [])
                if execution_results:
                    st.subheader("📊 실행 결과 요약")
                    
                    # 실행 결과 테이블
                    results_data = []
                    for result in execution_results:
                        results_data.append({
                            "실행차수": result["iteration"],
                            "실행시간(초)": f"{result['execution_time']:.1f}",
                            "성공률": f"{result['success_rate']:.1%}",
                            "패턴제안": "✅" if result.get("pattern_suggested") else "❌",
                            "신뢰도": f"{result.get('pattern_confidence', 0):.1%}"
                        })
                    
                    st.dataframe(pd.DataFrame(results_data), use_container_width=True)
                    
                    # 성과 지표
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        avg_time = sum(r["execution_time"] for r in execution_results) / len(execution_results)
                        st.metric("평균 실행시간", f"{avg_time:.1f}초")
                    
                    with col2:
                        pattern_suggested_count = sum(1 for r in execution_results if r.get("pattern_suggested"))
                        st.metric("패턴 제안 횟수", f"{pattern_suggested_count}회")
                    
                    with col3:
                        avg_confidence = sum(r.get("pattern_confidence", 0) for r in execution_results) / len(execution_results)
                        st.metric("평균 신뢰도", f"{avg_confidence:.1%}")
                
                # 피드백 섹션
                st.divider()
                st.subheader("💬 피드백 제공")
                
                with st.form("scenario_11_feedback"):
                    st.markdown("**실행 결과에 대한 피드백을 제공해주세요:**")
                    
                    rating = st.select_slider(
                        "전체적인 만족도",
                        options=[1, 2, 3, 4, 5],
                        value=3,
                        format_func=lambda x: "⭐" * x,
                        key="scenario_11_rating"
                    )
                    
                    comments = st.text_area(
                        "추가 의견",
                        placeholder="패턴 학습이 정확했나요? 실행 속도는 어땠나요?",
                        key="scenario_11_comments"
                    )
                    
                    # 구체적 피드백 체크박스
                    st.markdown("**구체적인 개선 사항 (해당되는 것을 선택하세요):**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        execution_slow = st.checkbox("실행 속도가 너무 느림", key="s11_slow")
                        pattern_inaccurate = st.checkbox("패턴 제안이 부정확함", key="s11_pattern")
                    
                    with col2:
                        wrong_tools = st.checkbox("잘못된 도구가 선택됨", key="s11_tools")  
                        needs_improvement = st.checkbox("전반적인 개선 필요", key="s11_improve")
                    
                    submitted = st.form_submit_button("피드백 제출", type="primary")
                    
                    if submitted:
                        # 피드백 API 호출
                        feedback_data = {
                            "scenario_id": "1.1",
                            "user_id": user_id,
                            "rating": rating,
                            "comments": comments,
                            "specific_feedback": {
                                "execution_too_slow": execution_slow,
                                "pattern_not_accurate": pattern_inaccurate,
                                "wrong_tools_selected": wrong_tools,
                                "needs_improvement": needs_improvement
                            }
                        }
                        
                        feedback_response = self.make_api_request(
                            "/scenarios/feedback",
                            method="POST",
                            data=feedback_data
                        )
                        
                        if feedback_response:
                            st.success("✅ 피드백이 성공적으로 제출되었습니다!")
                            st.session_state.scenario_11_feedback_submitted = True
                            
                            # 개선 효과 표시
                            result = feedback_response.get("result", {})
                            if result.get("improvement_applied"):
                                st.info("🔄 피드백이 시스템에 반영되었습니다!")
                                
                                improvements = result.get("improvement_details", [])
                                for improvement in improvements:
                                    st.write(f"• {improvement}")
                            
                            st.rerun()
                        else:
                            st.error("❌ 피드백 제출에 실패했습니다.")
                
                # 개선 효과 확인 버튼
                if st.session_state.get("scenario_11_feedback_submitted"):
                    st.divider()
                    if st.button("🔍 피드백 반영 효과 확인", key="check_improvement_11"):
                        st.session_state.show_scenario_11_comparison = True
                        st.rerun()
                
                # Before/After 비교 표시
                if st.session_state.get("show_scenario_11_comparison"):
                    self.render_scenario_comparison("1.1", user_id)
            
            else:
                st.error("❌ 시나리오 실행에 실패했습니다.")
                if results.get("error"):
                    st.error(f"에러: {results['error']}")
    
    def render_scenario_12_interface(self, user_id: str):
        """Scenario 1.2 인터페이스 렌더링"""
        st.subheader("🎯 Basic Mode 도구 선택 테스트")
        
        # 시나리오 설명
        with st.expander("🎯 시나리오 1.2 상세 정보", expanded=False):
            st.markdown("""
            **검증 목적**: 자연어 요청에서 최적 도구 조합 자동 추천 능력 확인
            
            **테스트 시나리오**:
            - 5가지 다양한 자연어 표현으로 동일한 의도 테스트
            - 도구 선택 정확도 학습 과정 관찰
            - 사용자 피드백 기반 개선 효과 측정
            
            **성공 기준**:
            - 의도 파악 정확도: 88% 이상
            - 정확도 개선: 70%→90% 향상
            - 사용자 만족도 향상
            """)
        
        # 실행 버튼과 진행 상태
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🚀 Scenario 1.2 자동 실행 시작", key="execute_scenario_12", type="primary"):
                st.session_state.scenario_12_executing = True
                st.session_state.scenario_12_results = None
        
        with col2:
            # 현재 상태 조회
            status_response = self.make_api_request(f"/scenarios/1.2/status?user_id={user_id}")
            if status_response and status_response.get("status"):
                status = status_response["status"]
                progress = status.get("progress", 0.0)
                st.metric("진행률", f"{progress:.1%}")
        
        # 실행 중 상태 표시
        if st.session_state.get("scenario_12_executing", False):
            with st.spinner("시나리오 1.2 실행 중... 잠시만 기다려주세요"):
                # API 호출로 시나리오 실행
                execution_response = self.make_api_request(
                    f"/scenarios/1.2/execute?user_id={user_id}", 
                    method="POST"
                )
                
                if execution_response and execution_response.get("result"):
                    st.session_state.scenario_12_results = execution_response["result"]
                    st.session_state.scenario_12_executing = False
                    st.success("✅ Scenario 1.2 실행 완료!")
                    st.rerun()
                else:
                    st.error("❌ 시나리오 실행에 실패했습니다.")
                    st.session_state.scenario_12_executing = False
        
        # 실행 결과 표시
        if st.session_state.get("scenario_12_results"):
            results = st.session_state.scenario_12_results
            
            if results.get("status") == "completed":
                st.success("🎉 시나리오 1.2 실행 완료!")
                
                # 실행 요약
                execution_results = results.get("execution_results", [])
                if execution_results:
                    st.subheader("📊 실행 결과 요약")
                    
                    # 실행 결과 테이블
                    results_data = []
                    for result in execution_results:
                        results_data.append({
                            "실행차수": result["iteration"],
                            "테스트 메시지": result["message"][:30] + "...",
                            "실행시간(초)": f"{result['execution_time']:.1f}",
                            "성공률": f"{result['success_rate']:.1%}",
                            "도구정확도": f"{result.get('tool_accuracy', 0):.1%}",
                            "컨텍스트적합성": f"{result.get('context_relevance', 0):.1%}"
                        })
                    
                    st.dataframe(pd.DataFrame(results_data), use_container_width=True)
                    
                    # 성과 지표
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        avg_accuracy = sum(r.get("tool_accuracy", 0) for r in execution_results) / len(execution_results)
                        st.metric("평균 도구 정확도", f"{avg_accuracy:.1%}")
                    
                    with col2:
                        avg_relevance = sum(r.get("context_relevance", 0) for r in execution_results) / len(execution_results)
                        st.metric("평균 컨텍스트 적합성", f"{avg_relevance:.1%}")
                    
                    with col3:
                        avg_time = sum(r["execution_time"] for r in execution_results) / len(execution_results)
                        st.metric("평균 실행시간", f"{avg_time:.1f}초")
                
                # 피드백 섹션
                st.divider()
                st.subheader("💬 피드백 제공")
                
                with st.form("scenario_12_feedback"):
                    st.markdown("**도구 선택 결과에 대한 피드백을 제공해주세요:**")
                    
                    rating = st.select_slider(
                        "전체적인 만족도",
                        options=[1, 2, 3, 4, 5],
                        value=3,
                        format_func=lambda x: "⭐" * x,
                        key="scenario_12_rating"
                    )
                    
                    comments = st.text_area(
                        "추가 의견",
                        placeholder="도구 선택이 적절했나요? 의도 파악이 정확했나요?",
                        key="scenario_12_comments"
                    )
                    
                    # 구체적 피드백 체크박스
                    st.markdown("**구체적인 개선 사항:**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        wrong_tools = st.checkbox("잘못된 도구 선택", key="s12_tools")
                        poor_intent = st.checkbox("의도 파악 부정확", key="s12_intent")
                    
                    with col2:
                        slow_response = st.checkbox("응답 속도 느림", key="s12_slow")
                        context_poor = st.checkbox("상황 맞지 않음", key="s12_context")
                    
                    submitted = st.form_submit_button("피드백 제출", type="primary")
                    
                    if submitted:
                        # 피드백 API 호출
                        feedback_data = {
                            "scenario_id": "1.2",
                            "user_id": user_id,
                            "rating": rating,
                            "comments": comments,
                            "specific_feedback": {
                                "wrong_tools_selected": wrong_tools,
                                "poor_intent_recognition": poor_intent,
                                "slow_response_time": slow_response,
                                "poor_context_understanding": context_poor
                            }
                        }
                        
                        feedback_response = self.make_api_request(
                            "/scenarios/feedback",
                            method="POST",
                            data=feedback_data
                        )
                        
                        if feedback_response:
                            st.success("✅ 피드백이 성공적으로 제출되었습니다!")
                            st.session_state.scenario_12_feedback_submitted = True
                            
                            # 개선 효과 표시
                            result = feedback_response.get("result", {})
                            if result.get("improvement_applied"):
                                st.info("🔄 피드백이 시스템에 반영되었습니다!")
                                
                                improvements = result.get("improvement_details", [])
                                for improvement in improvements:
                                    st.write(f"• {improvement}")
                            
                            st.rerun()
                        else:
                            st.error("❌ 피드백 제출에 실패했습니다.")
                
                # 개선 효과 확인 버튼
                if st.session_state.get("scenario_12_feedback_submitted"):
                    st.divider()
                    if st.button("🔍 피드백 반영 효과 확인", key="check_improvement_12"):
                        st.session_state.show_scenario_12_comparison = True
                        st.rerun()
                
                # Before/After 비교 표시
                if st.session_state.get("show_scenario_12_comparison"):
                    self.render_scenario_comparison("1.2", user_id)
            
            else:
                st.error("❌ 시나리오 실행에 실패했습니다.")
                if results.get("error"):
                    st.error(f"에러: {results['error']}")
    
    def render_scenario_comparison(self, scenario_id: str, user_id: str):
        """시나리오 Before/After 비교 렌더링"""
        st.subheader(f"📊 Scenario {scenario_id} 피드백 반영 효과")
        
        comparison_response = self.make_api_request(f"/scenarios/{scenario_id}/comparison?user_id={user_id}")
        
        if comparison_response and comparison_response.get("comparison"):
            comparison = comparison_response["comparison"]
            
            if "message" in comparison:
                st.info(comparison["message"])
                return
            
            # 비교 차트 생성
            if scenario_id == "1.1":
                # Flow Mode 비교
                current = comparison.get("current_metrics", {})
                baseline = comparison.get("baseline_metrics", {})
                improvement = comparison.get("improvement", {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📈 성능 개선 지표**")
                    
                    metrics_data = pd.DataFrame({
                        '지표': ['패턴 제안 정확도', '실행 시간 개선', '패턴 신뢰도'],
                        '이전': [0.0, 0.0, 0.0],
                        '현재': [
                            current.get('pattern_suggestion_accuracy', 0),
                            current.get('time_improvement_percentage', 0),
                            current.get('avg_pattern_confidence', 0)
                        ]
                    })
                    
                    fig = px.bar(
                        metrics_data,
                        x='지표',
                        y=['이전', '현재'],
                        title="Flow Mode 성능 비교",
                        barmode='group'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("**🎯 개선 효과**")
                    for key, value in improvement.items():
                        if value > 0:
                            st.success(f"✅ {key}: +{value:.1%}")
                        else:
                            st.info(f"➖ {key}: {value:.1%}")
            
            elif scenario_id == "1.2":
                # Basic Mode 비교
                current = comparison.get("current_metrics", {})
                baseline = comparison.get("baseline_metrics", {})
                improvement = comparison.get("improvement", {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📈 성능 개선 지표**")
                    
                    metrics_data = pd.DataFrame({
                        '지표': ['의도 파악 정확도', '정확도 개선', '만족도 개선'],
                        '이전': [
                            baseline.get('intent_recognition_accuracy', 0),
                            baseline.get('accuracy_improvement', 0),
                            baseline.get('satisfaction_improvement', 0)
                        ],
                        '현재': [
                            current.get('intent_recognition_accuracy', 0),
                            current.get('accuracy_improvement', 0),
                            current.get('satisfaction_improvement', 0)
                        ]
                    })
                    
                    fig = px.bar(
                        metrics_data,
                        x='지표',
                        y=['이전', '현재'],
                        title="Basic Mode 성능 비교",
                        barmode='group'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("**🎯 개선 효과**")
                    for key, value in improvement.items():
                        if value > 0:
                            st.success(f"✅ {key}: +{value:.1%}")
                        else:
                            st.info(f"➖ {key}: {value:.1%}")
        
        else:
            st.warning("비교 데이터를 가져올 수 없습니다.")
    
    def render_comparison_interface(self, user_id: str):
        """비교 분석 인터페이스 렌더링"""
        st.subheader("📊 종합 비교 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 종합 검증 보고서 생성", key="generate_comprehensive_report"):
                report = self.make_api_request(f"/verification/comprehensive-report/{user_id}")
                
                if report and report.get("report"):
                    st.session_state.comprehensive_report = report["report"]
                    st.rerun()
        
        with col2:
            if st.button("📊 실시간 시스템 상태", key="show_system_status"):
                st.session_state.show_system_status = True
                st.rerun()
        
        # 종합 보고서 표시
        if st.session_state.get("comprehensive_report"):
            report_data = st.session_state.comprehensive_report
            
            st.subheader("📋 종합 검증 보고서")
            
            # 성공 기준 달성 현황
            success_criteria = report_data.get("success_criteria", {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**✅ 달성된 기준**")
                achieved = [k for k, v in success_criteria.items() if v]
                for criterion in achieved:
                    st.success(f"✅ {criterion}")
            
            with col2:
                st.markdown("**❌ 미달성 기준**")
                not_achieved = [k for k, v in success_criteria.items() if not v]
                for criterion in not_achieved:
                    st.error(f"❌ {criterion}")
            
            # 전체 통과율
            overall_metrics = report_data.get("overall_metrics", {})
            pass_rate = overall_metrics.get("overall_pass_rate", 0)
            
            st.metric("🏆 전체 통과율", f"{pass_rate:.1%}", delta=f"{len(achieved)}/{len(success_criteria)}개 달성")
            
            # 주요 인사이트
            insights = report_data.get("key_insights", [])
            if insights:
                st.subheader("💡 주요 인사이트")
                for insight in insights:
                    st.info(f"💡 {insight}")
            
            # 개선 권장사항
            recommendations = report_data.get("recommendations", [])
            if recommendations:
                st.subheader("🎯 개선 권장사항")
                for rec in recommendations:
                    st.warning(f"🎯 {rec}")
        
        # 실시간 시스템 상태
        if st.session_state.get("show_system_status"):
            st.subheader("📊 실시간 시스템 상태")
            
            dashboard_data = self.make_api_request("/verification/dashboard")
            if dashboard_data and dashboard_data.get("dashboard"):
                data = dashboard_data["dashboard"]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("활성 사용자", data.get("active_users", 0))
                
                with col2:
                    st.metric("학습된 패턴", data.get("total_patterns_learned", 0))
                
                with col3:
                    st.metric("평균 패턴 신뢰도", f"{data.get('avg_pattern_confidence', 0):.1%}")
                
                with col4:
                    st.metric("최근 실행 수", data.get("recent_executions", 0))
                
                # 단계별 사용자 분포
                phase_dist = data.get("phase_distribution", {})
                if phase_dist:
                    st.subheader("👥 단계별 사용자 분포")
                    phase_df = pd.DataFrame(list(phase_dist.items()), columns=['단계', '사용자 수'])
                    
                    fig = px.pie(
                        phase_df, 
                        values='사용자 수', 
                        names='단계',
                        title="학습 단계별 사용자 분포"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    def run(self):
        """앱 실행"""
        # 사이드바 네비게이션
        with st.sidebar:
            st.title("🤖 Agentic AI Platform")
            
            page = st.selectbox(
                "페이지 선택",
                ["Chat", "Pattern Analytics", "Tool Analytics", "Verification Dashboard", "System Monitoring"]
            )
            
            st.divider()
            
            # 연결 상태 확인
            health_check = self.make_api_request("/health")
            if health_check:
                st.success("✅ 백엔드 연결됨")
                if "message" in health_check:
                    st.caption(health_check["message"])
            else:
                st.error("❌ 백엔드 연결 실패")
        
        # 메인 콘텐츠 렌더링
        if page == "Chat":
            self.render_chat_interface()
        elif page == "Pattern Analytics":
            self.render_pattern_analytics()
        elif page == "Tool Analytics":
            self.render_tool_analytics()
        elif page == "Verification Dashboard":
            self.render_verification_dashboard()
        elif page == "System Monitoring":
            self.render_system_monitoring()

def main():
    """메인 함수"""
    app = AgenticAIApp()
    app.run()

if __name__ == "__main__":
    main()