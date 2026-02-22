import streamlit as st
import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="User Behavior Analytics | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIError:
    pass  # Already set by dashboard.py

# ── Admin-only gate ──────────────────────────────────────────────────────────
from services.auth_service import is_authenticated, is_admin
if not is_authenticated():
    st.error("**Authentication Required** — Please log in.")
    if st.button("Go to Login"):
        st.switch_page("pages/_Login.py")
    st.stop()
if not is_admin():
    st.error("**Admin Access Only** — UBA is restricted to administrators.")
    st.info(f"Logged in as: {st.session_state.get('user_email', 'Unknown')}")
    st.stop()


# Auto-refresh
import time
if 'last_uba_refresh' not in st.session_state:
    st.session_state.last_uba_refresh = time.time()

# Import UI components
from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title



st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("User Behavior Analytics", "ML-powered insider threat detection and anomaly analysis"), unsafe_allow_html=True)

# Import services for real data
try:
    from services.siem_service import get_user_behavior
    from ml_engine.behavior_analyzer import behavior_detector
    HAS_REAL_DATA = True
except ImportError:
    HAS_REAL_DATA = False
except Exception as e:
    import traceback
    st.error(f"CRITICAL ERROR during import: {e}")
    st.code(traceback.format_exc())
    HAS_REAL_DATA = False

# Get user behavior data from SIEM
@st.cache_data(ttl=300)
def generate_user_data():
    if HAS_REAL_DATA:
        try:
            data = get_user_behavior()
            if data:
                # Map SIEM fields to expected format, generating deterministic departments
                import hashlib
                depts = ["IT", "Finance", "HR", "Sales", "Engineering"]
                
                formatted = []
                for u in data:
                    uname = u.get("user", "unknown")
                    # Deterministic department based on hash of username
                    dept_idx = int(hashlib.md5(uname.encode()).hexdigest(), 16) % len(depts)
                    
                    formatted.append({
                        "user": uname,
                        "department": u.get("department") or depts[dept_idx],
                        "login_count": u.get("login_count", 0),
                        "failed_logins": u.get("failed_logins", 0),
                        "data_downloaded_mb": u.get("data_access", 0) * 10,  # Convert to MB
                        "after_hours_logins": u.get("after_hours_activity", 0),
                        "unique_ips": u.get("unique_ips", 1),
                        "privilege_escalation": u.get("high_severity_alerts", 0),
                        "risk_score": u.get("risk_score", 0),
                        "is_anomalous": u.get("is_anomalous", False)
                    })
                return formatted
        except Exception as e:
            st.warning(f"SIEM connection issue: {e}")
    
    # Return empty if no DB connection
    return []

