import os
import json
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
from alerting.telegram_bot import TelegramNotifier
from alerting.email_sender import EmailNotifier

CONFIG_FILE = ".soc_config.json"

class AlertService:
    
    def __init__(self):
        self.config = self._load_config()
        self.telegram = TelegramNotifier(
            bot_token=self.config.get('telegram_token'),
            chat_id=self.config.get('telegram_chat_id')
        )
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
        self.telegram = TelegramNotifier(
            bot_token=self.config.get('telegram_token'),
            chat_id=self.config.get('telegram_chat_id')
        )
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
        results = {"telegram": False, "email": False}
        
        if not self.should_alert(event_data):
            return results
        
        if self.config.get('notification_telegram', True) and self.telegram.is_configured():
            results["telegram"] = self.telegram.send_alert(event_data)
        
        if self.config.get('notification_email', True) and self.email.is_configured():
            recipients = self.config.get('gmail_recipient', self.config.get('gmail_email', ''))
            if recipients:
                recipient_list = [r.strip() for r in recipients.split(',')]
                results["email"] = self.email.send_alert(recipient_list, event_data)
        
        return results
    
    def send_daily_summary(self, summary_data: Dict[str, Any]) -> dict:
        results = {"telegram": False, "email": False}
        
        if self.config.get('notification_telegram', True) and self.telegram.is_configured():
            results["telegram"] = self.telegram.send_daily_summary(summary_data)
        
        if self.config.get('notification_email', True) and self.email.is_configured():
            recipients = self.config.get('gmail_recipient', self.config.get('gmail_email', ''))
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
