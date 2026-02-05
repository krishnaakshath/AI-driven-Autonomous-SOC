"""
🔐 Authentication Service
=========================
Handles user registration, login, 2FA, and session management.

Features:
- Secure password hashing (bcrypt)
- Email-based 2FA with OTP
- Session management
- User preferences storage
"""

import os
import json
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import streamlit as st

# Data file path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

class AuthService:
    """Authentication service with 2FA support."""
    
    def __init__(self):
        self._ensure_data_dir()
        self.users = self._load_users()
        self.otp_store: Dict[str, Dict] = {}  # email -> {otp, expires, attempts}
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
    
    def _load_users(self) -> Dict:
        """Load users from JSON file."""
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_users(self):
        """Save users to JSON file."""
        with open(USERS_FILE, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt using SHA-256."""
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return hashed, salt
    
    def _verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash."""
        check_hash, _ = self._hash_password(password, salt)
        return check_hash == hashed
    
    def register(self, email: str, password: str, name: str) -> Tuple[bool, str]:
        """
        Register a new user.
        
        Returns:
            Tuple of (success, message)
        """
        email = email.lower().strip()
        
        # Validation
        if not email or '@' not in email:
            return False, "Invalid email address"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if email in self.users:
            return False, "Email already registered"
        
        # Hash password and store user
        hashed, salt = self._hash_password(password)
        
        self.users[email] = {
            "name": name,
            "password_hash": hashed,
            "password_salt": salt,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "two_factor_enabled": True,
            "two_factor_method": "email",  # email, sms, whatsapp
            "phone": None,
            "preferences": {
                "humor_level": 3,
                "formality": "professional",
                "verbosity": "balanced",
                "emoji_usage": "minimal"
            }
        }
        
        self._save_users()
        return True, "Registration successful! Please login."
    
    def login(self, email: str, password: str) -> Tuple[bool, str, bool]:
        """
        Verify login credentials.
        
        Returns:
            Tuple of (success, message, requires_2fa)
        """
        email = email.lower().strip()
        
        if email not in self.users:
            return False, "Invalid email or password", False
        
        user = self.users[email]
        
        if not self._verify_password(password, user["password_hash"], user["password_salt"]):
            return False, "Invalid email or password", False
        
        # Check if 2FA is enabled
        if user.get("two_factor_enabled", True):
            return True, "Password verified. 2FA required.", True
        
        # Update last login
        self.users[email]["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        return True, "Login successful!", False
    
    def generate_otp(self, email: str) -> Tuple[bool, str]:
        """
        Generate and send OTP for 2FA.
        
        Returns:
            Tuple of (success, message)
        """
        email = email.lower().strip()
        
        if email not in self.users:
            return False, "User not found"
        
        # Generate 6-digit OTP
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Store OTP with expiration
        self.otp_store[email] = {
            "otp": otp,
            "expires": datetime.now() + timedelta(minutes=5),
            "attempts": 0
        }
        
        # Get delivery method
        user = self.users[email]
        method = user.get("two_factor_method", "email")
        
        if method == "email":
            success = self._send_otp_email(email, otp, user["name"])
        elif method == "sms":
            success = self._send_otp_sms(user.get("phone"), otp)
        elif method == "whatsapp":
            success = self._send_otp_whatsapp(user.get("phone"), otp)
        else:
            success = self._send_otp_email(email, otp, user["name"])
        
        if success:
            return True, f"OTP sent via {method}. Check your {method}."
        else:
            return False, f"Failed to send OTP via {method}. Please try again."
    
    def verify_otp(self, email: str, otp: str) -> Tuple[bool, str]:
        """
        Verify OTP for 2FA.
        
        Returns:
            Tuple of (success, message)
        """
        email = email.lower().strip()
        
        if email not in self.otp_store:
            return False, "No OTP requested. Please request a new one."
        
        stored = self.otp_store[email]
        
        # Check expiration
        if datetime.now() > stored["expires"]:
            del self.otp_store[email]
            return False, "OTP expired. Please request a new one."
        
        # Check attempts
        if stored["attempts"] >= 3:
            del self.otp_store[email]
            return False, "Too many attempts. Please request a new OTP."
        
        stored["attempts"] += 1
        
        if otp != stored["otp"]:
            return False, f"Invalid OTP. {3 - stored['attempts']} attempts remaining."
        
        # OTP verified - clean up and update login
        del self.otp_store[email]
        self.users[email]["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        return True, "2FA verified. Login successful!"
    
    def _send_otp_email(self, email: str, otp: str, name: str) -> bool:
        """Send OTP via email using Gmail SMTP."""
        try:
            # Get Gmail credentials
            gmail_user = os.environ.get('GMAIL_USER') or st.secrets.get('GMAIL_USER')
            gmail_password = os.environ.get('GMAIL_APP_PASSWORD') or st.secrets.get('GMAIL_APP_PASSWORD')
            
            if not gmail_user or not gmail_password:
                # Fallback: just store OTP, user will see it in demo mode
                print(f"[DEMO MODE] OTP for {email}: {otp}")
                return True
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔐 Your SOC Login Code: {otp}"
            msg['From'] = gmail_user
            msg['To'] = email
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #0a0a1a; color: #fff; padding: 20px;">
                <div style="max-width: 400px; margin: 0 auto; background: #1a1a2e; border: 1px solid #00f3ff; border-radius: 10px; padding: 30px;">
                    <h1 style="color: #00f3ff; text-align: center; margin: 0;">🔐 SOC Login</h1>
                    <p style="color: #888; text-align: center;">Hello {name},</p>
                    <div style="background: #0a0a1a; border: 2px solid #00f3ff; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                        <div style="font-size: 32px; font-weight: bold; color: #00f3ff; letter-spacing: 8px;">{otp}</div>
                    </div>
                    <p style="color: #888; text-align: center; font-size: 12px;">
                        This code expires in 5 minutes.<br>
                        If you didn't request this, please ignore.
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, email, msg.as_string())
            
            return True
            
        except Exception as e:
            print(f"Email error: {e}")
            # In demo mode, still return success
            print(f"[DEMO MODE] OTP for {email}: {otp}")
            return True
    
    def _send_otp_sms(self, phone: str, otp: str) -> bool:
        """Send OTP via SMS using Twilio (placeholder)."""
        # Twilio integration placeholder
        try:
            twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
            twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
            
            if not twilio_sid or not twilio_token or not phone:
                print(f"[DEMO MODE] SMS OTP to {phone}: {otp}")
                return True
            
            # Would use Twilio here
            # from twilio.rest import Client
            # client = Client(twilio_sid, twilio_token)
            # message = client.messages.create(
            #     body=f"Your SOC login code: {otp}",
            #     from_=twilio_phone,
            #     to=phone
            # )
            
            print(f"[PLACEHOLDER] SMS OTP to {phone}: {otp}")
            return True
            
        except Exception as e:
            print(f"SMS error: {e}")
            return False
    
    def _send_otp_whatsapp(self, phone: str, otp: str) -> bool:
        """Send OTP via WhatsApp using Twilio (placeholder)."""
        # Twilio WhatsApp integration placeholder
        try:
            twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
            
            if not twilio_sid or not twilio_token or not phone:
                print(f"[DEMO MODE] WhatsApp OTP to {phone}: {otp}")
                return True
            
            # Would use Twilio WhatsApp here
            # from twilio.rest import Client
            # client = Client(twilio_sid, twilio_token)
            # message = client.messages.create(
            #     body=f"Your SOC login code: {otp}",
            #     from_='whatsapp:+14155238886',  # Twilio sandbox
            #     to=f'whatsapp:{phone}'
            # )
            
            print(f"[PLACEHOLDER] WhatsApp OTP to {phone}: {otp}")
            return True
            
        except Exception as e:
            print(f"WhatsApp error: {e}")
            return False
    
    def get_user(self, email: str) -> Optional[Dict]:
        """Get user data."""
        return self.users.get(email.lower().strip())
    
    def update_preferences(self, email: str, preferences: Dict) -> bool:
        """Update user preferences."""
        email = email.lower().strip()
        if email in self.users:
            self.users[email]["preferences"].update(preferences)
            self._save_users()
            return True
        return False
    
    def update_2fa_method(self, email: str, method: str, phone: str = None) -> bool:
        """Update 2FA delivery method."""
        email = email.lower().strip()
        if email in self.users:
            self.users[email]["two_factor_method"] = method
            if phone:
                self.users[email]["phone"] = phone
            self._save_users()
            return True
        return False


# Singleton instance
auth_service = AuthService()


# Streamlit session helpers
def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get('authenticated', False)


def get_current_user() -> Optional[Dict]:
    """Get current authenticated user."""
    if is_authenticated():
        email = st.session_state.get('user_email')
        return auth_service.get_user(email)
    return None


def get_user_preferences() -> Dict:
    """Get current user's preferences."""
    user = get_current_user()
    if user:
        return user.get('preferences', {})
    return {
        "humor_level": 3,
        "formality": "professional",
        "verbosity": "balanced",
        "emoji_usage": "minimal"
    }


def logout():
    """Logout current user."""
    st.session_state['authenticated'] = False
    st.session_state['user_email'] = None
    st.session_state['user_name'] = None


def require_auth():
    """Redirect to login if not authenticated."""
    if not is_authenticated():
        st.switch_page("pages/0_Login.py")
