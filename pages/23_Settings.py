import streamlit as st
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Settings | SOC", page_icon="", layout="wide")

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

# Check if user is admin
from services.auth_service import is_authenticated, is_admin

# Must be logged in to access settings
if not is_authenticated():
    st.error(" **Authentication Required**")
    st.info("Please log in to access settings.")
    if st.button("Go to Login"):
        st.switch_page("pages/_Login.py")
    st.stop()

IS_ADMIN = is_admin()

st.markdown(page_header("Settings", "Configure your account and preferences"), unsafe_allow_html=True)

# Show admin status
if IS_ADMIN:
    st.success(" **Admin Mode** - Full access to all settings")
else:
    st.info(" **User Mode** - Account and AI settings only. Contact admin for API configurations.")

# Session timeout check (30 min inactivity)
import time
SESSION_TIMEOUT = 1800  # 30 minutes in seconds

if 'last_activity' not in st.session_state:
    st.session_state.last_activity = time.time()

# Update last activity
st.session_state.last_activity = time.time()

CONFIG_FILE = ".soc_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

config = load_config()

# Logout function
def logout():
    for key in ['authenticated', 'user_email', 'user_name', 'login_step', 'pending_email', 'otp_store', 'cortex_messages']:
        if key in st.session_state:
            del st.session_state[key]
    st.switch_page("pages/_Login.py")

# Create tabs based on admin status
if IS_ADMIN:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([" Account", " CORTEX AI", " API Keys", " OAuth", " Notifications", " Thresholds", " About"])
else:
    tab1, tab2, tab7 = st.tabs([" Account", " CORTEX AI", " About"])

