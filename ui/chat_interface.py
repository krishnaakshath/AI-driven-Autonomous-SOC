import streamlit as st
from services.ai_assistant import ai_assistant
import time

def render_chat_interface():
    """
    Renders CORTEX as a floating holographic orb with modal chat interface.
    Premium, modern design - no dropdown/expander.
    """
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "CORTEX online. Ready to assist, Commander."})
    
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False

    # Build chat HTML
    chat_messages_html = ""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            chat_messages_html += f'''
            <div class="cortex-msg cortex-msg-user">
                <div class="msg-label">COMMANDER</div>
                <div class="msg-text">{msg["content"]}</div>
            </div>'''
        else:
            chat_messages_html += f'''
            <div class="cortex-msg cortex-msg-ai">
                <div class="msg-label">CORTEX</div>
                <div class="msg-text">{msg["content"]}</div>
            </div>'''

    # Inject the floating orb and modal using HTML/CSS/JS
    floating_orb_html = f'''
    <style>
    /* ============================================
       CORTEX FLOATING ORB - HOLOGRAPHIC DESIGN
       ============================================ */
    
    /* The Floating Orb Button */
    #cortex-orb {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00f3ff 0%, #bc13fe 50%, #ff0080 100%);
        border: 3px solid rgba(255,255,255,0.3);
        box-shadow: 
            0 0 30px rgba(0, 243, 255, 0.6),
            0 0 60px rgba(188, 19, 254, 0.4),
            inset 0 0 20px rgba(255,255,255,0.2);
        cursor: pointer;
        z-index: 99999;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        animation: orb-pulse 2s ease-in-out infinite, orb-float 3s ease-in-out infinite;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    #cortex-orb:hover {{
        transform: scale(1.15);
        box-shadow: 
            0 0 50px rgba(0, 243, 255, 0.8),
            0 0 100px rgba(188, 19, 254, 0.6),
            inset 0 0 30px rgba(255,255,255,0.3);
    }}
    
    @keyframes orb-pulse {{
        0%, 100% {{ box-shadow: 0 0 30px rgba(0, 243, 255, 0.6), 0 0 60px rgba(188, 19, 254, 0.4); }}
        50% {{ box-shadow: 0 0 50px rgba(0, 243, 255, 0.8), 0 0 80px rgba(188, 19, 254, 0.6); }}
    }}
    
    @keyframes orb-float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-8px); }}
    }}
    
    /* Ring animation around orb */
    #cortex-orb::before {{
        content: '';
        position: absolute;
        width: 90px;
        height: 90px;
        border-radius: 50%;
        border: 2px solid rgba(0, 243, 255, 0.5);
        animation: ring-expand 2s ease-out infinite;
    }}
    
    @keyframes ring-expand {{
        0% {{ transform: scale(0.8); opacity: 1; }}
        100% {{ transform: scale(1.5); opacity: 0; }}
    }}
    
    /* ============================================
       CORTEX CHAT MODAL
       ============================================ */
    
    #cortex-modal {{
        display: none;
        position: fixed;
        bottom: 110px;
        right: 30px;
        width: 380px;
        height: 500px;
        background: linear-gradient(145deg, rgba(15, 15, 35, 0.98), rgba(25, 25, 55, 0.95));
        border: 1px solid rgba(0, 243, 255, 0.3);
        border-radius: 20px;
        box-shadow: 
            0 25px 80px rgba(0, 0, 0, 0.5),
            0 0 40px rgba(0, 243, 255, 0.2),
            inset 0 1px 0 rgba(255,255,255,0.1);
        z-index: 99998;
        overflow: hidden;
        animation: modal-slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(20px);
    }}
    
    #cortex-modal.open {{
        display: flex;
        flex-direction: column;
    }}
    
    @keyframes modal-slide-in {{
        from {{ opacity: 0; transform: translateY(20px) scale(0.95); }}
        to {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    
    /* Modal Header */
    .cortex-header {{
        padding: 15px 20px;
        background: linear-gradient(90deg, rgba(0, 243, 255, 0.1), rgba(188, 19, 254, 0.1));
        border-bottom: 1px solid rgba(0, 243, 255, 0.2);
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .cortex-header-icon {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00f3ff, #bc13fe);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.4);
    }}
    
    .cortex-header-text {{
        flex: 1;
    }}
    
    .cortex-header-title {{
        font-size: 16px;
        font-weight: 700;
        color: #00f3ff;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    
    .cortex-header-status {{
        font-size: 11px;
        color: #0f0;
        display: flex;
        align-items: center;
        gap: 5px;
    }}
    
    .cortex-header-status::before {{
        content: '';
        width: 6px;
        height: 6px;
        background: #0f0;
        border-radius: 50%;
        animation: blink 1s infinite;
    }}
    
    @keyframes blink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.3; }}
    }}
    
    .cortex-close {{
        width: 30px;
        height: 30px;
        border: 1px solid rgba(255, 100, 100, 0.5);
        border-radius: 50%;
        background: transparent;
        color: #ff6b6b;
        cursor: pointer;
        font-size: 16px;
        transition: all 0.2s;
    }}
    
    .cortex-close:hover {{
        background: rgba(255, 100, 100, 0.2);
        transform: rotate(90deg);
    }}
    
    /* Messages Container */
    .cortex-messages {{
        flex: 1;
        overflow-y: auto;
        padding: 15px;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }}
    
    .cortex-messages::-webkit-scrollbar {{
        width: 4px;
    }}
    
    .cortex-messages::-webkit-scrollbar-thumb {{
        background: rgba(0, 243, 255, 0.3);
        border-radius: 2px;
    }}
    
    /* Message Bubbles */
    .cortex-msg {{
        max-width: 85%;
        padding: 10px 14px;
        border-radius: 12px;
        animation: msg-fade-in 0.3s ease-out;
    }}
    
    @keyframes msg-fade-in {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .cortex-msg-user {{
        align-self: flex-end;
        background: linear-gradient(135deg, rgba(0, 243, 255, 0.2), rgba(0, 102, 255, 0.2));
        border: 1px solid rgba(0, 243, 255, 0.3);
    }}
    
    .cortex-msg-ai {{
        align-self: flex-start;
        background: linear-gradient(135deg, rgba(188, 19, 254, 0.2), rgba(255, 0, 128, 0.15));
        border: 1px solid rgba(188, 19, 254, 0.3);
    }}
    
    .msg-label {{
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1.5px;
        margin-bottom: 4px;
        text-transform: uppercase;
    }}
    
    .cortex-msg-user .msg-label {{ color: #00f3ff; }}
    .cortex-msg-ai .msg-label {{ color: #bc13fe; }}
    
    .msg-text {{
        font-size: 13px;
        color: #e0e0e0;
        line-height: 1.5;
    }}
    
    /* Input Area */
    .cortex-input-area {{
        padding: 15px;
        border-top: 1px solid rgba(0, 243, 255, 0.2);
        background: rgba(0, 0, 0, 0.3);
    }}
    
    .cortex-input-hint {{
        font-size: 10px;
        color: #666;
        text-align: center;
        margin-top: 8px;
    }}
    </style>
    
    <!-- The Floating Orb -->
    <div id="cortex-orb" onclick="toggleCortexModal()">
        🤖
    </div>
    
    <!-- The Chat Modal -->
    <div id="cortex-modal">
        <div class="cortex-header">
            <div class="cortex-header-icon">🧠</div>
            <div class="cortex-header-text">
                <div class="cortex-header-title">CORTEX</div>
                <div class="cortex-header-status">NEURAL LINK ACTIVE</div>
            </div>
            <button class="cortex-close" onclick="toggleCortexModal()">✕</button>
        </div>
        <div class="cortex-messages">
            {chat_messages_html}
        </div>
        <div class="cortex-input-area">
            <div class="cortex-input-hint">Use the input below to command CORTEX ↓</div>
        </div>
    </div>
    
    <script>
    function toggleCortexModal() {{
        const modal = document.getElementById('cortex-modal');
        modal.classList.toggle('open');
    }}
    
    // Auto-scroll messages to bottom
    setTimeout(() => {{
        const msgs = document.querySelector('.cortex-messages');
        if (msgs) msgs.scrollTop = msgs.scrollHeight;
    }}, 100);
    </script>
    '''
    
    st.markdown(floating_orb_html, unsafe_allow_html=True)
    
    # Streamlit input (placed after the HTML so it's at the bottom)
    # Using columns to make it more compact
    col1, col2 = st.columns([4, 1])
    with col1:
        prompt = st.chat_input("Command CORTEX...", key="cortex_main_input")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("⚡ CORTEX processing..."):
            context = {"Page": st.session_state.get("current_page", "Unknown")}
            response = ai_assistant.chat(prompt, system_context=context)
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

def inject_chat_floating():
    render_chat_interface()
