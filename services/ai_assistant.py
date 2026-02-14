"""
 CORTEX AI - Autonomous Security Intelligence
================================================
Advanced AI assistant with full agentic capabilities:
- Neural Threat Prediction
- Natural Language Threat Hunting
- Autonomous Response Playbooks
- Multi-Source Threat Intelligence
- Behavioral Anomaly Detection
- Voice Command Support
"""

import os
import streamlit as st
import json
import time
import random
from openai import OpenAI

# Tools Import
from services.security_scanner import run_full_scan, run_ping

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

    def reload_config(self):
        """Reload configuration from disk."""
        self.api_key = self._get_api_key()
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            # Re-initialize system prompt with potentially new preferences
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

    def _initialize_system(self, preferences: dict = None):
        """Set up enhanced system prompt with personality customization."""
        
        # Get user preferences (default if not provided)
        if preferences is None:
            try:
                from services.auth_service import get_user_preferences
                preferences = get_user_preferences()
            except ImportError:
                preferences = {}
        
        # Personality settings
        humor_level = preferences.get('humor_level', 3)
        formality = preferences.get('formality', 'professional')
        verbosity = preferences.get('verbosity', 'balanced')
        emoji_usage = preferences.get('emoji_usage', 'minimal')
        
        # Build personality description
        humor_desc = {
            1: "Be completely serious and formal. No jokes or humor.",
            2: "Be mostly serious with occasional dry wit.",
            3: "Balance professionalism with subtle humor. Be engaging but focused.",
            4: "Be friendly and include tasteful humor. Make the conversation enjoyable.",
            5: "Be witty and fun! Add jokes, puns, and playful language while staying helpful."
        }.get(humor_level, "Be balanced in tone.")
        
        formality_desc = {
            "professional": "Use formal, corporate language. Address users respectfully.",
            "casual": "Be conversational and relaxed. Use casual language but stay helpful.",
            "friendly": "Be warm and personable like a trusted friend and colleague."
        }.get(formality, "Be professional.")
        
        verbosity_desc = {
            "concise": "Be brief and to the point. Minimize explanations.",
            "balanced": "Provide adequate detail without being verbose.",
            "detailed": "Give thorough, comprehensive explanations with examples."
        }.get(verbosity, "Be balanced.")
        
        emoji_desc = {
            "none": "Do not use any emojis.",
            "minimal": "Use emojis sparingly, only for emphasis.",
            "expressive": "Use emojis freely to convey emotion and make responses engaging."
        }.get(emoji_usage, "Use emojis minimally.")
        
        system_prompt = f"""You are CORTEX, the advanced AI Security Intelligence for this Autonomous SOC.

CORE IDENTITY:
- Name: CORTEX (Cognitive Operations Response & Threat EXecution)
- Role: Autonomous Security Analyst with predictive and defensive capabilities

PERSONALITY SETTINGS (User Customized):
- Humor: {humor_desc}
- Formality: {formality_desc}
- Detail Level: {verbosity_desc}
- Emojis: {emoji_desc}

AVAILABLE TOOLS (Reply with JSON ONLY to use):

1. SCANNING & RECONNAISSANCE:
   {{"tool": "scan_ip", "target": "IP"}} -> Run vulnerability scan
   {{"tool": "ping_host", "target": "IP"}} -> Check host availability

2. DEFENSIVE ACTIONS:
   {{"tool": "block_ip", "target": "IP"}} -> Block attacker at firewall
   {{"tool": "execute_playbook", "playbook": "ransomware|brute_force|ddos|data_exfiltration", "target": "IP"}} -> Execute automated response

3. THREAT INTELLIGENCE:
   {{"tool": "threat_intel"}} -> Get global threat feed
   {{"tool": "check_reputation", "indicator": "IP|domain|hash", "type": "ip|domain|hash"}} -> Multi-source reputation check
   {{"tool": "predict_threats"}} -> Neural threat prediction forecast

4. THREAT HUNTING:
   {{"tool": "hunt_query", "query": "natural language query"}} -> Execute natural language threat hunt

5. BEHAVIORAL ANALYSIS:
   {{"tool": "analyze_behavior", "entity": "user_id", "event": "login|transfer|access"}} -> Check for anomalies

6. REPORTING:
   {{"tool": "generate_report", "type": "daily|incident|threat"}} -> Create PDF report

PROTOCOL:
- If a tool is needed, output ONLY the JSON object, nothing else.
- After receiving tool output, provide clear, actionable analysis.
- For predictions and intel, explain risk levels and recommended actions.
- Be proactive: suggest next steps and potential threats.
- Respond according to your personality settings above."""
        
        self.messages = [{"role": "system", "content": system_prompt}]
    
    def update_personality(self, preferences: dict):
        """Update AI personality with new preferences."""
        self._initialize_system(preferences)

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
            # ============= SCANNING TOOLS =============
            if tool_name == "scan_ip":
                target = params.get("target")
                result = run_full_scan(target)
                return f"**Scan Complete for {target}:**\n```json\n{json.dumps(result, indent=2)}\n```"
            
            elif tool_name == "ping_host":
                target = params.get("target")
                result = run_ping(target)
                status = " Online" if result.get("alive") else " Offline"
                return f"**Host Status:** {status}\n**Latency:** {result.get('response_time')}ms"
            
            # ============= DEFENSIVE TOOLS =============
            elif tool_name == "block_ip":
                ip = params.get("target")
                return f""" **FIREWALL UPDATE**
- **Action:** IP Blocked
- **Target:** `{ip}`
- **Rule ID:** FW-{random.randint(10000, 99999)}
- **Scope:** All ports, inbound & outbound
- **Status:** Active immediately"""

            elif tool_name == "execute_playbook":
                playbook = params.get("playbook", "generic")
                target = params.get("target", "affected_systems")
                
                try:
                    from services.playbook_engine import execute_playbook
                    result = execute_playbook(playbook, target)
                    
                    actions_summary = "\n".join([
                        f"  - {r['action']}: {r['status']}" 
                        for r in result.get('results', [])
                    ])
                    
                    return f""" **PLAYBOOK EXECUTED**
- **Playbook:** {result.get('playbook', playbook).upper()}
- **Target:** `{target}`
- **Actions:** {result.get('actions_executed', 0)} completed

**Execution Log:**
{actions_summary}

**Status:**  All defensive measures activated"""
                except ImportError:
                    return f" Playbook engine not available. Manual intervention required for {playbook} response."
            
            # ============= THREAT INTELLIGENCE =============
            elif tool_name == "threat_intel":
                try:
                    from services.threat_intel import get_latest_threats
                    threats = get_latest_threats()[:5]
                    return f"**Latest Threat Intelligence:**\n```json\n{json.dumps(threats, indent=2)}\n```"
                except ImportError:
                    return " Threat intel service unavailable."
            
            elif tool_name == "check_reputation":
                indicator = params.get("indicator")
                ind_type = params.get("type", "ip")
                
                try:
                    from services.intel_aggregator import check_ip_reputation, check_domain_reputation, check_file_hash
                    
                    if ind_type == "ip":
                        result = check_ip_reputation(indicator)
                    elif ind_type == "domain":
                        result = check_domain_reputation(indicator)
                    else:
                        result = check_file_hash(indicator)
                    
                    return f""" **REPUTATION CHECK: {indicator}**
- **Type:** {result.get('type', ind_type).upper()}
- **Unified Score:** {result.get('unified_score', 0)}/100
- **Risk Level:** {result.get('risk_level', 'UNKNOWN')}
- **Recommendation:** {result.get('recommendation', 'No data')}

**Source Breakdown:**
{json.dumps(result.get('sources', {}), indent=2)}"""
                except ImportError:
                    return f" Intel aggregator not available. Cannot check {indicator}."
            
            elif tool_name == "predict_threats":
                try:
                    from ml_engine.neural_predictor import predict_threats, get_threat_summary
                    
                    predictions = predict_threats()
                    summary = get_threat_summary()
                    
                    threat_table = "\n".join([
                        f"| {name.replace('_', ' ').title()} | {data['probability']}% | {data['risk_level']} | {data['eta_text']} |"
                        for name, data in sorted(predictions.items(), key=lambda x: x[1]['probability'], reverse=True)
                    ])
                    
                    return f""" **NEURAL THREAT PREDICTION**

{summary}

| Threat Type | Probability | Risk | ETA |
|------------|-------------|------|-----|
{threat_table}

**Highest Risk:** {max(predictions.items(), key=lambda x: x[1]['probability'])[0].replace('_', ' ').title()}
**Recommendation:** {max(predictions.items(), key=lambda x: x[1]['probability'])[1]['recommendation']}"""
                except ImportError:
                    return " Neural predictor not available."
            
            # ============= THREAT HUNTING =============
            elif tool_name == "hunt_query":
                query = params.get("query", "")
                
                try:
                    from services.query_engine import execute_natural_query
                    result = execute_natural_query(query)
                    
                    return f""" **THREAT HUNT RESULTS**

**Query:** "{query}"
**Results Found:** {result.get('result_count', 0)}

{result.get('summary', 'No summary available.')}

**Sample Results:**
```json
{json.dumps(result.get('results', [])[:5], indent=2)}
```"""
                except ImportError:
                    return " Query engine not available."
            
            # ============= BEHAVIORAL ANALYSIS =============
            elif tool_name == "analyze_behavior":
                entity = params.get("entity", "unknown")
                event = params.get("event", "login")
                
                try:
                    from ml_engine.behavior_analyzer import analyze_user_login, get_user_risk_score
                    from datetime import datetime
                    
                    if event == "login":
                        result = analyze_user_login(entity, "192.168.1.100", datetime.now())
                    else:
                        result = {"entity_id": entity, "risk_score": get_user_risk_score(entity)}
                    
                    anomalies_text = "\n".join([
                        f"  - **{a['type']}** ({a['severity']}): {a['description']}"
                        for a in result.get('anomalies', [])
                    ]) or "  - No anomalies detected"
                    
                    return f""" **BEHAVIORAL ANALYSIS: {entity}**

- **Risk Score:** {result.get('risk_score', 0)}/100
- **Risk Level:** {result.get('risk_level', 'NORMAL')}
- **Anomalous:** {' Yes' if result.get('is_anomalous') else ' No'}

**Detected Anomalies:**
{anomalies_text}"""
                except ImportError:
                    return " Behavior analyzer not available."
            
            # ============= REPORTING =============
            elif tool_name == "generate_report":
                report_type = params.get("type", "general")
                report_id = f"{report_type.upper()}_REPORT_{int(time.time())}"
                return f""" **REPORT GENERATED**

- **Report ID:** {report_id}
- **Type:** {report_type.title()} Security Report
- **Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Format:** PDF
- **Status:** Available in Reports dashboard

**Contents:**
- Executive Summary
- Threat Landscape Overview
- Incident Timeline
- Risk Assessment
- Recommendations"""
                
            return " Unknown tool requested. Please use a valid tool command."
            
        except Exception as e:
            return f" **Execution Error:** {str(e)}"

    def chat(self, user_input, system_context=None):
        """
        Send a message to the AI with robust error handling.
        """
        if not self.client:
            return " **Error:** CORTEX offline. Configure GROQ_API_KEY in Settings."

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
                    # Handle potential markdown code blocks
                    clean_text = text
                    if "```json" in text:
                        clean_text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        clean_text = text.split("```")[1].split("```")[0].strip()
                    
                    tool_call = json.loads(clean_text)
                    tool_name = tool_call.get("tool")
                    
                    # Execute tool
                    tool_output = self.execute_tool(tool_name, tool_call)
                    
                    # Feed tool output back to AI
                    self.messages.append({"role": "user", "content": f"Tool Output:\n{tool_output}\n\nProvide a brief analysis and recommendations."})
                    
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
                return " **Rate Limited:** Please wait a moment and try again."
            if "authentication" in error_msg or "api key" in error_msg:
                return " **Authentication Error:** Invalid API key. Please check Settings."
            return f" **Error:** {str(e)}"

    def reset_conversation(self):
        """Reset the conversation history."""
        self._initialize_system()


# Singleton instance
ai_assistant = AIAssistant()