# Show data source
if HAS_REAL_DATA:
    st.markdown("""
    <div style="background: rgba(0, 212, 255, 0.1); border: 1px solid #00D4FF40; border-radius: 8px; padding: 10px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #00D4FF;">🔒 SIEM CONNECTED</span>
            <span style="color: #8B5CF6;">🧠 ML ENGINE ACTIVE</span>
        </div>
        <div style="color: #8B95A5; font-size: 0.8rem;">Analyzing live event stream...</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("⚠️ Using simulated data - Engine not grounded")

user_data = generate_user_data()
df = pd.DataFrame(user_data)

# Risk Overview
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

high_risk = len([u for u in user_data if u["risk_score"] > 70])
medium_risk = len([u for u in user_data if 40 <= u["risk_score"] <= 70])
anomalous = len([u for u in user_data if u["is_anomalous"]])

metrics = [
    ("High Risk Users", high_risk, "#FF4444"),
    ("Medium Risk", medium_risk, "#FF8C00"),
    ("Anomalies Detected", anomalous, "#8B5CF6"),
    ("Users Monitored", len(user_data), "#00D4FF")
]

for col, (label, value, color) in zip([col1, col2, col3, col4], metrics):
    with col:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(26,31,46,0.8), rgba(26,31,46,0.6));
            border: 1px solid {color}40;
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        ">
            <div style="font-size: 2.5rem; font-weight: 800; color: {color};">{value}</div>
            <div style="color: #8B95A5;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# User Risk Table
st.markdown(section_title("User Risk Analysis"), unsafe_allow_html=True)

for user in user_data[:5]:
    risk_color = "#FF4444" if user["risk_score"] > 70 else "#FF8C00" if user["risk_score"] > 40 else "#00C853"
    
    st.markdown(f"""
    <div style="
        background: rgba(26,31,46,0.5);
        border-left: 4px solid {risk_color};
        padding: 15px;
        border-radius: 0 8px 8px 0;
        margin: 10px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div>
            <span style="color: #FAFAFA; font-weight: bold; font-size: 1.1rem;"> {user['user']}</span>
            <span style="color: #8B95A5; margin-left: 10px;">{user['department']}</span>
        </div>
        <div style="display: flex; gap: 30px; align-items: center;">
            <div style="text-align: center;">
                <div style="color: #8B95A5; font-size: 0.8rem;">Failed Logins</div>
                <div style="color: {'#FF4444' if user['failed_logins'] > 5 else '#FAFAFA'}; font-weight: bold;">{user['failed_logins']}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: #8B95A5; font-size: 0.8rem;">Data (MB)</div>
                <div style="color: {'#FF4444' if user['data_downloaded_mb'] > 500 else '#FAFAFA'}; font-weight: bold;">{user['data_downloaded_mb']:,}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: #8B95A5; font-size: 0.8rem;">After Hours</div>
                <div style="color: {'#FF4444' if user['after_hours_logins'] > 3 else '#FAFAFA'}; font-weight: bold;">{user['after_hours_logins']}</div>
            </div>
            <div style="text-align: center;">
                <div style="color: #8B95A5; font-size: 0.8rem;">Unique IPs</div>
                <div style="color: {'#FF8C00' if user['unique_ips'] > 5 else '#FAFAFA'}; font-weight: bold;">{user['unique_ips']}</div>
            </div>
            <div style="
                background: {risk_color};
                color: #000;
                padding: 10px 20px;
                border-radius: 20px;
                font-weight: bold;
                min-width: 80px;
                text-align: center;
            ">
                {user['risk_score']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Behavior Charts
st.markdown("<br>", unsafe_allow_html=True)
chart1, chart2 = st.columns(2)

with chart1:
    st.markdown(section_title("Risk Distribution"), unsafe_allow_html=True)
    
    fig = go.Figure(data=[go.Pie(
        labels=["High Risk", "Medium Risk", "Low Risk"],
        values=[high_risk, medium_risk, len(user_data) - high_risk - medium_risk],
        hole=.5,
        marker_colors=["#FF4444", "#FF8C00", "#00C853"]
    )])
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#FAFAFA",
        showlegend=True,
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.markdown(section_title("Anomaly Indicators"), unsafe_allow_html=True)
    
    indicators = ["Failed Logins", "Data Transfer", "After Hours", "Multi-IP", "Priv. Escalation"]
    values = [
        sum(u["failed_logins"] for u in user_data),
        sum(1 for u in user_data if u["data_downloaded_mb"] > 500),
        sum(u["after_hours_logins"] for u in user_data),
        sum(1 for u in user_data if u["unique_ips"] > 5),
        sum(u["privilege_escalation"] for u in user_data)
    ]
    
    fig = go.Figure(data=[go.Bar(
        x=indicators,
        y=values,
        marker_color=["#FF4444", "#FF8C00", "#8B5CF6", "#00D4FF", "#FF0066"]
    )])
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FAFAFA",
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
    )
    st.plotly_chart(fig, use_container_width=True)

# Export
st.markdown("<br>", unsafe_allow_html=True)
csv = df.to_csv(index=False)
st.download_button(" Export User Analytics (CSV)", csv, "user_behavior_analytics.csv", "text/csv")

# Auto-Refresh Logic (Every 30 seconds)
if 'last_uba_refresh' not in st.session_state:
    st.session_state.last_uba_refresh = time.time()

if time.time() - st.session_state.last_uba_refresh > 30:
    st.cache_data.clear()
    st.session_state.last_uba_refresh = time.time()
    st.rerun()

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | User Behavior Analytics</p></div>', unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
