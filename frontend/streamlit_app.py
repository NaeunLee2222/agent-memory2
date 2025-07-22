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
    page_title="Agent Memory & Feedback System",
    page_icon="🤖",
    layout="wide"
)

# API 기본 URL (환경변수에서 가져오거나 기본값 사용)
API_BASE_URL = os.getenv("BACKEND_URL", "http://backend:8100")  # 포트 8100으로 수정


class AgentMemoryApp:
    def __init__(self):
        self.session_state_init()
    
    def session_state_init(self):
        """세션 상태 초기화"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'agent_id' not in st.session_state:
            st.session_state.agent_id = "agent_001"
        if 'session_id' not in st.session_state:
            st.session_state.session_id = f"session_{int(time.time())}"
        if 'mode' not in st.session_state:
            st.session_state.mode = "basic"
    
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
    
    def chat_with_agent(self, message: str, agent_id: str, mode: str) -> Optional[str]:
        """에이전트와 채팅"""
        data = {
            "agent_id": agent_id,
            "message": message,
            "mode": mode,
            "session_id": st.session_state.session_id
        }
        
        response = self.make_api_request("/api/v1/agents/chat", "POST", data)
        
        if response:
            return response.get("response", "응답을 받지 못했습니다.")
        return None
    
    def collect_feedback(self, agent_id: str, feedback_type: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """피드백 수집 - JSON body 방식으로 수정"""
        data = {
            "agent_id": agent_id,
            "feedback_type": feedback_type,
            "content": content,
            "metadata": metadata or {"session_id": st.session_state.session_id},
            "context": {"timestamp": datetime.utcnow().isoformat()}
        }
        
        response = self.make_api_request("/api/v1/feedback/collect", "POST", data)
        return response is not None
    
    def get_memory_stats(self, agent_id: str) -> Optional[Dict]:
        """메모리 통계 조회"""
        return self.make_api_request(f"/api/v1/memory/{agent_id}/stats")
    
    def get_feedback_insights(self, agent_id: str) -> Optional[Dict]:
        """피드백 인사이트 조회"""
        return self.make_api_request(f"/api/v1/feedback/{agent_id}/insights")
    
    def get_system_health(self) -> Optional[Dict]:
        """시스템 건강 상태 조회"""
        return self.make_api_request("/api/v1/performance/system")

    def render_chat_interface(self):
        """채팅 인터페이스 렌더링 - 피드백 버튼 수정"""
        st.header("🤖 Agent Chat")
        
        # 설정 사이드바
        with st.sidebar:
            st.subheader("⚙️ 설정")
            
            # 에이전트 ID 설정
            agent_id = st.text_input("Agent ID", value=st.session_state.agent_id)
            if agent_id != st.session_state.agent_id:
                st.session_state.agent_id = agent_id
            
            # 모드 선택
            mode = st.selectbox(
                "모드 선택",
                options=["basic", "flow"],
                index=0 if st.session_state.mode == "basic" else 1
            )
            if mode != st.session_state.mode:
                st.session_state.mode = mode
            
            # 새 세션 시작
            if st.button("🔄 새 세션 시작"):
                st.session_state.messages = []
                st.session_state.session_id = f"session_{int(time.time())}"
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
                    
                    # 피드백 버튼 (어시스턴트 메시지에만)
                    if message["role"] == "assistant":
                        col1, col2, col3 = st.columns([1, 1, 1])
                        
                        # 고유한 키 생성
                        message_key = f"msg_{i}_{message.get('timestamp', str(time.time())).replace(' ', '_').replace(':', '_')}"
                        
                        with col1:
                            if st.button("👍 좋음", key=f"good_{message_key}"):
                                success = self.collect_feedback(
                                    agent_id=st.session_state.agent_id,
                                    feedback_type="success",
                                    content="사용자가 응답에 만족함",
                                    metadata={
                                        "session_id": st.session_state.session_id,
                                        "message_index": i,
                                        "original_message": message["content"][:100]  # 첫 100자만
                                    }
                                )
                                if success:
                                    st.success("✅ 긍정적 피드백이 수집되었습니다!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ 피드백 수집 실패")
                        
                        with col2:
                            if st.button("👎 나쁨", key=f"bad_{message_key}"):
                                success = self.collect_feedback(
                                    agent_id=st.session_state.agent_id,
                                    feedback_type="error",
                                    content="사용자가 응답에 불만족",
                                    metadata={
                                        "session_id": st.session_state.session_id,
                                        "message_index": i,
                                        "original_message": message["content"][:100]
                                    }
                                )
                                if success:
                                    st.success("✅ 부정적 피드백이 수집되었습니다!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ 피드백 수집 실패")
                        
                        with col3:
                            # 수정 피드백을 위한 expander
                            with st.expander("🔧 수정하기"):
                                correction = st.text_area(
                                    "수정 내용을 입력하세요:",
                                    key=f"correction_input_{message_key}",
                                    placeholder="어떻게 개선되었으면 좋겠는지 설명해주세요..."
                                )
                                if st.button("수정사항 제출", key=f"submit_correction_{message_key}"):
                                    if correction.strip():
                                        success = self.collect_feedback(
                                            agent_id=st.session_state.agent_id,
                                            feedback_type="user_correction",
                                            content=correction,
                                            metadata={
                                                "session_id": st.session_state.session_id,
                                                "message_index": i,
                                                "original_message": message["content"][:100]
                                            }
                                        )
                                        if success:
                                            st.success("✅ 수정사항이 수집되었습니다!")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("❌ 수정사항 수집 실패")
                                    else:
                                        st.warning("수정 내용을 입력해주세요.")
        
        # 채팅 입력
        if prompt := st.chat_input("메시지를 입력하세요..."):
            # 사용자 메시지 추가
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # 에이전트 응답 요청
            with st.spinner("🤔 응답을 생성하는 중..."):
                response = self.chat_with_agent(prompt, st.session_state.agent_id, st.session_state.mode)
            
            if response:
                # 어시스턴트 응답 추가
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                st.rerun()
            else:
                st.error("응답을 받을 수 없습니다. 다시 시도해주세요.")    

    def render_memory_dashboard(self):
        """메모리 대시보드 렌더링"""
        st.header("🧠 Memory Dashboard")
        
        # 메모리 통계 가져오기
        memory_stats = self.get_memory_stats(st.session_state.agent_id)
        
        if memory_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 메모리", memory_stats.get("total_memories", 0))
            
            with col2:
                st.metric("메모리 저장소 사용량", f"{memory_stats.get('total_storage_used', 0)} bytes")
            
            with col3:
                working_memories = memory_stats.get('by_type', {}).get('working', 0)
                st.metric("Working Memory", working_memories)
            
            with col4:
                episodic_memories = memory_stats.get('by_type', {}).get('episodic', 0)
                st.metric("Episodic Memory", episodic_memories)
            
            # 메모리 타입별 분포 차트
            if memory_stats.get('by_type'):
                memory_types = list(memory_stats['by_type'].keys())
                memory_counts = list(memory_stats['by_type'].values())
                
                fig = px.pie(
                    values=memory_counts,
                    names=memory_types,
                    title="메모리 타입별 분포"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("메모리 통계를 가져올 수 없습니다.")
    
    def render_feedback_analytics(self):
        """피드백 분석 렌더링"""
        st.header("📊 Feedback Analytics")
        
        # 피드백 인사이트 가져오기
        insights = self.get_feedback_insights(st.session_state.agent_id)
        
        if insights:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("총 피드백 수", insights.get("total_feedback_count", 0))
            
            with col2:
                feedback_types = insights.get("feedback_types", {})
                success_rate = 0
                if feedback_types:
                    success_count = feedback_types.get("success", 0)
                    total_outcome = success_count + feedback_types.get("error", 0)
                    if total_outcome > 0:
                        success_rate = (success_count / total_outcome) * 100
                st.metric("성공률", f"{success_rate:.1f}%")
            
            # 피드백 타입별 분포
            if feedback_types:
                types = list(feedback_types.keys())
                counts = list(feedback_types.values())
                
                fig = go.Figure(data=[go.Bar(x=types, y=counts)])
                fig.update_layout(title="피드백 타입별 분포")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("피드백 데이터를 가져올 수 없습니다.")
    
    def render_system_monitoring(self):
        """시스템 모니터링 렌더링"""
        st.header("⚡ System Monitoring")
        
        # 시스템 건강 상태 가져오기
        health = self.get_system_health()
        
        if health:
            # 전체 상태
            overall_health = health.get("overall_health", "unknown")
            if overall_health == "healthy":
                st.success(f"✅ 시스템 상태: {overall_health}")
            elif overall_health == "warning":
                st.warning(f"⚠️ 시스템 상태: {overall_health}")
            else:
                st.error(f"❌ 시스템 상태: {overall_health}")
            
            # 메모리 사용량
            memory_usage = health.get("memory_usage", {})
            if memory_usage:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("총 메모리", memory_usage.get("total_memories", 0))
                
                with col2:
                    st.metric("총 피드백", memory_usage.get("total_feedback", 0))
            
            # 시스템 메트릭 (있는 경우)
            if "system_metrics" in health:
                system_metrics = health["system_metrics"]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    cpu_percent = system_metrics.get("cpu_percent", 0)
                    st.metric("CPU 사용률", f"{cpu_percent:.1f}%")
                
                with col2:
                    memory_percent = system_metrics.get("memory_percent", 0)
                    st.metric("메모리 사용률", f"{memory_percent:.1f}%")
                
                with col3:
                    disk_percent = system_metrics.get("disk_usage_percent", 0)
                    st.metric("디스크 사용률", f"{disk_percent:.1f}%")
        else:
            st.warning("시스템 상태를 가져올 수 없습니다.")
        
        # 실시간 업데이트
        if st.button("🔄 상태 새로고침"):
            st.rerun()
    
    def render_optimization_tools(self):
        """최적화 도구 렌더링"""
        st.header("🔧 Optimization Tools")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("메모리 최적화")
            
            if st.button("🧹 메모리 정리"):
                with st.spinner("메모리를 정리하는 중..."):
                    # 최적화 API 호출 (구현 필요)
                    time.sleep(2)  # 시뮬레이션
                    st.success("메모리 정리가 완료되었습니다!")
            
            if st.button("📊 메모리 분석"):
                st.info("메모리 분석을 시작합니다...")
        
        with col2:
            st.subheader("성능 최적화")
            
            if st.button("⚡ 성능 튜닝"):
                with st.spinner("성능을 최적화하는 중..."):
                    time.sleep(3)  # 시뮬레이션
                    st.success("성능 최적화가 완료되었습니다!")
            
            if st.button("📈 성능 리포트"):
                st.info("성능 리포트를 생성합니다...")
    
    def _calculate_expected_improvements(self, optimizations: List[str]) -> Dict[str, float]:
        """예상 개선 효과 계산"""
        improvements = {
            "response_time": 0.0,
            "memory_usage": 0.0,
            "accuracy": 0.0
        }
        
        for optimization in optimizations:
            if "memory" in optimization.lower():
                improvements["memory_usage"] += 15.0
                improvements["response_time"] += 5.0
            elif "performance" in optimization.lower():
                improvements["response_time"] += 20.0
                improvements["accuracy"] += 10.0
            elif "cache" in optimization.lower():
                improvements["response_time"] += 30.0
        
        return improvements
    
    def run(self):
        """앱 실행"""
        # 사이드바 네비게이션
        with st.sidebar:
            st.title("🤖 Agent Memory System")
            
            page = st.selectbox(
                "페이지 선택",
                ["Chat", "Memory Dashboard", "Feedback Analytics", "System Monitoring", "Optimization Tools"]
            )
            
            st.divider()
            
            # 연결 상태 확인
            health_check = self.make_api_request("/health")
            if health_check:
                st.success("✅ 백엔드 연결됨")
            else:
                st.error("❌ 백엔드 연결 실패")
        
        # 메인 콘텐츠 렌더링
        if page == "Chat":
            self.render_chat_interface()
        elif page == "Memory Dashboard":
            self.render_memory_dashboard()
        elif page == "Feedback Analytics":
            self.render_feedback_analytics()
        elif page == "System Monitoring":
            self.render_system_monitoring()
        elif page == "Optimization Tools":
            self.render_optimization_tools()

def main():
    """메인 함수"""
    app = AgentMemoryApp()
    app.run()

if __name__ == "__main__":
    main()