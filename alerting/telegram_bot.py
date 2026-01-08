import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime


class TelegramNotifier:
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
    
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        if not self.is_configured():
            print("[WARNING] Telegram not configured")
            return False
        
        try:
            response = requests.post(
                f"{self.api_base}/sendMessage",
                json={"chat_id": self.chat_id, "text": message, "parse_mode": parse_mode},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Telegram send failed: {e}")
            return False
    
    def send_alert(self, event_data: Dict[str, Any]) -> bool:
        risk_score = event_data.get('risk_score', 0)
        
        if risk_score >= 80:
            severity_emoji, severity_text = "🔴", "CRITICAL"
        elif risk_score >= 60:
            severity_emoji, severity_text = "🟠", "HIGH"
        elif risk_score >= 30:
            severity_emoji, severity_text = "🟡", "MEDIUM"
        else:
            severity_emoji, severity_text = "🟢", "LOW"
        
        decision = event_data.get('access_decision', 'UNKNOWN')
        decision_emoji = "🛑" if decision == "BLOCK" else "⚠️" if decision == "RESTRICT" else "✅"
        
        message = f"""
{severity_emoji} <b>SOC SECURITY ALERT</b> {severity_emoji}

<b>Severity:</b> {severity_text}
<b>Attack Type:</b> {event_data.get('attack_type', 'Unknown')}
<b>Risk Score:</b> {risk_score}/100

<b>Source IP:</b> <code>{event_data.get('source_ip', 'N/A')}</code>
<b>Target:</b> {event_data.get('target_host', 'N/A')}

{decision_emoji} <b>Decision:</b> {decision}
<b>Response:</b> {event_data.get('automated_response', 'None')}

<i>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
<i>🛡️ AI-Driven Autonomous SOC</i>
"""
        return self.send_message(message.strip())
    
    def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        message = f"""
📊 <b>DAILY SOC SUMMARY</b>

<b>Total Events:</b> {summary_data.get('total_events', 0):,}
<b>Blocked:</b> 🛑 {summary_data.get('blocked', 0):,}
<b>Restricted:</b> ⚠️ {summary_data.get('restricted', 0):,}
<b>Allowed:</b> ✅ {summary_data.get('allowed', 0):,}

<b>Average Risk Score:</b> {summary_data.get('avg_risk', 0):.1f}
<b>Critical Alerts:</b> {summary_data.get('critical', 0):,}

<i>🕐 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>
<i>🛡️ AI-Driven Autonomous SOC</i>
"""
        return self.send_message(message.strip())
    
    def test_connection(self) -> bool:
        return self.send_message("🔗 SOC Connection Test - Success! ✅")


def send_security_alert(event_data: Dict[str, Any], bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
    notifier = TelegramNotifier(bot_token, chat_id)
    return notifier.send_alert(event_data)
