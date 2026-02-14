"""Create and manage agents page"""
import streamlit as st
from utils import api

def show_create_agent_page():
    st.markdown("<h1 style='text-align: center;'>➕ Create Agent</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    ### 🤖 Custom Agent Builder
    
    Create your own AI voice agent with a unique personality and system prompt.
    """)
    
    with st.form("create_agent_form"):
        st.markdown("#### Agent Configuration")
        
        agent_name = st.text_input(
            "Agent Name *",
            placeholder="e.g., Customer Support Agent, Sales Bot, Technical Assistant",
            help="Give your agent a descriptive name"
        )
        
        system_prompt = st.text_area(
            "System Prompt *",
            placeholder="You are a helpful customer support agent. Be friendly, professional, and concise in your responses. Focus on solving customer problems efficiently.",
            help="Define your agent's personality, role, and behavior guidelines",
            height=200
        )
        
        conversation_model = st.selectbox(
            "Conversational Model",
            options=["llama3.2:1b", "llama3.2:3b", "qwen2.5:1.5b"],
            help="Select the LLM model for generating responses"
        )
        
        st.markdown("---")
        st.markdown("#### 💡 System Prompt Tips")
        st.markdown("""
        - **Role**: Define who the agent is (e.g., "You are a technical support specialist")
        - **Personality**: Specify tone and style (e.g., "Be friendly and empathetic")
        - **Constraints**: Set boundaries (e.g., "Keep responses under 50 words for voice clarity")
        - **Goals**: State the primary objective (e.g., "Help users troubleshoot technical issues")
        """)
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit = st.form_submit_button("🚀 Create Agent", use_container_width=True)
        
        if submit:
            if not agent_name or not system_prompt:
                st.error("❌ Please fill in all required fields")
            else:
                with st.spinner("Creating agent..."):
                    result = api.create_agent(
                        st.session_state.access_token,
                        name=agent_name,
                        system_prompt=system_prompt,
                        conversation_model=conversation_model
                    )
                    
                    if result["success"]:
                        st.success("✅ Agent created successfully!")
                        st.balloons()
                        
                        # Show agent details
                        agent_data = result["data"]
                        st.markdown("---")
                        st.markdown("### 🎉 Your New Agent")
                        st.json(agent_data)
                        
                        # Set flag for navigation
                        st.session_state.agent_just_created = True
                    else:
                        st.error(f"❌ Failed to create agent: {result['error']}")
    
    
    # Navigation button - OUTSIDE the form
    if st.session_state.get('agent_just_created', False):
        st.markdown("---")
        if st.button("🤖 Go to My Agents", type="primary", use_container_width=True):
            st.session_state.current_page = 'agents'
            st.session_state.agent_just_created = False
            st.rerun()
    
    st.markdown("---")
    
    # Example prompts
    st.markdown("### 📋 Example System Prompts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("💼 Customer Support Agent"):
            st.code("""You are a helpful customer support agent for an AI voice platform.

Your role:
- Answer customer questions clearly and concisely
- Be empathetic and professional
- Provide step-by-step solutions
- Keep responses voice-friendly (1-2 sentences)

Guidelines:
- Always greet customers warmly
- Listen actively and confirm understanding
- Offer to escalate complex issues
- End with "Is there anything else I can help with?"
""", language="text")
    
    with col2:
        with st.expander("📞 Sales Assistant"):
            st.code("""You are an enthusiastic sales assistant.

Your role:
- Understand customer needs
- Recommend appropriate products/services
- Handle objections professionally
- Close deals effectively

Guidelines:
- Build rapport quickly
- Ask open-ended questions
- Highlight key benefits
- Keep responses concise for voice
- Never be pushy or aggressive
""", language="text")
