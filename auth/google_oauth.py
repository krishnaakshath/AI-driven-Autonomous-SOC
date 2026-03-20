"""
 Google OAuth 2.0 Integration
================================
Handles Google Sign-In using the standard OAuth 2.0 authorization code flow.
No extra dependencies required — uses `requests` which is already installed.

Setup Instructions:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth 2.0 Client ID (Web application)
3. Add authorized redirect URI:  https://<your-app>.streamlit.app/
   (or http://localhost:8501/ for local)
4. Add credentials to .streamlit/secrets.toml:
   GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "your-client-secret"
   GOOGLE_REDIRECT_URI = "https://<your-app>.streamlit.app/"
"""

import os
import json
import requests
import streamlit as st
from urllib.parse import urlencode

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def _get_credentials():
    """Get Google OAuth credentials from secrets or env vars."""
    client_id = None
    client_secret = None
    redirect_uri = None

    # Try Streamlit secrets first
    try:
        client_id = st.secrets.get("GOOGLE_CLIENT_ID")
        client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET")
        redirect_uri = st.secrets.get("GOOGLE_REDIRECT_URI")
    except Exception:
        pass

    # Fall back to environment variables
    if not client_id:
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_secret:
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not redirect_uri:
        redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8501/")

    return client_id, client_secret, redirect_uri


def is_oauth_configured() -> bool:
    """Check if Google OAuth credentials are configured."""
    client_id, client_secret, _ = _get_credentials()
    return bool(client_id and client_secret)


def get_google_auth_url() -> str:
    """Generate the Google OAuth authorization URL."""
    client_id, _, redirect_uri = _get_credentials()
    if not client_id:
        return "#"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def handle_oauth_callback() -> dict | None:
    """
    Check if the current page load has an OAuth callback code.
    If so, exchange it for tokens and return user info.

    Returns:
        dict with 'email', 'name', 'picture' or None
    """
    # Check for authorization code in query params
    code = st.query_params.get("code")
    if not code:
        return None

    # Prevent re-processing the same code
    if st.session_state.get("_oauth_code_processed") == code:
        return None

    client_id, client_secret, redirect_uri = _get_credentials()
    if not client_id or not client_secret:
        return None

    try:
        # Exchange authorization code for tokens
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_response.raise_for_status()
        tokens = token_response.json()

        # Get user info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        user_response = requests.get(GOOGLE_USERINFO_URL, headers=headers, timeout=10)
        user_response.raise_for_status()
        user_info = user_response.json()

        # Mark this code as processed
        st.session_state["_oauth_code_processed"] = code

        # Clear the code from query params
        st.query_params.clear()

        return {
            "email": user_info.get("email", ""),
            "name": user_info.get("name", user_info.get("email", "")),
            "picture": user_info.get("picture", ""),
        }

    except Exception as e:
        print(f"[OAuth] Error during callback: {e}")
        # Clear the bad code
        st.query_params.clear()
        return None


def create_oauth_user(email: str, name: str) -> bool:
    """
    Create a user account for an OAuth login if they don't exist.
    Uses a random password since they'll always log in via Google.

    Returns:
        True if user was created or already exists
    """
    try:
        from services.auth_service import auth_service
        import secrets

        # Check if user already exists
        if auth_service.get_user(email):
            return True

        # Register with a random password (they'll use Google to login)
        random_password = secrets.token_urlsafe(32)
        success, _ = auth_service.register(email, random_password, name)
        return success

    except Exception as e:
        print(f"[OAuth] Error creating user: {e}")
        return False
