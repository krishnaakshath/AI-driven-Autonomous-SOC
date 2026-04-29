"""
Alert Notification Service
===========================
Sends email alerts to the SOC admin / affected user when HIGH or CRITICAL
events are detected. Uses Gmail SMTP with credentials from .soc_config.json.

Features:
- Rate-limited: max 1 email per recipient per 5 minutes to avoid spam
- HTML-formatted professional alert emails
- Supports per-user routing (if user email is known)
- Telegram fallback notification
"""

import os
import json
import smtplib
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from services.logger import get_logger

logger = get_logger("alert_notifier")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".soc_config.json")


def _load_config() -> dict:
    """Load notification config from .soc_config.json."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


class AlertNotifier:
    """Sends email/Telegram notifications for high-severity alerts."""

    # Rate-limit: at most 1 email per recipient per 5 minutes
    COOLDOWN_SECONDS = 300

    def __init__(self):
        cfg = _load_config()
        self.gmail_user = cfg.get("gmail_email", "")
        self.gmail_password = cfg.get("gmail_password", "")
        self.default_recipient = cfg.get("gmail_recipient", "")
        self.telegram_token = cfg.get("telegram_token", "")
        self.telegram_chat_id = cfg.get("telegram_chat_id", "")
        self.enabled_email = cfg.get("notification_email", "true").lower() == "true"
        self.enabled_telegram = cfg.get("notification_telegram", "true").lower() == "true"

        # {recipient_email: last_sent_timestamp}
        self._cooldowns: Dict[str, float] = {}
        self._lock = threading.Lock()

    def reload_config(self):
        """Reload credentials from disk (if changed at runtime)."""
        cfg = _load_config()
        self.gmail_user = cfg.get("gmail_email", "")
        self.gmail_password = cfg.get("gmail_password", "")
        self.default_recipient = cfg.get("gmail_recipient", "")

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def notify(self, alert: Dict, recipient: Optional[str] = None):
        """
        Send notification for a single alert.
        Only fires for HIGH / CRITICAL severity.
        Runs in a background thread to avoid blocking the UI.

        Args:
            alert: dict with keys like severity, title, source_ip, event_type, details, timestamp
            recipient: email to notify. Falls back to default_recipient.
        """
        severity = str(alert.get("severity", "")).upper()
        if severity not in ("HIGH", "CRITICAL"):
            return  # Only alert on high/critical

        target = (recipient or self.default_recipient or "").strip()
        if not target:
            logger.debug("No recipient configured — skipping notification")
            return

        # Rate-limit check
        with self._lock:
            last_sent = self._cooldowns.get(target, 0)
            if time.time() - last_sent < self.COOLDOWN_SECONDS:
                logger.debug("Cooldown active for %s — skipping", target)
                return
            self._cooldowns[target] = time.time()

        # Fire-and-forget in background thread
        t = threading.Thread(target=self._send, args=(alert, target), daemon=True)
        t.start()

    def notify_batch(self, alerts: List[Dict], recipient: Optional[str] = None):
        """
        Send a single digest email for a batch of HIGH/CRITICAL alerts.
        Useful when the SIEM ingests many events at once.
        """
        high_alerts = [a for a in alerts if str(a.get("severity", "")).upper() in ("HIGH", "CRITICAL")]
        if not high_alerts:
            return

        target = (recipient or self.default_recipient or "").strip()
        if not target:
            return

        with self._lock:
            last_sent = self._cooldowns.get(target, 0)
            if time.time() - last_sent < self.COOLDOWN_SECONDS:
                return
            self._cooldowns[target] = time.time()

        t = threading.Thread(target=self._send_digest, args=(high_alerts, target), daemon=True)
        t.start()

    # ═══════════════════════════════════════════════════════════════════════
    # EMAIL
    # ═══════════════════════════════════════════════════════════════════════

    def _send(self, alert: Dict, recipient: str):
        """Send a single alert email + optional Telegram."""
        severity = alert.get("severity", "HIGH")
        title = alert.get("title", alert.get("event_type", "Security Alert"))
        source_ip = alert.get("source_ip", "N/A")
        details = str(alert.get("details", ""))[:300]
        timestamp = alert.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        source = alert.get("source", "SIEM")

        sev_color = "#FF0066" if severity == "CRITICAL" else "#FF4444"

        # --- Email ---
        if self.enabled_email and self.gmail_user and self.gmail_password:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"[SOC {severity}] {title}"
                msg["From"] = self.gmail_user
                msg["To"] = recipient

                html = f"""
                <html>
                <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #0a0e1a; color: #e0e6f0; padding: 0; margin: 0;">
                  <div style="max-width: 560px; margin: 20px auto; background: #111827; border: 1px solid {sev_color}44; border-radius: 12px; overflow: hidden;">
                    <div style="background: {sev_color}; padding: 16px 24px;">
                      <h2 style="margin: 0; color: #fff; font-size: 1.1rem; letter-spacing: 1px;">
                        ⚠ {severity} ALERT — SOC Platform
                      </h2>
                    </div>
                    <div style="padding: 24px;">
                      <h3 style="color: #00d4ff; margin: 0 0 12px 0;">{title}</h3>
                      <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                        <tr>
                          <td style="color: #8b95a5; padding: 6px 0; width: 120px;">Severity</td>
                          <td style="color: {sev_color}; font-weight: bold;">{severity}</td>
                        </tr>
                        <tr>
                          <td style="color: #8b95a5; padding: 6px 0;">Source IP</td>
                          <td style="color: #e0e6f0; font-family: monospace;">{source_ip}</td>
                        </tr>
                        <tr>
                          <td style="color: #8b95a5; padding: 6px 0;">Source</td>
                          <td style="color: #e0e6f0;">{source}</td>
                        </tr>
                        <tr>
                          <td style="color: #8b95a5; padding: 6px 0;">Timestamp</td>
                          <td style="color: #e0e6f0;">{timestamp}</td>
                        </tr>
                      </table>
                      <div style="margin-top: 16px; padding: 12px; background: rgba(255,255,255,0.03); border-left: 3px solid {sev_color}; border-radius: 0 6px 6px 0;">
                        <p style="margin: 0; color: #c0c8d4; font-size: 0.85rem;">{details}</p>
                      </div>
                      <div style="margin-top: 20px; text-align: center;">
                        <a href="https://socdashboard.streamlit.app/SOAR_Response"
                           style="display: inline-block; padding: 10px 28px; background: {sev_color}; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 0.9rem;">
                          View in SOC Dashboard →
                        </a>
                      </div>
                    </div>
                    <div style="padding: 12px 24px; background: rgba(255,255,255,0.02); text-align: center;">
                      <p style="margin: 0; color: #4a5568; font-size: 0.7rem;">AI-Driven Autonomous SOC • Automated Alert</p>
                    </div>
                  </div>
                </body>
                </html>
                """
                msg.attach(MIMEText(html, "html"))

                with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
                    server.login(self.gmail_user, self.gmail_password)
                    server.sendmail(self.gmail_user, recipient, msg.as_string())

                logger.info("Alert email sent to %s: [%s] %s", recipient, severity, title)
            except Exception as e:
                logger.warning("Failed to send alert email: %s", e)

        # --- Telegram ---
        if self.enabled_telegram and self.telegram_token and self.telegram_chat_id:
            self._send_telegram(f"⚠️ *{severity} ALERT*\n\n*{title}*\nSource IP: `{source_ip}`\nTime: {timestamp}\n\n{details[:200]}")

    def _send_digest(self, alerts: List[Dict], recipient: str):
        """Send a digest email summarizing multiple alerts."""
        if not self.gmail_user or not self.gmail_password:
            return

        critical_count = sum(1 for a in alerts if a.get("severity") == "CRITICAL")
        high_count = len(alerts) - critical_count

        rows_html = ""
        for a in alerts[:15]:  # Cap at 15 rows
            sev = a.get("severity", "HIGH")
            sc = "#FF0066" if sev == "CRITICAL" else "#FF4444"
            rows_html += f"""
            <tr style="border-bottom: 1px solid #1e293b;">
              <td style="padding: 8px; color: {sc}; font-weight: bold; font-size: 0.8rem;">{sev}</td>
              <td style="padding: 8px; color: #e0e6f0; font-size: 0.85rem;">{a.get('title', a.get('event_type', 'Alert'))}</td>
              <td style="padding: 8px; color: #8b95a5; font-family: monospace; font-size: 0.8rem;">{a.get('source_ip', 'N/A')}</td>
            </tr>"""

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[SOC] {len(alerts)} High-Severity Alerts Detected"
            msg["From"] = self.gmail_user
            msg["To"] = recipient

            html = f"""
            <html>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #0a0e1a; color: #e0e6f0; padding: 0; margin: 0;">
              <div style="max-width: 600px; margin: 20px auto; background: #111827; border: 1px solid #FF444444; border-radius: 12px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #FF0066, #FF4444); padding: 16px 24px;">
                  <h2 style="margin: 0; color: #fff;">⚠ {len(alerts)} Security Alerts</h2>
                  <p style="margin: 4px 0 0; color: rgba(255,255,255,0.8); font-size: 0.85rem;">{critical_count} Critical • {high_count} High</p>
                </div>
                <div style="padding: 16px 24px;">
                  <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                      <tr style="border-bottom: 2px solid #1e293b;">
                        <th style="text-align: left; padding: 8px; color: #8b95a5; font-size: 0.75rem;">SEV</th>
                        <th style="text-align: left; padding: 8px; color: #8b95a5; font-size: 0.75rem;">ALERT</th>
                        <th style="text-align: left; padding: 8px; color: #8b95a5; font-size: 0.75rem;">SOURCE</th>
                      </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                  </table>
                  <div style="margin-top: 20px; text-align: center;">
                    <a href="https://socdashboard.streamlit.app/SOAR_Response"
                       style="display: inline-block; padding: 10px 28px; background: #FF4444; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600;">
                      Open SOC Dashboard →
                    </a>
                  </div>
                </div>
                <div style="padding: 10px 24px; background: rgba(255,255,255,0.02); text-align: center;">
                  <p style="margin: 0; color: #4a5568; font-size: 0.7rem;">AI-Driven Autonomous SOC • Alert Digest</p>
                </div>
              </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
                server.login(self.gmail_user, self.gmail_password)
                server.sendmail(self.gmail_user, recipient, msg.as_string())

            logger.info("Digest email sent to %s: %d alerts", recipient, len(alerts))
        except Exception as e:
            logger.warning("Failed to send digest email: %s", e)

        # Telegram summary
        if self.enabled_telegram and self.telegram_token and self.telegram_chat_id:
            self._send_telegram(f"🚨 *{len(alerts)} Security Alerts*\n{critical_count} Critical, {high_count} High\n\nCheck SOC Dashboard for details.")

    def _send_telegram(self, text: str):
        """Send a Telegram notification."""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            requests.post(url, json={
                "chat_id": self.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }, timeout=5)
            logger.info("Telegram notification sent")
        except Exception as e:
            logger.debug("Telegram failed: %s", e)


# Singleton
alert_notifier = AlertNotifier()
