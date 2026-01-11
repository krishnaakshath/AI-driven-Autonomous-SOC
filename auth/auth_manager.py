import os
import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import streamlit as st

AUTH_FILE = ".soc_users.json"
SESSION_DURATION = 86400


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hash_hex = stored_hash.split(':')
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hashed.hex() == hash_hex
    except:
        return False


def load_users() -> dict:
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "users": {},
        "sessions": {}
    }


def save_users(data: dict):
    with open(AUTH_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def register_user(email: str, password: str, name: str) -> Tuple[bool, str]:
    data = load_users()
    
    email = email.lower().strip()
    
    if email in data["users"]:
        return False, "Email already registered"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    if not "@" in email or not "." in email:
        return False, "Invalid email format"
    
    data["users"][email] = {
        "password": hash_password(password),
        "name": name,
        "role": "analyst",
        "created": datetime.now().isoformat(),
        "last_login": None
    }
    
    save_users(data)
    return True, "Registration successful"


def login_user(email: str, password: str) -> Tuple[bool, str, Optional[dict]]:
    data = load_users()
    
    email = email.lower().strip()
    
    if email not in data["users"]:
        return False, "Invalid email or password", None
    
    user = data["users"][email]
    
    if not verify_password(password, user["password"]):
        return False, "Invalid email or password", None
    
    session_token = secrets.token_hex(32)
    
    data["sessions"][session_token] = {
        "email": email,
        "created": time.time(),
        "expires": time.time() + SESSION_DURATION
    }
    
    data["users"][email]["last_login"] = datetime.now().isoformat()
    save_users(data)
    
    return True, "Login successful", {
        "email": email,
        "name": user["name"],
        "role": user["role"],
        "token": session_token
    }


def verify_session(token: str) -> Optional[dict]:
    if not token:
        return None
    
    data = load_users()
    
    if token not in data["sessions"]:
        return None
    
    session = data["sessions"][token]
    
    if time.time() > session["expires"]:
        del data["sessions"][token]
        save_users(data)
        return None
    
    email = session["email"]
    if email not in data["users"]:
        return None
    
    user = data["users"][email]
    return {
        "email": email,
        "name": user["name"],
        "role": user["role"]
    }


def logout_user(token: str):
    data = load_users()
    if token in data["sessions"]:
        del data["sessions"][token]
        save_users(data)


def init_default_admin():
    data = load_users()
    if "admin@soc.local" not in data["users"]:
        data["users"]["admin@soc.local"] = {
            "password": hash_password("admin123"),
            "name": "Administrator",
            "role": "admin",
            "created": datetime.now().isoformat(),
            "last_login": None
        }
        save_users(data)


def check_auth() -> Optional[dict]:
    if "auth_token" not in st.session_state:
        return None
    
    return verify_session(st.session_state.auth_token)


def require_auth():
    user = check_auth()
    if not user:
        st.switch_page("pages/0_Login.py")
        st.stop()
    return user


def show_user_info(user: dict):
    role_colors = {"admin": "#FF4444", "analyst": "#00D4FF"}
    initials = "".join([n[0].upper() for n in user['name'].split()[:2]]) if user['name'] else "U"
    
    st.sidebar.markdown(f"""
        <div style="background: rgba(26, 31, 46, 0.8); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.8rem;">
                <div style="width: 45px; height: 45px; border-radius: 50%; background: linear-gradient(135deg, #00D4FF 0%, #8B5CF6 100%); display: flex; align-items: center; justify-content: center; font-weight: 600; color: white;">{initials}</div>
                <div>
                    <p style="margin: 0; color: #FAFAFA; font-weight: 600;">{user['name']}</p>
                    <span style="background: {role_colors.get(user['role'], '#8B95A5')}; color: white; padding: 0.1rem 0.5rem; border-radius: 10px; font-size: 0.7rem; text-transform: uppercase;">{user['role']}</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("My Profile", use_container_width=True):
        st.switch_page("pages/98_Profile.py")
    
    if user.get('role') == 'admin':
        if st.sidebar.button("Admin Panel", use_container_width=True, type="secondary"):
            st.switch_page("pages/99_Admin.py")
    
    if st.sidebar.button("Logout", use_container_width=True):
        if "auth_token" in st.session_state:
            logout_user(st.session_state.auth_token)
            del st.session_state.auth_token
        st.switch_page("pages/0_Login.py")


def get_current_user() -> Optional[dict]:
    return check_auth()


def update_user_profile(email: str, updates: dict) -> bool:
    data = load_users()
    email = email.lower().strip()
    
    if email not in data["users"]:
        return False
    
    for key, value in updates.items():
        if key != "password":
            data["users"][email][key] = value
    
    save_users(data)
    return True


def change_password(email: str, current_password: str, new_password: str) -> bool:
    data = load_users()
    email = email.lower().strip()
    
    if email not in data["users"]:
        return False
    
    user = data["users"][email]
    
    if not verify_password(current_password, user["password"]):
        return False
    
    if len(new_password) < 6:
        return False
    
    data["users"][email]["password"] = hash_password(new_password)
    save_users(data)
    return True


def logout():
    if "auth_token" in st.session_state:
        logout_user(st.session_state.auth_token)
        del st.session_state.auth_token


def get_all_users() -> dict:
    data = load_users()
    return data.get("users", {})


def update_user_role(email: str, new_role: str) -> bool:
    data = load_users()
    email = email.lower().strip()
    
    if email not in data["users"]:
        return False
    
    data["users"][email]["role"] = new_role
    save_users(data)
    return True


def delete_user(email: str) -> bool:
    data = load_users()
    email = email.lower().strip()
    
    if email not in data["users"]:
        return False
    
    del data["users"][email]
    
    tokens_to_delete = [t for t, s in data["sessions"].items() if s.get("email") == email]
    for token in tokens_to_delete:
        del data["sessions"][token]
    
    save_users(data)
    return True


init_default_admin()


