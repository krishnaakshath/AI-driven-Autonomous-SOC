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
# Data file path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
SESSIONS_FILE = os.path.join(DATA_DIR, 'sessions.json')

class AuthService:
    """Authentication service with 2FA support and persistent storage."""
    
    def __init__(self):
        self._ensure_data_dir()
        # NOTE: users are loaded fresh from disk on every access via the
        # `users` property — this fixes the persistence bug where
        # registrations were lost because the old singleton cached data
        # in memory at import time.
    
    @property
    def users(self) -> Dict:
        """Always read users from disk to ensure persistence across sessions."""
        return self._load_users()
    
    @users.setter
    def users(self, value: Dict):
        """Write-through: setting users writes immediately to disk."""
        self._save_users_data(value)
    
    @property
    def otp_store(self):
        """Get OTP store from session state (persists across requests)."""
        if 'otp_store' not in st.session_state:
            st.session_state.otp_store = {}
        return st.session_state.otp_store
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def _load_users(self) -> Dict:
        """Load users from JSON file (called on every access)."""
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r') as f:
                    data = json.load(f)
                return data if isinstance(data, dict) else {}
            except (json.JSONDecodeError, IOError) as e:
                # Corrupted file — try backup
                backup = USERS_FILE + '.bak'
                if os.path.exists(backup):
                    try:
                        with open(backup, 'r') as f:
                            return json.load(f)
                    except Exception:
                        pass
                print(f"[AUTH] Warning: corrupted users.json: {e}")
        return {}
    
    def _save_users_data(self, data: Dict):
        """Atomically save users to JSON file (temp write + rename)."""
        import tempfile
        self._ensure_data_dir()
        # Write to temp file first, then atomic rename
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=DATA_DIR, suffix='.tmp', prefix='users_'
        )
        try:
            with os.fdopen(tmp_fd, 'w') as f:
                json.dump(data, f, indent=2)
            # Keep a backup of the previous file
            if os.path.exists(USERS_FILE):
                backup = USERS_FILE + '.bak'
                try:
                    import shutil
                    shutil.copy2(USERS_FILE, backup)
                except Exception:
                    pass
            # Atomic rename
            os.replace(tmp_path, USERS_FILE)
        except Exception as e:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise e
    
    def _save_users(self):
        """Save current in-memory users to disk."""
        self._save_users_data(self._load_users())
    
    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password using bcrypt (salt is part of hash)."""
        try:
            import bcrypt
            # Bcrypt handles salt internally
            pwd_bytes = password.encode('utf-8')
            salt_bytes = bcrypt.gensalt()
            hashed = bcrypt.hashpw(pwd_bytes, salt_bytes)
            return hashed.decode('utf-8'), salt_bytes.decode('utf-8')
        except ImportError:
            # Fallback
            if salt is None:
                salt = secrets.token_hex(16)
            hashed = hashlib.sha256((password + salt).encode()).hexdigest()
            return hashed, salt
    
    def _verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify password using bcrypt or SHA-256."""
        try:
            import bcrypt
            # Check if stored password looks like bcrypt
            if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            else:
                # Legacy SHA-256
                legacy_hashed = hashlib.sha256((password + salt).encode()).hexdigest()
                return legacy_hashed == hashed
        except ImportError:
            legacy_hashed = hashlib.sha256((password + salt).encode()).hexdigest()
            return legacy_hashed == hashed
    
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
        
        # Determine role: owner for ADMIN_EMAILS, user for everyone else
        role = 'owner' if email in [e.lower() for e in ADMIN_EMAILS] else 'user'
        
        # Load current users, add new user, save back
        current_users = self._load_users()
        current_users[email] = {
            "name": name,
            "password_hash": hashed,
            "password_salt": salt,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "two_factor_enabled": True,
            "two_factor_method": "email",
            "phone": None,
            "preferences": {
                "humor_level": 3,
                "formality": "professional",
                "verbosity": "balanced",
                "emoji_usage": "minimal"
            }
        }
        
        self._save_users_data(current_users)
        return True, "Registration successful! Please login."
    
    def login(self, email: str, password: str) -> Tuple[bool, str, bool]:
        """
        Verify login credentials.
        
        Returns:
            Tuple of (success, message, requires_2fa)
        """
        email = email.lower().strip()
        
        current_users = self._load_users()
        
        if email not in current_users:
            return False, "Invalid email or password", False
        
        user = current_users[email]
        
        if not self._verify_password(password, user["password_hash"], user["password_salt"]):
            return False, "Invalid email or password", False
        
        # ADMIN/OWNER BYPASS: Admins skip 2FA entirely
        if email in [e.lower() for e in ADMIN_EMAILS]:
            current_users[email]["last_login"] = datetime.now().isoformat()
            self._save_users_data(current_users)
            return True, "Admin login successful!", False
        
        # Check if 2FA is enabled for regular users
        if user.get("two_factor_enabled", True):
            return True, "Password verified. 2FA required.", True
        
        # Update last login
        current_users[email]["last_login"] = datetime.now().isoformat()
        self._save_users_data(current_users)
        
        return True, "Login successful!", False
    
    # ── Session Management ───────────────────────────────────────────────────
    
    def _load_sessions(self) -> Dict:
        """Load active sessions from disk."""
        if os.path.exists(SESSIONS_FILE):
            try:
                with open(SESSIONS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_sessions(self, sessions: Dict):
        """Save active sessions to disk."""
        self._ensure_data_dir()
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)

    def create_session(self, email: str, remember: bool = False) -> str:
        """Create a new persistent session token."""
        token = secrets.token_urlsafe(32)
        sessions = self._load_sessions()
        
        # Expiry: 7 days if remember me, else 24 hours
        duration = timedelta(days=7) if remember else timedelta(hours=24)
        expiry = (datetime.now() + duration).isoformat()
        
        sessions[token] = {
            "email": email,
            "expires": expiry,
            "created": datetime.now().isoformat()
        }
        
        # Clean up expired sessions while we're at it
        now = datetime.now().isoformat()
        sessions = {k: v for k, v in sessions.items() if v['expires'] > now}
        
        self._save_sessions(sessions)
        return token
    
    def validate_session(self, token: str) -> Optional[str]:
        """Validate a session token and return the email if valid."""
        if not token:
            return None
            
        sessions = self._load_sessions()
        if token not in sessions:
            return None
            
        session = sessions[token]
        if datetime.now().isoformat() > session['expires']:
            del sessions[token]
            self._save_sessions(sessions)
            return None
            
        return session['email']
    
    def invalidate_session(self, token: str):
        """Invalidate a session token (logout)."""
        if not token:
            return
        sessions = self._load_sessions()
        if token in sessions:
            del sessions[token]
            self._save_sessions(sessions)

    def generate_otp(self, email: str) -> Tuple[bool, str]:
        """
        Generate and send OTP for 2FA.
        
        Returns:
            Tuple of (success, message)
            Also stores otp_fallback_code in self for UI display when email fails.
        """
        email = email.lower().strip()
        
        if email not in self._load_users():
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
        user = self._load_users()[email]
        method = user.get("two_factor_method", "email")
        
        if method == "email":
            email_actually_sent = self._send_otp_email(email, otp, user["name"])
        elif method == "sms":
            email_actually_sent = self._send_otp_sms(user.get("phone"), otp)
        elif method == "whatsapp":
            email_actually_sent = self._send_otp_whatsapp(user.get("phone"), otp)
        else:
            email_actually_sent = self._send_otp_email(email, otp, user["name"])
        
        if email_actually_sent == 'sent':
            # Email was truly delivered via SMTP
            self._last_otp_fallback = None
            return True, f"OTP sent via {method}. Check your {method}."
        else:
            # Email failed to send — store OTP for UI fallback display
            self._last_otp_fallback = otp
            return True, f"OTP generated. (Email delivery unavailable — code shown on screen)."
    
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
        current_users = self._load_users()
        if email in current_users:
            current_users[email]["last_login"] = datetime.now().isoformat()
            self._save_users_data(current_users)
        
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
                print(f"[WARNING] No Gmail credentials configured. OTP for {email}: {otp}")
                return 'fallback'  # Signal that email was NOT sent
            
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Your SOC Login Code: {otp}"
            msg['From'] = gmail_user
            msg['To'] = email
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #0a0a1a; color: #fff; padding: 20px;">
                <div style="max-width: 400px; margin: 0 auto; background: #1a1a2e; border: 1px solid #00f3ff; border-radius: 10px; padding: 30px;">
                    <h1 style="color: #00f3ff; text-align: center; margin: 0;">SOC Login</h1>
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
            
            return 'sent'  # Email was actually delivered
            
        except Exception as e:
            print(f"Email error: {e}")
            print(f"[FALLBACK] OTP for {email}: {otp}")
            return 'fallback'  # Signal that email was NOT sent
    
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
        """Get user data (reads fresh from disk)."""
        return self._load_users().get(email.lower().strip())
    
    def get_all_users(self) -> Dict:
        """Get all users (reads fresh from disk). For admin use."""
        return self._load_users()
    
    def update_user_role(self, email: str, role: str) -> bool:
        """Update a user's role. Admin-only operation."""
        email = email.lower().strip()
        if role not in ('owner', 'admin', 'user'):
            return False
        current_users = self._load_users()
        if email in current_users:
            current_users[email]['role'] = role
            self._save_users_data(current_users)
            return True
        return False
    
    def disable_user(self, email: str) -> bool:
        """Disable a user account. Admin-only operation."""
        email = email.lower().strip()
        current_users = self._load_users()
        if email in current_users:
            current_users[email]['disabled'] = True
            self._save_users_data(current_users)
            return True
        return False
    
    def enable_user(self, email: str) -> bool:
        """Re-enable a disabled user account."""
        email = email.lower().strip()
        current_users = self._load_users()
        if email in current_users:
            current_users[email]['disabled'] = False
            self._save_users_data(current_users)
            return True
        return False
    
    def update_preferences(self, email: str, preferences: Dict) -> bool:
        """Update user preferences. Auto-creates admin user if missing."""
        email = email.lower().strip()
        current_users = self._load_users()
        
        # Self-healing: If user is missing but is an ADMIN, create them
        if email not in current_users and email in [e.lower() for e in ADMIN_EMAILS]:
            current_users[email] = {
                "name": "Admin",
                "password_hash": "", # No password needed for bypass admins
                "password_salt": "",
                "role": "owner",
                "created_at": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat(),
                "two_factor_enabled": False, # Admins bypass 2FA
                "preferences": {}
            }
            
        if email in current_users:
            current_users[email].setdefault('preferences', {}).update(preferences)
            self._save_users_data(current_users)
            return True
        return False
    
    def update_2fa_method(self, email: str, method: str, phone: str = None) -> bool:
        """Update 2FA delivery method."""
        email = email.lower().strip()
        current_users = self._load_users()
        if email in current_users:
            current_users[email]["two_factor_method"] = method
            if phone:
                current_users[email]["phone"] = phone
            self._save_users_data(current_users)
            return True
        return False
    
    # ── TOTP-based MFA ───────────────────────────────────────────────────
    
    def setup_totp(self, email: str) -> Tuple[bool, str]:
        """
        Generate a TOTP secret for a user and return the provisioning URI.
        The user scans this URI as a QR code in Google Authenticator / Authy.
        
        Returns:
            Tuple of (success, provisioning_uri_or_error)
        """
        email = email.lower().strip()
        current_users = self._load_users()
        if email not in current_users:
            return False, "User not found"
        
        try:
            import pyotp
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(
                name=email,
                issuer_name="SOC Platform"
            )
            
            # Store the TOTP secret in the user record
            current_users[email]['totp_secret'] = secret
            current_users[email]['two_factor_method'] = 'totp'
            current_users[email]['two_factor_enabled'] = True
            self._save_users_data(current_users)
            
            return True, uri
        except ImportError:
            return False, "pyotp not installed. Run: pip install pyotp"
        except Exception as e:
            return False, f"TOTP setup failed: {e}"
    
    def verify_totp(self, email: str, code: str) -> Tuple[bool, str]:
        """
        Verify a TOTP code from an authenticator app.
        
        Returns:
            Tuple of (success, message)
        """
        email = email.lower().strip()
        current_users = self._load_users()
        
        if email not in current_users:
            return False, "User not found"
        
        user = current_users[email]
        totp_secret = user.get('totp_secret')
        
        if not totp_secret:
            return False, "TOTP not set up. Please set up authenticator first."
        
        try:
            import pyotp
            totp = pyotp.TOTP(totp_secret)
            # valid_window=1 allows 1 step before/after (±30sec tolerance)
            if totp.verify(code, valid_window=1):
                current_users[email]["last_login"] = datetime.now().isoformat()
                self._save_users_data(current_users)
                return True, "TOTP verified. Login successful!"
            else:
                return False, "Invalid code. Please try again."
        except ImportError:
            return False, "pyotp not installed"
        except Exception as e:
            return False, f"Verification error: {e}"
    
    def get_totp_uri(self, email: str) -> Optional[str]:
        """Get TOTP provisioning URI for existing setup (for re-displaying QR)."""
        email = email.lower().strip()
        user = self._load_users().get(email)
        if not user or not user.get('totp_secret'):
            return None
        try:
            import pyotp
            totp = pyotp.TOTP(user['totp_secret'])
            return totp.provisioning_uri(name=email, issuer_name="SOC Platform")
        except Exception:
            return None
    
    def has_totp_setup(self, email: str) -> bool:
        """Check if user has TOTP configured."""
        email = email.lower().strip()
        user = self._load_users().get(email)
        return bool(user and user.get('totp_secret'))
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

