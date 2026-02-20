"""
 Login Page
=============
Cyberpunk themed login page matching SOC platform design.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    st.set_page_config(
        page_title="Login | SOC",
        page_icon="",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

# Import theme and auth
from ui.theme import CYBERPUNK_CSS, inject_particles

from services.auth_service import auth_service, is_authenticated, check_persistent_session, login_user

# Auto-login check (persistent session)
if check_persistent_session():
    st.rerun()

# Check if already logged in
if is_authenticated():
    st.rerun()

# Apply cyberpunk theme
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

# Hide sidebar completely
st.markdown("""
<style>
    /* Sidebar hidden */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* Animated background gradient */
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stApp {
        background: linear-gradient(-45deg, #0a0e17, #151c2c, #1a0b2e, #0f1623);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    
    /* Center the login form */
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 40px;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 243, 255, 0.1);
        border-radius: 12px;
        box-shadow: 0 0 40px rgba(0, 243, 255, 0.1);
    }
    
    /* Input Glow */
    .stTextInput > div > div {
        background: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div:focus-within {
        border-color: #00f3ff !important;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.2) !important;
        transform: scale(1.02);
    }
    
    .stTextInput input {
        color: #fff !important;
        letter-spacing: 1px;
    }
    
    /* Button Animation */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #00f3ff, #bc13fe, #00f3ff) !important;
        background-size: 200% auto !important;
        color: #000 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 14px 24px !important;
        border-radius: 8px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        transition: all 0.4s ease !important;
    }
    
    .stButton > button:hover {
        background-position: right center !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 5px 25px rgba(188, 19, 254, 0.5) !important;
    }
    
    /* Floating Title Animation */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .float-title {
        animation: float 6s ease-in-out infinite;
    }
</style>
    """, unsafe_allow_html=True)
    
# Particles only if not already running (handled by theme)
inject_particles()

# Initialize session states
if 'login_step' not in st.session_state:
    st.session_state.login_step = 'credentials'
if 'pending_email' not in st.session_state:
    st.session_state.pending_email = None

# Header with Typing Effect
st.markdown("""
<div style="text-align: center; padding: 40px 0 30px 0;" class="float-title">
<div style="font-size: 4rem; margin-bottom: 10px;"></div>
<h1 style="
    font-family: 'Orbitron', sans-serif !important;
    font-size: 3rem;
    background: linear-gradient(135deg, #00f3ff, #bc13fe);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 4px;
    margin: 0;
    text-shadow: 0 0 30px rgba(0,243,255,0.5);
">SOC <span style="color: #fff; -webkit-text-fill-color: #fff;">PLATFORM</span></h1>

<div style="height: 30px; margin-top: 15px;">
    <p id="typing-text" style="
        color: #8B95A5; 
        font-family: 'Share Tech Mono', monospace; 
        letter-spacing: 2px; 
        font-size: 1.1rem;
        border-right: 2px solid #00f3ff;
        display: inline-block;
        white-space: nowrap;
        overflow: hidden;
        animation: typing 3.5s steps(40, end), blink-caret .75s step-end infinite;
    ">AUTONOMOUS SECURITY OPERATIONS</p>
</div>

<style>
    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }
    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: #00f3ff; }
    }
