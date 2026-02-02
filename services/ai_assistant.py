import os
import google.generativeai as genai
import streamlit as st
import json

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

    def execute_tool(self, tool_name, params):
        """Execute the requested tool and return the output."""
        try:
            if tool_name == "scan_ip":
                target = params.get("target")
                result = run_full_scan(target)
                return f"SCAN COMPLETE. TARGET: {target}\nRESULTS: {json.dumps(result, indent=2)}"
            
            elif tool_name == "ping_host":
                target = params.get("target")
                result = run_ping(target)
                status = "ONLINE" if result.get("alive") else "OFFLINE"
                return f"PING RESULT: HOST {status}. LATENCY: {result.get('response_time')}ms"
                
            elif tool_name == "threat_intel":
                threats = get_latest_threats()[:3]
                return f"LATEST THREAT INTEL:\n{json.dumps(threats, indent=2)}"
                
            return "ERROR: UNKNOWN TOOL"
        except Exception as e:
            return f"EXECUTION ERROR: {str(e)}"

    def chat(self, user_input, system_context=None):
        """
        Send a message to the AI, handling tool execution loops.
        """
        if not self.model:
            return "❌ AI Core Offline. Configure GEMINI_API_KEY."

        if not self.chat_session:
            self.initialize_session()

        # Context injection
        context_prompt = ""
        if system_context:
            context_str = ", ".join([f"{k}: {v}" for k, v in system_context.items()])
            context_prompt = f"[SYSTEM TELEMETRY: {context_str}] "

        full_prompt = f"{context_prompt}{user_input}"
        
        try:
            # First pass: Get AI response (text or tool call)
            response = self.chat_session.send_message(full_prompt)
            text = response.text.strip()
            
            # Check for JSON tool call
            if text.startswith("{") and "tool" in text:
                try:
                    tool_call = json.loads(text)
                    tool_name = tool_call.get("tool")
                    params = tool_call
                    
                    # Return a special indicator to UI that we are running a tool
                    # But since we are backend, let's just run it and feed it back
                    
                    tool_output = self.execute_tool(tool_name, params)
                    
                    # Feed tool output back to AI for final response
                    final_response = self.chat_session.send_message(
                        f"TOOL OUTPUT: {tool_output}\n\nBased on this output, provide a strategic summary to the commander."
                    )
                    return final_response.text
                    
                except json.JSONDecodeError:
                    return text # Not valid JSON, treat as text
            
            return text
            
        except Exception as e:
            return f"⚠️ SYSTEM ERROR: {str(e)}"

# Singleton instance
ai_assistant = AIAssistant()
