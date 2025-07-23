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
        """피드백 수집 - 새로운 API 형식"""
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
                            # 상세 피드백
                            with st.expander("💬 상세 피드백"):
                                rating = st.selectbox("만족도", [5, 4, 3, 2, 1], key=f"rating_{message_key}")
                                comment = st.text_area("의견", key=f"comment_{message_key}")
                                if st.button("제출", key=f"submit_{message_key}"):
                                    if self.collect_feedback(st.session_state.session_id, rating, comment):
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
    
    def run(self):
        """앱 실행"""
        # 사이드바 네비게이션
        with st.sidebar:
            st.title("🤖 Agentic AI Platform")
            
            page = st.selectbox(
                "페이지 선택",
                ["Chat", "System Monitoring"]
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
        elif page == "System Monitoring":
            self.render_system_monitoring()

def main():
    """메인 함수"""
    app = AgenticAIApp()
    app.run()

if __name__ == "__main__":
    main()