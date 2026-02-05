import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from datetime import datetime


class EmailNotifier:
    
    def __init__(self, smtp_server: Optional[str] = None, smtp_port: int = 587,
                 username: Optional[str] = None, password: Optional[str] = None,
                 from_email: Optional[str] = None):
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port
        self.username = username or os.getenv("SENDER_EMAIL")
        _password = password or os.getenv("SENDER_PASSWORD")
        self.password = _password.replace(" ", "") if _password else None
        self.from_email = from_email or self.username
    
    def is_configured(self) -> bool:
        return bool(self.smtp_server and self.username and self.password)
    
    def send_email(self, to_emails: List[str], subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
        if not self.is_configured():
            print("[WARNING] Email not configured")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to_emails)
            
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_emails, msg.as_string())
            
            return True
        except Exception as e:
            print(f"[ERROR] Email send failed: {e}")
            return False
    
    def send_alert(self, to_emails: List[str], event_data: Dict[str, Any]) -> bool:
        risk_score = event_data.get('risk_score', 0)
        
        if risk_score >= 80:
            severity, color = "CRITICAL", "#FF4444"
        elif risk_score >= 60:
            severity, color = "HIGH", "#FF8C00"
        elif risk_score >= 30:
            severity, color = "MEDIUM", "#FFD700"
        else:
            severity, color = "LOW", "#00C853"
        
        attack_type = event_data.get('attack_type', 'Unknown')
        decision = event_data.get('access_decision', 'UNKNOWN')
        
        subject = f"[{severity}] SOC Alert: {attack_type} Detected"
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0E1117; color: #FAFAFA; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #1A1F2E; border-radius: 16px; padding: 30px; }}
        .header {{ border-bottom: 2px solid {color}; padding-bottom: 15px; margin-bottom: 20px; }}
        .severity {{ background: {color}; color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; }}
        .detail-row {{ padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        .label {{ color: #8B95A5; font-size: 12px; }}
        .value {{ color: #FAFAFA; font-weight: 500; }}
        .decision {{ padding: 10px 20px; border-radius: 8px; font-weight: bold; display: inline-block; margin-top: 15px; }}
        .block {{ background: #FF4444; color: white; }}
        .restrict {{ background: #FF8C00; color: white; }}
        .footer {{ margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); text-align: center; color: #8B95A5; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="severity">{severity}</span>
            <h2 style="margin: 15px 0 0 0;">🛡️ Security Alert</h2>
        </div>
        <div class="detail-row"><p class="label">ATTACK TYPE</p><p class="value">{attack_type}</p></div>
        <div class="detail-row"><p class="label">RISK SCORE</p><p class="value" style="color: {color}; font-size: 24px;">{risk_score}/100</p></div>
        <div class="detail-row"><p class="label">SOURCE IP</p><p class="value" style="font-family: monospace;">{event_data.get('source_ip', 'N/A')}</p></div>
        <div class="detail-row"><p class="label">TARGET</p><p class="value">{event_data.get('target_host', 'N/A')}</p></div>
        <div><p class="label">AUTOMATIC ACTION</p><span class="decision {'block' if decision == 'BLOCK' else 'restrict'}">{decision}</span><p style="margin-top: 10px; color: #00D4FF;">⚡ {event_data.get('automated_response', 'None')}</p></div>
        <div class="footer"><p>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p><p>AI-Driven Autonomous SOC</p></div>
    </div>
</body>
</html>
"""
        
        body_text = f"""
SOC SECURITY ALERT - {severity}

Attack Type: {attack_type}
Risk Score: {risk_score}/100
Source IP: {event_data.get('source_ip', 'N/A')}
Target: {event_data.get('target_host', 'N/A')}
Decision: {decision}
Response: {event_data.get('automated_response', 'None')}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
AI-Driven Autonomous SOC
"""
        
        return self.send_email(to_emails, subject, body_html, body_text)
    
    def send_daily_report(self, to_emails: List[str], summary_data: Dict[str, Any]) -> bool:
        subject = f"Daily SOC Security Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0E1117; color: #FAFAFA; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #1A1F2E; border-radius: 16px; padding: 30px; }}
        .metric {{ display: inline-block; background: rgba(0,212,255,0.1); border-radius: 12px; padding: 20px; margin: 10px; min-width: 100px; text-align: center; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #00D4FF; }}
        .metric-label {{ color: #8B95A5; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 style="margin: 0;">📊 Daily Security Report</h1>
        <p style="color: #8B95A5;">{datetime.now().strftime('%B %d, %Y')}</p>
        <div style="margin: 20px 0;">
            <div class="metric"><div class="metric-value">{summary_data.get('total_events', 0):,}</div><div class="metric-label">Total Events</div></div>
            <div class="metric"><div class="metric-value" style="color: #FF4444;">{summary_data.get('blocked', 0):,}</div><div class="metric-label">Blocked</div></div>
            <div class="metric"><div class="metric-value" style="color: #FF8C00;">{summary_data.get('restricted', 0):,}</div><div class="metric-label">Restricted</div></div>
        </div>
        <p style="text-align: center; color: #8B95A5; margin-top: 30px;">🛡️ AI-Driven Autonomous SOC</p>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_emails, subject, body_html)
    
    def test_connection(self, to_email: str) -> bool:
        return self.send_email([to_email], "SOC Email Test - Success! ✅", "<h1>🔗 Connection Test Successful</h1><p>Your SOC email alerts are configured correctly.</p>")


# ═══════════════════════════════════════════════════════════════════════════════
# SIMPLE HELPER FUNCTION FOR BACKGROUND MONITOR
# ═══════════════════════════════════════════════════════════════════════════════
def send_email_alert(subject: str, body: str, to_email: str) -> bool:
    """
    Simple function to send an email alert.
    Used by the background monitor service.
    """
    notifier = EmailNotifier()
    if not notifier.is_configured():
        print("[WARNING] Email not configured. Check SENDER_EMAIL and SENDER_PASSWORD environment variables.")
        return False
    
    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #0E1117; color: #FAFAFA; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #1A1F2E; border-radius: 16px; padding: 30px; border-left: 4px solid #FF4444;">
            <h2 style="color: #FF4444;">🚨 Security Alert</h2>
            <pre style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; white-space: pre-wrap; font-family: monospace;">{body}</pre>
            <p style="color: #8B95A5; margin-top: 20px;">AI-Driven Autonomous SOC</p>
        </div>
    </body>
    </html>
    """
    
    return notifier.send_email([to_email], subject, html_body, body)

