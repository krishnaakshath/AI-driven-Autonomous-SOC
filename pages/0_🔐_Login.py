import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Login | SOC", page_icon="🔐", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { display: none; }
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 2rem;
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-header h1 {
        background: linear-gradient(135deg, #00D4FF 0%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        margin: 0;
    }
    .login-card {
        background: rgba(26, 31, 46, 0.9);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 20px;
        padding: 2rem;
        backdrop-filter: blur(10px);
    }
    .oauth-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.8rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background: rgba(255, 255, 255, 0.05);
        color: #FAFAFA;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
        text-decoration: none;
    }
    .oauth-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: #00D4FF;
    }
    .oauth-google { border-color: #4285F4; }
    .oauth-google:hover { background: rgba(66, 133, 244, 0.2); }
    .oauth-github { border-color: #333; }
    .oauth-github:hover { background: rgba(51, 51, 51, 0.3); }
    .divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 1.5rem 0;
        color: #8B95A5;
    }
    .divider::before, .divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .divider span { padding: 0 1rem; font-size: 0.85rem; }
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        color: #FAFAFA !important;
    }
    .toggle-link {
        text-align: center;
        margin-top: 1rem;
        color: #8B95A5;
    }
    .toggle-link a {
        color: #00D4FF;
        text-decoration: none;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

from auth.auth_manager import login_user, register_user, check_auth

if check_auth():
    st.switch_page("pages/1_🏠_Dashboard.py")

st.markdown("""
    <div class="login-header">
        <p style="font-size: 3rem; margin: 0;">🛡️</p>
        <h1>AI-Driven SOC</h1>
        <p style="color: #8B95A5; margin-top: 0.5rem;">Security Operations Center</p>
    </div>
""", unsafe_allow_html=True)

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

st.markdown('<div class="login-card">', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("🔑 Login", use_container_width=True, type="primary" if st.session_state.auth_mode == "login" else "secondary"):
        st.session_state.auth_mode = "login"
        st.rerun()
with col2:
    if st.button("📝 Register", use_container_width=True, type="primary" if st.session_state.auth_mode == "register" else "secondary"):
        st.session_state.auth_mode = "register"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
    <a href="#" class="oauth-btn oauth-google">
        <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
        Continue with Google
    </a>
    <a href="#" class="oauth-btn oauth-github">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="#FAFAFA"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        Continue with GitHub
    </a>
""", unsafe_allow_html=True)

st.markdown('<div class="divider"><span>or continue with email</span></div>', unsafe_allow_html=True)

if st.session_state.auth_mode == "login":
    email = st.text_input("Email", placeholder="your@email.com", key="login_email")
    password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
    
    if st.button("🔓 Sign In", use_container_width=True, type="primary"):
        if email and password:
            success, message, user_data = login_user(email, password)
            if success:
                st.session_state.auth_token = user_data["token"]
                st.success("✅ " + message)
                st.balloons()
                st.switch_page("pages/1_🏠_Dashboard.py")
            else:
                st.error("❌ " + message)
        else:
            st.warning("Please enter email and password")
    
    st.markdown("""
        <p style="text-align: center; color: #8B95A5; margin-top: 1rem; font-size: 0.85rem;">
            Demo: <code>admin@soc.local</code> / <code>admin123</code>
        </p>
    """, unsafe_allow_html=True)

else:
    name = st.text_input("Full Name", placeholder="John Doe", key="reg_name")
    email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
    password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="reg_password")
    confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••", key="reg_confirm")
    
    if st.button("📝 Create Account", use_container_width=True, type="primary"):
        if not all([name, email, password, confirm]):
            st.warning("Please fill all fields")
        elif password != confirm:
            st.error("Passwords do not match")
        else:
            success, message = register_user(email, password, name)
            if success:
                st.success("✅ " + message + " Please login now.")
                st.session_state.auth_mode = "login"
                st.rerun()
            else:
                st.error("❌ " + message)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: #8B95A5; font-size: 0.8rem;">
        <p>🔒 Secure authentication with encrypted passwords</p>
        <p style="margin-top: 0.5rem;">AI-Driven Autonomous SOC</p>
    </div>
""", unsafe_allow_html=True)
