"""
 Registration Page
====================
Cyberpunk themed registration page matching SOC platform design.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    st.set_page_config(
        page_title="Register | SOC",
        page_icon="",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py navigation

# Import theme and auth
from ui.theme import CYBERPUNK_CSS, inject_particles
from services.auth_service import auth_service, is_authenticated

# Check if already logged in
if is_authenticated():
    st.switch_page("pages/01_Dashboard.py")

# Apply cyberpunk theme
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

# Hide sidebar completely
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    .css-1d391kg { display: none !important; }
    
    /* Form styling */
    .stTextInput > div > div {
        background: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid rgba(0, 243, 255, 0.3) !important;
        border-radius: 8px !important;
    }
    
    .stTextInput input {
        color: #fff !important;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, var(--neon-cyan, #00f3ff), var(--neon-purple, #bc13fe)) !important;
        color: #000 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 14px 24px !important;
        border-radius: 8px !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        transition: all 0.3s !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 20px rgba(0, 243, 255, 0.4) !important;
    }
    
    .stCheckbox label span {
        color: #8B95A5 !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style="text-align: center; padding: 30px 0 20px 0;">
    <div style="font-size: 3.5rem; margin-bottom: 10px;"></div>
    <h1 style="
        font-family: 'Orbitron', sans-serif !important;
        font-size: 2rem;
        background: linear-gradient(135deg, #bc13fe, #00f3ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 3px;
        margin: 0;
    ">CREATE ACCOUNT</h1>
    <p style="color: #666; font-family: 'Rajdhani', sans-serif; letter-spacing: 2px; margin-top: 8px;">
        JOIN THE AUTONOMOUS SOC PLATFORM
    </p>
</div>
""", unsafe_allow_html=True)

# Features section
st.markdown("""
<div style="background: rgba(0,243,255,0.05); border: 1px solid rgba(0,243,255,0.2); border-radius: 12px; padding: 20px; margin-bottom: 25px;">
    <div style="color: #00f3ff; font-family: 'Orbitron', sans-serif; font-size: 0.75rem; letter-spacing: 2px; margin-bottom: 12px;">WHAT YOU GET:</div>
    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
        <span style="background: rgba(0,243,255,0.1); color: #00f3ff; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-family: 'Rajdhani', sans-serif;"> Real-time Threat Monitoring</span>
        <span style="background: rgba(188,19,254,0.1); color: #bc13fe; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-family: 'Rajdhani', sans-serif;"> AI Security Analysis</span>
        <span style="background: rgba(0,255,0,0.1); color: #0f0; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-family: 'Rajdhani', sans-serif;"> Personal Dashboard</span>
        <span style="background: rgba(255,107,0,0.1); color: #ff6b00; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-family: 'Rajdhani', sans-serif;"> Custom Alerts</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Registration form
st.markdown("<h3 style='font-family: Orbitron, sans-serif; color: #00f3ff; letter-spacing: 2px; font-size: 1rem;'>ACCOUNT DETAILS</h3>", unsafe_allow_html=True)

reg_name = st.text_input("Full Name", placeholder="John Doe", key="reg_name")
reg_email = st.text_input("Email Address", placeholder="your@email.com", key="reg_email")
reg_password = st.text_input("Password", type="password", placeholder="Minimum 8 characters", key="reg_password")
reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_confirm")

agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy", key="agree_terms")

st.markdown("<br>", unsafe_allow_html=True)

# Register button
if st.button("INITIALIZE ACCOUNT", type="primary", key="register_btn"):
    if not all([reg_name, reg_email, reg_password, reg_confirm]):
        st.error(" All fields required")
    elif not agree_terms:
        st.error(" Accept Terms of Service")
    elif reg_password != reg_confirm:
        st.error(" Passwords do not match")
    elif len(reg_password) < 8:
        st.error(" Password: minimum 8 characters")
    elif '@' not in reg_email or '.' not in reg_email:
        st.error(" Invalid email format")
    else:
        success, message = auth_service.register(reg_email, reg_password, reg_name)
        if success:
            st.success(" ACCOUNT CREATED")
            st.info(" Redirecting to login...")
            
            try:
                from services.user_data import log_activity
                log_activity(reg_email, "account_created", {"name": reg_name})
            except:
                pass
            
            import time
            time.sleep(1.5)
            st.switch_page("pages/_Login.py")
        else:
            st.error(" " + message)

# Login link
st.markdown("""
<div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid rgba(0,243,255,0.2);">
    <p style="color: #666; font-family: 'Rajdhani', sans-serif;">Already have an account?</p>
</div>
""", unsafe_allow_html=True)

if st.button("← BACK TO LOGIN", key="back_to_login"):
    st.switch_page("pages/_Login.py")

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 40px; color: #444; font-size: 0.8rem; font-family: 'Rajdhani', sans-serif;">
    <p> SECURED BY AI-DRIVEN AUTONOMOUS SOC</p>
</div>
""", unsafe_allow_html=True)
