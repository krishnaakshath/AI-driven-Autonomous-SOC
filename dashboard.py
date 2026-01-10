import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="AI-Driven Autonomous SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from auth.auth_manager import check_auth, show_user_info

user = check_auth()
if not user:
    st.switch_page("pages/0_🔐_Login.py")
    st.stop()

show_user_info(user)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 1rem; }
    .hero-section {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00D4FF 0%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        color: #8B95A5;
        font-size: 1.1rem;
    }
    .status-card {
        background: rgba(26, 31, 46, 0.8);
        border: 1px solid rgba(0, 200, 83, 0.4);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .status-online {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(0, 200, 83, 0.15);
        border: 1px solid rgba(0, 200, 83, 0.4);
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-size: 1rem;
        color: #00C853;
        font-weight: 600;
    }
    .pulse-dot {
        width: 10px;
        height: 10px;
        background: #00C853;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.3); }
    }
    .feature-card {
        background: rgba(26, 31, 46, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        height: 100%;
        transition: all 0.3s ease;
    }
    .feature-card:hover {
        border-color: #00D4FF;
        transform: translateY(-5px);
    }
    .feature-icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .feature-title { color: #FAFAFA; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; }
    .feature-desc { color: #8B95A5; font-size: 0.9rem; }
    .quick-stat {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .stat-value { font-size: 2rem; font-weight: 700; color: #00D4FF; }
    .stat-label { color: #8B95A5; font-size: 0.85rem; text-transform: uppercase; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

try:
    from ml_engine.ml_scorer import check_ml_status
    ml_status = check_ml_status()
    ML_ONLINE = ml_status.get('ml_available', False)
except:
    ML_ONLINE = False

try:
    import json
    with open('.soc_config.json', 'r') as f:
        config = json.load(f)
    ALERTS_CONFIGURED = bool(config.get('telegram_token')) or bool(config.get('gmail_email'))
except:
    ALERTS_CONFIGURED = False

st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">🛡️ AI-Driven Autonomous SOC</h1>
        <p class="hero-subtitle">Enterprise Security Operations Center with Real-time Threat Detection</p>
        <br>
        <div class="status-online">
            <div class="pulse-dot"></div>
            System Active - Zero Trust Enforcement Enabled
        </div>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    ml_color = "#00C853" if ML_ONLINE else "#FF8C00"
    ml_text = "Online" if ML_ONLINE else "Standby"
    st.markdown(f"""
        <div class="quick-stat" style="border-color: {ml_color};">
            <p class="stat-value" style="color: {ml_color};">🧠</p>
            <p class="stat-label">ML Engine: {ml_text}</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    alert_color = "#00C853" if ALERTS_CONFIGURED else "#FF8C00"
    alert_text = "Active" if ALERTS_CONFIGURED else "Configure"
    st.markdown(f"""
        <div class="quick-stat" style="border-color: {alert_color};">
            <p class="stat-value" style="color: {alert_color};">🔔</p>
            <p class="stat-label">Alerts: {alert_text}</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="quick-stat" style="border-color: #00C853;">
            <p class="stat-value" style="color: #00C853;">⚡</p>
            <p class="stat-label">Response: Auto</p>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
        <div class="quick-stat" style="border-color: #8B5CF6;">
            <p class="stat-value" style="color: #8B5CF6;">🔒</p>
            <p class="stat-label">Zero Trust: Enabled</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("### 🚀 Quick Navigation")

nav1, nav2, nav3 = st.columns(3)

with nav1:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Security Dashboard</div>
            <div class="feature-desc">Real-time metrics, threat activity, and decision distribution</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Open Dashboard", key="dash"):
        st.switch_page("pages/1_🏠_Dashboard.py")

with nav2:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🚨</div>
            <div class="feature-title">Active Alerts</div>
            <div class="feature-desc">View and manage security alerts with severity filtering</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("View Alerts", key="alerts"):
        st.switch_page("pages/2_🚨_Alerts.py")

with nav3:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🌍</div>
            <div class="feature-title">Threat Map</div>
            <div class="feature-desc">Geographic visualization of attack sources worldwide</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("View Map", key="map"):
        st.switch_page("pages/3_🌍_Threat_Map.py")

st.markdown("<br>", unsafe_allow_html=True)

nav4, nav5, nav6 = st.columns(3)

with nav4:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔬</div>
            <div class="feature-title">Forensics</div>
            <div class="feature-desc">Deep-dive analysis, timeline, and behavioral analytics</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Open Forensics", key="forensics"):
        st.switch_page("pages/4_🔬_Forensics.py")

with nav5:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <div class="feature-title">IEEE Reports</div>
            <div class="feature-desc">Generate professional security reports in IEEE format</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Generate Reports", key="reports"):
        st.switch_page("pages/5_📊_Reports.py")

with nav6:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚙️</div>
            <div class="feature-title">Settings</div>
            <div class="feature-desc">Configure alerts, AI integration, and security policies</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Open Settings", key="settings"):
        st.switch_page("pages/6_⚙️_Settings.py")

st.markdown("---")

st.markdown("### 🔧 System Capabilities")

cap1, cap2 = st.columns(2)

with cap1:
    st.markdown("""
    **Machine Learning Engine**
    - Algorithm: Isolation Forest (150 trees)
    - Features: 11 network flow attributes
    - Contamination Rate: 5%
    - Training Data: CICIDS 2017 Dataset
    
    **Zero Trust Policy**
    - Risk ≥ 70: BLOCK (terminate session)
    - Risk 30-69: RESTRICT (require MFA)
    - Risk < 30: ALLOW (continue monitoring)
    """)

with cap2:
    st.markdown("""
    **Alerting Channels**
    - Telegram: Real-time notifications
    - Gmail: HTML-formatted alerts
    - Daily summary reports
    
    **AI Integration**
    - Google Gemini 2.0 Flash
    - Natural language threat analysis
    - Automated remediation suggestions
    """)

st.markdown("---")

st.markdown("""
    <div style="text-align: center; color: #8B95A5; padding: 1rem;">
        <p style="margin: 0; font-size: 1rem;">🛡️ AI-Driven Autonomous SOC</p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem;">Final Year Project | Zero Trust Security Platform</p>
    </div>
""", unsafe_allow_html=True)
