import streamlit as st
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Settings | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

# Check if user is admin
from services.auth_service import is_authenticated, is_admin, auth_service, get_user_preferences, get_current_user

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
    # Use centralized logout to clean up persistence
    from services.auth_service import logout as auth_logout
    auth_logout()
    st.rerun()

# Create tabs based on admin status
if IS_ADMIN:
    tab1, tab_sec, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([" Account", " Security", " CORTEX AI", " API Keys", " OAuth", " Notifications", " Thresholds", " About"])
else:
    tab1, tab_sec, tab2, tab7 = st.tabs([" Account", " Security", " CORTEX AI", " About"])

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

# Security Tab (MFA Setup)
with tab_sec:
    st.markdown(section_title("Security & MFA"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <h4 style="color: #00f3ff; margin: 0 0 0.5rem 0;">Two-Factor Authentication</h4>
            <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">
                Protect your account with an Authenticator App (Recommended) or Email OTP.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        from services.auth_service import auth_service, is_authenticated, get_current_user
        
        if is_authenticated():
            user = get_current_user()
            email = st.session_state.get('user_email')
            
            if not user:
                st.error("User record not found. Please log out and log in again.")
                if st.button("Log Out Now"):
                    logout()
                    st.rerun()
                st.stop()
            
            # Current Method Status
            current_method = user.get('two_factor_method', 'email')
            has_totp = auth_service.has_totp_setup(email)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Current Method:** `{current_method.upper()}`")
                st.markdown(f"**TOTP Setup:** {'✅ Configured' if has_totp else '❌ Not Set'}")
            
            with c2:
                # Toggle Method
                if has_totp and current_method != 'totp':
                    if st.button("Switch to Authenticator App"):
                        auth_service.update_2fa_method(email, 'totp')
                        st.rerun()
                elif current_method != 'email':
                    if st.button("Switch to Email OTP"):
                        auth_service.update_2fa_method(email, 'email')
                        st.rerun()
            
            st.markdown("---")
            
            # TOTP Setup Flow
            st.markdown("##### Setup Authenticator App")
            if st.button("Generate New QR Code"):
                success, uri = auth_service.setup_totp(email)
                if success:
                    st.session_state.totp_uri = uri
                else:
                    st.error(uri)
            
            if 'totp_uri' in st.session_state:
                st.info("Scan this QR code with Google Authenticator or Authy:")
                
                # Generate QR code
                import qrcode
                import io
                from PIL import Image
                
                qr = qrcode.QRCode(box_size=10, border=4)
                qr.add_data(st.session_state.totp_uri)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                # specific layout for QR
                col_qr, col_info = st.columns([1, 2])
                with col_qr:
                    st.image(img.get_image(), width=200)
                with col_info:
                    st.markdown("1. Open Authenticator App")
                    st.markdown("2. Select '+' -> 'Scan QR code'")
                    st.markdown("3. Scan the image on the left")
                    st.markdown("4. Verify by entering the code below")
                
                # Verification
                code = st.text_input("Enter 6-digit code to verify setup", max_chars=6)
                if st.button("Verify Setup"):
                    success, msg = auth_service.verify_totp(email, code)
                    if success:
                        st.success("✅ Setup Complete! 2FA method set to TOTP.")
                        auth_service.update_2fa_method(email, 'totp')
                        del st.session_state.totp_uri
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.warning("Please log in to configure security.")
            
    except ImportError:
        st.error("Auth module not available")
    except Exception as e:
        st.error(f"Error loading security settings: {e}")

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
                <h4 style="color: #00D4FF; margin: 0 0 0.5rem 0;">Groq AI (Llama 3)</h4>
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">High-speed AI inference engine for CORTEX assistant.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_ai1, col_ai2 = st.columns([3, 1])
        with col_ai1:
            groq_key = st.text_input("Groq API Key", value=config.get("GROQ_API_KEY", ""), type="password", key="groq_key")
        with col_ai2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Test Groq", key="test_groq"):
                if groq_key:
                    try:
                        # Temporarily set for test
                        os.environ["GROQ_API_KEY"] = groq_key
                        from services.ai_assistant import ai_assistant
                        # Force reload key
                        ai_assistant.api_key = groq_key
                        ai_assistant.client = __import__('openai').OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
                        
                        resp = ai_assistant.chat("Test connection. Reply with 'OK'.")
                        if "OK" in resp or "Error" not in resp:
                            st.success("Connected!")
                        else:
                            st.error(f"Failed: {resp}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Enter key first")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #8B5CF6; margin: 0 0 0.5rem 0;">VirusTotal</h4>
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">For URL and file malware scanning</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_vt1, col_vt2 = st.columns([3, 1])
        with col_vt1:
            vt_key = st.text_input("VirusTotal API Key", value=config.get("virustotal_api_key", ""), type="password", key="vt")
        with col_vt2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Test VT", key="test_vt"):
                if vt_key:
                    try:
                        from services.threat_intel import threat_intel
                        threat_intel.virustotal_key = vt_key
                        # Test with 8.8.8.8
                        res = threat_intel.check_ip_virustotal("8.8.8.8")
                        if "error" not in res:
                            st.success("Connected!")
                        else:
                            st.error(f"Failed: {res['error']}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #00C853; margin: 0 0 0.5rem 0;">AlienVault OTX</h4>
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">For real-time global threat intelligence feed</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_otx1, col_otx2 = st.columns([3, 1])
        with col_otx1:
            otx_key = st.text_input("OTX API Key", value=config.get("otx_api_key", ""), type="password", key="otx")
        with col_otx2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Test OTX", key="test_otx"):
                if otx_key:
                    try:
                        from services.threat_intel import threat_intel
                        threat_intel.otx_key = otx_key
                        res = threat_intel.get_otx_pulses(limit=1)
                        if res:
                            st.success(f"Connected! Data: {len(res)} pulses")
                        else:
                            st.warning("Connected but no data returned (or public fallback used).")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #FF8C00; margin: 0 0 0.5rem 0;">AbuseIPDB</h4>
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">For IP reputation and confidence scoring</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_ab1, col_ab2 = st.columns([3, 1])
        with col_ab1:
            abuse_key = st.text_input("AbuseIPDB API Key", value=config.get("abuseipdb_api_key", ""), type="password", key="abuse")
        with col_ab2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Test AbuseIPDB", key="test_abuse"):
                 if abuse_key:
                    try:
                        from services.threat_intel import threat_intel
                        threat_intel.abuseipdb_key = abuse_key
                        res = threat_intel.check_ip_abuseipdb("1.1.1.1")
                        if "error" not in res:
                            st.success("Connected!")
                        else:
                            st.error(f"Failed: {res['error']}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Save API Keys", type="primary"):
            config["GROQ_API_KEY"] = groq_key
            config["virustotal_api_key"] = vt_key
            config["otx_api_key"] = otx_key
            config["abuseipdb_api_key"] = abuse_key
            save_config(config)
            st.success("API keys saved successfully! Services updated.")

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

# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS & CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(page_header("Settings & Configuration", "Manage system parameters and user preferences"))

# ── Role-Based Access Control ────────────────────────────────────────────────
is_admin_user = is_admin()

# Tabs based on role
tabs = ["👤 User Preferences"]
if is_admin_user:
    tabs.append("🛠️ System Configuration")
tabs.append("ℹ️ About")

current_tab = st.radio("Category", tabs, horizontal=True, label_visibility="collapsed")
st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# TAB: USER PREFERENCES (Available to ALL)
# ──────────────────────────────────────────────────────────────────────────────
if "User Preferences" in current_tab:
    st.markdown("#### 🤖 CORTEX Personality")
    st.info("Customize how the AI Security Assistant interacts with you.")
    
    # Load current preferences
    # Load current preferences
    current_prefs = get_user_preferences()
    
    with st.form("user_prefs_form"):
        c1, c2 = st.columns(2)
        with c1:
            humor = st.slider("Humor Level", 1, 5, current_prefs.get('humor_level', 3), help="1=Robot, 5=Comedian")
            formality = st.selectbox("Formality", ["professional", "casual", "friendly"], index=["professional", "casual", "friendly"].index(current_prefs.get('formality', 'professional')))
        with c2:
            verbosity = st.select_slider("Response Length", ["concise", "balanced", "detailed"], value=current_prefs.get('verbosity', 'balanced'))
            emoji = st.selectbox("Emoji Usage", ["none", "minimal", "expressive"], index=["none", "minimal", "expressive"].index(current_prefs.get('emoji_usage', 'minimal')))
            
        st.markdown("#### 🔔 Notification Preferences")
        enable_email_alerts = st.checkbox("Receive Email Alerts", value=current_prefs.get('email_alerts', True))
        
        if st.form_submit_button("Save Preferences", type="primary"):
            new_prefs = {
                "humor_level": humor,
                "formality": formality,
                "verbosity": verbosity,
                "emoji_usage": emoji,
                "email_alerts": enable_email_alerts
            }
            if auth_service.update_preferences(st.session_state.user_email, new_prefs):
                # Update running AI instance immediately
                try:
                    from services.ai_assistant import ai_assistant
                    ai_assistant.update_personality(new_prefs)
                except:
                    pass
                st.success("Preferences saved successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to save preferences.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB: SYSTEM CONFIGURATION (Admin Only)
# ──────────────────────────────────────────────────────────────────────────────
if "System Configuration" in current_tab and is_admin_user:
    st.markdown("#### 🔑 Global API Keys & Integrations")
    st.warning("⚠️ These settings affect the entire platform. Only modify if you know what you are doing.")
    
    # Load config
    config = load_config()

    with st.form("system_config_form"):
        c1, c2 = st.columns(2)
        with c1:
            vt_key = st.text_input("VirusTotal API Key", value=config.get('virustotal_api_key', ''), type="password")
            otx_key = st.text_input("AlienVault OTX Key", value=config.get('otx_api_key', ''), type="password")
        with c2:
            groq_key = st.text_input("Groq API Key (Llama 3)", value=config.get('groq_api_key', ''), type="password")
            abuse_key = st.text_input("AbuseIPDB API Key", value=config.get('abuseipdb_api_key', ''), type="password")
            
        st.markdown("##### 📧 System Email (SMTP) Settings")
        st.caption("Used for sending OTPs and Critical Alerts to all users.")
        c3, c4 = st.columns(2)
        with c3:
            gmail_user = st.text_input("Gmail User (Sender)", value=config.get('gmail_email', ''), placeholder="system@soc.com")
            gmail_pass = st.text_input("Gmail App Password", value=config.get('gmail_password', ''), type="password")
        with c4:
            twilio_sid = st.text_input("Twilio Account SID", value=config.get('twilio_account_sid', ''), type="password")
            twilio_token = st.text_input("Twilio Auth Token", value=config.get('twilio_auth_token', ''), type="password")
            twilio_phone = st.text_input("Twilio Phone Number", value=config.get('twilio_phone_number', ''))

        st.markdown("---")
        st.markdown("##### 🚨 Alert Thresholds")
        
        c5, c6 = st.columns(2)
        with c5:
            st.markdown("Trigger alerts when risk > X")
            alert_threshold = st.slider("Alert Threshold", 0, 100, config.get("alert_threshold", 70), label_visibility="collapsed")
        with c6:
            st.markdown("Auto-block IP when risk > X")
            block_threshold = st.slider("Block Threshold", 0, 100, config.get("block_threshold", 90), label_visibility="collapsed")
            
        auto_block = st.checkbox("Enable Auto-Block", value=config.get("auto_block", True))
        auto_notify = st.checkbox("Enable Auto-Notify", value=config.get("auto_notify", True))

        if st.form_submit_button("Save System Configuration", type="primary"):
            # Update config dict
            config['groq_api_key'] = groq_key
            config['virustotal_api_key'] = vt_key
            config['otx_api_key'] = otx_key
            config['abuseipdb_api_key'] = abuse_key
            
            # OTP / Email Settings
            config['gmail_email'] = gmail_user
            config['gmail_password'] = gmail_pass
            config['twilio_account_sid'] = twilio_sid
            config['twilio_auth_token'] = twilio_token
            config['twilio_phone_number'] = twilio_phone
            
            # Thresholds
            config['alert_threshold'] = alert_threshold
            config['block_threshold'] = block_threshold
            config['auto_block'] = auto_block
            config['auto_notify'] = auto_notify

            save_config(config)
            
            # Reload services immediately
            try:
                from services.threat_intel import threat_intel
                threat_intel.reload_config()
                
                from services.ai_assistant import ai_assistant
                ai_assistant.reload_config()
                
                from alerting.alert_service import alert_service
                alert_service.reload_config()
                
                st.success("System configuration saved and services reloaded!")
            except Exception as e:
                st.warning(f"Settings saved, but service reload failed: {e}")
                
            time.sleep(1)
            st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# TAB: ABOUT (Available to ALL)
# ──────────────────────────────────────────────────────────────────────────────
if "About" in current_tab:
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

