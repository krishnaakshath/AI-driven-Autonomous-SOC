import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Forensics | SOC", page_icon="🔬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .timeline-event {
        background: rgba(26, 31, 46, 0.8);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        margin-left: 20px;
        border-left: 3px solid #00D4FF;
        transition: all 0.3s ease;
    }
    .timeline-event:hover { transform: translateX(5px); box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3); }
    .device-card {
        background: rgba(26, 31, 46, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .device-card:hover { border-color: #00D4FF; box-shadow: 0 5px 20px rgba(0, 212, 255, 0.1); }
    .log-line {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        padding: 0.5rem 1rem;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 4px;
        margin-bottom: 0.3rem;
        border-left: 3px solid;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔬 Forensics & Analysis")
st.markdown("Deep-dive investigation tools and behavioral analytics")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📅 Threat Timeline", "💻 Device States", "👤 User Behavior", "📜 Raw Logs"])

with tab1:
    st.markdown("### Attack Timeline")
    st.markdown("Chronological view of security events")
    
    base_time = datetime.now()
    timeline_events = [
        {"time": base_time - timedelta(minutes=5), "event": "Brute Force Detected", "severity": "HIGH", "source": "203.45.67.89", "action": "Blocked - Account locked"},
        {"time": base_time - timedelta(minutes=15), "event": "Port Scan Initiated", "severity": "MEDIUM", "source": "192.168.1.100", "action": "Monitored - Rate limited"},
        {"time": base_time - timedelta(minutes=32), "event": "SQL Injection Attempt", "severity": "CRITICAL", "source": "45.123.45.67", "action": "Blocked - IP banned"},
        {"time": base_time - timedelta(minutes=48), "event": "Suspicious File Download", "severity": "HIGH", "source": "Internal", "action": "Quarantined - Scanning"},
        {"time": base_time - timedelta(hours=1, minutes=15), "event": "DDoS Attack Wave 1", "severity": "CRITICAL", "source": "Multiple IPs", "action": "Mitigated - Traffic filtered"},
        {"time": base_time - timedelta(hours=2), "event": "Failed SSH Login (x15)", "severity": "MEDIUM", "source": "78.90.12.34", "action": "Restricted - MFA enforced"},
        {"time": base_time - timedelta(hours=3, minutes=30), "event": "Privilege Escalation", "severity": "CRITICAL", "source": "srv-db-01", "action": "Blocked - Session terminated"},
        {"time": base_time - timedelta(hours=5), "event": "Unusual Data Transfer", "severity": "HIGH", "source": "user-jsmith", "action": "Monitored - Alert sent"},
    ]
    
    for event in timeline_events:
        severity_color = "#FF4444" if event["severity"] == "CRITICAL" else "#FF8C00" if event["severity"] == "HIGH" else "#FFD700"
        time_str = event["time"].strftime("%H:%M:%S")
        st.markdown(f"""
            <div class="timeline-event" style="border-left-color: {severity_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="background: {severity_color}; color: white; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600;">{event["severity"]}</span><span style="font-weight: 600; color: #FAFAFA; margin-left: 0.5rem;">{event["event"]}</span></div>
                    <span style="color: #8B95A5; font-size: 0.85rem;">🕐 {time_str}</span>
                </div>
                <div style="margin-top: 0.8rem; display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div><span style="color: #8B95A5; font-size: 0.75rem;">Source:</span><span style="color: #00D4FF; margin-left: 0.5rem; font-family: monospace;">{event["source"]}</span></div>
                    <div><span style="color: #8B95A5; font-size: 0.75rem;">Action:</span><span style="color: #00C853; margin-left: 0.5rem;">{event["action"]}</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("### Endpoint Status Overview")
    devices = [
        {"name": "srv-web-01", "type": "Web Server", "os": "Ubuntu 22.04", "risk": 12, "status": "healthy", "last_seen": "2 min ago", "alerts": 0},
        {"name": "srv-db-01", "type": "Database Server", "os": "CentOS 8", "risk": 78, "status": "critical", "last_seen": "1 min ago", "alerts": 3},
        {"name": "srv-auth-01", "type": "Auth Server", "os": "Windows Server 2022", "risk": 45, "status": "warning", "last_seen": "30 sec ago", "alerts": 1},
        {"name": "srv-api-01", "type": "API Gateway", "os": "Alpine Linux", "risk": 8, "status": "healthy", "last_seen": "15 sec ago", "alerts": 0},
        {"name": "srv-file-01", "type": "File Server", "os": "Windows Server 2019", "risk": 62, "status": "warning", "last_seen": "5 min ago", "alerts": 2},
        {"name": "srv-mail-01", "type": "Mail Server", "os": "Debian 11", "risk": 35, "status": "warning", "last_seen": "1 min ago", "alerts": 1},
    ]
    col1, col2 = st.columns(2)
    for i, device in enumerate(devices):
        risk_color = "#FF4444" if device['risk'] >= 70 else "#FF8C00" if device['risk'] >= 30 else "#00C853"
        status_icon = "🟢" if device['status'] == 'healthy' else "🟡" if device['status'] == 'warning' else "🔴"
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
                <div class="device-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div><span style="font-size: 1.2rem;">{status_icon}</span><span style="font-weight: 600; color: #FAFAFA; margin-left: 0.5rem;">{device['name']}</span></div>
                        <span style="background: {risk_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 8px; font-weight: 600;">Risk: {device['risk']}</span>
                    </div>
                    <div style="margin-top: 1rem; display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.8rem;">
                        <div><p style="color: #8B95A5; font-size: 0.75rem; margin: 0;">Type</p><p style="color: #FAFAFA; margin: 0;">{device['type']}</p></div>
                        <div><p style="color: #8B95A5; font-size: 0.75rem; margin: 0;">OS</p><p style="color: #FAFAFA; margin: 0;">{device['os']}</p></div>
                        <div><p style="color: #8B95A5; font-size: 0.75rem; margin: 0;">Last Seen</p><p style="color: #00D4FF; margin: 0;">{device['last_seen']}</p></div>
                        <div><p style="color: #8B95A5; font-size: 0.75rem; margin: 0;">Active Alerts</p><p style="color: {'#FF4444' if device['alerts'] > 0 else '#00C853'}; margin: 0; font-weight: 600;">{device['alerts']}</p></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

with tab3:
    st.markdown("### User Behavioral Analytics (UEBA)")
    users = [
        {"user": "jsmith", "dept": "Engineering", "risk": 85, "anomalies": ["Unusual login time", "Large file transfer", "New device"], "logins": 45},
        {"user": "mwilson", "dept": "Finance", "risk": 62, "anomalies": ["Failed MFA attempts", "VPN from new location"], "logins": 23},
        {"user": "admin_01", "dept": "IT", "risk": 42, "anomalies": ["Multiple privilege changes"], "logins": 156},
        {"user": "tchen", "dept": "Marketing", "risk": 15, "anomalies": [], "logins": 34},
    ]
    for user in users:
        risk_color = "#FF4444" if user['risk'] >= 70 else "#FF8C00" if user['risk'] >= 30 else "#00C853"
        with st.expander(f"👤 {user['user']} - {user['dept']} | Risk: {user['risk']}"):
            ucol1, ucol2 = st.columns([2, 1])
            with ucol1:
                st.markdown("**Behavioral Anomalies:**")
                if user['anomalies']:
                    for anomaly in user['anomalies']:
                        st.markdown(f"- ⚠️ {anomaly}")
                else:
                    st.markdown("✅ No anomalies detected")
            with ucol2:
                fig = go.Figure(go.Indicator(mode="gauge+number", value=user['risk'],
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': risk_color}, 'bgcolor': "rgba(26, 31, 46, 0.8)",
                           'steps': [{'range': [0, 30], 'color': 'rgba(0, 200, 83, 0.2)'}, {'range': [30, 70], 'color': 'rgba(255, 140, 0, 0.2)'}, {'range': [70, 100], 'color': 'rgba(255, 68, 68, 0.2)'}]}))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA", height=150, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown("### Raw Security Logs")
    log_filter = st.selectbox("Filter by severity", ["All", "ERROR", "WARNING", "INFO"])
    logs = [
        {"time": "21:05:32", "level": "ERROR", "msg": "[FIREWALL] Blocked inbound TCP 203.45.67.89:4444 -> 10.0.1.15:22"},
        {"time": "21:05:28", "level": "WARNING", "msg": "[AUTH] Failed password for admin from 192.168.1.100 port 54321 ssh2"},
        {"time": "21:05:15", "level": "ERROR", "msg": "[IDS] SQL Injection attempt detected: SELECT * FROM users WHERE--"},
        {"time": "21:05:10", "level": "INFO", "msg": "[AUDIT] User jsmith accessed /sensitive/reports/q4_financial.xlsx"},
        {"time": "21:04:55", "level": "WARNING", "msg": "[NETWORK] Unusual traffic spike from 78.90.12.34 (500% increase)"},
        {"time": "21:04:42", "level": "ERROR", "msg": "[MALWARE] Ransomware signature detected in uploaded file document.docx.exe"},
        {"time": "21:04:30", "level": "INFO", "msg": "[SYSTEM] Backup completed successfully for srv-db-01"},
        {"time": "21:04:15", "level": "WARNING", "msg": "[POLICY] User attempted to disable endpoint protection"},
    ]
    for log in logs:
        if log_filter != "All" and log["level"] != log_filter:
            continue
        level_color = "#FF4444" if log["level"] == "ERROR" else "#FF8C00" if log["level"] == "WARNING" else "#00D4FF"
        st.markdown(f'<div class="log-line" style="border-left-color: {level_color};"><span style="color: #8B95A5;">{log["time"]}</span><span style="color: {level_color}; font-weight: 600; margin: 0 0.5rem;">[{log["level"]}]</span><span style="color: #FAFAFA;">{log["msg"]}</span></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">🛡️ AI-Driven Autonomous SOC | Deep Forensic Analysis</p></div>', unsafe_allow_html=True)