# Account Tab with Logout
with tab1:
    st.markdown(section_title("Account & Session"), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #00D4FF; margin: 0 0 0.5rem 0;">Current Session</h4>
            </div>
        """, unsafe_allow_html=True)
        
        user_email = st.session_state.get('user_email', 'Guest')
        user_name = st.session_state.get('user_name', 'Unknown')
        
        st.markdown(f"**User:** {user_name}")
        st.markdown(f"**Email:** {user_email}")
        
        # Session time
        session_start = st.session_state.get('session_start', time.time())
        session_duration = int((time.time() - session_start) / 60)
        st.markdown(f"**Session Duration:** {session_duration} minutes")
        st.markdown(f"**Session Timeout:** 30 minutes of inactivity")
    
    with col2:
        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #FF4444; margin: 0 0 0.5rem 0;">Session Actions</h4>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button(" Logout", type="primary", use_container_width=True):
            logout()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button(" Refresh Session", use_container_width=True):
            st.session_state.last_activity = time.time()
            st.success("Session refreshed!")

# CORTEX AI Personality Settings
with tab2:
    st.markdown(section_title("CORTEX AI Personality"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <h4 style="color: #00D4FF; margin: 0 0 0.5rem 0;">Customize Your AI Assistant</h4>
            <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">
                Adjust CORTEX's personality to match your preferences. Changes take effect on next conversation.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Get current preferences
    try:
        from services.auth_service import get_user_preferences, is_authenticated, get_current_user
        from services.auth_service import auth_service
        
        if is_authenticated():
            user = get_current_user()
            current_prefs = user.get('preferences', {}) if user else {}
            user_email = st.session_state.get('user_email')
        else:
            current_prefs = config.get('ai_preferences', {})
            user_email = None
    except ImportError:
        current_prefs = config.get('ai_preferences', {})
        user_email = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Humor Level")
        humor_level = st.slider(
            "How witty should CORTEX be?",
            min_value=1,
            max_value=5,
            value=current_prefs.get('humor_level', 3),
            help="1 = Serious, 3 = Balanced, 5 = Witty"
        )
        
        humor_labels = {
            1: " **Serious** - Formal and professional",
            2: " **Dry Wit** - Mostly serious",
            3: " **Balanced** - Professional with charm",
            4: " **Friendly** - Warm and engaging",
            5: " **Witty** - Fun and playful"
        }
        st.markdown(humor_labels.get(humor_level, ""))
        
        st.markdown("### Verbosity")
        verbosity = st.selectbox(
            "Response detail level",
            options=["concise", "balanced", "detailed"],
            index=["concise", "balanced", "detailed"].index(current_prefs.get('verbosity', 'balanced'))
        )
    
    with col2:
        st.markdown("### Formality")
        formality = st.selectbox(
            "Communication style",
            options=["professional", "casual", "friendly"],
            index=["professional", "casual", "friendly"].index(current_prefs.get('formality', 'professional'))
        )
        
        st.markdown("### Emoji Usage")
        emoji_usage = st.selectbox(
            "How many emojis to use",
            options=["none", "minimal", "expressive"],
            index=["none", "minimal", "expressive"].index(current_prefs.get('emoji_usage', 'minimal'))
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Preview
    with st.expander(" Preview Response Style"):
        preview_texts = {
            (1, "professional"): "I have analyzed the network traffic. The anomaly detection system identified 3 suspicious connections originating from IP 192.168.1.105. Recommended action: immediate isolation and forensic analysis.",
            (3, "professional"): "Found some interesting activity!  Our anomaly detector flagged 3 suspicious connections from 192.168.1.105. I'd recommend we isolate that endpoint and take a closer look.",
            (5, "friendly"): "Whoa, heads up!  Our digital watchdog just caught some sneaky traffic! 3 fishy connections from 192.168.1.105 - let's quarantine that box before things get spicy! ",
            (5, "casual"): "Yo!  Just spotted some weird stuff - 3 sus connections from .105. Might wanna yeet that endpoint off the network real quick! "
        }
        
        key = (humor_level, formality)
        if key not in preview_texts:
            key = (3, "professional")
        
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.3); border-left: 3px solid #00f3ff; padding: 15px; border-radius: 0 8px 8px 0;">
            <div style="color: #00f3ff; font-size: 0.8rem; margin-bottom: 5px;">CORTEX PREVIEW</div>
            <div style="color: #fff;">{preview_texts[key]}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button(" Save Personality Settings", type="primary"):
        new_prefs = {
            'humor_level': humor_level,
            'formality': formality,
            'verbosity': verbosity,
            'emoji_usage': emoji_usage
        }
        
        if user_email:
            auth_service.update_preferences(user_email, new_prefs)
        else:
            config['ai_preferences'] = new_prefs
            save_config(config)
        
        # Update the AI assistant
        try:
            from services.ai_assistant import ai_assistant
            ai_assistant.update_personality(new_prefs)
        except:
            pass
        
        st.success(" Personality settings saved! CORTEX will use these settings in new conversations.")

# Admin-only tabs (API Keys, OAuth, Notifications, Thresholds)
if IS_ADMIN:
    with tab3:
        st.markdown(section_title("API Integration"), unsafe_allow_html=True)
        
        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #00D4FF; margin: 0 0 0.5rem 0;">Google Gemini AI</h4>
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">For AI-powered threat analysis and report generation</p>
            </div>
        """, unsafe_allow_html=True)
        
        gemini_key = st.text_input("Gemini API Key", value=config.get("gemini_api_key", ""), type="password", key="gemini")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #8B5CF6; margin: 0 0 0.5rem 0;">VirusTotal</h4>
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">For URL and file malware scanning</p>
            </div>
        """, unsafe_allow_html=True)
        
        vt_key = st.text_input("VirusTotal API Key", value=config.get("virustotal_api_key", ""), type="password", key="vt")
        
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #00C853; margin: 0 0 0.5rem 0;">AlienVault OTX</h4>
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">For real-time global threat intelligence feed</p>
            </div>
        """, unsafe_allow_html=True)
        
        otx_key = st.text_input("OTX API Key", value=config.get("otx_api_key", ""), type="password", key="otx")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Save API Keys", type="primary"):
            config["gemini_api_key"] = gemini_key
            config["virustotal_api_key"] = vt_key
            config["otx_api_key"] = otx_key
            save_config(config)
            st.success("API keys saved successfully!")

    with tab4:
        st.markdown(section_title("Social Login"), unsafe_allow_html=True)
        
        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #4285F4; margin: 0 0 0.5rem 0;">Google OAuth Configuration</h4>
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">Enable 'Sign in with Google' by adding your credentials from Google Cloud Console.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_oauth1, col_oauth2 = st.columns(2)
        with col_oauth1:
            google_client_id = st.text_input("Client ID", value=config.get("google_client_id", ""), key="g_client_id")
            google_redirect = st.text_input("Redirect URI", value=config.get("google_redirect_uri", "http://localhost:8501"), key="g_redirect")
        
        with col_oauth2:
            google_client_secret = st.text_input("Client Secret", value=config.get("google_client_secret", ""), type="password", key="g_secret")
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("Redirect URI must match exactly what is configured in Google Cloud Console.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Save OAuth Settings", type="primary"):
            config["google_client_id"] = google_client_id
            config["google_client_secret"] = google_client_secret
            config["google_redirect_uri"] = google_redirect
            save_config(config)
            st.success("OAuth settings saved! Google Login will activate if Client ID is present.")

    with tab5:
        st.markdown(section_title("Notification Settings"), unsafe_allow_html=True)
        
        st.markdown("""<div class="glass-card" style="margin-bottom: 1.5rem;">
<h4 style="color: #FF4444; margin: 0 0 1rem 0;">Email Alerts (Gmail)</h4>
<p style="color: #8B95A5; margin: 0 0 1rem 0; font-size: 0.9rem;">
Configure SMTP settings to receive critical security alerts. 
Use an App Password for Gmail.
</p>
<div style="background: rgba(255, 68, 68, 0.1); border-left: 3px solid #FF4444; padding: 0.8rem; border-radius: 4px; margin-bottom: 1rem;">
<p style="color: #FAFAFA; margin: 0; font-size: 0.85rem;"> Alerts are sent securely using TLS encryption.</p>
</div>
</div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            gmail_email = st.text_input("Gmail Address", value=config.get("gmail_email", ""), key="gmail_email")
            gmail_password = st.text_input("App Password", value=config.get("gmail_password", ""), type="password", key="gmail_pass")
        
        with col2:
            gmail_recipient = st.text_input("Alert Recipient", value=config.get("gmail_recipient", ""), key="gmail_to")
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("Tip: You can add multiple recipients separated by commas.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_save, col_test = st.columns(2)
        
        with col_save:
            if st.button("Save Notifications", type="primary", use_container_width=True):
                config["gmail_email"] = gmail_email
                config["gmail_password"] = gmail_password
                config["gmail_recipient"] = gmail_recipient
                # Clean up old keys
                config.pop("telegram_token", None)
                config.pop("telegram_chat_id", None)
                config.pop("notification_telegram", None)
                
                save_config(config)
                st.success("Notification settings saved!")
        
        with col_test:
            if st.button("Send Test Alert", use_container_width=True):
                try:
                    from alerting.alert_service import send_test_alert
                    result = send_test_alert()
                    if result.get("email"):
                        st.success("Test alert sent to email! ")
                    else:
                        st.warning("Failed to send email. Check your credentials.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab6:
        st.markdown(section_title("Alert Thresholds"), unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("""
                <div class="glass-card" style="margin-bottom: 1rem;">
                    <h4 style="color: #FF8C00; margin: 0 0 0.5rem 0;">Alert Threshold</h4>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">Trigger alerts when risk exceeds this value</p>
                </div>
            """, unsafe_allow_html=True)
            alert_threshold = st.slider("", 0, 100, config.get("alert_threshold", 70), key="alert_thresh", label_visibility="collapsed")
        
        with c2:
            st.markdown("""
                <div class="glass-card" style="margin-bottom: 1rem;">
                    <h4 style="color: #FF4444; margin: 0 0 0.5rem 0;">Auto-Block Threshold</h4>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">Automatically block when risk exceeds this value</p>
                </div>
            """, unsafe_allow_html=True)
            block_threshold = st.slider("", 0, 100, config.get("block_threshold", 90), key="block_thresh", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        auto_block = st.checkbox("Enable Auto-Block", value=config.get("auto_block", True))
        auto_notify = st.checkbox("Enable Auto-Notify", value=config.get("auto_notify", True))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Save Thresholds", type="primary"):
            config["alert_threshold"] = alert_threshold
            config["block_threshold"] = block_threshold
            config["auto_block"] = auto_block
            config["auto_notify"] = auto_notify
            save_config(config)
            st.success("Thresholds saved!")

# About tab - available to all users
with tab7:
    st.markdown(section_title("About This Platform"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card">
            <h3 style="background: linear-gradient(135deg, #00D4FF, #8B5CF6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 1rem 0;">AI-Driven Autonomous SOC</h3>
            <p style="color: #8B95A5; line-height: 1.7;">
                A comprehensive Security Operations Center platform featuring real-time threat detection, 
                ML-based anomaly scoring, automated response actions, and multi-channel alerting.
            </p>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 1.5rem 0;">
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                <div>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">Version</p>
                    <p style="color: #FAFAFA; margin: 0.2rem 0 0 0; font-weight: 600;">2.0.0</p>
                </div>
                <div>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">Framework</p>
                    <p style="color: #FAFAFA; margin: 0.2rem 0 0 0; font-weight: 600;">Streamlit</p>
                </div>
                <div>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">ML Engine</p>
                    <p style="color: #FAFAFA; margin: 0.2rem 0 0 0; font-weight: 600;">Isolation Forest</p>
                </div>
                <div>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">Last Update</p>
                    <p style="color: #FAFAFA; margin: 0.2rem 0 0 0; font-weight: 600;">""" + datetime.now().strftime("%Y-%m-%d") + """</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Settings</p></div>', unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()

