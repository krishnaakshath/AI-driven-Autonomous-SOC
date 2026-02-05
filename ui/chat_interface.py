import streamlit as st
from services.ai_assistant import ai_assistant
import time

def render_chat_interface():
    """
    Renders the AI chat interface in the sidebar or main data area.
    """
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Initial greeting
        st.session_state.messages.append({"role": "assistant", "content": "Security Operations AI online. Systems nominal. How can I assist with your threat analysis today?"})
    # Floating Command Center using Expander
    st.markdown("---")
    with st.expander("💬 CORTEX COMMAND CENTER", expanded=False):
        st.markdown('<div class="command-center-terminal">', unsafe_allow_html=True)
        
        # Chat container
        chat_container = st.container()
        
        # Display chat messages
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div style="
                        background: rgba(0, 243, 255, 0.05); 
                        padding: 10px; 
                        border-radius: 4px; 
                        margin-bottom: 8px; 
                        text-align: right; 
                        border-right: 2px solid #00f3ff;
                        margin-left: 20%;
                    ">
                        <div style="color: #00f3ff; font-size: 0.7rem; margin-bottom: 2px;">COMMANDER</div>
                        <span style="color: #eee;">{message["content"]}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="
                        background: rgba(188, 19, 254, 0.05); 
                        padding: 10px; 
                        border-radius: 4px; 
                        margin-bottom: 8px; 
                        border-left: 2px solid #bc13fe;
                        margin-right: 20%;
                    ">
                        <div style="color: #bc13fe; font-size: 0.7rem; margin-bottom: 2px;">CORTEX CORE</div>
                        <span style="color: #eee;">{message["content"]}</span>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Chat input within the expander
        col1, col2, col3 = st.columns([1, 6, 1])
        
        # 🎙️ VOICE COMMAND MODULE
        with col1:
            voice_js = """
            <script>
            function startDictation() {
                if (window.hasOwnProperty('webkitSpeechRecognition')) {
                    var recognition = new webkitSpeechRecognition();
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.lang = "en-US";
                    recognition.start();

                    recognition.onresult = function(e) {
                        var text = e.results[0][0].transcript;
                        // Locate the chat input and set value (Hack via DOM)
                        var inputs = window.parent.document.querySelectorAll('input[type="text"]');
                        for (var i = 0; i < inputs.length; i++) {
                            if (inputs[i].ariaLabel && inputs[i].ariaLabel.includes("command")) {
                                inputs[i].value = text;
                                inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
                                inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                                break;
                            }
                        }
                    };
                    recognition.onerror = function(e) {
                         console.error("Speech Recognition Error", e);
                    };
                }
            }
            </script>
            <button onclick="parent.startDictation()" style="
                border: 1px solid #00f3ff; 
                background: rgba(0, 243, 255, 0.1); 
                color: #00f3ff; 
                border-radius: 4px; 
                width: 100%; 
                height: 42px; 
                cursor: pointer;
                font-size: 1.2rem;
                display: flex; align-items: center; justify-content: center;
                transition: all 0.2s;
            " onmouseover="this.style.background='rgba(0,243,255,0.2)'" onmouseout="this.style.background='rgba(0,243,255,0.1)'">
                🎙️
            </button>
            """
            st.components.v1.html(voice_js, height=50)

        with col2:
            prompt = st.text_input("Enter command...", key="main_chat_input", label_visibility="collapsed", help="Type or use Voice Command")
        with col3:
            send_btn = st.button("SEND", type="primary", use_container_width=True)
        
        if prompt and (send_btn or st.session_state.get('last_prompt') != prompt):
             # Simple debounce check if needed, or just rely on manual send for now to avoid complexity in this view
             # Actually, st.chat_input is better even in expander if available, but let's stick to text_input+btn for control if chat_input is buggy in expanders in old streamlit
             # Let's try standard logic:
             pass

        # Re-implementing input logic nicely:
        if prompt and send_btn:
            # Add user message to state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get AI response
            with st.spinner("⚡ CORTEX ANALYZING..."):
                # Gather simple context
                context = {
                    "Page": st.session_state.get("current_page", "Unknown"),
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
