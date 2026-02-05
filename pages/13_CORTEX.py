import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.ai_assistant import ai_assistant

# Page Config
st.set_page_config(
    page_title="CORTEX AI | Autonomous SOC",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, .stTextInput input, .stButton button {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Full dark immersive background */
.stApp {
    background: linear-gradient(135deg, #0a0e17 0%, #151c2c 50%, #0d1320 100%);
}

/* Header */
.cortex-hero {
    text-align: center;
    padding: 30px 20px;
    background: linear-gradient(180deg, rgba(0,243,255,0.1) 0%, transparent 100%);
    border-bottom: 1px solid rgba(0,243,255,0.2);
    margin-bottom: 20px;
}

.cortex-logo {
    font-size: 60px;
    margin-bottom: 10px;
    animation: pulse-glow 2s infinite;
}

@keyframes pulse-glow {
    0%, 100% { filter: drop-shadow(0 0 20px rgba(0,243,255,0.5)); }
    50% { filter: drop-shadow(0 0 40px rgba(188,19,254,0.8)); }
}

.cortex-title {
    font-size: 42px;
    font-weight: 800;
    background: linear-gradient(90deg, #00f3ff, #bc13fe, #ff0080);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 8px;
    margin-bottom: 10px;
}

.cortex-subtitle {
    color: #888;
    font-size: 12px;
    letter-spacing: 4px;
    text-transform: uppercase;
}

.cortex-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(0,255,0,0.1);
    border: 1px solid rgba(0,255,0,0.3);
    padding: 6px 16px;
    border-radius: 20px;
    margin-top: 15px;
    color: #0f0;
    font-size: 11px;
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

/* Capabilities Grid */
.capabilities {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    max-width: 900px;
    margin: 20px auto;
    padding: 0 20px;
}

.capability {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 12px;
    text-align: center;
    transition: all 0.3s;
}

.capability:hover {
    background: rgba(0,243,255,0.1);
    border-color: rgba(0,243,255,0.3);
    transform: translateY(-3px);
}

.capability-icon { font-size: 20px; margin-bottom: 6px; }
.capability-text { color: #888; font-size: 10px; letter-spacing: 1px; }

/* Voice button styling */
.voice-btn {
    background: linear-gradient(135deg, #ff0080, #bc13fe) !important;
    animation: voice-pulse 1.5s infinite;
}

@keyframes voice-pulse {
    0%, 100% { box-shadow: 0 0 10px rgba(255,0,128,0.3); }
    50% { box-shadow: 0 0 25px rgba(188,19,254,0.6); }
}

/* File upload styling */
.file-upload-zone {
    background: rgba(0,0,0,0.3);
    border: 2px dashed rgba(0,243,255,0.3);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin: 15px 0;
    transition: all 0.3s;
}

.file-upload-zone:hover {
    border-color: #00f3ff;
    background: rgba(0,243,255,0.05);
}
</style>

<div class="cortex-hero">
    <div class="cortex-logo">🧠</div>
    <div class="cortex-title">CORTEX</div>
    <div class="cortex-subtitle">Autonomous Security Intelligence</div>
    <div class="cortex-status">NEURAL LINK ACTIVE</div>
</div>

<div class="capabilities">
    <div class="capability">
        <div class="capability-icon">🔍</div>
        <div class="capability-text">SCAN</div>
    </div>
    <div class="capability">
        <div class="capability-icon">🛡️</div>
        <div class="capability-text">DEFEND</div>
    </div>
    <div class="capability">
        <div class="capability-icon">📊</div>
        <div class="capability-text">REPORT</div>
    </div>
    <div class="capability">
        <div class="capability-icon">🧪</div>
        <div class="capability-text">ANALYZE</div>
    </div>
    <div class="capability">
        <div class="capability-icon">🎤</div>
        <div class="capability-text">VOICE</div>
    </div>
</div>
""", unsafe_allow_html=True)

# File Upload Section
with st.expander("📁 **Upload File for Analysis** - Check files for malware"):
    uploaded_file = st.file_uploader(
        "Drop any file to scan for malware",
        type=["exe", "dll", "ps1", "bat", "vbs", "js", "doc", "docx", "xls", "xlsx", "pdf", "zip", "rar", "py", "sh", "txt", "json", "xml", "csv"],
        help="CORTEX will analyze this file using the sandbox and provide a detailed verdict"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**File:** `{uploaded_file.name}` ({uploaded_file.size:,} bytes)")
        
        with col2:
            if st.button("🔬 Analyze with CORTEX", type="primary", use_container_width=True):
                with st.spinner("🧪 Detonating in sandbox..."):
                    try:
                        from services.sandbox_service import analyze_file
                        import time
                        time.sleep(1.5)  # Simulate analysis
                        
                        content = uploaded_file.read()
                        result = analyze_file(content, uploaded_file.name)
                        
                        # Create detailed analysis message
                        verdict_emoji = {"MALICIOUS": "🔴", "SUSPICIOUS": "🟠", "CLEAN": "🟢"}.get(result["verdict"], "⚪")
                        
                        analysis_report = f"""
**{verdict_emoji} FILE ANALYSIS COMPLETE**

**File:** `{result['filename']}`
**Verdict:** **{result['verdict']}** ({result['severity']} Severity)
**Analysis Time:** {result['analysis_time']}s

**🔑 Hashes:**
- MD5: `{result['hashes']['md5']}`
- SHA256: `{result['hashes']['sha256'][:32]}...`

**📊 Behavioral Analysis:**
- Processes Spawned: {len(result['behavior']['processes_spawned'])}
- Files Modified: {result['behavior']['files_modified']}
- Network Connections: {len(result['behavior']['network_connections'])}

"""
                        if result['behavior']['processes_spawned']:
                            analysis_report += f"**⚠️ Suspicious Processes:** {', '.join(result['behavior']['processes_spawned'])}\n\n"
                        
                        if result['behavior']['network_connections']:
                            analysis_report += "**🌐 C2 Connections:**\n"
                            for conn in result['behavior']['network_connections']:
                                analysis_report += f"- `{conn['ip']}:{conn['port']}` ({conn['type']})\n"
                        
                        if result['mitre_techniques']:
                            analysis_report += "\n**⚔️ MITRE ATT&CK:**\n"
                            for tech in result['mitre_techniques']:
                                analysis_report += f"- {tech['id']}: {tech['name']}\n"
                        
                        if result['verdict'] == "MALICIOUS":
                            analysis_report += "\n**🛡️ Recommended Actions:**\n1. Quarantine this file immediately\n2. Do not execute under any circumstances\n3. Scan affected systems for similar files\n4. Report to threat intelligence"
                        elif result['verdict'] == "SUSPICIOUS":
                            analysis_report += "\n**⚠️ Recommendations:**\n1. Exercise caution with this file\n2. Run additional analysis before execution\n3. Monitor system if already executed"
                        else:
                            analysis_report += "\n**✅ File appears safe.** However, always exercise caution with unknown files."
                        
                        st.session_state.cortex_messages.append({"role": "user", "content": f"Analyze file: {uploaded_file.name}"})
                        st.session_state.cortex_messages.append({"role": "assistant", "content": analysis_report})
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

# Voice Commands Section
with st.expander("🎤 **Voice Commands** - Speak to CORTEX"):
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <p style="color: #888; font-size: 0.9rem;">Click the button below and speak your command.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # JavaScript for voice recognition
        st.markdown("""
        <script>
        function startVoice() {
            if ('webkitSpeechRecognition' in window) {
                const recognition = new webkitSpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';
                
                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    // Update Streamlit session state
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: transcript}, '*');
                };
                
                recognition.start();
            } else {
                alert('Voice recognition not supported in this browser. Try Chrome.');
            }
        }
        </script>
        """, unsafe_allow_html=True)
        
        if st.button("🎤 Start Voice Command", type="primary", use_container_width=True):
            st.markdown("""
            <div style="
                background: rgba(255,0,128,0.1);
                border: 1px solid #ff0080;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                margin-top: 10px;
            ">
                <div style="color: #ff0080; font-size: 0.9rem;">🎤 Listening...</div>
                <div style="color: #888; font-size: 0.8rem; margin-top: 5px;">Speak: "Scan IP 8.8.8.8" or "Block threat"</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**Example Voice Commands:**")
    voice_examples = [
        "Scan IP address 192.168.1.1",
        "Block malicious IP 10.0.0.5",
        "Generate threat report",
        "Check reputation of suspicious.com",
        "Analyze file for malware",
        "Show active threats"
    ]
    cols = st.columns(3)
    for i, example in enumerate(voice_examples):
        with cols[i % 3]:
            if st.button(f"📢 {example}", key=f"voice_{i}", use_container_width=True):
                st.session_state.cortex_messages.append({"role": "user", "content": example})
                with st.spinner("⚡ Processing..."):
                    response = ai_assistant.chat(example, system_context={"Page": "CORTEX AI", "Mode": "Voice Command"})
                    st.session_state.cortex_messages.append({"role": "assistant", "content": response})
                st.rerun()

st.markdown("---")

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