def check_persistent_session():
    """Run at startup: Check for persistent session token file."""
    if is_authenticated():
        return
    
    # Check for local token file (simulating cookie for desktop app)
    token_file = os.path.join(DATA_DIR, '.session_token')
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                token = f.read().strip()
            
            email = auth_service.validate_session(token)
            if email:
                # Auto-login
                st.session_state['authenticated'] = True
                st.session_state['user_email'] = email
                user = auth_service.get_user(email)
                st.session_state['user_name'] = user.get('name') if user else email
                st.session_state['auth_token'] = token
                return True
        except:
            pass
    return False

def login_user(email: str, remember: bool = False):
    """Log in the user and set persistence."""
    st.session_state['authenticated'] = True
    st.session_state['user_email'] = email
    user = auth_service.get_user(email)
    st.session_state['user_name'] = user.get('name') if user else email
    
    # Create and save session token
    token = auth_service.create_session(email, remember)
    st.session_state['auth_token'] = token
    
    # Save to local file for persistence across restarts
    token_file = os.path.join(DATA_DIR, '.session_token')
    with open(token_file, 'w') as f:
        f.write(token)


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
    st.session_state['user_email'] = None
    st.session_state['user_name'] = None
    
    # Clear persistence
    token = st.session_state.get('auth_token')
    if token:
        auth_service.invalidate_session(token)
        st.session_state.pop('auth_token', None)
        
    token_file = os.path.join(DATA_DIR, '.session_token')
    if os.path.exists(token_file):
        try:
            os.remove(token_file)
        except:
            pass


def require_auth():
    """Redirect to login if not authenticated."""
    if not is_authenticated():
        st.switch_page("pages/_Login.py")


def get_api_token_expiry():
    """Get API token expiry time in seconds."""
    return API_TOKEN_EXPIRY_SECONDS

