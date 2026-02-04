import os
import google.generativeai as genai
import streamlit as st
import json
import time
import random

# Tools Import
from services.security_scanner import run_full_scan, run_ping
from services.threat_intel import get_latest_threats

class AIAssistant:
    def __init__(self):
        # Initialize Gemini API
        self.api_key = self._get_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.chat_session = None
        else:
            self.model = None

    def _get_api_key(self):
        """Retrieve API key from streamlit secrets or local config."""
        if 'GEMINI_API_KEY' in st.secrets:
            return st.secrets['GEMINI_API_KEY']
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.soc_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('GEMINI_API_KEY')
        except:
            pass
        return None

    def initialize_session(self):
        """Start a new chat session with system context."""
        if not self.model:
            return None
            
        system_prompt = """
        You are the AI Security Analyst for this Autonomous SOC.
        
        CORE DIRECTIVES:
        1. ANALYZE: Provide professional, data-driven security insights.
        2. ASSIST: Help operators manage threats efficiently and accurately.
        3. PROTECT: Prioritize network integrity and data safety.
        
        TONE & STYLE:
        - Professional, concise, and authoritative.
        - Use standard cybersecurity terminology.
        - Be a helpful expert colleague, not a robot.
        - Format outputs cleanly using Markdown.
        
        AVAILABLE TOOLS (Reply with JSON ONLY to use):
        1. {"tool": "scan_ip", "target": "IP_ADDRESS"} -> Full vulnerability scan.
        2. {"tool": "ping_host", "target": "IP_ADDRESS"} -> Availability check.
        3. {"tool": "threat_intel"} -> Latest threat feed.
        
        PROTOCOL:
        - If a tool is needed, output ONLY the JSON.
        - After tool output, provide a clear summary of findings.
        """
        
        history = [
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["Security Analyst online. Ready to assist."]}
        ]
        self.chat_session = self.model.start_chat(history=history)
        return self.chat_session

    def _retry_api_call(self, func, *args, **kwargs):
        """Retries an API call with exponential backoff."""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str:
                    if attempt < max_retries - 1:
                        delay = (base_delay * (2 ** attempt)) + (random.random() * 0.5)
                        time.sleep(delay)
                        continue
                raise e

    def execute_tool(self, tool_name, params):
        """Execute the requested tool and return the output."""
        try:
            if tool_name == "scan_ip":
                target = params.get("target")
                result = run_full_scan(target)
                return f"TARGET ACQUIRED: {target}\nSCAN METRICS: {json.dumps(result, indent=2)}"
            
            elif tool_name == "ping_host":
                target = params.get("target")
                result = run_ping(target)
                status = "ONLINE" if result.get("alive") else "OFFLINE"
                return f"HOST STATUS: {status}\nLATENCY: {result.get('response_time')}ms"
                
            elif tool_name == "threat_intel":
                threats = get_latest_threats()[:3]
                return f"GLOBAL INTEL FEED:\n{json.dumps(threats, indent=2)}"
                
            return "SYSTEM ERROR: UNKNOWN PROTOCOL"
        except Exception as e:
            return f"EXECUTION FAILURE: {str(e)}"

    def chat(self, user_input, system_context=None):
        """
        Send a message to the AI with robust error handling and retries.
        """
        if not self.model:
            return "❌ **CRITICAL ERROR:** AI CORE OFFLINE. API KEY MISSING."

        if not self.chat_session:
            self.initialize_session()

        # Context injection
        context_prompt = ""
        if system_context:
            context_str = " | ".join([f"{k.upper()}: {v}" for k, v in system_context.items()])
            context_prompt = f"[TELEMETRY: {context_str}] "

        full_prompt = f"{context_prompt}{user_input}"
        
        try:
            # First pass: Get AI response with retry
            response = self._retry_api_call(self.chat_session.send_message, full_prompt)
            text = response.text.strip()
            
            # Check for JSON tool call
            if text.startswith("{") and "tool" in text:
                try:
                    tool_call = json.loads(text)
                    tool_name = tool_call.get("tool")
                    
                    # Execute tool
                    tool_output = self.execute_tool(tool_name, tool_call)
                    
                    # Feed tool output back to AI
                    final_response = self._retry_api_call(
                        self.chat_session.send_message,
                        f"TOOL DATA RECEIVED:\n{tool_output}\n\nPROVIDE STRATEGIC ANALYSIS:"
                    )
                    return final_response.text
                    
                except json.JSONDecodeError:
                    return text 
            
            return text
            
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "429" in error_msg:
                return "⚠️ **SYSTEM OVERLOAD:** NETWORK CONGESTION DETECTED (Code 429). PLEASE STAND BY AND RETRY..."
            if "flagged" in error_msg:
                 return "⚠️ **SECURITY ALERT:** PROMPT REJECTED BY SAFETY PROTOCOLS."
            return f"❌ **SYSTEM FAILURE:** {str(e)}"

# Singleton instance
ai_assistant = AIAssistant()
