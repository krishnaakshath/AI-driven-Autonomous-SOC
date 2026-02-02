import os
import google.generativeai as genai
import streamlit as st
import json

class AIAssistant:
    def __init__(self):
        # Initialize Gemini API
        self.api_key = self._get_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.chat_session = None
        else:
            self.model = None

    def _get_api_key(self):
        """Retrieve API key from streamlit secrets or local config."""
        # Try Streamlit secrets first
        if 'GEMINI_API_KEY' in st.secrets:
            return st.secrets['GEMINI_API_KEY']
        
        # Try local config file
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
            
        history = [
            {"role": "user", "parts": ["System Initialization: You are the AI Core of an advanced autonomous Security Operations Center (SOC). Your name is 'CORTEX'. You speak in a concise, futuristic, somewhat robotic but helpful tone. You always stay in character as a high-tech system interface. Never break character. Use technical terminology appropriate for cybersecurity."]},
            {"role": "model", "parts": ["CORTEX ONLINE. SYSTEMS NOMINAL. AWAITING INSTRUCTIONS. READY TO ANALYZE THREAT VECTORS AND DEFEND NETWORK INTEGRITY."]}
        ]
        self.chat_session = self.model.start_chat(history=history)
        return self.chat_session

    def chat(self, user_input, system_context=None):
        """
        Send a message to the AI and get a response.
        system_context: Optional dict of current system stats to make the AI aware of dashboard state.
        """
        if not self.model:
            return "❌ AI Core Offline. Please configure GEMINI_API_KEY in settings."

        if not self.chat_session:
            self.initialize_session()

        # Inject context if provided
        context_prompt = ""
        if system_context:
            context_str = ", ".join([f"{k}: {v}" for k, v in system_context.items()])
            context_prompt = f"[SYSTEM TELEMETRY: {context_str}] "

        full_prompt = f"{context_prompt}{user_input}"
        
        try:
            response = self.chat_session.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"⚠️ SYSTEM ERROR: {str(e)}"

# Singleton instance
ai_assistant = AIAssistant()
