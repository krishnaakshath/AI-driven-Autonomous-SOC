"""
 Login Page
=============
Premium cyberpunk login page with animated effects, Google OAuth,
and persistent session support.
"""

import streamlit as st
import sys
import os
import time as _time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    st.set_page_config(
        page_title="Login | SOC",
        page_icon="■",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

# Import theme and auth
from ui.theme import CYBERPUNK_CSS, inject_particles
from services.auth_service import auth_service, is_authenticated, check_persistent_session, login_user

# Google OAuth (optional — module may not be present)
try:
    from auth.google_oauth import is_oauth_configured, get_google_auth_url, handle_oauth_callback, create_oauth_user
    oauth_user = handle_oauth_callback()
    if oauth_user:
        create_oauth_user(oauth_user['email'], oauth_user['name'])
        login_user(oauth_user['email'], remember=True)
        st.session_state.session_start = _time.time()
        st.success(f"ACCESS GRANTED: Welcome {oauth_user['name']}")
        _time.sleep(0.5)
        st.rerun()
except (ImportError, ModuleNotFoundError):
    def is_oauth_configured(): return False
    def get_google_auth_url(): return "#"

# Auto-login check (persistent session)
if check_persistent_session():
    st.rerun()

# Check if already logged in
if is_authenticated():
    st.rerun()

# Apply cyberpunk theme
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM LOGIN PAGE STYLES
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap');

    /* ── Hide sidebar ── */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* ── Animated background ── */
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(-45deg, #030712, #0c1222, #150a2e, #0a1628, #030712) !important;
        background-size: 400% 400% !important;
        animation: gradientBG 20s ease infinite !important;
        overflow: hidden;
    }

    /* ── Ambient Orbs ── */
    .ambient-orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(80px);
        pointer-events: none;
        z-index: 0;
    }

    .orb-1 {
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(0,243,255,0.15) 0%, transparent 70%);
        top: -100px; right: -100px;
        animation: orbFloat1 12s ease-in-out infinite;
    }

    .orb-2 {
        width: 350px; height: 350px;
        background: radial-gradient(circle, rgba(188,19,254,0.12) 0%, transparent 70%);
        bottom: -100px; left: -100px;
        animation: orbFloat2 15s ease-in-out infinite;
    }

    .orb-3 {
        width: 250px; height: 250px;
        background: radial-gradient(circle, rgba(0,255,136,0.08) 0%, transparent 70%);
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        animation: orbFloat3 18s ease-in-out infinite;
    }

    @keyframes orbFloat1 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(-40px, 30px) scale(1.1); }
        66% { transform: translate(20px, -20px) scale(0.9); }
    }
    @keyframes orbFloat2 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(50px, -40px) scale(1.15); }
    }
    @keyframes orbFloat3 {
        0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
        50% { transform: translate(-50%, -50%) scale(1.3); opacity: 0.8; }
    }

    /* ── Cyber Grid Lines ── */
    .cyber-grid {
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        pointer-events: none;
        z-index: 0;
        background:
            linear-gradient(rgba(0,243,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,243,255,0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
        -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
    }

    /* ── Floating hex particles ── */
    @keyframes hexFloat {
        0%   { transform: translateY(100vh) rotate(0deg); opacity: 0; }
        10%  { opacity: 0.3; }
        90%  { opacity: 0.3; }
        100% { transform: translateY(-10vh) rotate(360deg); opacity: 0; }
    }

    .hex-particle {
        position: fixed;
        width: 8px; height: 8px;
        border: 1px solid rgba(0,243,255,0.2);
        pointer-events: none;
        z-index: 0;
    }

    .hex-p1 { left: 10%; animation: hexFloat 14s linear infinite; animation-delay: 0s; }
    .hex-p2 { left: 25%; animation: hexFloat 18s linear infinite; animation-delay: 3s; border-color: rgba(188,19,254,0.2); }
    .hex-p3 { left: 45%; animation: hexFloat 12s linear infinite; animation-delay: 6s; }
    .hex-p4 { left: 65%; animation: hexFloat 20s linear infinite; animation-delay: 2s; border-color: rgba(0,255,136,0.15); }
    .hex-p5 { left: 80%; animation: hexFloat 16s linear infinite; animation-delay: 8s; border-color: rgba(188,19,254,0.15); }
    .hex-p6 { left: 92%; animation: hexFloat 22s linear infinite; animation-delay: 4s; }

    /* ── Main Login Card ── */
    .login-card {
        position: relative;
        max-width: 460px;
        margin: 0 auto;
        padding: 48px 40px 40px 40px;
        background: rgba(8, 12, 24, 0.85);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(0, 243, 255, 0.12);
        border-radius: 20px;
        box-shadow:
            0 0 60px rgba(0, 243, 255, 0.06),
            0 25px 50px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255,255,255,0.05);
        z-index: 1;
    }

    .login-card::before {
        content: '';
        position: absolute;
        top: -1px; left: -1px;
        right: -1px; bottom: -1px;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(0,243,255,0.3), rgba(188,19,254,0.1), rgba(0,243,255,0.3));
        background-size: 200% 200%;
        animation: borderGlow 4s ease infinite;
        z-index: -1;
        mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        mask-composite: exclude;
        -webkit-mask-composite: xor;
        padding: 1px;
    }

    @keyframes borderGlow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    /* ── Shield Icon ── */
    @keyframes shieldPulse {
        0%, 100% { transform: scale(1); filter: drop-shadow(0 0 15px rgba(0,243,255,0.4)); }
        50% { transform: scale(1.08); filter: drop-shadow(0 0 25px rgba(0,243,255,0.6)); }
    }

    .shield-icon {
        width: 64px;
        height: 64px;
        margin: 0 auto;
        animation: shieldPulse 3s ease-in-out infinite;
        display: inline-block;
    }
    
    .shield-icon svg {
        filter: drop-shadow(0 0 10px rgba(0,243,255,0.5));
    }

    /* ── Title Styling ── */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
        100% { transform: translateY(0px); }
    }

    .float-title {
        animation: float 6s ease-in-out infinite;
    }

    /* ── Input Glow ── */
    .stTextInput > div > div {
        background: rgba(0, 8, 20, 0.7) !important;
        border: 1px solid rgba(0, 243, 255, 0.15) !important;
        border-radius: 12px !important;
        transition: all 0.4s cubic-bezier(0.19, 1, 0.22, 1) !important;
    }

    .stTextInput > div > div:focus-within {
        border-color: rgba(0, 243, 255, 0.6) !important;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.15), 0 0 40px rgba(0, 243, 255, 0.05) !important;
        transform: scale(1.01);
    }

    .stTextInput input {
        color: #e0e8f0 !important;
        letter-spacing: 0.5px;
        font-size: 0.95rem !important;
    }

    .stTextInput input::placeholder {
        color: rgba(255,255,255,0.25) !important;
    }

    /* ── Primary Button ── */
    .stButton > button[kind="primary"],
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #00d4ff 0%, #0099cc 30%, #bc13fe 70%, #8b0fcc 100%) !important;
        background-size: 200% 200% !important;
        color: #fff !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        border: none !important;
        padding: 16px 28px !important;
        border-radius: 14px !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        transition: all 0.4s cubic-bezier(0.19, 1, 0.22, 1) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3) !important;
        clip-path: none !important;
    }

    .stButton > button:hover {
        background-position: right center !important;
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 8px 30px rgba(188, 19, 254, 0.4), 0 4px 15px rgba(0, 212, 255, 0.3) !important;
    }

    .stButton > button:active {
        transform: translateY(-1px) scale(0.98) !important;
    }

    /* ── Checkbox Styling ── */
    .stCheckbox label span {
        color: #7a8599 !important;
        font-size: 0.85rem !important;
    }

    /* ── Divider ── */
    .divider-line {
        display: flex;
        align-items: center;
        gap: 16px;
        margin: 24px 0;
    }
    .divider-line::before, .divider-line::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,243,255,0.2), transparent);
    }
    .divider-text {
        color: #4a5568;
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        white-space: nowrap;
    }

    /* ── Google Button ── */
    .google-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        width: 100%;
        padding: 14px 20px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        color: #c8d0dc;
        font-family: 'Rajdhani', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-decoration: none;
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .google-btn:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(255,255,255,0.05);
        color: #fff;
        text-decoration: none;
    }

    .google-btn img {
        width: 20px;
        height: 20px;
    }

    /* ── Status Badge ── */
    @keyframes securityPulse {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }

    .security-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0,255,136,0.05);
        border: 1px solid rgba(0,255,136,0.15);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.65rem;
        color: rgba(0,255,136,0.7);
        font-family: 'Share Tech Mono', monospace;
        letter-spacing: 1px;
    }

    .security-badge .dot {
        width: 5px; height: 5px;
        background: #00ff88;
        border-radius: 50%;
        animation: securityPulse 2s ease infinite;
    }

    /* ── Typing animation ── */
    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }
    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: #00f3ff; }
    }

    /* ── Mobile responsive ── */
    @media (max-width: 640px) {
        .login-card {
            margin: 0 16px;
            padding: 32px 24px;
        }
        .shield-icon { font-size: 2.4rem; }
    }
