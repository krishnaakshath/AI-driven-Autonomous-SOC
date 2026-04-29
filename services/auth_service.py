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
import re
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import streamlit as st
from services.logger import get_logger
logger = get_logger("auth")


# Data file path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
SESSIONS_FILE = os.path.join(DATA_DIR, 'sessions.json')

class AuthService:
    """Authentication service with 2FA support and persistent storage."""

    # Rate limiting: max attempts per minute per email
    MAX_ATTEMPTS_PER_MIN = 5

    def __init__(self):
        self._ensure_data_dir()
        self._rate_limiter = {}  # {email: [timestamps]}
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

                        logger.debug("Suppressed exception", exc_info=True)
                logger.warning("Corrupted users.json: %s", e)
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

                    logger.debug("Suppressed exception", exc_info=True)
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
        
        if len(password) < 12:
            return False, "Password must be at least 12 characters"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain an uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain a lowercase letter"
        if not re.search(r"[0-9]", password):
            return False, "Password must contain a number"
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain a special character"
        
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
        
        # Log to DB
        from services.database import db
        import uuid
        db.insert_event({
            "id": f"EVT-AUTH-{str(uuid.uuid4())[:8]}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "Active Directory",
            "event_type": "User Registration",
            "severity": "LOW",
            "source_ip": "127.0.0.1",
            "dest_ip": "127.0.0.1",
            "user": email,
            "status": "Resolved"
        })
        
        return True, "Registration successful! Please login."
    
    def _check_rate_limit(self, key: str) -> Tuple[bool, str]:
        """Returns (allowed, message). Prunes old timestamps."""
        now = datetime.now()
        window = timedelta(minutes=1)
        attempts = self._rate_limiter.get(key, [])
        attempts = [t for t in attempts if now - t < window]
        if len(attempts) >= self.MAX_ATTEMPTS_PER_MIN:
            return False, "Too many attempts. Please wait 60 seconds."
        attempts.append(now)
        self._rate_limiter[key] = attempts
        return True, ""

    def login(self, email: str, password: str) -> Tuple[bool, str, bool]:
        """
        Verify login credentials.
        
        Returns:
            Tuple of (success, message, requires_2fa)
        """
        email = email.lower().strip()

        # Rate limit check
        allowed, rate_msg = self._check_rate_limit(f"login:{email}")
        if not allowed:
            return False, rate_msg, False

        current_users = self._load_users()
        
        from services.database import db
        import uuid
        
        def log_auth_event(event_type: str, severity: str, user: str):
            db.insert_event({
                "id": f"EVT-AUTH-{str(uuid.uuid4())[:8]}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Active Directory",
                "event_type": event_type,
                "severity": severity,
                "source_ip": "127.0.0.1",
                "dest_ip": "127.0.0.1",
                "user": user,
                "status": "Resolved" if severity == "LOW" else "Open"
            })
            
        if email not in current_users:
            # AUTO-CREATE ADMIN: If admin email not in users.json (e.g. after
            # Streamlit Cloud redeploy wiped the filesystem), create admin on
            # the fly so they can always access the platform.
            if email in [e.lower() for e in ADMIN_EMAILS]:
                hashed, salt = self._hash_password(password)
                current_users[email] = {
                    "name": "Admin",
                    "password_hash": hashed,
                    "password_salt": salt,
                    "role": "owner",
                    "created_at": datetime.now().isoformat(),
                    "last_login": datetime.now().isoformat(),
                    "two_factor_enabled": False,
                    "failed_attempts": 0,
                    "preferences": {}
                }
                self._save_users_data(current_users)
                log_auth_event("Admin Auto-Provisioned", "LOW", email)
                return True, "Admin account created. Welcome!", False
            
            log_auth_event("Login Failure - Unknown User", "MEDIUM", email)
            return False, "Invalid email or password", False
        
        user = current_users[email]
        
        # Check if account is locked
        locked_until_str = user.get("locked_until")
        if locked_until_str:
            locked_until = datetime.fromisoformat(locked_until_str)
            if datetime.now() < locked_until:
                log_auth_event("Login Failure - Account Locked", "HIGH", email)
                return False, "Account locked. Try again later.", False
            else:
                user["locked_until"] = None
                user["failed_attempts"] = 0
        
        if not self._verify_password(password, user["password_hash"], user["password_salt"]):
            failed_attempts = user.get("failed_attempts", 0) + 1
            user["failed_attempts"] = failed_attempts
            if failed_attempts >= 5:
                # Lock account for 15 minutes
                user["locked_until"] = (datetime.now() + timedelta(minutes=15)).isoformat()
                log_auth_event("Account Locked - Bruteforce Protection", "CRITICAL", email)
                msg = "Account locked due to too many failed attempts. Try again in 15 minutes."
            else:
                log_auth_event("Login Failure - Bad Password", "HIGH", email)
                msg = "Invalid email or password"
            self._save_users_data(current_users)
            return False, msg, False
        
        # Reset failed attempts on success
        user["failed_attempts"] = 0
        user["locked_until"] = None
        
        # ADMIN/OWNER BYPASS: Admins skip 2FA entirely
        if email in [e.lower() for e in ADMIN_EMAILS]:
            user["last_login"] = datetime.now().isoformat()
            self._save_users_data(current_users)
            log_auth_event("Login Success (Admin Bypass)", "LOW", email)
            return True, "Admin login successful!", False
        
        # Check if 2FA is enabled for regular users
        if user.get("two_factor_enabled", True):
            log_auth_event("Login Success - Pending 2FA", "LOW", email)
            self._save_users_data(current_users)
            return True, "Password verified. 2FA required.", True
        
        # Update last login
        user["last_login"] = datetime.now().isoformat()
        self._save_users_data(current_users)
        
        log_auth_event("Login Success", "LOW", email)
        
        return True, "Login successful!", False
    
    # ── Session Management ───────────────────────────────────────────────────
    
    def _create_db_session(self, token: str, email: str, expiry: str):
        """Store session in Supabase if available."""
        from services.database import db
        if db._use_supabase:
            try:
                # Attempt to use a sessions table if it exists
                db._supabase.insert("sessions", {
                    "token": token,
                    "email": email,
                    "expires": expiry,
                    "created_at": datetime.now().isoformat()
                })
            except Exception:
                pass
                
    def _delete_db_session(self, token: str):
        """Delete session from Supabase if available."""
        from services.database import db
        if db._use_supabase:
            try:
                import requests
                requests.delete(
                    f"{db._supabase.url}/rest/v1/sessions?token=eq.{token}",
                    headers=db._supabase.headers,
                    timeout=5
                )
            except Exception:
                pass

    def _load_sessions(self) -> Dict:
        """Load active sessions from disk."""
        if os.path.exists(SESSIONS_FILE):
            try:
                with open(SESSIONS_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                logger.debug("Suppressed exception", exc_info=True)
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
        
        # Clean up expired sessions locally
        now = datetime.now().isoformat()
        sessions = {k: v for k, v in sessions.items() if v['expires'] > now}
        
        self._save_sessions(sessions)
        self._create_db_session(token, email, expiry)
        return token
    
    def validate_session(self, token: str) -> Optional[str]:
        """Validate a session token and return the email if valid."""
        if not token:
            return None
            
        sessions = self._load_sessions()
        # Fallback to Supabase if not in local cache but Supabase is connected
        if token not in sessions:
            from services.database import db
            if db._use_supabase:
                try:
                    res = db._supabase.select("sessions", limit=1, params={"token": f"eq.{token}"})
                    if res and len(res) > 0:
                        session = res[0]
                        if datetime.now().isoformat() <= session['expires']:
                            # Cache it locally
                            sessions[token] = {
                                "email": session['email'],
                                "expires": session['expires'],
                                "created": session.get('created_at', datetime.now().isoformat())
                            }
                            self._save_sessions(sessions)
                            return session['email']
                except Exception:
                    pass
            return None
            
        session = sessions[token]
        if datetime.now().isoformat() > session['expires']:
            del sessions[token]
            self._save_sessions(sessions)
            self._delete_db_session(token)
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
        self._delete_db_session(token)

    def generate_otp(self, email: str) -> Tuple[bool, str]:
        """
        Generate and send OTP for 2FA.
        
        Returns:
            Tuple of (success, message)
            Also stores otp_fallback_code in self for UI display when email fails.
        """
        email = email.lower().strip()

        # Rate limit check
        allowed, rate_msg = self._check_rate_limit(f"otp:{email}")
        if not allowed:
            return False, rate_msg

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
                except Exception:

                    logger.debug("Suppressed exception", exc_info=True)
            
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
                        logger.error("Error loading config from %s: %s", config_file, e)
            
            if not gmail_user or not gmail_password:
                logger.warning("No Gmail credentials configured. OTP for %s: %s", email, otp)
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
            logger.warning("Email: %s", e)
            logger.info("[FALLBACK] OTP for %s: %s", email, otp)
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
                    logger.error("Error loading Twilio config: %s", e)
            
            if not twilio_sid or not twilio_token or not twilio_phone:
                logger.error("Twilio credentials not configured. Cannot send SMS to %s.", phone)
                return False
            
            # Send SMS using Twilio
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            
            message = client.messages.create(
                body=f" Your SOC Login Code: {otp}\n\nThis code expires in 5 minutes.",
                from_=twilio_phone,
                to=phone
            )
            
            logger.info("SMS sent successfully. SID: %s", message.sid)
            return True
            
        except ImportError:
            logger.error("Twilio library not installed. Run: pip install twilio")
            return False
        except Exception as e:
            logger.warning("SMS: %s", e)
            return False
    
    def _send_otp_whatsapp(self, phone: str, otp: str) -> bool:
        """Send OTP via WhatsApp using Twilio (placeholder)."""
        # Twilio WhatsApp integration placeholder
        try:
            twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
            
            if not twilio_sid or not twilio_token or not phone:
                logger.info("[DEMO MODE] WhatsApp OTP to %s: %s", phone, otp)
                return True
            
            # Would use Twilio WhatsApp here
            # from twilio.rest import Client
            # client = Client(twilio_sid, twilio_token)
            # message = client.messages.create(
            #     body=f"Your SOC login code: {otp}",
            #     from_='whatsapp:+14155238886',  # Twilio sandbox
            #     to=f'whatsapp:{phone}'
            # )
            
            logger.info("[PLACEHOLDER] WhatsApp OTP to %s: %s", phone, otp)
            return True
            
        except Exception as e:
            logger.warning("WhatsApp: %s", e)
            return False
    
    def get_user(self, email: str) -> Optional[Dict]:
        """Get user data (reads fresh from disk)."""
        return self._load_users().get(email.lower().strip())
    
    def get_all_users(self) -> Dict:
        """Get all users (reads fresh from disk). For admin use."""
        return self._load_users()
    
    def update_user_role(self, email: str, role: str) -> bool:
        """Update a user's role. Admin-only operation with Audit Trail."""
        email = email.lower().strip()
        if role not in ('owner', 'admin', 'user'):
            return False
            
        current_users = self._load_users()
        if email in current_users:
            old_role = current_users[email].get('role', 'user')
            current_users[email]['role'] = role
            self._save_users_data(current_users)
            
            # DB Audit Trail for Role Changes
            try:
                from services.database import db
                import uuid
                db.insert_event({
                    "id": f"EVT-RBAC-{str(uuid.uuid4())[:8]}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "Active Directory",
                    "event_type": "Privilege Escalation" if role in ("owner", "admin") and old_role == "user" else "Role Modification",
                    "severity": "CRITICAL" if role in ("owner", "admin") else "HIGH",
                    "source_ip": "127.0.0.1",
                    "dest_ip": "127.0.0.1",
                    "user": email,
                    "status": "Audited",
                    "details": f"RBAC Audit: {email} transitioned from '{old_role}' to '{role}'"
                })
            except Exception as e:
                logger.error("Failed to append RBAC Audit Trail: %s", e)
                
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
    """Run at startup: Check for persistent session token via query params or file."""
    if is_authenticated():
        return False
    
    token = None
    
    # 1. Check query params first (works on Streamlit Cloud)
    try:
        token = st.query_params.get('session_token')
    except Exception:

        logger.debug("Suppressed exception", exc_info=True)
    
    # 2. Fall back to local token file (works locally)
    if not token:
        token_file = os.path.join(DATA_DIR, '.session_token')
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    token = f.read().strip()
            except Exception:

                logger.debug("Suppressed exception", exc_info=True)
    
    if token:
        email = auth_service.validate_session(token)
        if email:
            # Auto-login
            st.session_state['authenticated'] = True
            st.session_state['user_email'] = email
            user = auth_service.get_user(email)
            st.session_state['user_name'] = user.get('name') if user else email
            st.session_state['auth_token'] = token
            return True
    
    return False

def login_user(email: str, remember: bool = False):
    """Log in the user and set persistence via query params + file."""
    st.session_state['authenticated'] = True
    st.session_state['user_email'] = email
    user = auth_service.get_user(email)
    st.session_state['user_name'] = user.get('name') if user else email
    
    # Create and save session token
    token = auth_service.create_session(email, remember)
    st.session_state['auth_token'] = token
    
    # Save token to query params (works on Streamlit Cloud)
    try:
        st.query_params['session_token'] = token
    except Exception:

        logger.debug("Suppressed exception", exc_info=True)
    
    # Also save to local file for persistence across restarts
    try:
        token_file = os.path.join(DATA_DIR, '.session_token')
        with open(token_file, 'w') as f:
            f.write(token)
    except Exception:

        logger.debug("Suppressed exception", exc_info=True)  # May fail on read-only filesystems (Cloud)


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
    """Logout current user and clear all persistence."""
    st.session_state['authenticated'] = False
    st.session_state['user_email'] = None
    st.session_state['user_name'] = None
    
    # Clear persistence
    token = st.session_state.get('auth_token')
    if token:
        auth_service.invalidate_session(token)
        st.session_state.pop('auth_token', None)
    
    # Clear query param token
    try:
        if 'session_token' in st.query_params:
            del st.query_params['session_token']
    except Exception:

        logger.debug("Suppressed exception", exc_info=True)
        
    # Clear local token file
    token_file = os.path.join(DATA_DIR, '.session_token')
    if os.path.exists(token_file):
        try:
            os.remove(token_file)
        except Exception:

            logger.debug("Suppressed exception", exc_info=True)


def require_auth():
    """Redirect to login if not authenticated."""
    if not is_authenticated():
        st.switch_page("pages/_Login.py")


def get_api_token_expiry():
    """Get API token expiry time in seconds."""
    return API_TOKEN_EXPIRY_SECONDS

