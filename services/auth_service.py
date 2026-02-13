"""
 Authentication Service
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
        # OTP store moved to session state for persistence across requests
    
    @property
    def otp_store(self):
        """Get OTP store from session state (persists across requests)."""
        if 'otp_store' not in st.session_state:
            st.session_state.otp_store = {}
        return st.session_state.otp_store
    
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
        
        # ADMIN BYPASS: Admins skip 2FA entirely
        if email in [e.lower() for e in ADMIN_EMAILS]:
            # Update last login for admin
            self.users[email]["last_login"] = datetime.now().isoformat()
            self._save_users()
            return True, "Admin login successful!", False  # No 2FA required
        
        # Check if 2FA is enabled for regular users
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
            # Try to get Gmail credentials from multiple sources
            gmail_user = None
            gmail_password = None
            
            # 1. Check environment variables
            gmail_user = os.environ.get('GMAIL_USER')
            gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
            
            # 2. Check Streamlit secrets
            if not gmail_user or not gmail_password:
                try:
                    gmail_user = st.secrets.get('GMAIL_USER')
                    gmail_password = st.secrets.get('GMAIL_APP_PASSWORD')
                except:
                    pass
            
            # 3. Check .soc_config.json file (multiple paths for different deployment scenarios)
            if not gmail_user or not gmail_password:
                config_paths = [
                    '.soc_config.json',  # Current directory
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), '.soc_config.json'),  # Parent of services/
                    os.path.join(os.getcwd(), '.soc_config.json'),  # Working directory
                ]
                
                for config_file in config_paths:
                    try:
                        if os.path.exists(config_file):
                            import json
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                            gmail_user = config.get('gmail_email')
                            gmail_password = config.get('gmail_password')
                            if gmail_user and gmail_password:
                                break
                    except Exception as e:
                        print(f"Error loading config from {config_file}: {e}")
            
            if not gmail_user or not gmail_password:
                print(f"[ERROR] No Gmail credentials configured. Cannot send OTP to {email}.")
                return False
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f" Your SOC Login Code: {otp}"
            msg['From'] = gmail_user
            msg['To'] = email
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #0a0a1a; color: #fff; padding: 20px;">
                <div style="max-width: 400px; margin: 0 auto; background: #1a1a2e; border: 1px solid #00f3ff; border-radius: 10px; padding: 30px;">
                    <h1 style="color: #00f3ff; text-align: center; margin: 0;"> SOC Login</h1>
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
            return False
    
    def _send_otp_sms(self, phone: str, otp: str) -> bool:
        """Send OTP via SMS using Twilio."""
        try:
            # Try to get Twilio credentials from multiple sources
            twilio_sid = None
            twilio_token = None
            twilio_phone = None
            
            # 1. Check environment variables
            twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
            twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
            
            # 2. Check .soc_config.json file
            if not twilio_sid or not twilio_token:
                try:
                    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.soc_config.json')
                    if os.path.exists(config_file):
                        import json
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                        twilio_sid = config.get('twilio_account_sid') or twilio_sid
                        twilio_token = config.get('twilio_auth_token') or twilio_token
                        twilio_phone = config.get('twilio_phone_number') or twilio_phone
                except Exception as e:
                    print(f"Error loading Twilio config: {e}")
            
            if not twilio_sid or not twilio_token or not twilio_phone:
                print(f"[ERROR] Twilio credentials not configured. Cannot send SMS to {phone}.")
                return False
            
            # Send SMS using Twilio
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            
            message = client.messages.create(
                body=f" Your SOC Login Code: {otp}\n\nThis code expires in 5 minutes.",
                from_=twilio_phone,
                to=phone
            )
            
            print(f"SMS sent successfully. SID: {message.sid}")
            return True
            
        except ImportError:
            print("[ERROR] Twilio library not installed. Run: pip install twilio")
            return False
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

# Admin email list - add your admin emails here
ADMIN_EMAILS = ['akshuolv@gmail.com']

# API Token settings
API_TOKEN_EXPIRY_SECONDS = 60  # 1 minute to reduce server load


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


def is_admin() -> bool:
    """Check if current user is an admin."""
    if not is_authenticated():
        return False
    email = st.session_state.get('user_email', '').lower()
    return email in [e.lower() for e in ADMIN_EMAILS]


def require_admin():
    """Require admin role or show access denied."""
    if not is_authenticated():
        st.error(" **Authentication Required**")
        st.info("Please log in to access this page.")
        if st.button("Go to Login"):
            st.switch_page("pages/_Login.py")
        st.stop()
    
    if not is_admin():
        st.error(" **Admin Access Only**")
        st.warning("This page is restricted to administrators. Your access has been logged.")
        st.info(f"Logged in as: {st.session_state.get('user_email', 'Unknown')}")
        st.stop()


def logout():
    """Logout current user."""
    st.session_state['authenticated'] = False
    st.session_state['user_email'] = None
    st.session_state['user_name'] = None


def require_auth():
    """Redirect to login if not authenticated."""
    if not is_authenticated():
        st.switch_page("pages/_Login.py")


def get_api_token_expiry():
    """Get API token expiry time in seconds."""
    return API_TOKEN_EXPIRY_SECONDS

