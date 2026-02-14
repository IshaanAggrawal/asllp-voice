"""Sessions management page"""
import streamlit as st
from utils import api
import pandas as pd

def show_sessions_page():
    st.markdown("<h1 style='text-align: center;'>📊 Sessions</h1>", unsafe_allow_html=True)
    
    # Fetch sessions
    with st.spinner("Loading sessions..."):
        result = api.list_sessions(st.session_state.access_token)
    
    if not result["success"]:
        st.error(f"Failed to load sessions: {result['error']}")
        return
    
    sessions = result["data"]
    
    if len(sessions) == 0:
        st.info("No sessions yet. Start a voice call to create a session!")
        if st.button("📞 Start Voice Call"):
            st.session_state.current_page = 'call'
            st.rerun()
        return
    
    # Stats
    st.markdown("### 📈 Session Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Sessions", len(sessions))
    
    with col2:
        active_count = len([s for s in sessions if s.get('status') == 'active'])
        st.metric("Active Sessions", active_count)
    
    with col3:
        ended_count = len([s for s in sessions if s.get('status') == 'ended'])
        st.metric("Ended Sessions", ended_count)
    
    st.markdown("---")
    
    # Filter
    status_filter = st.selectbox("Filter by status", ["All", "Active", "Ended"])
    
    # Apply filter
    filtered_sessions = sessions
    if status_filter == "Active":
        filtered_sessions = [s for s in sessions if s.get('status') == 'active']
    elif status_filter == "Ended":
        filtered_sessions = [s for s in sessions if s.get('status') == 'ended']
    
    st.markdown(f"### Showing {len(filtered_sessions)} sessions")
    
    # Display sessions
    for session in filtered_sessions:
        status_emoji = "🟢" if session.get('status') == 'active' else "⚪"
        
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"{status_emoji} **Session:** `{session.get('id', 'N/A')[:16]}...`")
                st.caption(f"Agent: {session.get('agent_name', 'N/A')} | Started: {session.get('started_at', 'N/A')}")
            
            with col2:
                if session.get('status') == 'active':
                    if st.button("⏹️ End", key=f"end_{session['id']}", use_container_width=True):
                        with st.spinner("Ending session..."):
                            end_result = api.end_session(st.session_state.access_token, session['id'])
                            if end_result["success"]:
                                st.success("Session ended")
                                st.rerun()
                            else:
                                st.error(f"Failed: {end_result['error']}")
            
            with col3:
                if st.button("📋 Logs", key=f"logs_{session['id']}", use_container_width=True):
                    st.session_state.selected_session_logs = session['id']
            
            # Show logs if selected
            if st.session_state.get('selected_session_logs') == session['id']:
                with st.expander("📋 Session Logs", expanded=True):
                    with st.spinner("Loading logs..."):
                        logs_result = api.get_session_logs(st.session_state.access_token, session['id'])
                    
                    if logs_result["success"]:
                        logs = logs_result["data"]
                        if logs:
                            st.markdown("##### 📜 Conversation History")
                            for log in logs:
                                is_user = log.get('speaker') == 'user'
                                align = "flex-end" if is_user else "flex-start"
                                bg = "#1a1a1a" if is_user else "#000000"
                                border = "1px solid #333" if is_user else "1px solid #222"
                                
                                st.markdown(f"""
                                <div style='display: flex; justify-content: {align}; margin-bottom: 0.5rem;'>
                                    <div style='background: {bg}; border: {border}; padding: 0.8rem; border-radius: 8px; max-width: 80%;'>
                                        <div style='font-size: 0.75rem; color: #666; margin-bottom: 0.2rem;'>
                                            {log.get('speaker', '').upper()} • {log.get('timestamp', '')[11:19]}
                                        </div>
                                        <div style='color: #eee;'>{log.get('transcript', '')}</div>
                                        {f"<div style='font-size: 0.7rem; color: #444; margin-top: 5px; border-top: 1px solid #222; padding-top: 3px;'>Latency: {log.get('latency_ms')}ms</div>" if log.get('latency_ms') else ""}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No logs available for this session")
                    else:
                        st.error(f"Failed to load logs: {logs_result['error']}")
                    
                    if st.button("Close Logs", key=f"close_logs_{session['id']}"):
                        del st.session_state.selected_session_logs
                        st.rerun()
            
            # Session details
            with st.expander("View Details"):
                st.markdown(f"**Session ID:** `{session.get('id', 'N/A')}`")
                st.markdown(f"**Agent ID:** `{session.get('agent', 'N/A')}`")
                st.markdown(f"**Agent Name:** {session.get('agent_name', 'N/A')}")
                st.markdown(f"**Status:** {session.get('status', 'N/A')}")
                st.markdown(f"**Started At:** {session.get('started_at', 'N/A')}")
                st.markdown(f"**Ended At:** {session.get('ended_at', 'Not yet' if session.get('status') == 'active' else 'N/A')}")
            
            st.markdown("---")
