import streamlit as st
from services.ai_assistant import ai_assistant
import streamlit.components.v1 as components

def render_chat_interface():
    """
    Renders CORTEX as a floating holographic orb with expandable chat.
    Uses st.popover for reliable interaction + custom styling for premium look.
    """
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "CORTEX online. Neural link established. How may I assist you, Commander?"})

    # Premium CSS styling
    st.markdown("""
    <style>
    /* ============================================
       CORTEX FLOATING ORB STYLING
       ============================================ */
    
    /* Target the popover trigger button */
    [data-testid="stPopover"] {
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        z-index: 99999 !important;
    }
    
    /* Style the popover button as a glowing orb */
    [data-testid="stPopover"] > div > button {
        width: 70px !important;
        height: 70px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #00f3ff 0%, #bc13fe 50%, #ff0080 100%) !important;
        border: 3px solid rgba(255,255,255,0.4) !important;
        box-shadow: 
            0 0 30px rgba(0, 243, 255, 0.6),
            0 0 60px rgba(188, 19, 254, 0.4),
            inset 0 0 20px rgba(255,255,255,0.2) !important;
        font-size: 32px !important;
        padding: 0 !important;
        min-height: unset !important;
        animation: orb-glow 2s ease-in-out infinite !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stPopover"] > div > button:hover {
        transform: scale(1.1) !important;
        box-shadow: 
            0 0 50px rgba(0, 243, 255, 0.9),
            0 0 100px rgba(188, 19, 254, 0.7) !important;
    }
    
    [data-testid="stPopover"] > div > button p {
        margin: 0 !important;
        font-size: 28px !important;
    }
    
    @keyframes orb-glow {
        0%, 100% { 
            box-shadow: 0 0 30px rgba(0, 243, 255, 0.6), 0 0 60px rgba(188, 19, 254, 0.4);
        }
        50% { 
            box-shadow: 0 0 50px rgba(0, 243, 255, 0.9), 0 0 80px rgba(188, 19, 254, 0.6);
        }
    }
    
    /* Style the popover content */
    [data-testid="stPopoverBody"] {
        background: linear-gradient(145deg, rgba(10, 10, 25, 0.98), rgba(20, 20, 45, 0.95)) !important;
        border: 1px solid rgba(0, 243, 255, 0.3) !important;
        border-radius: 16px !important;
        box-shadow: 
            0 25px 80px rgba(0, 0, 0, 0.6),
            0 0 40px rgba(0, 243, 255, 0.2) !important;
        backdrop-filter: blur(20px) !important;
        min-width: 380px !important;
        max-width: 420px !important;
    }
    
    /* Chat message styling */
    .cortex-header {
        background: linear-gradient(90deg, rgba(0, 243, 255, 0.15), rgba(188, 19, 254, 0.15));
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 15px;
        border: 1px solid rgba(0, 243, 255, 0.2);
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .cortex-icon {
        font-size: 28px;
        background: linear-gradient(135deg, #00f3ff, #bc13fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .cortex-title {
        font-size: 16px;
        font-weight: 700;
        color: #00f3ff;
        letter-spacing: 3px;
        text-transform: uppercase;
    }
    
    .cortex-status {
        font-size: 10px;
        color: #0f0;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .cortex-status::before {
        content: '';
        width: 6px;
        height: 6px;
        background: #0f0;
        border-radius: 50%;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    
    .msg-user {
        background: linear-gradient(135deg, rgba(0, 243, 255, 0.15), rgba(0, 102, 255, 0.1));
        border: 1px solid rgba(0, 243, 255, 0.25);
        border-radius: 12px;
        padding: 10px 14px;
        margin: 8px 0;
        margin-left: 15%;
        text-align: right;
    }
    
    .msg-ai {
        background: linear-gradient(135deg, rgba(188, 19, 254, 0.15), rgba(255, 0, 128, 0.1));
        border: 1px solid rgba(188, 19, 254, 0.25);
        border-radius: 12px;
        padding: 10px 14px;
        margin: 8px 0;
        margin-right: 15%;
    }
    
    .msg-label {
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1.5px;
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    
    .msg-user .msg-label { color: #00f3ff; }
    .msg-ai .msg-label { color: #bc13fe; }
    
    .msg-text {
        font-size: 13px;
        color: #e8e8e8;
        line-height: 1.5;
    }
    
    /* Hide default popover arrow */
    [data-testid="stPopoverBody"]::before {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 🤖 FLOATING CORTEX ORB using st.popover
    with st.popover("🤖"):
        # Header
        st.markdown("""
        <div class="cortex-header">
            <span class="cortex-icon">🧠</span>
            <div>
                <div class="cortex-title">CORTEX</div>
                <div class="cortex-status">NEURAL LINK ACTIVE</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat Container with scroll
        chat_container = st.container(height=350)
        
        with chat_container:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f'''
                    <div class="msg-user">
                        <div class="msg-label">COMMANDER</div>
                        <div class="msg-text">{msg["content"]}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div class="msg-ai">
                        <div class="msg-label">CORTEX</div>
                        <div class="msg-text">{msg["content"]}</div>
                    </div>
                    ''', unsafe_allow_html=True)
        
        # Input
        st.markdown("---")
        prompt = st.chat_input("Command CORTEX...", key="cortex_popover_input")
        
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("⚡ Processing..."):
                context = {"Page": st.session_state.get("current_page", "Unknown")}
                response = ai_assistant.chat(prompt, system_context=context)
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

def inject_chat_floating():
    render_chat_interface()
