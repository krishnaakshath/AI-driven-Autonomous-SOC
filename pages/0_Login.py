import streamlit as st
import os
import sys
import hashlib
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Login | SOC", page_icon="L", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
    
    .stApp { background: linear-gradient(135deg, #0a0e17 0%, #151c2c 50%, #0d1320 100%); }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: 
            radial-gradient(circle at 20% 80%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
        pointer-events: none;
    }
    
    .login-card {
        background: rgba(26, 31, 46, 0.85);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2rem;
        max-width: 400px;
        margin: 0.5rem auto;
    }
    
    .logo-shield {
        width: 60px; height: 60px;
        background: linear-gradient(135deg, #00D4FF 0%, #8B5CF6 100%);
        border-radius: 18px;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 1rem;
        box-shadow: 0 8px 30px rgba(0, 212, 255, 0.3);
    }
    
    .logo-title {
        font-size: 1.6rem; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #FFF 0%, #00D4FF 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .stTextInput > div > div > input {
        background: rgba(15, 20, 30, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: #FAFAFA !important;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #00D4FF 0%, #0099CC 100%) !important;
        color: white !important; border: none !important; border-radius: 10px !important;
        padding: 0.75rem !important; font-weight: 600 !important;
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.3) !important;
    }
    
    .oauth-btn {
        display: flex; align-items: center; justify-content: center; gap: 0.7rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px; padding: 0.75rem;
        color: #FAFAFA; font-weight: 500; cursor: pointer;
        transition: all 0.3s ease; text-decoration: none; margin: 0.4rem 0;
    }
    
    .oauth-btn:hover { background: rgba(255, 255, 255, 0.1); transform: translateY(-2px); }
    
    .divider { display: flex; align-items: center; margin: 1rem 0; gap: 0.8rem; }
    .divider-line { flex: 1; height: 1px; background: rgba(255, 255, 255, 0.1); }
    .divider-text { color: #8B95A5; font-size: 0.8rem; }
    
    #MainMenu, footer, header { visibility: hidden; }
    section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

from auth.auth_manager import login_user, register_user, check_auth
from auth.two_factor import create_otp, verify_otp, send_otp_email, send_otp_telegram, is_device_trusted, add_trusted_device

def get_device_id():
    if 'device_id' not in st.session_state:
        st.session_state.device_id = hashlib.md5(str(uuid.getnode()).encode()).hexdigest()[:16]
    return st.session_state.device_id

# Check if already logged in
if check_auth():
    st.switch_page("pages/1_Dashboard.py")

# Logo
st.markdown("""
<div class="login-card">
    <div class="logo-shield">
        <svg width="30" height="30" viewBox="0 0 24 24" fill="white">
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
        </svg>
    </div>
    <h1 class="logo-title">SOC Platform</h1>
    <p style="color: #8B95A5; text-align: center; margin: 0.3rem 0 0 0; font-size: 0.85rem;">Autonomous Security Operations</p>
</div>
""", unsafe_allow_html=True)

# OAuth buttons - Coming Soon
st.markdown("""
<div class="oauth-btn" style="opacity: 0.5; cursor: not-allowed;">
    <svg width="18" height="18" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
    Google (Coming Soon)
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="oauth-btn" style="opacity: 0.5; cursor: not-allowed;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
        <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
    </svg>
    Apple (Coming Soon)
</div>
""", unsafe_allow_html=True)


st.markdown('<div class="divider"><div class="divider-line"></div><span class="divider-text">or continue with email</span><div class="divider-line"></div></div>', unsafe_allow_html=True)

# Initialize state
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'pending_user' not in st.session_state:
    st.session_state.pending_user = None

# Mode tabs
col1, col2 = st.columns(2)
with col1:
    if st.button("Login", use_container_width=True, type="primary" if st.session_state.auth_mode == 'login' else "secondary"):
        st.session_state.auth_mode = 'login'
        st.session_state.otp_sent = False
        st.rerun()
with col2:
    if st.button("Register", use_container_width=True, type="primary" if st.session_state.auth_mode == 'register' else "secondary"):
        st.session_state.auth_mode = 'register'
        st.session_state.otp_sent = False
        st.rerun()

# OTP Verification
if st.session_state.otp_sent and st.session_state.pending_user:
    st.markdown('<p style="color: #00D4FF; text-align: center;">Enter verification code</p>', unsafe_allow_html=True)
    st.markdown('<p style="color: #8B95A5; text-align: center; font-size: 0.85rem;">After verification, this device will be trusted until you logout</p>', unsafe_allow_html=True)
    
    otp_code = st.text_input("6-Digit Code", placeholder="000000", max_chars=6, key="otp")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Verify", type="primary", use_container_width=True):
            if otp_code and len(otp_code) == 6:
                success, msg = verify_otp(st.session_state.pending_user['email'], otp_code)
                if success:
                    st.session_state.auth_token = st.session_state.pending_user['token']
                    # Always trust device after successful 2FA
                    add_trusted_device(st.session_state.pending_user['email'], get_device_id())
                    st.session_state.otp_sent = False
                    st.switch_page("pages/1_Dashboard.py")
                else:
                    st.error(msg)
    with c2:
        if st.button("Resend", use_container_width=True):
            otp = create_otp(st.session_state.pending_user['email'])
            send_otp_email(st.session_state.pending_user['email'], otp)
            send_otp_telegram(otp)
            st.success("Code sent!")

elif st.session_state.auth_mode == 'login':
    email = st.text_input("Email", placeholder="you@company.com", key="login_email")
    password = st.text_input("Password", type="password", placeholder="Password", key="login_pass")
    
    if st.button("Sign In", type="primary", use_container_width=True):
        if email and password:
            success, msg, user = login_user(email, password)
            if success and user:
                if is_device_trusted(email, get_device_id()):
                    st.session_state.auth_token = user['token']
                    st.switch_page("pages/1_Dashboard.py")
                else:
                    otp = create_otp(email)
                    if send_otp_email(email, otp, email)[0]:
                        st.session_state.otp_sent = True
                        st.session_state.pending_user = user
                        st.rerun()
                    else:
                        st.session_state.auth_token = user['token']
                        st.switch_page("pages/1_Dashboard.py")
            else:
                st.error(msg)

else:
    st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3 style="color: #00D4FF; margin-bottom: 0.5rem;">Access Restricted</h3>
            <p style="color: #8B95A5; margin-bottom: 1.5rem;">New account creation is currently disabled. This system is for authorized administrators only.</p>
            <div style="background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 1rem; border: 1px dashed rgba(255, 255, 255, 0.2);">
                <p style="margin: 0; color: #FAFAFA; font-weight: 500;">Registration Coming Soon</p>
                <p style="margin: 0.3rem 0 0 0; color: #8B95A5; font-size: 0.8rem;">We are upgrading our security policies.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

