"""
 Voice Command Interface
===========================
Web Speech API integration for voice-controlled SOC operations.
Enables hands-free threat hunting and system control.

Commands:
- "CORTEX, scan the network"
- "Show me threats from the last hour"
- "Block all traffic from China"
"""

import streamlit as st
from typing import Optional, Callable

def inject_voice_interface(on_command_callback: Optional[Callable] = None):
    """
    Inject voice command interface into Streamlit page.
    Uses browser's Web Speech API for speech recognition.
    
    Args:
        on_command_callback: Optional callback function when voice command is received
    """
    
    # Voice interface CSS and JavaScript
    st.markdown("""
    <style>
    /* Voice Interface Styling */
    .voice-container {
        position: fixed;
        bottom: 110px;
        right: 30px;
        z-index: 99998;
    }
    
    .voice-btn {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 2px solid rgba(0, 243, 255, 0.3);
        color: #00f3ff;
        font-size: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    .voice-btn:hover {
        transform: scale(1.1);
        border-color: rgba(0, 243, 255, 0.6);
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
    }
    
    .voice-btn.listening {
        animation: voice-pulse 1s infinite;
        border-color: #ff0040;
        color: #ff0040;
    }
    
    @keyframes voice-pulse {
        0%, 100% { 
            box-shadow: 0 0 0 0 rgba(255, 0, 64, 0.6);
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 0 15px rgba(255, 0, 64, 0);
            transform: scale(1.05);
        }
    }
    
    .voice-status {
        position: absolute;
        right: 60px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(0, 0, 0, 0.9);
        border: 1px solid rgba(0, 243, 255, 0.3);
        border-radius: 8px;
        padding: 8px 14px;
        color: #00f3ff;
        font-size: 12px;
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
    }
    
    .voice-status.visible {
        opacity: 1;
    }
    
    .voice-transcript {
        position: fixed;
        bottom: 170px;
        right: 30px;
        background: rgba(0, 0, 0, 0.95);
        border: 1px solid rgba(188, 19, 254, 0.5);
        border-radius: 12px;
        padding: 12px 18px;
        color: #fff;
        font-size: 14px;
        max-width: 300px;
        z-index: 99999;
        display: none;
    }
    
    .voice-transcript.active {
        display: block;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .voice-transcript .label {
        font-size: 10px;
        color: #bc13fe;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    </style>
    
    <div class="voice-container">
        <button class="voice-btn" id="voiceBtn" onclick="toggleVoice()" title="Voice Command (Hold to speak)">
            
        </button>
        <div class="voice-status" id="voiceStatus">Click to start</div>
    </div>
    
    <div class="voice-transcript" id="voiceTranscript">
        <div class="label">VOICE COMMAND</div>
        <div class="text" id="transcriptText"></div>
    </div>
    
    <script>
    // Voice Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isListening = false;
    
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        recognition.onstart = function() {
            isListening = true;
            document.getElementById('voiceBtn').classList.add('listening');
            showStatus('Listening...');
        };
        
        recognition.onend = function() {
            isListening = false;
            document.getElementById('voiceBtn').classList.remove('listening');
            showStatus('Click to start');
            setTimeout(() => hideTranscript(), 3000);
        };
        
        recognition.onresult = function(event) {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            
            showTranscript(transcript);
            
            // If final result, process command
            if (event.results[event.results.length - 1].isFinal) {
                processVoiceCommand(transcript);
            }
        };
        
        recognition.onerror = function(event) {
            console.error('Voice recognition error:', event.error);
            showStatus('Error: ' + event.error);
            isListening = false;
            document.getElementById('voiceBtn').classList.remove('listening');
        };
    }
    
    function toggleVoice() {
        if (!recognition) {
            showStatus('Voice not supported');
            return;
        }
        
        if (isListening) {
            recognition.stop();
        } else {
            recognition.start();
        }
    }
    
    function showStatus(text) {
        const status = document.getElementById('voiceStatus');
        status.textContent = text;
        status.classList.add('visible');
    }
    
    function showTranscript(text) {
        const transcript = document.getElementById('voiceTranscript');
        const textEl = document.getElementById('transcriptText');
        textEl.textContent = text;
        transcript.classList.add('active');
    }
    
    function hideTranscript() {
        document.getElementById('voiceTranscript').classList.remove('active');
    }
    
    function processVoiceCommand(command) {
        // Send command to Streamlit via query params or hidden input
        const cleanCommand = command.toLowerCase().trim();
        
        // Store in sessionStorage for Streamlit to read
        sessionStorage.setItem('voiceCommand', command);
        sessionStorage.setItem('voiceCommandTime', Date.now());
        
        // Trigger page reload with voice command
        const url = new URL(window.location.href);
        url.searchParams.set('voice_cmd', encodeURIComponent(command));
        window.location.href = url.toString();
    }
    </script>
    """, unsafe_allow_html=True)