</style>
</div>
""", unsafe_allow_html=True)

# Main login flow
if st.session_state.login_step == 'credentials':
    st.markdown("<h3 style='font-family: Orbitron, sans-serif; color: #00f3ff; letter-spacing: 2px;'>SYSTEM ACCESS</h3>", unsafe_allow_html=True)
    
    email = st.text_input("Email Address", placeholder="your@email.com", key="login_email")
    password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
    
    remember_me = st.checkbox("Remember this device", value=False)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("AUTHENTICATE", type="primary", key="login_btn"):
        if email and password:
            success, message, requires_2fa = auth_service.login(email, password)
            
            if success:
                if requires_2fa:
                    st.session_state.pending_email = email
                    st.session_state.login_step = '2fa_select'
                    st.session_state.remember_me = remember_me
                    st.rerun()
                else:
                    # Login successful without 2FA (e.g. Admin)
                    login_user(email, remember=remember_me)
                    st.session_state.session_start = __import__('time').time()
                    
                    # Track login footprint + check for suspicious activity
                    try:
                        from services.user_data import log_login_attempt, check_suspicious_login
                        log_login_attempt(email, success=True, ip_address="127.0.0.1")
                        sus = check_suspicious_login(email, current_ip="127.0.0.1")
                        if sus.get('is_suspicious'):
                            st.session_state['login_warning'] = sus
                    except:
                        pass
                    
                    st.success(" ACCESS GRANTED")
                    st.rerun()
            else:
                # Track failed login attempt
                try:
                    from services.user_data import log_login_attempt
                    log_login_attempt(email, success=False, ip_address="127.0.0.1")
                except:
                    pass
                st.error(" " + message)
        else:
            st.warning(" Enter credentials")
    
    # Create account section
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(0,243,255,0.2);">
        <p style="color: #666; font-family: 'Rajdhani', sans-serif;">New to the platform?</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("CREATE ACCOUNT", key="create_account_btn"):
        st.switch_page("pages/_Register.py")

elif st.session_state.login_step == '2fa_select':
    st.markdown("<h3 style='font-family: Orbitron, sans-serif; color: #00f3ff; letter-spacing: 2px;'>2FA VERIFICATION</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8B95A5;'>Select verification method:</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: rgba(0,243,255,0.1); border-radius: 12px; border: 1px solid rgba(0,243,255,0.3);">
            <div style="font-size: 2.5rem;">📱</div>
            <div style="color: #00f3ff; font-family: 'Orbitron', sans-serif; font-size: 0.8rem; margin-top: 8px;">AUTHENTICATOR</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Check if user has TOTP setup
        has_totp = auth_service.has_totp_setup(st.session_state.pending_email)
        
        if st.button("USE APP", key="2fa_app_btn", use_container_width=True):
            if has_totp:
                st.session_state.login_step = '2fa_verify'
                st.session_state.otp_method = 'totp'
                st.rerun()
            else:
                st.warning(" Authenticator not set up. Please use email then configure in Settings.")

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: rgba(188,19,254,0.1); border-radius: 12px; border: 1px solid rgba(188,19,254,0.3);">
            <div style="font-size: 2.5rem;">✉️</div>
            <div style="color: #bc13fe; font-family: 'Orbitron', sans-serif; font-size: 0.8rem; margin-top: 8px;">EMAIL</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("SEND EMAIL", key="2fa_email", use_container_width=True):
            auth_service.update_2fa_method(st.session_state.pending_email, "email")
            success, message = auth_service.generate_otp(st.session_state.pending_email)
            if success:
                st.session_state.login_step = '2fa_verify'
                st.session_state.otp_method = 'email'
                st.rerun()
            else:
                st.error(message)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 2.5rem; opacity: 0.5;">💬</div>
            <div style="color: #666; font-family: 'Orbitron', sans-serif; font-size: 0.8rem; margin-top: 8px;">SMS</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("COMING SOON", disabled=True, key="2fa_sms_btn", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← BACK", key="back_from_2fa"):
        st.session_state.login_step = 'credentials'
        st.session_state.pending_email = None
        st.rerun()

elif st.session_state.login_step == '2fa_verify':
    st.markdown("<h3 style='font-family: Orbitron, sans-serif; color: #00f3ff; letter-spacing: 2px;'>ENTER CODE</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: rgba(0,243,255,0.1); border-left: 3px solid #00f3ff; padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
        <p style="color: #00f3ff; margin: 0; font-family: 'Rajdhani', sans-serif;"> 6-digit code sent. Check your inbox.</p>
        <p style="color: #666; margin: 5px 0 0 0; font-size: 0.85rem;">Code expires in 5 minutes.</p>
    </div>
    """, unsafe_allow_html=True)
    
    otp = st.text_input("Verification Code", placeholder="000000", max_chars=6, key="otp_input")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("VERIFY", type="primary", use_container_width=True):
            if otp and len(otp) == 6:
                method = st.session_state.get('otp_method', 'email')
                
                if method == 'totp':
                    # Verify using TOTP
                    success, message = auth_service.verify_totp(st.session_state.pending_email, otp)
                else:
                    # Verify using Email/SMS OTP
                    success, message = auth_service.verify_otp(st.session_state.pending_email, otp)
                
                if success:
                    # Verified 2FA login
                    remember = st.session_state.get('remember_me', False)
                    pending = st.session_state.pending_email
                    login_user(pending, remember=remember)
                    
                    st.session_state.session_start = __import__('time').time()
                    st.session_state.login_step = 'credentials'
                    
                    # Track login footprint + check for suspicious activity
                    try:
                        from services.user_data import log_login_attempt, check_suspicious_login
                        log_login_attempt(pending, success=True, ip_address="127.0.0.1")
                        sus = check_suspicious_login(pending, current_ip="127.0.0.1")
                        if sus.get('is_suspicious'):
                            st.session_state['login_warning'] = sus
                    except:
                        pass
                    
                    st.session_state.pending_email = None
                    st.success(" ACCESS GRANTED")
                    st.rerun()
                else:
                    st.error(" " + message)
            else:
                st.warning(" Enter 6-digit code")
    
    with col2:
        if st.button("RESEND", use_container_width=True):
            success, message = auth_service.generate_otp(st.session_state.pending_email)
            if success:
                st.success(" Code sent!")
            else:
                st.error(message)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← BACK", key="back_from_verify"):
        st.session_state.login_step = '2fa_select'
        st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 50px; color: #444; font-size: 0.8rem; font-family: 'Rajdhani', sans-serif;">
    <p> AI-DRIVEN AUTONOMOUS SOC v2.0</p>
</div>
""", unsafe_allow_html=True)
