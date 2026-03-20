import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.ai_assistant import ai_assistant

# Page Config
try:
    st.set_page_config(
        page_title="CORTEX AI | Autonomous SOC",
        page_icon="",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

# Initialize chat history and boot sequence
if "cortex_messages" not in st.session_state:
    # Audio hook (played once per session)
    st.markdown('''
        <audio autoplay>
            <source src="https://actions.google.com/sounds/v1/science_fiction/sci_fi_computer_processing.ogg" type="audio/ogg">
        </audio>
    ''', unsafe_allow_html=True)
    
    # Visual Boot Sequence
    boot_container = st.empty()
    boot_text = ""
    for step in [
        "[SYS] Initiating neural pathways...",
        "[SYS] Loading threat intelligence matrices...",
        "[SYS] Calibrating heuristic anomaly models...",
        "[SYS] Establishing direct SOAR uplink...",
        "[SYS] CORTEX AI Online."
    ]:
        boot_text += f"<span style='opacity: 0.8;'>{step}</span><br>"
        boot_container.markdown(f"""
        <div style="background: rgba(10,10,15,0.9); padding: 2.5rem; border: 1px solid rgba(0,243,255,0.3); border-left: 4px solid #00f3ff; border-radius: 8px; font-family: 'Share Tech Mono', monospace; color: #00f3ff; min-height: 250px; box-shadow: 0 0 30px rgba(0,243,255,0.1); margin: 2rem auto; max-width: 800px;">
            <div style="font-size: 1.2rem; margin-bottom: 1.5rem; color: #bc13fe; letter-spacing: 2px;">// CORTEX SYSTEM BOOT //</div>
            <div style="line-height: 1.8; font-size: 1.05rem;">
                {boot_text}
            </div>
            <div style="width: 12px; height: 18px; background: #00f3ff; display: inline-block; animation: pulse 1s infinite alternate; margin-top: 5px;"></div>
        </div>
        """, unsafe_allow_html=True)
        import time
        time.sleep(0.5)
    
    boot_container.empty()
    
    st.session_state.cortex_messages = []
    st.session_state.cortex_messages.append({
        "role": "assistant", 
        "content": "CORTEX AI initialized. Neural systems online. All defensive protocols active. How may I assist you, Commander?"
    })

# Premium Full-Page Styling
# --- PREMIUM THEME INJECTION ---
from ui.theme import CYBERPUNK_CSS, inject_particles, status_indicator
from ui.page_layout import init_page, kpi_row, content_section, section_gap, page_footer, show_empty, show_error
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown("""
<style>
    .chat-container {
        max-width: 1000px;
        margin: 0 auto;
        padding-bottom: 100px;
    }
    
    .msg-box {
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 4px;
        position: relative;
        overflow: hidden;
    }
    
    .msg-commander {
        background: rgba(0, 243, 255, 0.05);
        border-left: 3px solid var(--neon-cyan);
        margin-left: 10%;
    }
    
    .msg-cortex {
        background: rgba(188, 19, 254, 0.05);
        border-left: 3px solid var(--neon-purple);
        margin-right: 10%;
    }
    
    .msg-label {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.7rem;
        letter-spacing: 2px;
        margin-bottom: 0.8rem;
        opacity: 0.7;
    }
    
    .msg-content {
        font-family: 'Share Tech Mono', monospace;
        font-size: 1rem;
        line-height: 1.6;
        color: #f0f0f0;
    }

    /* Terminal-style scanline overlay for CORTEX messages */
    .msg-cortex::after {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%);
        background-size: 100% 4px;
        pointer-events: none;
        opacity: 0.1;
    }
</style>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    html_content = f"""
<div style="text-align: center; padding: 2.5rem 0;">
    <div style="font-size: 4rem; margin-bottom: 1rem; filter: drop-shadow(0 0 20px rgba(0,243,255,0.3));">🧠</div>
    <h1 style="font-family: 'Orbitron', sans-serif; letter-spacing: 12px; margin: 0; background: linear-gradient(90deg, #00f3ff, #bc13fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">CORTEX</h1>
    <p style="font-family: 'Share Tech Mono', monospace; color: #666; letter-spacing: 4px; text-transform: uppercase;">// NEURAL-LINK INTERFACE V2.4.9 //</p>
    <div style="display: flex; justify-content: center; margin-top: 1rem;">
        {status_indicator('online')}
    </div>
</div>
"""
    st.markdown(html_content, unsafe_allow_html=True)

st.markdown("---")

# Chat Messages Display
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.cortex_messages):
    if msg["role"] == "user":
        st.markdown(f'''
        <div class="msg-box msg-commander">
            <div class="msg-label" style="color: var(--neon-cyan);">COMMANDER</div>
            <div class="msg-content">{msg["content"]}</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div class="msg-box msg-cortex">
            <div class="msg-label" style="color: var(--neon-purple);">CORTEX AI</div>
            <div class="msg-content">{msg["content"]}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Action Execution capability for AI recommendations
        msg_text = str(msg["content"]).lower()
        if "block" in msg_text or "isolate" in msg_text or "firewall" in msg_text:
            key_id = f"execute_{i}"
            is_executed = st.session_state.get(key_id, False)
            
            c_exec_1, c_exec_2 = st.columns([8, 2])
            with c_exec_2:
                if is_executed:
                    st.button("✅ Action Executed", disabled=True, use_container_width=True, key=f"btn_{key_id}")
                else:
                    if st.button("🚀 Execute Recommended Action", type="primary", use_container_width=True, key=f"btn_{key_id}"):
                        st.session_state[key_id] = True
                        st.toast("CORTEX: Action executed successfully via SOAR integration.", icon="✅")
                        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Chat Input
st.markdown("---")
prompt = st.chat_input("Command CORTEX... (e.g., 'Scan 8.8.8.8', 'Block 10.0.0.1', 'Generate report')")

# Suggested prompt buttons
if len(st.session_state.cortex_messages) <= 1:
    st.markdown("##### 💡 Suggested Commands")
    sp1, sp2, sp3 = st.columns(3)
    with sp1:
        if st.button("🔍 Latest critical threats", use_container_width=True, key="sp1"):
            prompt = "What are the latest critical threats in the SIEM?"
    with sp2:
        if st.button("📊 Security posture summary", use_container_width=True, key="sp2"):
            prompt = "Give me a summary of our current security posture"
    with sp3:
        if st.button("🛡️ Suggest a playbook", use_container_width=True, key="sp3"):
            prompt = "Suggest a response playbook for SQL Injection attacks"

if prompt:
    st.session_state.cortex_messages.append({"role": "user", "content": prompt})
    
    with st.spinner(" CORTEX processing neural query..."):
        context = {"Page": "CORTEX AI Interface", "Mode": "Direct Command"}
        response = ai_assistant.chat(prompt, system_context=context)
        st.session_state.cortex_messages.append({"role": "assistant", "content": response})
    
    st.rerun()

