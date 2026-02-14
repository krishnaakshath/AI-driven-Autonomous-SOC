import os
import json
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
from typing import Optional, Dict, Any
from alerting.email_sender import EmailNotifier

CONFIG_FILE = ".soc_config.json"

class AlertService:
    
    def __init__(self):
        self.config = self._load_config()
        self.email = EmailNotifier(
            username=self.config.get('gmail_email'),
            password=self.config.get('gmail_password')
        )
        self.alert_threshold = self.config.get('alert_threshold', 70)
        self.last_alert_time = {}
        self.cooldown_seconds = 60
    
    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def reload_config(self):
        self.config = self._load_config()
        self.email = EmailNotifier(
            username=self.config.get('gmail_email'),
            password=self.config.get('gmail_password')
        )
        self.alert_threshold = self.config.get('alert_threshold', 70)
    
    def should_alert(self, event_data: Dict[str, Any]) -> bool:
        risk_score = event_data.get('risk_score', 0)
        decision = event_data.get('access_decision', '')
        
        if decision == 'BLOCK' or risk_score >= self.alert_threshold:
            event_key = f"{event_data.get('source_ip', '')}_{event_data.get('attack_type', '')}"
            now = time.time()
            
            if event_key in self.last_alert_time:
                if now - self.last_alert_time[event_key] < self.cooldown_seconds:
                    return False
            
            self.last_alert_time[event_key] = now
            return True
        
        return False
    
    def send_alert(self, event_data: Dict[str, Any]) -> dict:
        results = {"email": False}
        
        if not self.should_alert(event_data):
            return results
        
        # Load user preferences for broadcasting
        try:
            from services.auth_service import auth_service
            users_data = auth_service.get_all_users()
        except Exception as e:
            print(f"Error loading users: {e}")
            users_data = {}
            
        email_recipients = []

        # 1. Global Admin Config recipients
        global_recipients = self.config.get('gmail_recipient') or self.config.get('gmail_email')
        if global_recipients:
            email_recipients.extend([r.strip() for r in global_recipients.split(',')])
        
        # 2. Add Users based on preferences
        risk_score = event_data.get('risk_score', 0)
        is_critical = risk_score >= 80

        for email, u in users_data.items():
             prefs = u.get('preferences', {})
             # Email
             if prefs.get('email_alerts', True):
                 if prefs.get('critical_only', False) and not is_critical:
                     pass
                 else:
                     if email not in email_recipients:
                        email_recipients.append(email)
             
        # 3. Send Alerts
        # Email (batch)
        if self.config.get('auto_notify', True) and self.email.is_configured():
            # Dedup emails
            email_recipients = list(set(email_recipients))
            if email_recipients:
                results["email"] = self.email.send_alert(email_recipients, event_data)
        
        return results
    
    def send_daily_summary(self, summary_data: Dict[str, Any]) -> dict:
        results = {"email": False}
        
        if self.config.get('auto_notify', True) and self.email.is_configured():
            recipients = self.config.get('gmail_recipient') or self.config.get('gmail_email')
            if recipients:
                recipient_list = [r.strip() for r in recipients.split(',')]
                results["email"] = self.email.send_daily_report(recipient_list, summary_data)
        
        return results


alert_service = AlertService()


def trigger_alert(event_data: Dict[str, Any]) -> dict:
    return alert_service.send_alert(event_data)


def send_test_alert():
    test_event = {
        "attack_type": "Test Alert",
        "risk_score": 85,
        "source_ip": "192.168.1.100",
        "target_host": "srv-test-01",
        "access_decision": "BLOCK",
        "automated_response": "Test - No action taken"
    }
    return alert_service.send_alert(test_event)
