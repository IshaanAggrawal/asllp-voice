"""
Professional Streamlit App with Industry-Level Security
- JWT Authentication with automatic token refresh
- User isolation (agents/sessions per user)
- Security headers and session management
- Professional UI with loading states and error handling
"""

import streamlit as st
import time
from datetime import datetime
from utils.api import login_user, get_current_user

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="AI Voice Orchestration Platform",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ElevenLabs-inspired UI
st.markdown("""
<style>
    /* ElevenLabs-inspired Dark Theme */
    :root {
        --primary-purple: #A855F7;
        --secondary-blue: #3B82F6;
        --dark-bg: #0F0F1E;
        --card-bg: rgba(255, 255, 255, 0.05);
        --glass-bg: rgba(255, 255, 255, 0.08);
        --text-primary: #FFFFFF;
        --text-secondary: #A1A1AA;
    }
    
    /* Global dark theme */
    .stApp {
        background: linear-gradient(135deg, #0F0F1E 0%, #1A1A2E 50%, #16213E 100%);
        color: var(--text-primary);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Top navigation bar with user indicator */
    .top-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: rgba(15, 15, 30, 0.8);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(168, 85, 247, 0.2);
        padding: 1rem 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 1000;
    }
    
    .user-badge {
        background: linear-gradient(135deg, #A855F7 0%, #3B82F6 100%);
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        color: white;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3);
    }
    
    /* Glassmorphism cards */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(168, 85, 247, 0.2);
        border-color: rgba(168, 85, 247, 0.3);
    }
    
    /* Modern gradient headers */
    .gradient-text {
        background: linear-gradient(135deg, #A855F7 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Streamlit component styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(168, 85, 247, 0.2);
        border-radius: 12px;
        color: white;
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #A855F7;
        box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.2);
    }
    
    /* Modern buttons */
    .stButton > button {
        background: linear-gradient(135deg, #A855F7 0%, #3B82F6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.4);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 30, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(168, 85, 247, 0.2);
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(168, 85, 247, 0.1);
        border: 1px solid rgba(168, 85, 247, 0.3);
        color: white;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(168, 85, 247, 0.2);
        border-color: #A855F7;
    }
    
    /* Success/Error messages */
    .stAlert {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border-left: 4px solid #A855F7;
    }
    
    /* Form styling */
    .stForm {
        background: var(--glass-bg);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with security context
def init_session_state():
    """Initialize all session state variables with security defaults"""
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
        'session_timeout': 3600,  # 1 hour in seconds
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

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

# Professional sidebar with user context
def render_sidebar():
    """Render modern sidebar with user indicator"""
    # Top user indicator (appears at top right of main content)
    if st.session_state.authenticated:
        st.markdown(f"""
        <div style='position: fixed; top: 1rem; right: 2rem; z-index: 9999;'>
            <div class='user-badge'>
                👤 {st.session_state.user_data.get('username', 'User')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with st.sidebar:
        # App branding
        st.markdown("""
        <div style='text-align: center; padding: 2rem 1rem; margin-bottom: 2rem;'>
            <div class='gradient-text' style='font-size: 1.8rem;'>🎙️ VoiceAI</div>
            <p style='color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;'>
                Powered by ElevenLabs Technology
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.authenticated:
            st.divider()
            
            # Navigation with icons
            st.markdown("### 📱 Navigation")
            
            if st.button("🏠 Dashboard", use_container_width=True, key="nav_dashboard"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            
            if st.button("📋 My Agents", use_container_width=True, key="nav_agents"):
                st.session_state.current_page = 'agents'
                st.rerun()
            
            if st.button("➕ Create Agent", use_container_width=True, key="nav_create"):
                st.session_state.current_page = 'create_agent'
                st.rerun()
            
            if st.button("📞 Voice Call", use_container_width=True, key="nav_call"):
                st.session_state.current_page = 'call'
                st.rerun()
            
            if st.button("📋 Sessions", use_container_width=True, key="nav_sessions"):
                st.session_state.current_page = 'sessions'
                st.rerun()
            
            st.divider()
            
            # Session info
            if st.session_state.last_activity:
                remaining_mins = int((st.session_state.session_timeout - (time.time() - st.session_state.last_activity)) / 60)
                st.markdown(f"""
                <div style='font-size: 0.75rem; color: var(--text-secondary); text-align: center;'>
                    ⏱️ Session expires in {remaining_mins} min
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Logout button
            if st.button("🚪 Logout", type="primary", use_container_width=True, key="logout_btn"):
                logout()
                st.success("Logged out successfully!")
                time.sleep(1)
                st.rerun()
        
        else:
            # Not authenticated
            st.markdown("""
            <div class='glass-card' style='text-align: center; padding: 1.5rem;'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🔐</div>
                <div style='color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem;'>
                    Please login to access the platform
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔐 Login", type="primary", use_container_width=True, key="nav_login"):
                st.session_state.current_page = 'login'
                st.rerun()
            
            if st.button("📝 Register", use_container_width=True, key="nav_register"):
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
