"""Voice call interface page"""
import streamlit as st
from utils import api

def show_call_page():
    # Modern header
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0 3rem 0;'>
        <div class='gradient-text'>📞 Voice Call</div>
        <p style='color: var(--text-secondary); font-size: 1.1rem; margin-top: 0.5rem;'>
            Start an AI voice conversation
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Agent selection
    st.markdown("### Select Agent")
    
    # Fetch agents
    with st.spinner("Loading agents..."):
        result = api.list_agents(st.session_state.access_token)
    
    if not result.get("success"):
        st.error(f"❌ Failed to load agents: {result.get('error', 'Unknown error')}")
        return
    
    agents = result.get("data", [])
    
    if len(agents) == 0:
        st.markdown("""
        <div class='glass-card' style='text-align: center; padding: 2rem;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🤖</div>
            <h3>No Agents Available</h3>
            <p style='color: var(--text-secondary);'>Create an agent first to start a voice call!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➕ Create Agent", type="primary"):
            st.session_state.current_page = 'create_agent'
            st.rerun()
        return
    
    # Check if agent is pre-selected
    if 'selected_agent' in st.session_state and st.session_state.selected_agent:
        selected_agent = st.session_state.selected_agent
    else:
        # Ensure agents is a list
        if not isinstance(agents, list):
            st.error("❌ Invalid agent data received")
            return
            
        agent_options = {f"{a.get('name', 'Unknown')} (ID: {str(a.get('id', 'N/A'))[:8]}...)": a for a in agents}
        selected_key = st.selectbox("Choose an agent", list(agent_options.keys()))
        selected_agent = agent_options[selected_key]
    
    # Display selected agent info
    with st.expander("🤖 Selected Agent Details", expanded=True):
        st.markdown(f"**Name:** {selected_agent['name']}")
        st.markdown(f"**Model:** {selected_agent.get('conversation_model', 'N/A')}")
        st.markdown("**System Prompt:**")
        st.code(selected_agent.get('system_prompt', 'No prompt')[:200] + "...", language="text")
    
    st.markdown("---")
    
    # Session management
    st.markdown("### 🎙️ Voice Session")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start Session", use_container_width=True, type="primary"):
            with st.spinner("Starting session..."):
                session_result = api.start_session(st.session_state.access_token, selected_agent['id'])
                
                if session_result.get("success"):
                    st.session_state.current_session = session_result.get("data", {})
                    st.success("✅ Session started!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to start session: {session_result.get('error', 'Unknown error')}")
    
    with col2:
        if st.session_state.get('current_session'):
            session_id = st.session_state.current_session.get('id', '')
            if st.button("⏹️ End Session", use_container_width=True):
                with st.spinner("Ending session..."):
                    end_result = api.end_session(st.session_state.access_token, session_id)
                    if end_result.get("success"):
                        st.session_state.current_session = None
                        st.success("✅ Session ended!")
                        st.rerun()
    
    # Show active session with production voice interface
    if st.session_state.get('current_session'):
        session = st.session_state.current_session
        session_id = session.get('id', 'N/A')
        
        st.markdown("---")
        st.markdown("### 🟢 Active Session")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Session ID", f"{str(session_id)[:8]}...")
        with col2:
            st.metric("Status", session.get('status', 'UNKNOWN').upper())
        with col3:
            st.metric("Agent", selected_agent['name'])
        
        # Production Voice Call Interface
        st.markdown("---")
        st.markdown("### 🎤 Voice Call Interface")
        
        # Load voice interface HTML
        from components.voice_interface import VOICE_CALL_HTML
        
        # Replace session ID placeholder
        voice_html = VOICE_CALL_HTML.replace("SESSION_ID_PLACEHOLDER", str(session_id))
        
        # Inject agent config (name and system prompt)
        import json
        agent_name_json = json.dumps(selected_agent.get('name', 'Voice Assistant'))
        system_prompt_json = json.dumps(selected_agent.get('system_prompt', 'You are a helpful AI.'))
        
        voice_html = voice_html.replace("AGENT_NAME_PLACEHOLDER", agent_name_json)
        voice_html = voice_html.replace("SYSTEM_PROMPT_PLACEHOLDER", system_prompt_json)
        
        # Render voice interface
        import time
        st.components.v1.html(voice_html, height=700, scrolling=False)
        
        # Instructions
        with st.expander("📖 How to Use the Voice Call", expanded=False):
            st.markdown("""
            ### Quick Start:
            
            1. **Click "🎤 Start Voice Call"** button above
            2. **Allow microphone access** when browser asks
            3. **Speak naturally** into your microphone
            4. **Listen** to AI responses (plays automatically)
            5. **Click "⏹️ End Call"** when finished
            
            ### What's Happening:
            - Your voice → **Deepgram STT** → Text
            - Text → **Dual-LLM Agents** (Qwen + LLaMA) → Response
            - Response → **Cartesia TTS** → Audio
            - Audio plays in browser automatically
            
            ### Technical Stack:
            - **WebSocket**: Real-time bidirectional communication
            - **STT**: Deepgram Nova-2 (speech-to-text)
            - **Orchestrator**: Qwen 1.5B (intent classification)
            - **Responder**: LLaMA 1B (conversation)
            - **TTS**: Cartesia (text-to-speech)
            - **Format**: WebM → PCM → Base64 streaming
            """)
    else:
        st.info("ℹ️ Start a session to begin your voice call")
