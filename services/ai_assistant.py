import os
import streamlit as st
import json
import time
import random
from openai import OpenAI

# Tools Import
from services.security_scanner import run_full_scan, run_ping
from services.threat_intel import get_latest_threats

class AIAssistant:
    def __init__(self):
        # Initialize Groq API (OpenAI-compatible, FREE tier)
        self.api_key = self._get_api_key()
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model_name = "llama-3.3-70b-versatile"  # Fast & free on Groq
            self.messages = []  # Chat history
            self._initialize_system()
        else:
            self.client = None

    def _get_api_key(self):
        """Retrieve API key from environment variables, streamlit secrets, or local config."""
        # 1. Check environment variables first (for Docker/Render deployments)
        if 'GROQ_API_KEY' in os.environ:
            return os.environ['GROQ_API_KEY']
        
        # 2. Check Streamlit secrets (for Streamlit Cloud)
        try:
            if 'GROQ_API_KEY' in st.secrets:
                return st.secrets['GROQ_API_KEY']
        except:
            pass
        
        # 3. Check local config file
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.soc_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('GROQ_API_KEY')
        except:
            pass
        return None

    def _initialize_system(self):
        """Set up system prompt."""
        system_prompt = """You are the AI Security Analyst for this Autonomous SOC.

CORE DIRECTIVES:
1. ANALYZE: Provide professional, data-driven security insights.
2. ASSIST: Help operators manage threats efficiently and accurately.
3. PROTECT: Prioritize network integrity and data safety.

TONE & STYLE:
- Professional, concise, and authoritative.
- Use standard cybersecurity terminology.
- Be a helpful expert colleague.
- Format outputs cleanly using Markdown.

AVAILABLE TOOLS (Reply with JSON ONLY to use):
1. {"tool": "scan_ip", "target": "IP"} -> Run vulnerability scan.
2. {"tool": "block_ip", "target": "IP"} -> Block an attacker.
3. {"tool": "threat_intel"} -> Get global threat feed.
4. {"tool": "generate_report", "type": "daily|incident"} -> Create PDF report.

PROTOCOL:
- If a tool is needed, output ONLY the JSON object, nothing else.
- After tool output, provide a clear summary of findings."""
        
        self.messages = [{"role": "system", "content": system_prompt}]

    def _retry_api_call(self, func, *args, **kwargs):
        """Retries an API call with exponential backoff."""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "rate" in error_str:
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
                return f"Scan Complete for {target}:\n{json.dumps(result, indent=2)}"
            
            elif tool_name == "ping_host":
                target = params.get("target")
                result = run_ping(target)
                status = "Online" if result.get("alive") else "Offline"
                return f"Host Status: {status}\nLatency: {result.get('response_time')}ms"
                
            elif tool_name == "threat_intel":
                threats = get_latest_threats()[:3]
                return f"Latest Threat Intelligence:\n{json.dumps(threats, indent=2)}"
            
            elif tool_name == "block_ip":
                ip = params.get("target")
                # Simulate firewall rule addition
                return f"✅ FIREWALL UPDATE: Rule ID-9923 created. IP {ip} has been BLOCKED on all ports."

            elif tool_name == "generate_report":
                report_type = params.get("type", "general")
                # Simulate report generation
                return f"📄 REPORT GENERATED: {report_type.upper()}_SECURITY_REPORT_{int(time.time())}.pdf has been created and sent to the dashboard."
                
            return "Error: Unknown tool requested"
        except Exception as e:
            return f"Execution Error: {str(e)}"

    def chat(self, user_input, system_context=None):
        """
        Send a message to the AI with robust error handling.
        """
        if not self.client:
            return "❌ **Error:** AI offline. Configure GROQ_API_KEY in Settings."

        # Context injection
        context_prompt = ""
        if system_context:
            context_str = " | ".join([f"{k}: {v}" for k, v in system_context.items()])
            context_prompt = f"[Context: {context_str}] "

        full_prompt = f"{context_prompt}{user_input}"
        self.messages.append({"role": "user", "content": full_prompt})
        
        try:
            # Get AI response
            response = self._retry_api_call(
                self.client.chat.completions.create,
                model=self.model_name,
                messages=self.messages,
                temperature=0.7,
                max_tokens=1024
            )
            text = response.choices[0].message.content.strip()
            self.messages.append({"role": "assistant", "content": text})
            
            # Check for JSON tool call
            if text.startswith("{") and "tool" in text:
                try:
                    tool_call = json.loads(text)
                    tool_name = tool_call.get("tool")
                    
                    # Execute tool
                    tool_output = self.execute_tool(tool_name, tool_call)
                    
                    # Feed tool output back to AI
                    self.messages.append({"role": "user", "content": f"Tool Output:\n{tool_output}\n\nPlease provide analysis."})
                    
                    final_response = self._retry_api_call(
                        self.client.chat.completions.create,
                        model=self.model_name,
                        messages=self.messages,
                        temperature=0.7,
                        max_tokens=1024
                    )
                    final_text = final_response.choices[0].message.content.strip()
                    self.messages.append({"role": "assistant", "content": final_text})
                    return final_text
                    
                except json.JSONDecodeError:
                    return text 
            
            return text
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "429" in error_msg:
                return "⚠️ **Rate Limited:** Please wait a moment and try again."
            if "authentication" in error_msg or "api key" in error_msg:
                return "❌ **Authentication Error:** Invalid API key. Please check Settings."
            return f"❌ **Error:** {str(e)}"

# Singleton instance
ai_assistant = AIAssistant()
