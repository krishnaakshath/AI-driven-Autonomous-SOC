# Google OAuth Authentication
import os
import json
import secrets
import requests
from urllib.parse import urlencode, parse_qs
from typing import Optional, Dict, Tuple
import streamlit as st

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_oauth_config() -> Dict:
    """Load OAuth config from secrets or config file"""
    config = {}
    
    # Try Streamlit secrets first
    try:
        if hasattr(st, 'secrets') and 'google_oauth' in st.secrets:
            return dict(st.secrets['google_oauth'])
    except:
        pass
    
    # Try config file
    if os.path.exists('.soc_config.json'):
        with open('.soc_config.json', 'r') as f:
            config = json.load(f)
    
    return {
        'client_id': config.get('google_client_id', ''),
        'client_secret': config.get('google_client_secret', ''),
        'redirect_uri': config.get('google_redirect_uri', 'http://localhost:8501')
    }


def get_google_auth_url(state: str = None) -> str:
    """Generate Google OAuth authorization URL"""
    config = get_oauth_config()
    
    if not config.get('client_id'):
        return None
    
    if not state:
        state = secrets.token_urlsafe(32)
    
    params = {
        'client_id': config['client_id'],
        'redirect_uri': config['redirect_uri'],
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'prompt': 'select_account'
    }
    
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> Optional[Dict]:
    """Exchange authorization code for access token"""
    config = get_oauth_config()
    
    if not config.get('client_id') or not config.get('client_secret'):
        return None
    
    data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': code,
        'redirect_uri': config['redirect_uri'],
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Token exchange error: {e}")
    
    return None


def get_google_user_info(access_token: str) -> Optional[Dict]:
    """Get user info from Google"""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(GOOGLE_USERINFO_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"User info error: {e}")
    
    return None


def handle_oauth_callback() -> Optional[Dict]:
    """Handle OAuth callback and return user info"""
    query_params = st.query_params
    
    if 'code' in query_params:
        code = query_params['code']
        
        # Exchange code for token
        token_data = exchange_code_for_token(code)
        
        if token_data and 'access_token' in token_data:
            # Get user info
            user_info = get_google_user_info(token_data['access_token'])
            
            # Clear query params
            st.query_params.clear()
            
            return user_info
    
    return None


def create_oauth_user(google_user: Dict) -> Dict:
    """Create or get user from Google OAuth data"""
    from auth.auth_manager import load_users, save_users, hash_password
    
    email = google_user.get('email', '').lower()
    name = google_user.get('name', email.split('@')[0])
    picture = google_user.get('picture', '')
    
    data = load_users()
    
    if email not in data['users']:
        # Create new user
        data['users'][email] = {
            'password': hash_password(secrets.token_urlsafe(32)),  # Random password
            'name': name,
            'role': 'analyst',
            'oauth_provider': 'google',
            'picture': picture,
            'created': __import__('datetime').datetime.now().isoformat(),
            'last_login': None
        }
        save_users(data)
    
    # Create session
    from auth.auth_manager import login_user
    import time
    
    session_token = secrets.token_hex(32)
    data['sessions'][session_token] = {
        'email': email,
        'created': time.time(),
        'expires': time.time() + 2592000  # 30 days
    }
    data['users'][email]['last_login'] = __import__('datetime').datetime.now().isoformat()
    save_users(data)
    
    return {
        'email': email,
        'name': name,
        'role': data['users'][email]['role'],
        'token': session_token,
        'picture': picture
    }


def is_oauth_configured() -> bool:
    """Check if Google OAuth is configured"""
    config = get_oauth_config()
    return bool(config.get('client_id'))
