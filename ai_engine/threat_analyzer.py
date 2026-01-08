import os
from typing import Optional, Dict, Any

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class ThreatAnalyzer:
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
            except Exception as e:
                print(f"[WARNING] Failed to initialize Gemini: {e}")
    
    def is_available(self) -> bool:
        return self.model is not None
    
    def analyze_threat(self, event_data: Dict[str, Any]) -> str:
        if not self.is_available():
            return self._fallback_analysis(event_data)
        
        prompt = f"""You are a Security Operations Center analyst. Analyze this security event:

Attack Type: {event_data.get('attack_type', 'Unknown')}
Risk Score: {event_data.get('risk_score', 0)}/100
Source IP: {event_data.get('source_ip', 'Unknown')}
Target: {event_data.get('target_host', 'Unknown')}
Decision: {event_data.get('access_decision', 'Unknown')}

Provide: 1) 2-3 sentence threat summary 2) Attack vector explanation 3) One immediate recommendation. Keep response concise."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception:
            return self._fallback_analysis(event_data)
    
    def generate_incident_summary(self, incidents: list) -> str:
        if not self.is_available():
            return self._fallback_incident_summary(incidents)
        
        attack_counts = {}
        total_blocked = sum(1 for inc in incidents if inc.get('access_decision') == 'BLOCK')
        
        for inc in incidents:
            attack_type = inc.get('attack_type', 'Unknown')
            attack_counts[attack_type] = attack_counts.get(attack_type, 0) + 1
        
        top_attacks = sorted(attack_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        prompt = f"""As a SOC analyst, write an executive summary:

Total Incidents: {len(incidents)}
Blocked: {total_blocked}
Top Attacks: {', '.join([f"{a}: {c}" for a, c in top_attacks])}

Write 3-4 sentences covering threat landscape, concerns, and defense effectiveness."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception:
            return self._fallback_incident_summary(incidents)
    
    def get_remediation_recommendation(self, attack_type: str, risk_score: float) -> str:
        if not self.is_available():
            return self._fallback_remediation(attack_type, risk_score)
        
        prompt = f"""Provide 3 remediation steps for: Attack: {attack_type}, Risk: {risk_score}. Format as numbered list."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception:
            return self._fallback_remediation(attack_type, risk_score)
    
    def chat(self, user_message: str, context: Optional[str] = None) -> str:
        if not self.is_available():
            return "AI assistant not available. Configure Gemini API key in Settings."
        
        full_prompt = f"You are an AI SOC assistant. {f'Context: {context}. ' if context else ''}Question: {user_message}"
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _fallback_analysis(self, event_data: Dict[str, Any]) -> str:
        attack_type = event_data.get('attack_type', 'Unknown')
        risk_score = event_data.get('risk_score', 0)
        severity = "Critical" if risk_score >= 80 else "High" if risk_score >= 60 else "Medium" if risk_score >= 30 else "Low"
        
        insights = {
            "Port Scan": "Reconnaissance activity. Review firewall rules.",
            "DDoS Attack": "Volumetric attack. Enable rate limiting.",
            "Brute Force": "Credential attack. Enforce MFA.",
            "SQL Injection": "Database attack. Use parameterized queries.",
            "XSS Attack": "Script injection. Implement CSP headers.",
            "Malware C2": "C2 communication. Isolate endpoint immediately.",
            "Data Exfiltration": "Data theft attempt. Check DLP policies.",
            "Privilege Escalation": "Unauthorized access. Audit permissions."
        }
        
        return f"**{severity} Severity {attack_type}**\nRisk: {risk_score}/100\n{insights.get(attack_type, 'Review security logs.')}"
    
    def _fallback_incident_summary(self, incidents: list) -> str:
        total = len(incidents)
        blocked = sum(1 for i in incidents if i.get('access_decision') == 'BLOCK')
        return f"**Summary**\nTotal: {total} | Blocked: {blocked} ({blocked/total*100:.1f}%)\nEnable AI for enhanced analysis."
    
    def _fallback_remediation(self, attack_type: str, risk_score: float) -> str:
        defaults = {"Port Scan": ["Block source IP", "Minimize exposed ports", "Enable IDS"],
                    "Brute Force": ["Enable account lockout", "Enforce MFA", "Add CAPTCHA"],
                    "DDoS Attack": ["Enable DDoS mitigation", "Rate limit", "Use CDN"],
                    "SQL Injection": ["Use parameterized queries", "Deploy WAF", "Input validation"]}
        steps = defaults.get(attack_type, ["Investigate incident", "Apply restrictions", "Update policies"])
        return "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)])


def analyze_event(event_data: Dict[str, Any], api_key: Optional[str] = None) -> str:
    return ThreatAnalyzer(api_key).analyze_threat(event_data)
