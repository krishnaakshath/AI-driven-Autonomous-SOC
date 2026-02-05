import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.ai_assistant import ai_assistant
from ui.theme import apply_theme

# Page Config
st.set_page_config(
    page_title="CORTEX AI | Autonomous SOC",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_theme()

# Initialize chat history
if "cortex_messages" not in st.session_state:
    st.session_state.cortex_messages = []
    st.session_state.cortex_messages.append({
        "role": "assistant", 
        "content": "CORTEX AI initialized. Neural systems online. All defensive protocols active. How may I assist you, Commander?"
    })

# Premium Full-Page Styling
st.markdown("""
<style>
/* Hide sidebar on this page for immersive experience */
[data-testid="stSidebar"] {
    display: none;
}

/* Full dark immersive background */
.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2a 50%, #0a1a2a 100%);
}

/* Header */
.cortex-hero {
    text-align: center;
    padding: 40px 20px;
    background: linear-gradient(180deg, rgba(0,243,255,0.1) 0%, transparent 100%);
    border-bottom: 1px solid rgba(0,243,255,0.2);
    margin-bottom: 30px;
}

.cortex-logo {
    font-size: 80px;
    margin-bottom: 10px;
    animation: pulse-glow 2s infinite;
}

@keyframes pulse-glow {
    0%, 100% { filter: drop-shadow(0 0 20px rgba(0,243,255,0.5)); }
    50% { filter: drop-shadow(0 0 40px rgba(188,19,254,0.8)); }
}

.cortex-title {
    font-size: 48px;
    font-weight: 800;
    background: linear-gradient(90deg, #00f3ff, #bc13fe, #ff0080);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 8px;
    margin-bottom: 10px;
}

.cortex-subtitle {
    color: #888;
    font-size: 14px;
    letter-spacing: 4px;
    text-transform: uppercase;
}

.cortex-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(0,255,0,0.1);
    border: 1px solid rgba(0,255,0,0.3);
    padding: 8px 20px;
    border-radius: 20px;
    margin-top: 20px;
    color: #0f0;
    font-size: 12px;
    letter-spacing: 2px;
}

.cortex-status::before {
    content: '';
    width: 8px;
    height: 8px;
    background: #0f0;
    border-radius: 50%;
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* Chat Container */
.chat-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Message Bubbles */
.msg-commander {
    background: linear-gradient(135deg, rgba(0,243,255,0.15), rgba(0,102,255,0.1));
    border: 1px solid rgba(0,243,255,0.3);
    border-radius: 16px;
    padding: 16px 20px;
    margin: 15px 0;
    margin-left: 20%;
    animation: slide-in-right 0.3s ease-out;
}

.msg-cortex {
    background: linear-gradient(135deg, rgba(188,19,254,0.15), rgba(255,0,128,0.1));
    border: 1px solid rgba(188,19,254,0.3);
    border-radius: 16px;
    padding: 16px 20px;
    margin: 15px 0;
    margin-right: 20%;
    animation: slide-in-left 0.3s ease-out;
}

@keyframes slide-in-right {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes slide-in-left {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.msg-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 8px;
    text-transform: uppercase;
}

.msg-commander .msg-label { color: #00f3ff; }
.msg-cortex .msg-label { color: #bc13fe; }

.msg-content {
    color: #e8e8e8;
    font-size: 15px;
    line-height: 1.7;
}

/* Back Button */
.back-btn {
    position: fixed;
    top: 20px;
    left: 20px;
    background: rgba(0,243,255,0.1);
    border: 1px solid rgba(0,243,255,0.3);
    color: #00f3ff;
    padding: 10px 20px;
    border-radius: 8px;
    cursor: pointer;
    text-decoration: none;
    font-size: 14px;
    z-index: 1000;
    transition: all 0.3s;
}

.back-btn:hover {
    background: rgba(0,243,255,0.2);
    box-shadow: 0 0 20px rgba(0,243,255,0.3);
}

/* Capabilities Grid */
.capabilities {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    max-width: 900px;
    margin: 30px auto;
    padding: 0 20px;
}

.capability {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 15px;
    text-align: center;
    transition: all 0.3s;
}

.capability:hover {
    background: rgba(0,243,255,0.1);
    border-color: rgba(0,243,255,0.3);
    transform: translateY(-3px);
}

.capability-icon { font-size: 24px; margin-bottom: 8px; }
.capability-text { color: #888; font-size: 11px; letter-spacing: 1px; }
</style>

<a href="/" class="back-btn">← BACK TO SOC</a>

<div class="cortex-hero">
    <div class="cortex-logo">🧠</div>
    <div class="cortex-title">CORTEX</div>
    <div class="cortex-subtitle">Autonomous Security Intelligence</div>
    <div class="cortex-status">NEURAL LINK ACTIVE</div>
</div>

<div class="capabilities">
    <div class="capability">
        <div class="capability-icon">🔍</div>
        <div class="capability-text">SCAN TARGETS</div>
    </div>
    <div class="capability">
        <div class="capability-icon">🛡️</div>
        <div class="capability-text">BLOCK THREATS</div>
    </div>
    <div class="capability">
        <div class="capability-icon">📊</div>
        <div class="capability-text">GENERATE REPORTS</div>
    </div>
    <div class="capability">
        <div class="capability-icon">🌐</div>
        <div class="capability-text">THREAT INTEL</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Chat Messages Display
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state.cortex_messages:
    if msg["role"] == "user":
        st.markdown(f'''
        <div class="msg-commander">
            <div class="msg-label">COMMANDER</div>
            <div class="msg-content">{msg["content"]}</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div class="msg-cortex">
            <div class="msg-label">CORTEX</div>
            <div class="msg-content">{msg["content"]}</div>
        </div>
        ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Chat Input
st.markdown("---")
prompt = st.chat_input("Command CORTEX... (e.g., 'Scan 8.8.8.8', 'Block 10.0.0.1', 'Generate report')")

if prompt:
    st.session_state.cortex_messages.append({"role": "user", "content": prompt})
    
    with st.spinner("⚡ CORTEX processing neural query..."):
        context = {"Page": "CORTEX AI Interface", "Mode": "Direct Command"}
        response = ai_assistant.chat(prompt, system_context=context)
        st.session_state.cortex_messages.append({"role": "assistant", "content": response})
    
    st.rerun()
