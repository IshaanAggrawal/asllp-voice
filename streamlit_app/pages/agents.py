"""Agents management page"""
import streamlit as st
from utils import api

def show_agents_page():
    # Modern header
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0 3rem 0;'>
        <div class='gradient-text'>🤖 My Agents</div>
        <p style='color: var(--text-secondary); font-size: 1.1rem; margin-top: 0.5rem;'>
            Manage your AI voice agents
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch agents with proper error handling
    with st.spinner("Loading agents..."):
        result = api.list_agents(st.session_state.access_token)
    
    # Handle API response
    if not result.get("success"):
        st.error(f"❌ Failed to load agents: {result.get('error', 'Unknown error')}")
        return
    
    agents = result.get("data", [])
    
    if len(agents) == 0:
        st.markdown("""
        <div class='glass-card' style='text-align: center; padding: 2rem;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🤖</div>
            <h3>No Agents Yet</h3>
            <p style='color: var(--text-secondary);'>Create your first AI voice agent to get started!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➕ Create Your First Agent", use_container_width=True, type="primary"):
            st.session_state.current_page = 'create_agent'
            st.rerun()
        return
    
    # Stats bar
    st.markdown(f"""
    <div class='glass-card' style='padding: 1rem; margin-bottom: 2rem; text-align: center;'>
        <strong>{len(agents)}</strong> Total Agents
    </div>
    """, unsafe_allow_html=True)
    
    # Search
    search = st.text_input("🔍 Search agents", placeholder="Search by name...", label_visibility="collapsed")
    
    # Filter agents by search
    if search:
        agents = [a for a in agents if isinstance(a, dict) and search.lower() in a.get('name', '').lower()]
    
    # Debug: Check what type agents contains
    if agents and not isinstance(agents[0], dict):
        st.error(f"❌ Invalid agent data format. Expected dict, got {type(agents[0])}")
        st.code(f"First agent data: {agents[0]}")
        return
    
    # Display agents
    for agent in agents:
        # Safety check
        if not isinstance(agent, dict):
            continue
            
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### 🤖 {agent.get('name', 'Unnamed Agent')}")
                st.caption(f"ID: `{agent.get('id', 'N/A')}`")
            
            with col2:
                if st.button("📞 Call", key=f"call_{agent['id']}", use_container_width=True):
                    st.session_state.selected_agent = agent
                    st.session_state.current_page = 'call'
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{agent['id']}", use_container_width=True):
                    if st.session_state.get(f"confirm_delete_{agent['id']}", False):
                        # Actually delete
                        with st.spinner("Deleting..."):
                            delete_result = api.delete_agent(st.session_state.access_token, agent['id'])
                            if delete_result["success"]:
                                st.success("Agent deleted!")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete: {delete_result['error']}")
                    else:
                        # Ask for confirmation
                        st.session_state[f"confirm_delete_{agent['id']}"] = True
                        st.warning("Click again to confirm deletion")
            
            # Agent details
            with st.expander("View Details"):
                st.markdown(f"**Model:** {agent.get('conversation_model', 'N/A')}")
                st.markdown(f"**Created:** {agent.get('created_at', 'N/A')}")
                st.markdown("**System Prompt:**")
                st.code(agent.get('system_prompt', 'No system prompt'), language="text")
                
                # Edit functionality
                st.markdown("---")
                st.markdown("#### ✏️ Edit Agent")
                
                with st.form(key=f"edit_form_{agent['id']}"):
                    new_name = st.text_input("Name", value=agent.get('name', ''))
                    new_prompt = st.text_area("System Prompt", value=agent.get('system_prompt', ''), height=150)
                    
                    if st.form_submit_button("💾 Save Changes"):
                        update_data = {}
                        if new_name != agent.get('name'):
                            update_data['name'] = new_name
                        if new_prompt != agent.get('system_prompt'):
                            update_data['system_prompt'] = new_prompt
                        
                        if update_data:
                            with st.spinner("Updating..."):
                                update_result = api.update_agent(
                                    st.session_state.access_token,
                                    agent['id'],
                                    **update_data
                                )
                                if update_result["success"]:
                                    st.success("✅ Agent updated!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Update failed: {update_result['error']}")
                        else:
                            st.info("No changes detected")
            
            st.markdown("---")
