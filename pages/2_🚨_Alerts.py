import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import json
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from alerting.alert_service import trigger_alert, send_test_alert
    ALERTING_AVAILABLE = True
except ImportError:
    ALERTING_AVAILABLE = False

st.set_page_config(page_title="Alerts | SOC", page_icon="🚨", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .alert-card {
        background: rgba(26, 31, 46, 0.8);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid;
        transition: all 0.3s ease;
    }
    .alert-card:hover { transform: translateX(5px); box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3); }
    .alert-critical { border-left-color: #FF4444; background: linear-gradient(90deg, rgba(255, 68, 68, 0.1) 0%, rgba(26, 31, 46, 0.8) 100%); }
    .alert-high { border-left-color: #FF8C00; background: linear-gradient(90deg, rgba(255, 140, 0, 0.1) 0%, rgba(26, 31, 46, 0.8) 100%); }
    .alert-medium { border-left-color: #FFD700; background: linear-gradient(90deg, rgba(255, 215, 0, 0.1) 0%, rgba(26, 31, 46, 0.8) 100%); }
    .alert-low { border-left-color: #00C853; background: linear-gradient(90deg, rgba(0, 200, 83, 0.1) 0%, rgba(26, 31, 46, 0.8) 100%); }
    .severity-badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .badge-critical { background: linear-gradient(135deg, #FF4444, #CC0000); color: white; }
    .badge-high { background: linear-gradient(135deg, #FF8C00, #CC6600); color: white; }
    .badge-medium { background: linear-gradient(135deg, #FFD700, #CC9900); color: #1A1F2E; }
    .badge-low { background: linear-gradient(135deg, #00C853, #009624); color: white; }
    .decision-badge { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
    .decision-block { background: #FF4444; color: white; }
    .decision-restrict { background: #FF8C00; color: white; }
    .stat-box { background: rgba(26, 31, 46, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1rem; text-align: center; }
    .filter-section { background: rgba(26, 31, 46, 0.5); border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

DATA_PATH = "data/parsed_logs/incident_responses.csv"
FULL_MODE = os.path.exists(DATA_PATH)

@st.cache_data(ttl=30)
def load_alerts_data():
    if FULL_MODE:
        df = pd.read_csv(DATA_PATH)
        df = df[df["access_decision"] != "ALLOW"]
        return df
    else:
        np.random.seed(int(datetime.now().timestamp()) % 1000)
        n = 500
        base_time = datetime.now()
        timestamps = [base_time - timedelta(minutes=random.randint(1, 1440)) for _ in range(n)]
        timestamps.sort(reverse=True)
        attack_types = np.random.choice(
            ["Port Scan", "DDoS Attack", "Brute Force", "SQL Injection", "XSS Attack", "Malware C2", 
             "Data Exfiltration", "Privilege Escalation", "Ransomware", "Phishing", "Cryptomining"],
            size=n, p=[0.20, 0.15, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03, 0.02]
        )
        risk_scores = []
        for attack in attack_types:
            if attack in ["Port Scan", "Brute Force"]: risk_scores.append(np.random.normal(55, 15))
            elif attack in ["DDoS Attack", "SQL Injection", "XSS Attack"]: risk_scores.append(np.random.normal(72, 10))
            else: risk_scores.append(np.random.normal(88, 7))
        risk_scores = np.clip(risk_scores, 30, 100).round(2)
        decisions = ["BLOCK" if r >= 70 else "RESTRICT" for r in risk_scores]
        responses = {
            "BLOCK": ["Block IP permanently", "Isolate endpoint", "Terminate session", "Quarantine file", "Disable user account"],
            "RESTRICT": ["Require MFA", "Throttle connection", "Enhanced monitoring", "Temporary IP block", "Rate limit applied"]
        }
        auto_responses = [random.choice(responses[d]) for d in decisions]
        source_ips = [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(n)]
        target_hosts = [f"srv-{random.choice(['web', 'db', 'auth', 'api', 'file'])}-{random.randint(1,10):02d}" for _ in range(n)]
        countries = ["China", "Russia", "United States", "Iran", "North Korea", "Ukraine", "Brazil", "India", "Germany", "Netherlands"]
        source_countries = np.random.choice(countries, size=n, p=[0.25, 0.20, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03])
        return pd.DataFrame({
            "timestamp": timestamps, "attack_type": attack_types, "risk_score": risk_scores,
            "access_decision": decisions, "automated_response": auto_responses,
            "source_ip": source_ips, "target_host": target_hosts, "source_country": source_countries
        })

df = load_alerts_data()

with st.sidebar:
    st.markdown("### 🔔 Notification Controls")
    
    if ALERTING_AVAILABLE:
        if st.button("📤 Send Test Alert", type="primary"):
            try:
                result = send_test_alert()
                if result.get("telegram") or result.get("email"):
                    st.success("✅ Test alert sent!")
                else:
                    st.warning("⚠️ Configure alerts in Settings first")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        st.markdown("**Quick Send Critical Alerts**")
        st.caption("Click on any CRITICAL alert below to send notification")
    else:
        st.warning("⚠️ Alerting module not loaded")
    
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    critical_count = (df["risk_score"] >= 80).sum()
    block_count = (df["access_decision"] == "BLOCK").sum()
    st.metric("Critical Threats", critical_count)
    st.metric("Blocked", block_count)

st.markdown("# 🚨 Security Alerts")
st.markdown("Active threats requiring attention")
st.markdown("---")

def get_severity(risk):
    if risk >= 80: return "CRITICAL"
    elif risk >= 60: return "HIGH"
    elif risk >= 40: return "MEDIUM"
    else: return "LOW"

df["severity"] = df["risk_score"].apply(get_severity)

stat1, stat2, stat3, stat4, stat5 = st.columns(5)
with stat1:
    st.markdown(f'<div class="stat-box"><p style="font-size: 2rem; font-weight: 700; color: #00D4FF; margin: 0;">{len(df)}</p><p style="color: #8B95A5; font-size: 0.85rem; margin: 0;">Total Alerts</p></div>', unsafe_allow_html=True)
with stat2:
    st.markdown(f'<div class="stat-box"><p style="font-size: 2rem; font-weight: 700; color: #FF4444; margin: 0;">{(df["severity"] == "CRITICAL").sum()}</p><p style="color: #8B95A5; font-size: 0.85rem; margin: 0;">Critical</p></div>', unsafe_allow_html=True)
with stat3:
    st.markdown(f'<div class="stat-box"><p style="font-size: 2rem; font-weight: 700; color: #FF8C00; margin: 0;">{(df["severity"] == "HIGH").sum()}</p><p style="color: #8B95A5; font-size: 0.85rem; margin: 0;">High</p></div>', unsafe_allow_html=True)
with stat4:
    st.markdown(f'<div class="stat-box"><p style="font-size: 2rem; font-weight: 700; color: #FF6B6B; margin: 0;">{(df["access_decision"] == "BLOCK").sum()}</p><p style="color: #8B95A5; font-size: 0.85rem; margin: 0;">Blocked</p></div>', unsafe_allow_html=True)
with stat5:
    st.markdown(f'<div class="stat-box"><p style="font-size: 2rem; font-weight: 700; color: #FFD700; margin: 0;">{(df["access_decision"] == "RESTRICT").sum()}</p><p style="color: #8B95A5; font-size: 0.85rem; margin: 0;">Restricted</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="filter-section">', unsafe_allow_html=True)
filter1, filter2, filter3, filter4 = st.columns(4)
with filter1:
    severity_filter = st.multiselect("Severity", options=["CRITICAL", "HIGH", "MEDIUM", "LOW"], default=["CRITICAL", "HIGH"])
with filter2:
    decision_filter = st.multiselect("Decision", options=["BLOCK", "RESTRICT"], default=["BLOCK", "RESTRICT"])
with filter3:
    attack_filter = st.multiselect("Attack Type", options=df["attack_type"].unique().tolist(), default=[])
with filter4:
    limit = st.slider("Show alerts", min_value=10, max_value=100, value=30)
st.markdown('</div>', unsafe_allow_html=True)

filtered_df = df.copy()
if severity_filter: filtered_df = filtered_df[filtered_df["severity"].isin(severity_filter)]
if decision_filter: filtered_df = filtered_df[filtered_df["access_decision"].isin(decision_filter)]
if attack_filter: filtered_df = filtered_df[filtered_df["attack_type"].isin(attack_filter)]
filtered_df = filtered_df.head(limit)

st.markdown(f"### Showing {len(filtered_df)} alerts")
st.markdown("<br>", unsafe_allow_html=True)

for idx, row in filtered_df.iterrows():
    severity = row["severity"]
    severity_class = f"alert-{severity.lower()}"
    badge_class = f"badge-{severity.lower()}"
    decision_class = f"decision-{row['access_decision'].lower()}"
    timestamp_str = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(row["timestamp"], "strftime") else str(row["timestamp"])
    
    st.markdown(f"""
        <div class="alert-card {severity_class}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div><span class="severity-badge {badge_class}">{severity}</span><span style="margin-left: 0.5rem; font-weight: 600; color: #FAFAFA;">{row['attack_type']}</span></div>
                <span class="decision-badge {decision_class}">{row['access_decision']}</span>
            </div>
            <div style="margin-top: 1rem; display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;">
                <div><p style="color: #8B95A5; font-size: 0.75rem; margin: 0;">Risk Score</p><p style="color: #FAFAFA; font-weight: 600; margin: 0;">{row['risk_score']:.1f}</p></div>
                <div><p style="color: #8B95A5; font-size: 0.75rem; margin: 0;">Source IP</p><p style="color: #FAFAFA; font-weight: 600; margin: 0; font-family: monospace;">{row.get('source_ip', 'N/A')}</p></div>
                <div><p style="color: #8B95A5; font-size: 0.75rem; margin: 0;">Target</p><p style="color: #FAFAFA; font-weight: 600; margin: 0;">{row.get('target_host', 'N/A')}</p></div>
                <div><p style="color: #8B95A5; font-size: 0.75rem; margin: 0;">Time</p><p style="color: #FAFAFA; font-weight: 600; margin: 0;">{timestamp_str}</p></div>
            </div>
            <div style="margin-top: 1rem; padding-top: 0.8rem; border-top: 1px solid rgba(255,255,255,0.1);">
                <p style="color: #8B95A5; font-size: 0.75rem; margin: 0;">Automated Response</p>
                <p style="color: #00D4FF; font-weight: 500; margin: 0.25rem 0 0 0;">⚡ {row['automated_response']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">🛡️ AI-Driven Autonomous SOC | Real-time Threat Detection</p></div>', unsafe_allow_html=True)
