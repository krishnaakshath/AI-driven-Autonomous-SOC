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
    .main .block-container { padding-top: 2rem !important; }
    .stApp > header { display: none; }
    .login-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .login-header h1 {
        background: linear-gradient(135deg, #00D4FF 0%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        margin: 0;
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

col1, col2 = st.columns(2)
with col1:
    if st.button("🔑 Login", use_container_width=True, type="primary" if st.session_state.auth_mode == "login" else "secondary"):
        st.session_state.auth_mode = "login"
        st.rerun()
with col2:
    if st.button("📝 Register", use_container_width=True, type="primary" if st.session_state.auth_mode == "register" else "secondary"):
        st.session_state.auth_mode = "register"
        st.rerun()

oauth_col1, oauth_col2 = st.columns(2)
with oauth_col1:
    if st.button("🔵 Google", use_container_width=True):
        st.info("🔧 **Google OAuth Setup Required**\n\nTo enable Google login:\n1. Go to Google Cloud Console\n2. Create OAuth credentials\n3. Add to Settings page")
with oauth_col2:
    if st.button("⚫ GitHub", use_container_width=True):
        st.info("🔧 **GitHub OAuth Setup Required**\n\nTo enable GitHub login:\n1. Go to GitHub Developer Settings\n2. Create OAuth App\n3. Add to Settings page")

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



st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: #8B95A5; font-size: 0.8rem;">
        <p>🔒 Secure authentication with encrypted passwords</p>
        <p style="margin-top: 0.5rem;">AI-Driven Autonomous SOC</p>
    </div>
""", unsafe_allow_html=True)
