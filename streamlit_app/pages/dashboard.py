"""
Professional Dashboard with User-Specific Data and Security Context
- Shows only user's own agents and sessions
- Real-time statistics
- Security indicators
- Professional metrics display
"""

import streamlit as st
import time
from datetime import datetime, timezone
from utils.api import list_agents, list_sessions

def show_dashboard_page():
    """Professional dashboard with user isolation"""
    # Safety check: ensure user_data is a dictionary
    if not isinstance(st.session_state.get('user_data'), dict):
        st.error("❌ Session data invalid. Please log in again.")
        if st.button("🔐 Go to Login"):
            st.session_state.current_page = 'login'
            st.rerun()
        return
    
    # Header with user context
    user = st.session_state.user_data
    display_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('username', 'User')
    
    st.markdown(f"""
    <div style='text-align: center; margin: 2rem 0 3rem 0;'>
        <div class='gradient-text'>🏠 Welcome, {display_name}!</div>
        <p style='color: var(--text-secondary); font-size: 1.1rem; margin-top: 0.5rem;'>
            Your personal AI voice orchestration dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    
    st.divider()

    
    # Fetch user-specific data
    with st.spinner("Loading your data..."):
        try:
            agents_result = list_agents(st.session_state.access_token)
            sessions_result = list_sessions(st.session_state.access_token)
            
            # Extract data from API response
            agents = agents_result.get('data', []) if agents_result.get('success') else []
            sessions = sessions_result.get('data', []) if sessions_result.get('success') else []
            
            # Calculate statistics
            total_agents = len(agents) if agents else 0
            total_sessions = len(sessions) if sessions else 0
            active_sessions = len([s for s in sessions if s.get('status') == 'active']) if sessions else 0
            
            # Metrics row with professional styling
            st.subheader("📊 Your Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white;'>
                    <div style='font-size: 2rem; font-weight: 700;'>{total_agents}</div>
                    <div style='opacity: 0.9;'>AI Agents</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white;'>
                    <div style='font-size: 2rem; font-weight: 700;'>{total_sessions}</div>
                    <div style='opacity: 0.9;'>Total Sessions</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white;'>
                    <div style='font-size: 2rem; font-weight: 700;'>{active_sessions}</div>
                    <div style='opacity: 0.9;'>Active Now</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                account_age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(st.session_state.user_data.get('date_joined').replace('Z', '+00:00'))).days if st.session_state.user_data.get('date_joined') else 0
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white;'>
                    <div style='font-size: 2rem; font-weight: 700;'>{account_age_days}</div>
                    <div style='opacity: 0.9;'>Days Active</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Quick Actions
            st.subheader("⚡ Quick Actions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("➕ Create New Agent", use_container_width=True, type="primary"):
                    st.session_state.current_page = 'create_agent'
                    st.rerun()
            
            with col2:
                if st.button("📞 Start Voice Call", use_container_width=True):
                    st.session_state.current_page = 'call'
                    st.rerun()
            
            with col3:
                if st.button("📋 View All Sessions", use_container_width=True):
                    st.session_state.current_page = 'sessions'
                    st.rerun()
            
            st.divider()
            
            # Recent Agents with user isolation indicator
            st.subheader(f"🤖 Your Recent Agents ({total_agents} total)")
            
            if agents and len(agents) > 0:
                # Show up to 3 recent agents
                for agent in agents[:3]:
                    with st.container():
                        st.markdown(f"""
                        <div class='agent-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <div>
                                    <h3 style='margin: 0; color: #4F46E5;'>🤖 {agent['name']}</h3>
                                    <p style='margin: 0.25rem 0; color: #6B7280; font-size: 0.875rem;'>
                                        Model: {agent.get('conversation_model', 'N/A')}
                                    </p>
                                    <p style='margin: 0.25rem 0; color: #6B7280; font-size: 0.875rem;'>
                                        Created: {agent.get('created_at', 'N/A')[:10]}
                                    </p>
                                </div>
                                <div>
                                    <span style='background: #10B981; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'>
                                        🔒 Your Agent
                                    </span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                if total_agents > 3:
                    if st.button(f"View all {total_agents} agents →", use_container_width=True):
                        st.session_state.current_page = 'agents'
                        st.rerun()
            else:
                st.info("No agents yet. Create your first AI agent to get started!")
                if st.button("Create Your First Agent", type="primary"):
                    st.session_state.current_page = 'create_agent'
                    st.rerun()
            
            st.divider()
            
            # Recent Sessions with status indicators
            st.subheader(f"📞 Recent Sessions ({active_sessions} active)")
            
            if sessions and len(sessions) > 0:
                for session in sessions[:3]:
                    status_color = {
                        'active': '#10B981',
                        'ended': '#6B7280',
                        'error': '#EF4444'
                    }
                    
                    status_icon = {
                        'active': '🟢',
                        'ended': '⚫',
                        'error': '🔴'
                    }
                    
                    st.markdown(f"""
                    <div class='agent-card'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <h4 style='margin: 0;'>{status_icon.get(session['status'])} {session.get('agent_name', 'Unknown Agent')}</h4>
                                <p style='margin: 0.25rem 0; color: #6B7280; font-size: 0.875rem;'>
                                    Started: {session.get('started_at', 'N/A')[:19].replace('T', ' ')}
                                </p>
                                <p style='margin: 0.25rem 0; color: #6B7280; font-size: 0.875rem;'>
                                    Turns: {session.get('total_turns', 0)}
                                </p>
                            </div>
                            <div>
                                <span style='background: {status_color.get(session["status"], "#6B7280")}; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'>
                                    {session['status'].upper()}
                                </span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if total_sessions > 3:
                    if st.button(f"View all {total_sessions} sessions →", use_container_width=True):
                        st.session_state.current_page = 'sessions'
                        st.rerun()
            else:
                st.info("No sessions yet. Start a voice call to create your first session!")
        
        except Exception as e:
            st.error(f"❌ Error loading dashboard data: {str(e)}")
            st.info("💡 **Troubleshooting**: Ensure the Django backend is running on port 8000")
    
    st.divider()
    
    # Interview Explanation
    with st.expander("💼 User Isolation & Security (For Interviews)"):
        st.markdown(f"""
        **How User Isolation Works:**
        
        1. **Authentication Layer:**
           ```python
           # JWT token contains user ID
           headers = {{"Authorization": f"Bearer {{access_token}}"}}
           # Backend validates token and extracts user
           ```
        
        2. **Database Query Filtering:**
           ```python
           # Django automatically filters by request.user
           def get_queryset(self):
               return AgentConfiguration.objects.filter(user=self.request.user)
           # User {st.session_state.user_data.get('id')} can ONLY see their own agents
           ```
        
        3. **Foreign Key Constraints:**
           ```sql
           CREATE TABLE agents_agentconfiguration (
               id UUID PRIMARY KEY,
               user_id INTEGER REFERENCES auth_user(id),
               -- ENSURES data isolation at DB level
           );
           ```
        
        4. **API Security:**
           - All endpoints require authentication (`IsAuthenticated`)
           - ViewSets automatically filter by `request.user`
           - No user can access another user's data
           - Even with direct API calls, backend enforces isolation
        
        **Testing User Isolation:**
        1. Create two accounts
        2. Create agents in each account
        3. Verify Account A cannot see Account B's agents
        4. Check database: `SELECT * FROM agents WHERE user_id = {st.session_state.user_data.get('id')}`
        
        **Production Considerations:**
        - Row-level security in PostgreSQL
        - Audit logging for data access
        - Rate limiting per user
        - GDPR compliance for data export/deletion
        """)
