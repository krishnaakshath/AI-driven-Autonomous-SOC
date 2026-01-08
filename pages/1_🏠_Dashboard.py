import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os

st.set_page_config(page_title="Dashboard | SOC", page_icon="🏠", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .metric-container {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0, 212, 255, 0.15);
    }
    .big-number { font-size: 3rem; font-weight: 700; color: #00D4FF; line-height: 1; }
    .metric-label { font-size: 0.9rem; color: #8B95A5; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.5rem; }
    .section-header { font-size: 1.3rem; font-weight: 600; color: #FAFAFA; margin-bottom: 1rem; }
    .live-indicator {
        display: inline-flex; align-items: center; gap: 0.5rem;
        background: rgba(0, 200, 83, 0.15); border: 1px solid rgba(0, 200, 83, 0.3);
        padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; color: #00C853;
    }
    .pulse { width: 8px; height: 8px; background: #00C853; border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.3); } }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

DATA_PATH = "data/parsed_logs/incident_responses.csv"
FULL_MODE = os.path.exists(DATA_PATH)

@st.cache_data(ttl=30)
def load_soc_data():
    if FULL_MODE:
        return pd.read_csv(DATA_PATH)
    else:
        np.random.seed(int(datetime.now().timestamp()) % 1000)
        n = 2000
        base_time = datetime.now()
        timestamps = [base_time - timedelta(minutes=random.randint(1, 2880)) for _ in range(n)]
        timestamps.sort(reverse=True)
        attack_types = np.random.choice(
            ["Normal", "Port Scan", "DDoS", "Brute Force", "SQL Injection", "XSS", "Malware C2", "Data Exfil", "Privilege Esc", "Ransomware"],
            size=n, p=[0.60, 0.12, 0.08, 0.07, 0.04, 0.03, 0.02, 0.02, 0.01, 0.01]
        )
        risk_scores = []
        for attack in attack_types:
            if attack == "Normal": risk_scores.append(np.random.normal(12, 6))
            elif attack in ["Port Scan", "Brute Force"]: risk_scores.append(np.random.normal(48, 12))
            elif attack in ["DDoS", "SQL Injection", "XSS"]: risk_scores.append(np.random.normal(68, 10))
            else: risk_scores.append(np.random.normal(88, 6))
        risk_scores = np.clip(risk_scores, 0, 100).round(2)
        decisions = ["BLOCK" if r >= 70 else "RESTRICT" if r >= 30 else "ALLOW" for r in risk_scores]
        countries = ["United States", "China", "Russia", "Germany", "Brazil", "India", "Ukraine", "Iran", "North Korea", "Netherlands"]
        return pd.DataFrame({
            "timestamp": timestamps,
            "attack_type": attack_types,
            "risk_score": risk_scores,
            "access_decision": decisions,
            "source_country": np.random.choice(countries, size=n, p=[0.25, 0.20, 0.15, 0.10, 0.08, 0.07, 0.05, 0.04, 0.03, 0.03]),
            "source_ip": [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(n)],
            "dest_port": np.random.choice([22, 80, 443, 3389, 445, 8080, 3306, 21], size=n)
        })

df = load_soc_data()

col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.markdown("# 🏠 Security Dashboard")
    st.markdown("Real-time overview of your security posture")
with col_header2:
    st.markdown('<div class="live-indicator" style="float: right; margin-top: 1rem;"><div class="pulse"></div>Live Monitoring</div>', unsafe_allow_html=True)

st.markdown("---")

total = len(df)
blocked = (df["access_decision"] == "BLOCK").sum()
restricted = (df["access_decision"] == "RESTRICT").sum()
allowed = (df["access_decision"] == "ALLOW").sum()
avg_risk = df["risk_score"].mean()
critical = (df["risk_score"] >= 80).sum()

m1, m2, m3, m4, m5, m6 = st.columns(6)
metrics = [
    (m1, total, "Total Events", "#00D4FF", "📊"),
    (m2, critical, "Critical", "#FF4444", "🔴"),
    (m3, blocked, "Blocked", "#FF6B6B", "🛑"),
    (m4, restricted, "Restricted", "#FF8C00", "⚠️"),
    (m5, allowed, "Allowed", "#00C853", "✅"),
    (m6, f"{avg_risk:.1f}", "Avg Risk", "#8B5CF6", "📈")
]

for col, value, label, color, icon in metrics:
    with col:
        display_value = f"{value:,}" if isinstance(value, (int, np.integer)) else value
        st.markdown(f'<div class="metric-container" style="border-color: {color};"><p style="font-size: 0.9rem; margin: 0;">{icon}</p><p class="big-number" style="color: {color};">{display_value}</p><p class="metric-label">{label}</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

chart1, chart2 = st.columns(2)

with chart1:
    st.markdown('<p class="section-header">📈 Threat Activity (Last 48 Hours)</p>', unsafe_allow_html=True)
    if hasattr(df["timestamp"].iloc[0], "hour"):
        df["hour"] = df["timestamp"].apply(lambda x: x.replace(minute=0, second=0, microsecond=0))
        hourly = df.groupby("hour").size().reset_index(name="count")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hourly["hour"], y=hourly["count"], mode="lines+markers", fill="tozeroy",
                                  line=dict(color="#00D4FF", width=2), marker=dict(size=6), fillcolor="rgba(0, 212, 255, 0.1)"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA",
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
                          margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Timeline data not available in demo mode")

with chart2:
    st.markdown('<p class="section-header">🎯 Decision Distribution</p>', unsafe_allow_html=True)
    decision_counts = df["access_decision"].value_counts()
    fig2 = go.Figure(data=[go.Pie(labels=decision_counts.index, values=decision_counts.values, hole=0.5,
                                   marker_colors=["#00C853", "#FF8C00", "#FF4444"], textinfo="label+percent", textfont_size=12)])
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA",
                       showlegend=False, margin=dict(l=20, r=20, t=20, b=20), height=300)
    st.plotly_chart(fig2, use_container_width=True)

chart3, chart4 = st.columns(2)

with chart3:
    st.markdown('<p class="section-header">🔥 Top Attack Types</p>', unsafe_allow_html=True)
    attack_counts = df[df["attack_type"] != "Normal"]["attack_type"].value_counts().head(6)
    fig3 = go.Figure(go.Bar(x=attack_counts.values, y=attack_counts.index, orientation="h",
                             marker=dict(color=attack_counts.values, colorscale=[[0, "#00D4FF"], [0.5, "#8B5CF6"], [1, "#FF4444"]])))
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA",
                       xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"), yaxis=dict(showgrid=False),
                       margin=dict(l=20, r=20, t=20, b=20), height=280)
    st.plotly_chart(fig3, use_container_width=True)

with chart4:
    st.markdown('<p class="section-header">🌍 Attack Sources by Country</p>', unsafe_allow_html=True)
    if "source_country" in df.columns:
        country_counts = df[df["attack_type"] != "Normal"]["source_country"].value_counts().head(6)
        fig4 = go.Figure(go.Bar(x=country_counts.index, y=country_counts.values,
                                 marker=dict(color=country_counts.values, colorscale=[[0, "#FF8C00"], [1, "#FF4444"]])))
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA",
                           xaxis=dict(showgrid=False, tickangle=-45), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
                           margin=dict(l=20, r=20, t=20, b=60), height=280)
        st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.markdown('<p class="section-header">🎚️ Overall Security Health</p>', unsafe_allow_html=True)

gauge_col1, gauge_col2, gauge_col3 = st.columns([1, 2, 1])

with gauge_col2:
    security_score = max(0, 100 - avg_risk)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=security_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Security Score", 'font': {'size': 20, 'color': '#FAFAFA'}},
        delta={'reference': 75, 'increasing': {'color': "#00C853"}, 'decreasing': {'color': "#FF4444"}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "#FAFAFA"},
            'bar': {'color': "#00D4FF"},
            'bgcolor': "rgba(26, 31, 46, 0.7)",
            'borderwidth': 2, 'bordercolor': "rgba(255, 255, 255, 0.1)",
            'steps': [{'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.3)'},
                      {'range': [40, 70], 'color': 'rgba(255, 140, 0, 0.3)'},
                      {'range': [70, 100], 'color': 'rgba(0, 200, 83, 0.3)'}],
            'threshold': {'line': {'color': "#FAFAFA", 'width': 4}, 'thickness': 0.75, 'value': security_score}
        }
    ))
    fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#FAFAFA", 'family': "Inter"}, height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">🛡️ AI-Driven Autonomous SOC | Zero Trust Security Platform</p></div>', unsafe_allow_html=True)
