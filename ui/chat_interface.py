import streamlit as st
from services.ai_assistant import ai_assistant
import time

def render_chat_interface():
    """
    Renders the AI chat interface as a Floating Orb (Popover).
    """
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Security Operations AI online. Systems nominal."})

    # CSS to transform the Popover Button into a Floating Orb
    st.markdown("""
    <style>
    /* Position the popover container fixed at bottom right */
    [data-testid="stPopover"] {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 9999;
    }

    /* Style the button inside the popover to look like an Orb */
    [data-testid="stPopover"] > button {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #00f3ff, #0066ff);
        border: 2px solid #fff;
        box-shadow: 0 0 20px #00f3ff, 0 0 40px #0066ff;
        color: white;
        font-size: 24px;
        transition: all 0.3s ease;
        overflow: hidden;
    }
    
    /* Hover effect */
    [data-testid="stPopover"] > button:hover {
        transform: scale(1.1) rotate(180deg);
        box-shadow: 0 0 30px #00f3ff, 0 0 60px #0066ff;
        background: radial-gradient(circle at 30% 30%, #fff, #00f3ff);
    }

    /* Pulse animation */
    @keyframes pulse-orb {
        0% { box-shadow: 0 0 20px #00f3ff; }
        50% { box-shadow: 0 0 40px #00f3ff, 0 0 10px white; }
        100% { box-shadow: 0 0 20px #00f3ff; }
    }
    [data-testid="stPopover"] > button {
        animation: pulse-orb 2s infinite;
    }

    /* Message styling inside popover */
    .cortex-msg-user {
        background: rgba(0, 243, 255, 0.1);
        border-right: 2px solid #00f3ff;
        text-align: right;
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 5px;
        font-size: 0.9rem;
    }
    .cortex-msg-ai {
        background: rgba(188, 19, 254, 0.1);
        border-left: 2px solid #bc13fe;
        text-align: left;
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 5px;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # 🤖 FLOATING CORTEX ORB
    # We use st.popover if available (Streamlit 1.34+), else fallback to expander
    try:
        Popover = st.popover
        use_popover = True
    except AttributeError:
        use_popover = False

    if use_popover:
        with st.popover("🤖", help="CORTEX AI"):
            st.markdown("### 🧠 CORTEX AGENT")
            
            # Chat Container
            chat_box = st.container(height=400)
            
            with chat_box:
                for msg in st.session_state.messages:
                    role_class = "cortex-msg-user" if msg["role"] == "user" else "cortex-msg-ai"
                    st.markdown(f'<div class="{role_class}">{msg["content"]}</div>', unsafe_allow_html=True)

            # Input
            prompt = st.chat_input("Command CORTEX...", key="cortex_input_popover")
            
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Processing..."):
                     # Scan page context
                    context = {"Page": st.session_state.get("current_page", "Unknown")}
                    response = ai_assistant.chat(prompt, system_context=context)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

    else:
        # Fallback for older streamlit versions (Still floating via CSS above, but using Expander)
        # We wrap expander in a fixed div
        st.markdown('<div style="position: fixed; bottom: 20px; right: 20px; width: 350px; z-index: 9999;">', unsafe_allow_html=True)
        with st.expander("🤖 CORTEX", expanded=False):
             # Reuse similar logic...
             pass
        st.markdown('</div>', unsafe_allow_html=True)

def inject_chat_floating():
    render_chat_interface()

