"""
📝 Registration Page
====================
Clean, dedicated registration page for new users.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Register | SOC",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Import auth service
from services.auth_service import auth_service, is_authenticated

# Check if already logged in
if is_authenticated():
    st.switch_page("pages/01_Dashboard.py")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@400;600&display=swap');
    
    /* Hide sidebar completely */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    .css-1d391kg { display: none !important; }
    
    /* Dark background with animated gradient */
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #0a0a1a 100%);
    }
    
    /* Register container */
    .register-container {
        max-width: 450px;
        margin: 30px auto;
        padding: 40px;
        background: rgba(10, 10, 26, 0.95);
        border: 1px solid rgba(0, 243, 255, 0.3);
        border-radius: 20px;
        box-shadow: 0 0 60px rgba(0, 243, 255, 0.15);
    }
    
    .register-header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .register-logo {
        font-size: 48px;
        margin-bottom: 10px;
    }
    
    .register-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.6rem;
        color: #00f3ff;
        letter-spacing: 2px;
        margin: 0;
    }
    
    .register-subtitle {
        color: #666;
        font-size: 0.85rem;
        letter-spacing: 1px;
    }
    
    /* Form styling */
    .stTextInput > div > div {
        background: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(0, 243, 255, 0.2) !important;
        border-radius: 10px !important;
    }
    
    .stTextInput input {
        color: #fff !important;
        font-size: 1rem !important;
    }
    
    .stTextInput input::placeholder {
        color: #666 !important;
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
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(0, 243, 255, 0.4) !important;
    }
    
    /* Link styling */
    .login-link {
        text-align: center;
        margin-top: 25px;
        padding-top: 20px;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    .login-link a {
        color: #00f3ff;
        text-decoration: none;
    }
    
    /* Feature list */
    .feature-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        color: #8B95A5;
        font-size: 0.9rem;
    }
    
    .check-icon {
        color: #00C853;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="register-header">
    <div class="register-logo">🛡️</div>
    <h1 class="register-title">CREATE ACCOUNT</h1>
    <p class="register-subtitle">Join the Autonomous SOC Platform</p>
</div>
""", unsafe_allow_html=True)

# What you get section
st.markdown("""
<div style="background: rgba(0,243,255,0.05); border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <div style="color: #00f3ff; font-size: 0.85rem; font-weight: 600; margin-bottom: 10px;">WHAT YOU GET:</div>
    <div class="feature-item"><span class="check-icon">✓</span> Real-time threat monitoring</div>
    <div class="feature-item"><span class="check-icon">✓</span> AI-powered security analysis</div>
    <div class="feature-item"><span class="check-icon">✓</span> Personal scan & report history</div>
    <div class="feature-item"><span class="check-icon">✓</span> Custom alert configurations</div>
</div>
""", unsafe_allow_html=True)

# Registration form
st.markdown("### Account Details")

reg_name = st.text_input("Full Name", placeholder="John Doe", key="reg_name")
reg_email = st.text_input("Email Address", placeholder="your@email.com", key="reg_email")
reg_password = st.text_input("Password", type="password", placeholder="Minimum 8 characters", key="reg_password")
reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_confirm")

# Terms checkbox
agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy", key="agree_terms")

st.markdown("<br>", unsafe_allow_html=True)

# Register button
if st.button("Create Account", type="primary", key="register_btn"):
    if not all([reg_name, reg_email, reg_password, reg_confirm]):
        st.error("⚠️ Please fill in all fields")
    elif not agree_terms:
        st.error("⚠️ Please agree to the Terms of Service")
    elif reg_password != reg_confirm:
        st.error("❌ Passwords do not match")
    elif len(reg_password) < 8:
        st.error("❌ Password must be at least 8 characters")
    elif '@' not in reg_email or '.' not in reg_email:
        st.error("❌ Please enter a valid email address")
    else:
        success, message = auth_service.register(reg_email, reg_password, reg_name)
        if success:
            st.success("✅ " + message)
            st.info("🔄 Redirecting to login...")
            
            # Log the registration
            try:
                from services.user_data import log_activity
                log_activity(reg_email, "account_created", {"name": reg_name})
            except:
                pass
            
            import time
            time.sleep(1.5)
            st.switch_page("pages/_Login.py")
        else:
            st.error("❌ " + message)

# Login link
st.markdown("""
<div class="login-link">
    <p style="color: #8B95A5; margin: 0;">Already have an account?</p>
</div>
""", unsafe_allow_html=True)

if st.button("← Back to Login", key="back_to_login"):
    st.switch_page("pages/_Login.py")

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 40px; color: #444; font-size: 0.75rem;">
    <p>🔐 Your data is encrypted and secure</p>
</div>
""", unsafe_allow_html=True)
