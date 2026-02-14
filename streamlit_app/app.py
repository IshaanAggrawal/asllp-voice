"""
Professional Streamlit App with Industry-Level Security
- JWT Authentication with persistence
- User isolation (agents/sessions per user)
- Security headers and session management
- Professional Black & White UI
"""

import streamlit as st
import time
from datetime import datetime
from utils.api import login_user, get_current_user

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Voice Orchestration Platform",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Black & White UI
st.markdown("""
<style>
    /* Professional Monochrome Theme */
    :root {
        --bg-color: #000000;
        --card-bg: #111111;
        --text-primary: #FFFFFF;
        --text-secondary: #888888;
        --accent: #FFFFFF;
        --border: #333333;
    }
    
    /* Global dark theme */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-primary);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Top navigation user badge */
    .user-badge {
        background: var(--card-bg);
        border: 1px solid var(--border);
        padding: 0.5rem 1.5rem;
        border-radius: 4px;
        color: var(--text-primary);
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    /* Minimalist cards */
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 2rem;
        transition: all 0.2s ease;
    }
    
    .glass-card:hover {
        border-color: var(--text-primary);
    }
    
    /* Typography */
    .gradient-text {
        color: var(--text-primary);
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: #000000;
        border: 1px solid var(--border);
        border-radius: 6px;
        color: white;
        padding: 0.75rem 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: white;
        box-shadow: none;
    }
    
    /* Button styling */
    .stButton > button {
        background: white;
        color: black;
        border: 1px solid white;
        border-radius: 6px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background: #dddddd;
        border-color: #dddddd;
        color: black;
        transform: translateY(-1px);
    }
    
    /* Secondary button styling */
    button[kind="secondary"] {
        background: transparent;
        color: white;
        border: 1px solid var(--border);
    }
    
    button[kind="secondary"]:hover {
        border-color: white;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #050505;
        border-right: 1px solid var(--border);
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent;
        border: none;
        color: #888888;
        text-align: left;
        padding-left: 0;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        color: white;
        background: transparent;
    }
    
    /* Success/Error messages */
    .stAlert {
        background: var(--card-bg);
        border: 1px solid var(--border);
        color: white;
    }

    /* Hide default sidebar nav (fallback) */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with persistence check
def init_session_state():
    """Initialize session state and check for persistent auth"""
    defaults = {
        'authenticated': False,
        'access_token': None,
        'refresh_token': None,
        'user_data': None,
        'current_page': 'home',
        'selected_agent': None,
        'selected_session': None,
        'conversation_history': [],
        'last_activity': None,
        'session_timeout': 3600,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
    # Auth Persistence: Check URL query params for token if not authenticated
    if not st.session_state.authenticated:
        try:
            params = st.query_params
            token = params.get("token")
            if token:
                # Verify token
                result = get_current_user(token)
                if result and result.get('success'):
                    st.session_state.authenticated = True
                    st.session_state.access_token = token
                    st.session_state.user_data = result.get('data', {})
                    st.session_state.last_activity = time.time()
        except Exception:
            pass
            
    # Ensure token stays in URL if authenticated (fixes refresh logout issue)
    if st.session_state.authenticated and st.session_state.access_token:
        # Check if token is in params, if not, add it back
        # This prevents the token from disappearing during navigation
        current_token = st.query_params.get("token")
        if current_token != st.session_state.access_token:
            st.query_params["token"] = st.session_state.access_token

# Security: Check session timeout
def check_session_timeout():
    """Check if user session has timed out due to inactivity"""
    if st.session_state.authenticated and st.session_state.last_activity:
        elapsed = time.time() - st.session_state.last_activity
        if elapsed > st.session_state.session_timeout:
            st.warning("⚠️ Session expired due to inactivity. Please login again.")
            logout()
            return True
    
    # Update last activity
    st.session_state.last_activity = time.time()
    return False

# Security: Token validation
def validate_token():
    """Validate JWT token and refresh if needed"""
    if not st.session_state.access_token:
        return False
    
    try:
        # Verify token by making a test API call
        result = get_current_user(st.session_state.access_token)
        if result and result.get('success'):
            st.session_state.user_data = result.get('data', {})
            return True
        return False
    except Exception:
        return False

# Logout function
def logout():
    """Secure logout with session cleanup"""
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_data = None
    st.session_state.selected_agent = None
    st.session_state.selected_session = None
    st.session_state.conversation_history = []
    st.session_state.current_page = 'home'
    st.query_params.clear()

# Professional sidebar with user context
def render_sidebar():
    """Render modern sidebar with user indicator"""

    # Top user indicator with Logout
    if st.session_state.authenticated:
        # Refresh user data to ensure we have the latest name
        # We only do this if we suspect data is stale or on full reruns, 
        # but to be safe and fix the "User" name bug immediately without re-login:
        if 'last_user_fetch' not in st.session_state or (time.time() - st.session_state.get('last_user_fetch', 0) > 300):
             result = get_current_user(st.session_state.access_token)
             if result.get('success'):
                 st.session_state.user_data = result.get('data', {})
                 st.session_state.last_user_fetch = time.time()

        user = st.session_state.user_data
        display_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('username', 'User')
        
        # User Badge (Fixed Top Right)
        st.markdown(f"""
        <div style='position: fixed; top: 1.5rem; right: 2rem; z-index: 9999; display: flex; align-items: center;'>
            <div class='user-badge' style='background: #111; border: 1px solid #333; color: white;'>
                👤 <span style='color: #4ade80;'>{display_name}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.sidebar:
        # App branding
        st.markdown("""
        <div style='padding: 2rem 0; margin-bottom: 2rem;'>
            <div style='font-size: 1.5rem; font-weight: 700; color: white; letter-spacing: -1px;'>Voice Orchestrator</div>
            <div style='font-size: 0.8rem; color: #666; margin-top: 5px;'>ENTERPRISE EDITION</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.authenticated:
            st.markdown("##### MAIN MENU")
            
            if st.button("📊 Dashboard", use_container_width=True, key="nav_dashboard"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            
            if st.button("🤖 My Agents", use_container_width=True, key="nav_agents"):
                st.session_state.current_page = 'agents'
                st.rerun()
            
            if st.button("➕ New Agent", use_container_width=True, key="nav_create"):
                st.session_state.current_page = 'create_agent'
                st.rerun()
            
            if st.button("🎙️ Voice Terminal", use_container_width=True, key="nav_call"):
                st.session_state.current_page = 'call'
                st.rerun()
            
            if st.button("📝 Session Logs", use_container_width=True, key="nav_sessions"):
                st.session_state.current_page = 'sessions'
                st.rerun()
            
            st.divider()
            
            st.divider()
            
            # Logout
            if st.button("Log out", use_container_width=True, key="logout_btn"):
                logout()
                st.rerun()
        
        else:
            # Not authenticated
            st.info("System Locked. Please authenticate.")
            
            if st.button("Login", type="primary", use_container_width=True, key="nav_login"):
                st.session_state.current_page = 'login'
                st.rerun()
            
            if st.button("Register Account", use_container_width=True, key="nav_register"):
                st.session_state.current_page = 'register'
                st.rerun()

# Page routing
def route_page():
    """Route to appropriate page with security checks"""
    # Check session timeout
    if check_session_timeout():
        st.rerun()
        return
    
    page = st.session_state.current_page
    
    # Public pages
    if page in ['home', 'login', 'register']:
        if page == 'home':
            from pages.login import show_home_page
            show_home_page()
        elif page == 'login':
            from pages.login import show_login_page
            show_login_page()
        elif page == 'register':
            from pages.register import show_register_page
            show_register_page()
    
    # Protected pages - require authentication
    elif st.session_state.authenticated:
        # Validate token before accessing protected pages
        if not validate_token():
            st.error("🔒 Authentication expired. Please login again.")
            logout()
            st.rerun()
            return
        
        if page == 'dashboard':
            from pages.dashboard import show_dashboard_page
            show_dashboard_page()
        elif page == 'agents':
            from pages.agents import show_agents_page
            show_agents_page()
        elif page == 'create_agent':
            from pages.create_agent import show_create_agent_page
            show_create_agent_page()
        elif page == 'call':
            from pages.call import show_call_page
            show_call_page()
        elif page == 'sessions':
            from pages.sessions import show_sessions_page
            show_sessions_page()
    
    else:
        # Not authenticated - redirect to login
        st.warning("🔒 Please login to access this page")
        time.sleep(2)
        st.session_state.current_page = 'login'
        st.rerun()

# Main application
def main():
    """Main application entry point"""
    init_session_state()
    render_sidebar()
    route_page()

if __name__ == "__main__":
    main()

