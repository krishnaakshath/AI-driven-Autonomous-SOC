"""
🔐 Login Page
=============
Clean, modern login page with 2FA support.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Login | SOC",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Import auth service
from services.auth_service import auth_service, is_authenticated

# Check if already logged in
if is_authenticated():
    st.switch_page("pages/01_Dashboard.py")

# Custom CSS for login page
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap');
    
    /* Hide sidebar completely */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    .css-1d391kg { display: none !important; }
    
    /* Dark background */
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #0a0a1a 100%);
    }
    
    /* Login header */
    .login-header {
        text-align: center;
        margin-bottom: 30px;
        padding-top: 40px;
    }
    
    .login-logo {
        font-size: 64px;
        margin-bottom: 10px;
    }
    
    .login-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2rem;
        color: #00f3ff;
        letter-spacing: 4px;
        margin: 0;
        text-shadow: 0 0 20px rgba(0,243,255,0.5);
    }
    
    .login-subtitle {
        color: #666;
        font-size: 0.9rem;
        letter-spacing: 2px;
        margin-top: 5px;
    }
    
    /* Form container */
    .form-container {
        max-width: 400px;
        margin: 0 auto;
        background: rgba(10, 10, 26, 0.9);
        border: 1px solid rgba(0, 243, 255, 0.3);
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 0 40px rgba(0, 243, 255, 0.1);
    }
    
    /* Form styling */
    .stTextInput > div > div {
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(0, 243, 255, 0.2) !important;
        border-radius: 10px !important;
    }
    
    .stTextInput input {
        color: #fff !important;
        font-size: 1rem !important;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #00f3ff, #bc13fe) !important;
        color: #000 !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 14px 24px !important;
        border-radius: 10px !important;
        font-size: 1.1rem !important;
        letter-spacing: 1px !important;
        transition: all 0.3s !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 20px rgba(0, 243, 255, 0.4) !important;
    }
    
    /* Secondary button */
    .secondary-btn button {
        background: transparent !important;
        border: 1px solid rgba(0, 243, 255, 0.5) !important;
        color: #00f3ff !important;
    }
    
    /* Divider */
    .divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 25px 0;
    }
    
    .divider::before, .divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .divider span {
        padding: 0 15px;
        color: #666;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session states
if 'login_step' not in st.session_state:
    st.session_state.login_step = 'credentials'
if 'pending_email' not in st.session_state:
    st.session_state.pending_email = None

# Header
st.markdown("""
<div class="login-header">
    <div class="login-logo">🛡️</div>
    <h1 class="login-title">SOC PLATFORM</h1>
    <p class="login-subtitle">AUTONOMOUS SECURITY OPERATIONS</p>
</div>
""", unsafe_allow_html=True)

# Main login flow
if st.session_state.login_step == 'credentials':
    st.markdown("### Welcome Back")
    
    email = st.text_input("Email Address", placeholder="your@email.com", key="login_email")
    password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Login", type="primary", key="login_btn"):
        if email and password:
            success, message, requires_2fa = auth_service.login(email, password)
            
            if success:
                if requires_2fa:
                    st.session_state.pending_email = email
                    st.session_state.login_step = '2fa_select'
                    st.rerun()
                else:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    user = auth_service.get_user(email)
                    st.session_state.user_name = user.get('name', 'User')
                    st.session_state.session_start = __import__('time').time()
                    
                    # Log login activity
                    try:
                        from services.user_data import log_activity
                        log_activity(email, "login", {"method": "password"})
                    except:
                        pass
                    
                    st.success("✅ Login successful!")
                    st.switch_page("pages/01_Dashboard.py")
            else:
                st.error("❌ " + message)
        else:
            st.warning("⚠️ Please enter email and password")
    
    # Create account section
    st.markdown("""
    <div class="divider"><span>New to SOC Platform?</span></div>
    """, unsafe_allow_html=True)
    
    if st.button("Create Account", key="create_account_btn"):
        st.switch_page("pages/_Register.py")

elif st.session_state.login_step == '2fa_select':
    st.markdown("### Two-Factor Authentication")
    st.markdown("Select how you want to receive your verification code:")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 10px; border: 1px solid rgba(0,243,255,0.2);">
            <div style="font-size: 2rem;">📧</div>
            <div style="color: #8B95A5; font-size: 0.9rem; margin-top: 5px;">Email</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Send to Email", key="2fa_email", use_container_width=True):
            auth_service.update_2fa_method(st.session_state.pending_email, "email")
            success, message = auth_service.generate_otp(st.session_state.pending_email)
            if success:
                st.session_state.login_step = '2fa_verify'
                st.session_state.otp_method = 'email'
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 2rem;">📱</div>
            <div style="color: #666; font-size: 0.9rem; margin-top: 5px;">SMS</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Coming Soon", disabled=True, key="2fa_sms", use_container_width=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 2rem;">💬</div>
            <div style="color: #666; font-size: 0.9rem; margin-top: 5px;">WhatsApp</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Coming Soon", disabled=True, key="2fa_wa", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Login", key="back_from_2fa"):
        st.session_state.login_step = 'credentials'
        st.session_state.pending_email = None
        st.rerun()

elif st.session_state.login_step == '2fa_verify':
    st.markdown("### Enter Verification Code")
    
    st.markdown("""
    <div style="background: rgba(0,243,255,0.1); border-left: 3px solid #00f3ff; padding: 12px 15px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
        <p style="color: #00f3ff; margin: 0; font-size: 0.9rem;">📧 A 6-digit code was sent to your email</p>
        <p style="color: #666; margin: 5px 0 0 0; font-size: 0.8rem;">Check your inbox and spam folder. Code expires in 5 minutes.</p>
    </div>
    """, unsafe_allow_html=True)
    
    otp = st.text_input(
        "Verification Code",
        placeholder="Enter 6-digit code",
        max_chars=6,
        key="otp_input"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Verify & Login", type="primary", use_container_width=True):
            if otp and len(otp) == 6:
                success, message = auth_service.verify_otp(st.session_state.pending_email, otp)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_email = st.session_state.pending_email
                    user = auth_service.get_user(st.session_state.pending_email)
                    st.session_state.user_name = user.get('name', 'User')
                    st.session_state.session_start = __import__('time').time()
                    st.session_state.login_step = 'credentials'
                    
                    # Log login activity
                    try:
                        from services.user_data import log_activity
                        log_activity(st.session_state.pending_email, "login", {"method": "2fa_email"})
                    except:
                        pass
                    
                    st.session_state.pending_email = None
                    st.success("✅ Login successful!")
                    st.switch_page("pages/01_Dashboard.py")
                else:
                    st.error("❌ " + message)
            else:
                st.warning("⚠️ Please enter a 6-digit code")
    
    with col2:
        if st.button("Resend Code", use_container_width=True):
            success, message = auth_service.generate_otp(st.session_state.pending_email)
            if success:
                st.success("✅ New code sent!")
            else:
                st.error(message)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back", key="back_from_verify"):
        st.session_state.login_step = '2fa_select'
        st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 50px; color: #444; font-size: 0.8rem;">
    <p>🔐 Secured by AI-Driven Autonomous SOC</p>
</div>
""", unsafe_allow_html=True)
