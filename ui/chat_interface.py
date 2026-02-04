import streamlit as st
from services.ai_assistant import ai_assistant
import time

def render_chat_interface():
    """
    Renders the AI chat interface in the sidebar or main data area.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### CORTEX AI CORE")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Initial greeting
        st.session_state.messages.append({"role": "assistant", "content": "INITIALIZING CORTEX... SYSTEMS ONLINE. HOW CAN I ASSIST YOU, COMMANDER?"})

    # Chat container in sidebar
    chat_container = st.sidebar.container()
    
    # Display chat messages
    with chat_container:
        # Use a scrollable container for messages if possible, or just list them
        # In sidebar, we print them directly
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.sidebar.markdown(f"""
                <div style="background: rgba(0, 243, 255, 0.1); padding: 8px; border-radius: 4px; margin-bottom: 5px; text-align: right; border-right: 2px solid #00f3ff;">
                    <span style="color: #00f3ff; font-weight: bold;">YOU:</span> <span style="color: #fff;">{message["content"]}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.sidebar.markdown(f"""
                <div style="background: rgba(188, 19, 254, 0.1); padding: 8px; border-radius: 4px; margin-bottom: 5px; border-left: 2px solid #bc13fe;">
                    <span style="color: #bc13fe; font-weight: bold;">CORTEX:</span> <span style="color: #fff;">{message["content"]}</span>
                </div>
                """, unsafe_allow_html=True)

    # Chat input
    # Note: st.chat_input doesn't work well in sidebar in some versions, but let's try standard input first
    # Or use st.chat_input if available (Streamlit > 1.24)
    
    prompt = st.sidebar.chat_input("Enter command...", key="sidebar_chat_input")
    
    if prompt:
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get AI response
        with st.sidebar:
            with st.spinner("PROCESSING..."):
                # Gather simple context
                context = {
                    "Page": st.session_state.get("current_page", "Unknown"),
                    # We could inject more stats here if we had global state management
                }
                response = ai_assistant.chat(prompt, system_context=context)
                
        # Add assistant message to state
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update chat
        st.rerun()

def inject_chat_floating():
    """
    Injects a floating chat button (CSS only) that toggles sidebar.
    """
    # This is handled by Streamlit's native sidebar toggle usually, 
    # but we can style the sidebar to look cool.
    pass