def get_voice_command() -> Optional[str]:
    """
    Check if a voice command was received via URL parameters.
    
    Returns:
        Voice command string if present, None otherwise
    """
    import urllib.parse
    
    # Check query parameters
    query_params = st.query_params
    
    if "voice_cmd" in query_params:
        command = urllib.parse.unquote(query_params["voice_cmd"])
        # Clear the parameter to avoid re-processing
        del query_params["voice_cmd"]
        return command
    
    return None


def parse_voice_command(command: str) -> dict:
    """
    Parse a voice command into action and parameters.
    
    Args:
        command: Raw voice command string
        
    Returns:
        Parsed command dictionary
    """
    command = command.lower().strip()
    
    # Remove wake word if present
    wake_words = ["cortex", "hey cortex", "ok cortex", "computer"]
    for wake in wake_words:
        if command.startswith(wake):
            command = command[len(wake):].strip()
            if command.startswith(","):
                command = command[1:].strip()
    
    # Parse action
    result = {
        "original": command,
        "action": None,
        "target": None,
        "parameters": {}
    }
    
    # Scan commands
    if any(word in command for word in ["scan", "check", "analyze"]):
        result["action"] = "scan"
        # Extract target
        import re
        ip_match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', command)
        if ip_match:
            result["target"] = ip_match.group()
        elif "network" in command:
            result["target"] = "network"
    
    # Block commands
    elif any(word in command for word in ["block", "blacklist", "deny"]):
        result["action"] = "block"
        import re
        ip_match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', command)
        if ip_match:
            result["target"] = ip_match.group()
        
        # Check for geo block
        geos = ["china", "russia", "north korea", "iran"]
        for geo in geos:
            if geo in command:
                result["target"] = f"geo:{geo}"
                break
    
    # Show/display commands
    elif any(word in command for word in ["show", "display", "list", "get"]):
        result["action"] = "query"
        result["parameters"]["query"] = command
    
    # Report commands
    elif any(word in command for word in ["report", "generate", "create"]):
        result["action"] = "report"
        if "daily" in command:
            result["parameters"]["type"] = "daily"
        elif "weekly" in command:
            result["parameters"]["type"] = "weekly"
    
    # Threat/alert commands
    elif any(word in command for word in ["threat", "alert", "warning", "attack"]):
        result["action"] = "threats"
    
    return result


def render_voice_button_mini():
    """Render a compact voice button for embedding in other components."""
    st.markdown("""
    <style>
    .voice-mini {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(0, 243, 255, 0.2);
        border-radius: 20px;
        padding: 5px 12px;
        color: #00f3ff;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .voice-mini:hover {
        border-color: rgba(0, 243, 255, 0.5);
        background: rgba(0, 243, 255, 0.1);
    }
    </style>
    
    <div class="voice-mini" onclick="toggleVoice()">
         Voice Command
    </div>
    """, unsafe_allow_html=True)
