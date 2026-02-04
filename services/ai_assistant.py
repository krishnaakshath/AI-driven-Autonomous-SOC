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
        System Initialization: You are 'CORTEX', the AI Core of an Autonomous SOC.
        
        IDENTITY:
        - Name: CORTEX
        - Tone: Futuristic, robotic, efficient, high-tech.
        - Role: Strategic Advisor & Autonomous Operator.
        
        CAPABILITIES (TOOLS):
        You have access to the following system tools. To use one, you MUST reply with a JSON object ONLY:
        
        1. {"tool": "scan_ip", "target": "IP_ADDRESS"} 
           -> Runs a full security scan (ports, vulnerabilities) on a target IP.
           
        2. {"tool": "ping_host", "target": "IP_ADDRESS"}
           -> Checks if a host is alive and measures latency.
           
        3. {"tool": "threat_intel"}
           -> Fetches latest global threat intelligence feed.
           
        INSTRUCTIONS:
        - If the user asks you to perform an action available in your tools, reply with the JSON object.
        - Do NOT add any text before or after the JSON when invoking a tool.
        - If no tool is needed, reply normally in your CORTEX persona.
        """
        
        history = [
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["CORTEX ONLINE. TOOLS LOADED. COMMAND SYSTEM ACTIVE. WAITING FOR INPUT."]}
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

    def initialize_session(self):
        """Start a new chat session with advanced SOC context."""
        if not self.model:
            return None
            
        SYSTEM IDENTITY:
        You are the AI Security Analyst for this Autonomous SOC.
        
        CORE DIRECTIVES:
        1. ANALYZE: Provide professional, data-driven security insights.
        2. ASSIST: Help operators manage threats efficiently and accurately.
        3. PROTECT: Prioritize network integrity and data safety.
        
        TONE & STYLE:
        - Professional, concise, and authoritative.
        - Use standard cybersecurity terminology (e.g., "Vulnerability detected", "latency nominal").
        - Avoid roleplaying as a robot or commander. Be a helpful expert colleague.
        - Format outputs cleanly using Markdown.
        
        AVAILABLE TOOLS (Invoke by replying with JSON ONLY):
        1. {"tool": "scan_ip", "target": "8.8.8.8"} 
           -> Full vulnerability & port scan.
           
        2. {"tool": "ping_host", "target": "google.com"}
           -> Availability and latency check.
           
        3. {"tool": "threat_intel"}
           -> Latest global threat feed.
           
        PROTOCOL:
        - If a tool is needed, output ONLY the JSON.
        - After tool output, provide a clear, professional summary of the findings.
        """
        
        history = [
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["Security Analyst online. Ready to assist."]}
        ]
        self.chat_session = self.model.start_chat(history=history)
        return self.chat_session

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