</style>
""", unsafe_allow_html=True)

# ── Background Elements ──
st.markdown("""
<div class="ambient-orb orb-1"></div>
<div class="ambient-orb orb-2"></div>
<div class="ambient-orb orb-3"></div>
<div class="cyber-grid"></div>
<div class="hex-particle hex-p1"></div>
<div class="hex-particle hex-p2"></div>
<div class="hex-particle hex-p3"></div>
<div class="hex-particle hex-p4"></div>
<div class="hex-particle hex-p5"></div>
<div class="hex-particle hex-p6"></div>
""", unsafe_allow_html=True)

inject_particles()

# Initialize session states
if 'login_step' not in st.session_state:
    st.session_state.login_step = 'credentials'
if 'pending_email' not in st.session_state:
    st.session_state.pending_email = None

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align: center; padding: 20px 0 10px 0;" class="float-title">
    <div class="shield-icon">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" stroke="#00f3ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" fill="url(#shield_grad)" fill-opacity="0.3"/>
            <defs>
                <linearGradient id="shield_grad" x1="4" y1="2" x2="20" y2="22" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#00f3ff" />
                    <stop offset="1" stop-color="#bc13fe" />
                </linearGradient>
            </defs>
            <path d="M9 12L11 14L15 10" stroke="#00f3ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    </div>
    <h1 style="
        font-family: 'Orbitron', sans-serif !important;
        font-size: 2.8rem;
        background: linear-gradient(135deg, #00f3ff 0%, #66d9ff 25%, #bc13fe 75%, #d966ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 5px;
        margin: 12px 0 0 0;
    ">SOC <span style="color: #fff; -webkit-text-fill-color: #fff; font-weight: 400;">PLATFORM</span></h1>
    <div style="height: 28px; margin-top: 12px;">
        <p style="
            color: #5a6a7f;
            font-family: 'Share Tech Mono', monospace;
            letter-spacing: 3px;
            font-size: 0.85rem;
            border-right: 2px solid #00f3ff;
            display: inline-block;
            white-space: nowrap;
            overflow: hidden;
            animation: typing 3s steps(35, end), blink-caret .75s step-end infinite;
        ">AUTONOMOUS SECURITY OPERATIONS</p>
    </div>
    <div style="text-align: center; margin-top: 12px;">
        <span class="security-badge"><span class="dot"></span> ENCRYPTED CONNECTION</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN FORM
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.login_step == 'credentials':
    st.markdown("""
    <h3 style='
        font-family: Orbitron, sans-serif;
        color: #00f3ff;
        letter-spacing: 3px;
        font-size: 1rem;
        margin-bottom: 24px;
        text-align: center;
    '>SYSTEM ACCESS</h3>
    """, unsafe_allow_html=True)

    email = st.text_input("Email Address", placeholder="your@email.com", key="login_email")
    password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

    remember_me = st.checkbox("Remember this device", value=True)

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
                    login_user(email, remember=remember_me)
                    st.session_state.session_start = _time.time()

                    try:
                        from services.user_data import log_login_attempt, check_suspicious_login
                        log_login_attempt(email, success=True, ip_address="127.0.0.1")
                        sus = check_suspicious_login(email, current_ip="127.0.0.1")
                        if sus.get('is_suspicious'):
                            st.session_state['login_warning'] = sus
                    except Exception:
                        pass

                    st.success("✅ ACCESS GRANTED")
                    st.rerun()
            else:
                try:
                    from services.user_data import log_login_attempt
                    log_login_attempt(email, success=False, ip_address="127.0.0.1")
                except Exception:
                    pass
                st.error("ACCESS DENIED: " + message)
        else:
            st.warning("Enter credentials")

    # ── Google Sign-In Divider & Button ──
    st.markdown("""
    <div class="divider-line">
        <span class="divider-text">or continue with</span>
    </div>
    """, unsafe_allow_html=True)

    if is_oauth_configured():
        auth_url = get_google_auth_url()
        st.markdown(f"""
        <a href="{auth_url}" target="_self" class="google-btn">
            <svg width="20" height="20" viewBox="0 0 48 48">
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            </svg>
            Sign in with Google
        </a>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <a href="#" class="google-btn" style="opacity: 0.4; cursor: not-allowed; pointer-events: none;">
            <svg width="20" height="20" viewBox="0 0 48 48">
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            </svg>
            Google Sign-In (Not Configured)
        </a>
        <div style="text-align: center; margin-top: 8px;">
            <span style="color: #3a4456; font-size: 0.7rem; font-family: 'Share Tech Mono', monospace;">
                Add GOOGLE_CLIENT_ID to secrets to enable
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Create account section
    st.markdown("""
    <div style="text-align: center; margin-top: 28px; padding-top: 20px; border-top: 1px solid rgba(0,243,255,0.08);">
        <p style="color: #4a5568; font-family: 'Rajdhani', sans-serif; font-size: 0.95rem;">New to the platform?</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("CREATE ACCOUNT", key="create_account_btn"):
        st.switch_page("pages/_Register.py")

elif st.session_state.login_step == '2fa_select':
    st.markdown("<h3 style='font-family: Orbitron, sans-serif; color: #00f3ff; letter-spacing: 2px; text-align: center;'>2FA VERIFICATION</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #5a6a7f; text-align: center; font-family: Rajdhani, sans-serif;'>Select your verification method:</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 24px 12px; background: rgba(0,243,255,0.06); border-radius: 16px; border: 1px solid rgba(0,243,255,0.15);">
            <div style="font-size: 2rem; color: #00f3ff; margin-bottom: 8px;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>
            </div>
            <div style="color: #00f3ff; font-family: 'Orbitron', sans-serif; font-size: 0.7rem; margin-top: 10px; letter-spacing: 1px;">AUTHENTICATOR</div>
        </div>
        """, unsafe_allow_html=True)

        has_totp = auth_service.has_totp_setup(st.session_state.pending_email)

        if st.button("USE APP", key="2fa_app_btn", use_container_width=True):
            if has_totp:
                st.session_state.login_step = '2fa_verify'
                st.session_state.otp_method = 'totp'
                st.rerun()
            else:
                st.warning("Authenticator not set up. Please use email then configure in Settings.")

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 24px 12px; background: rgba(188,19,254,0.06); border-radius: 16px; border: 1px solid rgba(188,19,254,0.15);">
            <div style="font-size: 2rem; color: #bc13fe; margin-bottom: 8px;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
            </div>
            <div style="color: #bc13fe; font-family: 'Orbitron', sans-serif; font-size: 0.7rem; margin-top: 10px; letter-spacing: 1px;">EMAIL</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("SEND EMAIL", key="2fa_email", use_container_width=True):
            auth_service.update_2fa_method(st.session_state.pending_email, "email")
            success, message = auth_service.generate_otp(st.session_state.pending_email)
            if success:
                fallback_code = getattr(auth_service, '_last_otp_fallback', None)
                if fallback_code:
                    st.session_state._otp_fallback_code = fallback_code
                st.session_state.login_step = '2fa_verify'
                st.session_state.otp_method = 'email'
                st.rerun()
            else:
                st.error(message)

    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 24px 12px; background: rgba(255,255,255,0.02); border-radius: 16px; border: 1px solid rgba(255,255,255,0.06);">
            <div style="font-size: 2rem; color: #444; margin-bottom: 8px;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            </div>
            <div style="color: #444; font-family: 'Orbitron', sans-serif; font-size: 0.7rem; margin-top: 10px; letter-spacing: 1px;">SMS</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("COMING SOON", disabled=True, key="2fa_sms_btn", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← BACK", key="back_from_2fa"):
        st.session_state.login_step = 'credentials'
        st.session_state.pending_email = None
        st.rerun()

elif st.session_state.login_step == '2fa_verify':
    st.markdown("<h3 style='font-family: Orbitron, sans-serif; color: #00f3ff; letter-spacing: 2px; text-align: center;'>ENTER CODE</h3>", unsafe_allow_html=True)

    # Show OTP fallback if email delivery failed
    fallback_code = st.session_state.get('_otp_fallback_code')
    if fallback_code:
        st.info(f"**Email not configured. Your verification code is: `{fallback_code}`**")
    else:
        st.markdown("""
        <div style="background: rgba(0,243,255,0.06); border-left: 3px solid #00f3ff; padding: 16px; border-radius: 0 12px 12px 0; margin-bottom: 20px;">
            <p style="color: #00f3ff; margin: 0; font-family: 'Rajdhani', sans-serif;">6-digit code sent. Check your inbox.</p>
            <p style="color: #4a5568; margin: 5px 0 0 0; font-size: 0.85rem;">Code expires in 5 minutes.</p>
        </div>
        """, unsafe_allow_html=True)

    otp = st.text_input("Verification Code", placeholder="000000", max_chars=6, key="otp_input")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("VERIFY", type="primary", use_container_width=True):
            if otp and len(otp) == 6:
                method = st.session_state.get('otp_method', 'email')

                if method == 'totp':
                    success, message = auth_service.verify_totp(st.session_state.pending_email, otp)
                else:
                    success, message = auth_service.verify_otp(st.session_state.pending_email, otp)

                if success:
                    remember = st.session_state.get('remember_me', False)
                    pending = st.session_state.pending_email
                    login_user(pending, remember=remember)

                    st.session_state.session_start = _time.time()
                    st.session_state.login_step = 'credentials'

                    try:
                        from services.user_data import log_login_attempt, check_suspicious_login
                        log_login_attempt(pending, success=True, ip_address="127.0.0.1")
                        sus = check_suspicious_login(pending, current_ip="127.0.0.1")
                        if sus.get('is_suspicious'):
                            st.session_state['login_warning'] = sus
                    except Exception:
                        pass

                    st.session_state.pending_email = None
                    st.success("ACCESS GRANTED")
                    st.rerun()
                else:
                    st.error("INVALID CODE: " + message)
            else:
                st.warning("Enter 6-digit code")

    with col2:
        if st.button("RESEND", use_container_width=True):
            success, message = auth_service.generate_otp(st.session_state.pending_email)
            if success:
                fallback_code = getattr(auth_service, '_last_otp_fallback', None)
                if fallback_code:
                    st.session_state._otp_fallback_code = fallback_code
                    st.info(f"**New code: `{fallback_code}`**")
                else:
                    st.session_state._otp_fallback_code = None
                    st.success("Code sent!")
            else:
                st.error(message)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← BACK", key="back_from_verify"):
        st.session_state.login_step = '2fa_select'
        st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 40px; color: #2a3444; font-size: 0.75rem; font-family: 'Share Tech Mono', monospace;">
    <p>AI-DRIVEN AUTONOMOUS SOC v2.0</p>
    <p style="font-size: 0.6rem; color: #1e2838; margin-top: 4px;">SECURED • ENCRYPTED • MONITORED</p>
</div>
""", unsafe_allow_html=True)
