import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Alerts | SOC", page_icon="A", layout="wide")

from ui.theme import PREMIUM_CSS, page_header, alert_card, section_title
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


# Authentication removed - public dashboard

# Page header
st.markdown(page_header("Security Alerts", "Real-time threat detection and response"), unsafe_allow_html=True)

# Auto-refresh every 30 seconds
import time
if 'last_alert_refresh' not in st.session_state:
    st.session_state.last_alert_refresh = time.time()

# Refresh button and auto-refresh indicator
col_refresh, col_time = st.columns([1, 3])
with col_refresh:
    if st.button("Refresh Alerts", type="primary"):
        st.cache_data.clear()
        st.session_state.last_alert_refresh = time.time()
        st.rerun()

with col_time:
    st.markdown(f'''
        <div style="display: flex; align-items: center; gap: 0.5rem; height: 38px;">
            <span style="color: #00C853;">●</span>
            <span style="color: #8B95A5;">Auto-refreshing every 30s</span>
        </div>
    ''', unsafe_allow_html=True)

# Auto-refresh logic
if time.time() - st.session_state.last_alert_refresh > 30:
    st.cache_data.clear()
    st.session_state.last_alert_refresh = time.time()
    st.rerun()

# Generate alerts data
@st.cache_data(ttl=30)
def get_alerts():
    np.random.seed(int(datetime.now().timestamp()) % 100)
    n = 50
    severities = np.random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"], n, p=[0.1, 0.25, 0.35, 0.3])
    attack_types = np.random.choice([
        "Brute Force Attack", "SQL Injection Attempt", "DDoS Detection",
        "Port Scan Detected", "Malware Communication", "Privilege Escalation",
        "Data Exfiltration", "Ransomware Activity", "Phishing Attempt"
    ], n)
    
    alerts = []
    base_time = datetime.now()
    for i in range(n):
        alerts.append({
            "id": f"ALT-{1000+i}",
            "severity": severities[i],
            "type": attack_types[i],
            "source_ip": f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "time": base_time - timedelta(minutes=random.randint(1, 1440)),
            "status": random.choice(["Active", "Investigating", "Resolved"]),
            "risk_score": random.randint(30, 99)
        })
    return pd.DataFrame(alerts)

alerts_df = get_alerts()

# Stats
critical = (alerts_df["severity"] == "CRITICAL").sum()
high = (alerts_df["severity"] == "HIGH").sum()
active = (alerts_df["status"] == "Active").sum()
resolved = (alerts_df["status"] == "Resolved").sum()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF4444;">{critical}</p><p class="metric-label">Critical</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF8C00;">{high}</p><p class="metric-label">High</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00D4FF;">{active}</p><p class="metric-label">Active</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00C853;">{resolved}</p><p class="metric-label">Resolved</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    sev_filter = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
with col2:
    status_filter = st.selectbox("Status", ["All", "Active", "Investigating", "Resolved"])
with col3:
    sort_by = st.selectbox("Sort By", ["Time (Newest)", "Risk Score", "Severity"])

# Filter data
filtered = alerts_df.copy()
if sev_filter != "All":
    filtered = filtered[filtered["severity"] == sev_filter]
if status_filter != "All":
    filtered = filtered[filtered["status"] == status_filter]

if sort_by == "Time (Newest)":
    filtered = filtered.sort_values("time", ascending=False)
elif sort_by == "Risk Score":
    filtered = filtered.sort_values("risk_score", ascending=False)
else:
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    filtered["sev_order"] = filtered["severity"].map(sev_order)
    filtered = filtered.sort_values("sev_order")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_title(f"Active Alerts ({len(filtered)})"), unsafe_allow_html=True)

# Display alerts
for _, alert in filtered.head(20).iterrows():
    time_str = alert["time"].strftime("%H:%M") if hasattr(alert["time"], "strftime") else str(alert["time"])[:5]
    desc = f"Source: {alert['source_ip']} | Risk: {alert['risk_score']}/100 | Status: {alert['status']}"
    st.markdown(alert_card(alert["severity"], f"{alert['id']} - {alert['type']}", desc, time_str), unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Alerts</p></div>', unsafe_allow_html=True)
