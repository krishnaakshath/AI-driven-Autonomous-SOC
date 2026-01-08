import streamlit as st
import os
import json

st.set_page_config(page_title="Settings | SOC", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .settings-card {
        background: rgba(26, 31, 46, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .settings-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #FAFAFA;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .success-msg {
        background: rgba(0, 200, 83, 0.1);
        border: 1px solid rgba(0, 200, 83, 0.3);
        border-radius: 8px;
        padding: 1rem;
        color: #00C853;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

CONFIG_FILE = ".soc_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'gmail_email': '', 'gmail_password': '', 'gmail_recipient': '',
        'telegram_token': '', 'telegram_chat_id': '',
        'gemini_api_key': '',
        'alert_threshold': 70, 'auto_block': True, 'mfa_enforcement': True,
        'notification_email': True, 'notification_telegram': True
    }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

if 'config' not in st.session_state:
    st.session_state.config = load_config()

st.markdown("# ⚙️ Settings")
st.markdown("Configure SOC platform settings and integrations")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📧 Gmail Alerts", "📱 Telegram Alerts", "🤖 AI Integration", "🛡️ Security Policy"])

with tab1:
    st.markdown("### Gmail SMTP Configuration")
    st.markdown("Configure Gmail to send security alerts via email")
    
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    
    st.info("""
    **Setup Instructions:**
    1. Enable 2-Factor Authentication on your Gmail account
    2. Go to Google Account → Security → App Passwords
    3. Generate an App Password for "Mail"
    4. Use that 16-character password below (not your regular Gmail password)
    """)
    
    gmail_email = st.text_input("Gmail Address", value=st.session_state.config.get('gmail_email', ''), placeholder="your-email@gmail.com")
    gmail_password = st.text_input("App Password", value=st.session_state.config.get('gmail_password', ''), type="password", placeholder="xxxx xxxx xxxx xxxx")
    gmail_recipient = st.text_input("Alert Recipients", value=st.session_state.config.get('gmail_recipient', ''), placeholder="security-team@company.com, ciso@company.com")
    
    gmail_enabled = st.toggle("Enable Gmail Alerts", value=st.session_state.config.get('notification_email', True))
    
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        if st.button("💾 Save Gmail Settings", type="primary"):
            st.session_state.config.update({
                'gmail_email': gmail_email,
                'gmail_password': gmail_password,
                'gmail_recipient': gmail_recipient,
                'notification_email': gmail_enabled
            })
            save_config(st.session_state.config)
            st.success("✅ Gmail settings saved successfully!")
    
    with gcol2:
        if st.button("🔗 Test Gmail Connection"):
            if gmail_email and gmail_password:
                try:
                    import smtplib
                    from email.mime.text import MIMEText
                    
                    msg = MIMEText("🔗 SOC Gmail Alert Test - Connection Successful!")
                    msg["Subject"] = "SOC Alert Test"
                    msg["From"] = gmail_email
                    msg["To"] = gmail_recipient or gmail_email
                    
                    with smtplib.SMTP("smtp.gmail.com", 587) as server:
                        server.starttls()
                        server.login(gmail_email, gmail_password)
                        server.sendmail(gmail_email, [gmail_recipient or gmail_email], msg.as_string())
                    
                    st.success("✅ Test email sent successfully!")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
            else:
                st.warning("Please enter Gmail credentials first")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown("### Telegram Bot Configuration")
    st.markdown("Receive instant security alerts via Telegram")
    
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    
    st.info("""
    **Setup Instructions:**
    1. Open Telegram and search for **@BotFather**
    2. Send `/newbot` and follow the prompts to create a bot
    3. Copy the **Bot Token** provided
    4. Add your bot to a group or message it directly
    5. To get your Chat ID, message **@userinfobot** or use `https://api.telegram.org/bot<TOKEN>/getUpdates`
    """)
    
    telegram_token = st.text_input("Bot Token", value=st.session_state.config.get('telegram_token', ''), type="password", placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
    telegram_chat_id = st.text_input("Chat ID", value=st.session_state.config.get('telegram_chat_id', ''), placeholder="-1001234567890")
    
    telegram_enabled = st.toggle("Enable Telegram Alerts", value=st.session_state.config.get('notification_telegram', True))
    
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        if st.button("💾 Save Telegram Settings", type="primary"):
            st.session_state.config.update({
                'telegram_token': telegram_token,
                'telegram_chat_id': telegram_chat_id,
                'notification_telegram': telegram_enabled
            })
            save_config(st.session_state.config)
            st.success("✅ Telegram settings saved successfully!")
    
    with tcol2:
        if st.button("🔗 Test Telegram Connection"):
            if telegram_token and telegram_chat_id:
                try:
                    import requests
                    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                    data = {"chat_id": telegram_chat_id, "text": "🔗 SOC Alert Test - Connection Successful! ✅", "parse_mode": "HTML"}
                    response = requests.post(url, json=data, timeout=10)
                    if response.status_code == 200:
                        st.success("✅ Test message sent successfully!")
                    else:
                        st.error(f"❌ Failed: {response.json().get('description', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
            else:
                st.warning("Please enter Telegram credentials first")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown("### AI Integration")
    st.markdown("Configure Google Gemini for AI-powered threat analysis")
    
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    
    st.info("""
    **Get Your Free Gemini API Key:**
    1. Visit [Google AI Studio](https://aistudio.google.com/)
    2. Sign in with your Google account
    3. Click "Get API Key" → "Create API Key"
    4. Copy and paste the key below
    """)
    
    gemini_key = st.text_input("Gemini API Key", value=st.session_state.config.get('gemini_api_key', ''), type="password", placeholder="AIzaSy...")
    
    st.markdown("**AI Features Enabled:**")
    st.markdown("""
    - 🔍 Natural language threat analysis
    - 📝 AI-generated incident summaries
    - 💡 Automated remediation recommendations
    - 🤖 Conversational SOC assistant
    """)
    
    acol1, acol2 = st.columns(2)
    with acol1:
        if st.button("💾 Save Gemini API Key", type="primary"):
            st.session_state.config['gemini_api_key'] = gemini_key
            save_config(st.session_state.config)
            os.environ['GEMINI_API_KEY'] = gemini_key
            st.success("✅ Gemini API key saved!")
    
    with acol2:
        if st.button("🔗 Test Gemini Connection"):
            if gemini_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content("Say 'Connection successful' in exactly 3 words.")
                    st.success(f"✅ Connected! Response: {response.text[:50]}...")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
            else:
                st.warning("Please enter API key first")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown("### Security Policy Configuration")
    
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("#### Zero Trust Thresholds")
    
    pcol1, pcol2 = st.columns(2)
    with pcol1:
        block_threshold = st.slider("BLOCK Threshold (Risk Score)", 0, 100, st.session_state.config.get('block_threshold', 70))
        restrict_threshold = st.slider("RESTRICT Threshold (Risk Score)", 0, 100, st.session_state.config.get('restrict_threshold', 30))
    
    with pcol2:
        auto_block = st.checkbox("Auto-block high-risk IPs", value=st.session_state.config.get('auto_block', True))
        mfa_enforcement = st.checkbox("Enforce MFA on RESTRICT", value=st.session_state.config.get('mfa_enforcement', True))
        rate_limit = st.checkbox("Rate limit suspicious IPs", value=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("#### Automated Response Actions")
    
    st.multiselect("Enabled Auto-Response Actions", 
                   ["Block IP", "Throttle Connection", "Require MFA", "Isolate Endpoint", "Terminate Session", "Quarantine File", "Lock Account"],
                   default=["Block IP", "Throttle Connection", "Require MFA"])
    
    st.number_input("Auto-block duration (minutes)", min_value=5, max_value=1440, value=60)
    st.checkbox("Require analyst approval for permanent blocks", value=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("#### Alert Thresholds")
    
    alert_threshold = st.slider("Minimum Risk Score for Alerts", 0, 100, st.session_state.config.get('alert_threshold', 70))
    
    st.checkbox("Alert on all BLOCK decisions", value=True)
    st.checkbox("Alert on CRITICAL severity only", value=False)
    st.checkbox("Daily summary email", value=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("💾 Save All Security Settings", type="primary"):
        st.session_state.config.update({
            'block_threshold': block_threshold,
            'restrict_threshold': restrict_threshold,
            'auto_block': auto_block,
            'mfa_enforcement': mfa_enforcement,
            'alert_threshold': alert_threshold
        })
        save_config(st.session_state.config)
        st.success("✅ Security settings saved!")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">🛡️ AI-Driven Autonomous SOC | Configuration Center</p></div>', unsafe_allow_html=True)
