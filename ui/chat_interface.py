import streamlit as st
from services.ai_assistant import ai_assistant
import time

def render_chat_interface():
    """
    Renders the AI chat interface in the sidebar or main data area.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### CORTEX AI")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Initial greeting
        st.session_state.messages.append({"role": "assistant", "content": "Security Operations AI online. Systems nominal. How can I assist with your threat analysis today?"})

    # Chat container in sidebar
    chat_container = st.sidebar.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.sidebar.markdown(f"""
                <div style="
                    background: rgba(0, 243, 255, 0.05); 
                    padding: 10px; 
                    border-radius: 4px; 
                    margin-bottom: 8px; 
                    text-align: right; 
                    border-right: 2px solid #00f3ff;
                ">
                    <div style="color: #00f3ff; font-size: 0.7rem; margin-bottom: 2px;">COMMANDER</div>
                    <span style="color: #eee;">{message["content"]}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.sidebar.markdown(f"""
                <div style="
                    background: rgba(188, 19, 254, 0.05); 
                    padding: 10px; 
                    border-radius: 4px; 
                    margin-bottom: 8px; 
                    border-left: 2px solid #bc13fe;
                ">
                    <div style="color: #bc13fe; font-size: 0.7rem; margin-bottom: 2px;">CORTEX CORE</div>
                    <span style="color: #eee;">{message["content"]}</span>
                </div>
                """, unsafe_allow_html=True)

    # Chat input
    prompt = st.sidebar.chat_input("Input command...", key="sidebar_chat_input")
    
    if prompt:
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get AI response
        with st.sidebar:
            with st.spinner("⚡ CORTEX ANALYZING..."):
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
