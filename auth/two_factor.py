# Two-Factor Authentication Module
import os
import json
import random
import string
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Tuple

OTP_FILE = ".otp_codes.json"
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3


def load_otp_data() -> dict:
    if os.path.exists(OTP_FILE):
        try:
            with open(OTP_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_otp_data(data: dict):
    with open(OTP_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def generate_otp() -> str:
    """Generate a 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=6))


def create_otp(email: str) -> str:
    """Create and store OTP for email"""
    data = load_otp_data()
    otp = generate_otp()
    
    data[email] = {
        "code": otp,
        "created": datetime.now().isoformat(),
        "expires": (datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat(),
        "attempts": 0
    }
    
    save_otp_data(data)
    return otp


def verify_otp(email: str, code: str) -> Tuple[bool, str]:
    """Verify OTP code for email"""
    data = load_otp_data()
    
    if email not in data:
        return False, "No OTP requested"
    
    otp_data = data[email]
    
    # Check expiry
    expires = datetime.fromisoformat(otp_data["expires"])
    if datetime.now() > expires:
        del data[email]
        save_otp_data(data)
        return False, "OTP expired. Please request a new one."
    
    # Check attempts
    if otp_data["attempts"] >= MAX_OTP_ATTEMPTS:
        del data[email]
        save_otp_data(data)
        return False, "Too many attempts. Please request a new OTP."
    
    # Verify code
    if otp_data["code"] != code:
        data[email]["attempts"] += 1
        save_otp_data(data)
        remaining = MAX_OTP_ATTEMPTS - data[email]["attempts"]
        return False, f"Invalid code. {remaining} attempts remaining."
    
    # Success - remove OTP
    del data[email]
    save_otp_data(data)
    return True, "Verified successfully"


def send_otp_email(email: str, otp: str, recipient_email: str = None) -> Tuple[bool, str]:
    """Send OTP via Gmail"""
    try:
        config = {}
        if os.path.exists('.soc_config.json'):
            with open('.soc_config.json', 'r') as f:
                config = json.load(f)
        
        gmail_email = config.get('gmail_email', '')
        gmail_password = config.get('gmail_password', '')
        
        if not gmail_email or not gmail_password:
            return False, "Gmail not configured"
        
        target_email = recipient_email or email
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'SOC Login Verification Code: {otp}'
        msg['From'] = gmail_email
        msg['To'] = target_email
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #0a0e17; padding: 20px;">
            <div style="max-width: 400px; margin: 0 auto; background: #1a1f2e; border-radius: 16px; padding: 30px; border: 1px solid rgba(0,212,255,0.2);">
                <h2 style="color: #00D4FF; margin: 0 0 20px 0; text-align: center;">Security Verification</h2>
                <p style="color: #8B95A5; margin: 0 0 20px 0; text-align: center;">Your one-time verification code is:</p>
                <div style="background: linear-gradient(135deg, #00D4FF, #8B5CF6); border-radius: 12px; padding: 20px; text-align: center;">
                    <span style="font-size: 32px; font-weight: bold; color: white; letter-spacing: 8px;">{otp}</span>
                </div>
                <p style="color: #8B95A5; font-size: 12px; margin: 20px 0 0 0; text-align: center;">
                    This code expires in {OTP_EXPIRY_MINUTES} minutes.<br>
                    If you didn't request this, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_email, gmail_password)
            server.sendmail(gmail_email, target_email, msg.as_string())
        
        return True, f"Code sent to {target_email[:3]}***{target_email.split('@')[0][-2:]}@{target_email.split('@')[1]}"
    
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"





def get_trusted_devices(email: str) -> list:
    """Get list of trusted devices for user"""
    data = load_otp_data()
    return data.get(f"{email}_trusted", [])


def add_trusted_device(email: str, device_id: str, days: int = 365):
    """Add device to trusted list - lasts 365 days (until explicit logout)"""
    data = load_otp_data()
    key = f"{email}_trusted"
    
    if key not in data:
        data[key] = []
    
    # Clean expired devices
    data[key] = [d for d in data[key] if datetime.fromisoformat(d["expires"]) > datetime.now()]
    
    # Remove existing entry for this device if exists
    data[key] = [d for d in data[key] if d["device_id"] != device_id]
    
    # Add new device
    data[key].append({
        "device_id": device_id,
        "created": datetime.now().isoformat(),
        "expires": (datetime.now() + timedelta(days=days)).isoformat()
    })
    
    save_otp_data(data)


def remove_trusted_device(email: str, device_id: str):
    """Remove device from trusted list (on logout)"""
    data = load_otp_data()
    key = f"{email}_trusted"
    
    if key in data:
        data[key] = [d for d in data[key] if d["device_id"] != device_id]
        save_otp_data(data)


def clear_all_trusted_devices(email: str):
    """Clear all trusted devices for user (force re-verification)"""
    data = load_otp_data()
    key = f"{email}_trusted"
    
    if key in data:
        del data[key]
        save_otp_data(data)


def is_device_trusted(email: str, device_id: str) -> bool:
    """Check if device is trusted"""
    devices = get_trusted_devices(email)
    for d in devices:
        if d["device_id"] == device_id:
            if datetime.fromisoformat(d["expires"]) > datetime.now():
                return True
    return False

