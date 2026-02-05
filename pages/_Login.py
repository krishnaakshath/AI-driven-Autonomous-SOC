"""
🔐 Login Page
=============
Secure login with 2FA support.
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
    st.switch_page("pages/1_Dashboard.py")

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
    
    /* Login container */
    .login-container {
        max-width: 400px;
        margin: 50px auto;
        padding: 40px;
        background: rgba(10, 10, 26, 0.9);
        border: 1px solid rgba(0, 243, 255, 0.3);
        border-radius: 16px;
        box-shadow: 0 0 40px rgba(0, 243, 255, 0.1);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .login-logo {
        font-size: 48px;
        margin-bottom: 10px;
    }
    
    .login-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.8rem;
        color: #00f3ff;
        letter-spacing: 3px;
        margin: 0;
    }
    
    .login-subtitle {
        color: #666;
        font-size: 0.85rem;
        letter-spacing: 2px;
    }
    
    /* Form styling */
    .stTextInput > div > div {
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(0, 243, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    
    .stTextInput input {
        color: #fff !important;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #00f3ff, #bc13fe) !important;
        color: #000 !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        letter-spacing: 1px !important;
        transition: all 0.3s !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 20px rgba(0, 243, 255, 0.4) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #888;
        border-radius: 8px;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(0, 243, 255, 0.1);
        color: #00f3ff;
    }
    
    /* OTP input */
    .otp-container {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 20px 0;
    }
    
    /* 2FA method buttons */
    .method-btn {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(0, 243, 255, 0.2);
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .method-btn:hover {
        border-color: #00f3ff;
        background: rgba(0, 243, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session states
if 'login_step' not in st.session_state:
    st.session_state.login_step = 'credentials'  # credentials, 2fa_select, 2fa_verify
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
    tab1, tab2 = st.tabs(["🔓 Login", "📝 Register"])
    
    with tab1:
        st.markdown("### Welcome Back")
        
        email = st.text_input("Email", placeholder="your@email.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
        
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
                        st.success("Login successful!")
                        st.switch_page("pages/1_Dashboard.py")
                else:
                    st.error(message)
            else:
                st.warning("Please enter email and password")
    
    with tab2:
        st.markdown("### Create Account")
        
        reg_name = st.text_input("Full Name", placeholder="John Doe", key="reg_name")
        reg_email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
        reg_password = st.text_input("Password", type="password", placeholder="Min 8 characters", key="reg_password")
        reg_confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••", key="reg_confirm")
        
        if st.button("Register", type="primary", key="reg_btn"):
            if not all([reg_name, reg_email, reg_password, reg_confirm]):
                st.warning("Please fill all fields")
            elif reg_password != reg_confirm:
                st.error("Passwords do not match")
            else:
                success, message = auth_service.register(reg_email, reg_password, reg_name)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)

elif st.session_state.login_step == '2fa_select':
    st.markdown("### Two-Factor Authentication")
    st.markdown("Select how you want to receive your verification code:")
    
    user = auth_service.get_user(st.session_state.pending_email)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Email", use_container_width=True):
            auth_service.update_2fa_method(st.session_state.pending_email, "email")
            success, message = auth_service.generate_otp(st.session_state.pending_email)
            if success:
                st.session_state.login_step = '2fa_verify'
                st.session_state.otp_method = 'email'
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        if st.button("📱 SMS", use_container_width=True):
            phone = st.text_input("Phone Number", placeholder="+1234567890", key="sms_phone")
            if phone:
                auth_service.update_2fa_method(st.session_state.pending_email, "sms", phone)
                success, message = auth_service.generate_otp(st.session_state.pending_email)
                if success:
                    st.session_state.login_step = '2fa_verify'
                    st.session_state.otp_method = 'sms'
                    st.rerun()
                else:
                    st.error(message)
    
    with col3:
        if st.button("💬 WhatsApp", use_container_width=True):
            phone = st.text_input("WhatsApp Number", placeholder="+1234567890", key="wa_phone")
            if phone:
                auth_service.update_2fa_method(st.session_state.pending_email, "whatsapp", phone)
                success, message = auth_service.generate_otp(st.session_state.pending_email)
                if success:
                    st.session_state.login_step = '2fa_verify'
                    st.session_state.otp_method = 'whatsapp'
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("---")
    if st.button("← Back to Login"):
        st.session_state.login_step = 'credentials'
        st.session_state.pending_email = None
        st.rerun()

elif st.session_state.login_step == '2fa_verify':
    st.markdown("### Enter Verification Code")
    
    method_icon = {"email": "📧", "sms": "📱", "whatsapp": "💬"}.get(st.session_state.otp_method, "📧")
    st.markdown(f"A 6-digit code was sent via {method_icon} {st.session_state.otp_method}")
    
    # DEMO MODE: Show OTP if available in session state
    pending_email = st.session_state.pending_email
    if pending_email and 'otp_store' in st.session_state:
        otp_data = st.session_state.otp_store.get(pending_email)
        if otp_data:
            st.info(f"🔧 **Demo Mode:** Your verification code is **{otp_data['otp']}**")
    
    otp = st.text_input(
        "Verification Code",
        placeholder="000000",
        max_chars=6,
        key="otp_input"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Verify", type="primary", use_container_width=True):
            if otp and len(otp) == 6:
                success, message = auth_service.verify_otp(st.session_state.pending_email, otp)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_email = st.session_state.pending_email
                    user = auth_service.get_user(st.session_state.pending_email)
                    st.session_state.user_name = user.get('name', 'User')
                    st.session_state.login_step = 'credentials'
                    st.session_state.pending_email = None
                    st.success("Login successful!")
                    st.switch_page("pages/1_Dashboard.py")
                else:
                    st.error(message)
            else:
                st.warning("Please enter a 6-digit code")
    
    with col2:
        if st.button("Resend Code", use_container_width=True):
            success, message = auth_service.generate_otp(st.session_state.pending_email)
            if success:
                st.success("New code sent!")
            else:
                st.error(message)
    
    st.markdown("---")
    if st.button("← Back"):
        st.session_state.login_step = '2fa_select'
        st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 50px; color: #444; font-size: 0.8rem;">
    <p>🔐 Secured by AI-Driven Autonomous SOC</p>
</div>
""", unsafe_allow_html=True)
