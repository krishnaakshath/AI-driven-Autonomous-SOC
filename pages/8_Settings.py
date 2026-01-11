import streamlit as st
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Settings | SOC", page_icon="S", layout="wide")

from ui.theme import PREMIUM_CSS, page_header, section_title
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

from auth.auth_manager import check_auth, show_user_info

user = check_auth()
if not user:
    st.switch_page("pages/0_Login.py")
    st.stop()

show_user_info(user)

st.markdown(page_header("Settings", "Configure integrations, notifications, and thresholds"), unsafe_allow_html=True)

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

tab1, tab2, tab3, tab4 = st.tabs(["API Keys", "Notifications", "Thresholds", "About"])

with tab1:
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
    
    if st.button("Save API Keys", type="primary"):
        config["gemini_api_key"] = gemini_key
        config["virustotal_api_key"] = vt_key
        save_config(config)
        st.success("API keys saved successfully!")

with tab2:
    st.markdown(section_title("Notification Settings"), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="glass-card">
                <h4 style="color: #FF4444; margin: 0 0 1rem 0;">Email Alerts (Gmail)</h4>
            </div>
        """, unsafe_allow_html=True)
        
        gmail_email = st.text_input("Gmail Address", value=config.get("gmail_email", ""), key="gmail_email")
        gmail_password = st.text_input("App Password", value=config.get("gmail_password", ""), type="password", key="gmail_pass")
        gmail_recipient = st.text_input("Alert Recipient", value=config.get("gmail_recipient", ""), key="gmail_to")
    
    with col2:
        st.markdown("""
            <div class="glass-card">
                <h4 style="color: #00D4FF; margin: 0 0 1rem 0;">Telegram Bot</h4>
            </div>
        """, unsafe_allow_html=True)
        
        telegram_token = st.text_input("Bot Token", value=config.get("telegram_token", ""), type="password", key="tg_token")
        telegram_chat = st.text_input("Chat ID", value=config.get("telegram_chat_id", ""), key="tg_chat")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Save Notifications", type="primary"):
        config["gmail_email"] = gmail_email
        config["gmail_password"] = gmail_password
        config["gmail_recipient"] = gmail_recipient
        config["telegram_token"] = telegram_token
        config["telegram_chat_id"] = telegram_chat
        save_config(config)
        st.success("Notification settings saved!")

with tab3:
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

with tab4:
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
