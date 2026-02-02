import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Dashboard | SOC", page_icon="D", layout="wide")

# Premium animated theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0e17 0%, #151c2c 50%, #0d1320 100%);
    }
    
    /* Animated background glow */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: 
            radial-gradient(ellipse at 20% 80%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(139, 92, 246, 0.08) 0%, transparent 50%);
        pointer-events: none;
        animation: bgPulse 15s ease-in-out infinite;
    }
    
    @keyframes bgPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* Header with gradient text */
    .premium-header {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 24px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .premium-header::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(0, 212, 255, 0.15) 0%, transparent 70%);
        animation: float 8s ease-in-out infinite;
    }
    
    .premium-header h1 {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #00D4FF 50%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        position: relative;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(5deg); }
    }
    
    /* Metric cards with glow */
    .metric-card {
        background: linear-gradient(145deg, rgba(26, 31, 46, 0.9) 0%, rgba(15, 20, 30, 0.95) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 1.8rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.6s ease;
    }
    
    .metric-card:hover::before {
        left: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-8px) scale(1.02);
        border-color: rgba(0, 212, 255, 0.5);
        box-shadow: 0 20px 40px rgba(0, 212, 255, 0.2);
    }
    
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        animation: iconBounce 3s ease-in-out infinite;
    }
    
    @keyframes iconBounce {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 800;
        margin: 0.3rem 0;
        text-shadow: 0 0 30px currentColor;
    }
    
    .metric-label {
        color: #8B95A5;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    /* Live indicator */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        background: rgba(0, 200, 83, 0.15);
        border: 1px solid rgba(0, 200, 83, 0.4);
        padding: 0.5rem 1.2rem;
        border-radius: 30px;
        font-size: 0.9rem;
        color: #00C853;
        animation: livePulse 2s ease-in-out infinite;
    }
    
    .live-dot {
        width: 10px; height: 10px;
        background: #00C853;
        border-radius: 50%;
        animation: dotPulse 1.5s ease-in-out infinite;
    }
    
    @keyframes dotPulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.5); opacity: 0.5; }
    }
    
    @keyframes livePulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(0, 200, 83, 0.4); }
        50% { box-shadow: 0 0 0 10px rgba(0, 200, 83, 0); }
    }
    
    /* Section headers */
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #FAFAFA;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(0, 212, 255, 0.3), transparent);
    }
    
    /* Charts container */
    .chart-container {
        background: rgba(26, 31, 46, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .chart-container:hover {
        border-color: rgba(0, 212, 255, 0.2);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00D4FF 0%, #0099CC 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(0, 212, 255, 0.5);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(26, 31, 46, 0.5); }
    ::-webkit-scrollbar-thumb { 
        background: linear-gradient(135deg, #00D4FF, #8B5CF6); 
        border-radius: 4px; 
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 14, 23, 0.98) 0%, rgba(15, 20, 30, 0.98) 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)



# Import advanced UI components
from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title, metric_card
from ui.chat_interface import render_chat_interface

# Inject Advanced CSS & Particles
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()
render_chat_interface()

# Authentication removed - public dashboard

DATA_PATH = "data/parsed_logs/incident_responses.csv"
FULL_MODE = os.path.exists(DATA_PATH)

@st.cache_data(ttl=30)
def load_soc_data():
    if FULL_MODE:
        return pd.read_csv(DATA_PATH)
    else:
        # Dynamic Simulation enriched with Real OTX Data
        from services.threat_intel import get_latest_threats, get_threat_stats
        
        # 1. Fetch live intel
        real_countries = ["United States", "China", "Russia", "Germany", "Brazil", "India"] # Fallback
        real_ips = []
        try:
            pulses = get_latest_threats()
            for p in pulses:
                # Basic parsing of pulse description for country context
                desc = (p.get('name', '') + ' ' + p.get('description', '')).lower()
                for c_name in ["China", "Russia", "Iran", "Korea", "Vietnam", "India", "Brazil", "Ukraine", "France", "Germany", "Israel", "United States"]:
                    if c_name.lower() in desc:
                        real_countries.append(c_name)
        except:
            pass
            
        # Vary total events to make it look "live"
        base_n = 2000
        volatility = random.randint(-300, 500)
        n = base_n + volatility
        
        # Vary probabilities slightly for dynamic charts
        p_normal = max(0.4, 0.6 + random.uniform(-0.1, 0.05))
        remaining = 1.0 - p_normal
        other_p = np.random.dirichlet(np.ones(9)) * remaining
        
        probs = [p_normal] + list(other_p)
        
        base_time = datetime.now()
        timestamps = [base_time - timedelta(minutes=random.randint(1, 1440)) for _ in range(n)]
        timestamps.sort(reverse=True)
        
        attack_types = np.random.choice(
            ["Normal", "Port Scan", "DDoS", "Brute Force", "SQL Injection", "XSS", "Malware C2", "Data Exfil", "Privilege Esc", "Ransomware"],
            size=n, p=probs
        )
        risk_scores = []
        for attack in attack_types:
            noise = random.uniform(-5, 5)
            if attack == "Normal": risk_scores.append(max(0, np.random.normal(12, 6) + noise))
            elif attack in ["Port Scan", "Brute Force"]: risk_scores.append(np.random.normal(48, 12) + noise)
            elif attack in ["DDoS", "SQL Injection", "XSS"]: risk_scores.append(np.random.normal(68, 10) + noise)
            else: risk_scores.append(min(100, np.random.normal(88, 6) + noise))
            
        risk_scores = np.clip(risk_scores, 0, 100).round(2)
        decisions = ["BLOCK" if r >= 70 else "RESTRICT" if r >= 30 else "ALLOW" for r in risk_scores]
        
        # Use Real Countries if found
        uniq_countries = list(set(real_countries))
        if len(uniq_countries) < 5:
            uniq_countries = ["United States", "China", "Russia", "Germany", "Brazil", "India", "Ukraine", "Iran", "North Korea", "Netherlands"]
            
        # Shuffle countries bias
        country_p = np.random.dirichlet(np.ones(len(uniq_countries)))
        
        return pd.DataFrame({
            "timestamp": timestamps,
            "attack_type": attack_types,
            "risk_score": risk_scores,
            "access_decision": decisions,
            "source_country": np.random.choice(uniq_countries, size=n, p=country_p),
            "source_ip": [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}" for _ in range(n)],
            "dest_port": np.random.choice([22, 80, 443, 3389, 445, 8080, 3306, 21], size=n)
        })

df = load_soc_data()

# Alert service for critical events
try:
    from alerting.alert_service import trigger_alert, send_test_alert
    ALERTS_AVAILABLE = True
except:
    ALERTS_AVAILABLE = False

# Check for critical events and send alerts
if ALERTS_AVAILABLE:
    critical_events = df[df["risk_score"] >= 80]
    if len(critical_events) > 0 and 'last_alert_check' not in st.session_state:
        st.session_state.last_alert_check = True
        # Send alert for the most critical event
        worst_event = critical_events.iloc[0]
        alert_data = {
            "attack_type": worst_event.get("attack_type", "Unknown"),
            "risk_score": float(worst_event.get("risk_score", 0)),
            "source_ip": worst_event.get("source_ip", "Unknown"),
            "access_decision": worst_event.get("access_decision", "BLOCK"),
            "source_country": worst_event.get("source_country", "Unknown"),
            "dest_port": int(worst_event.get("dest_port", 0)),
            "timestamp": str(worst_event.get("timestamp", datetime.now()))
        }
        result = trigger_alert(alert_data)
        if result.get("telegram") or result.get("email"):
            st.toast("🚨 Critical alert sent!", icon="🔔")


# Premium Header
c_head, c_live = st.columns([3, 1])
with c_head:
    st.markdown(page_header("Security Operations Center", "Real-time threat monitoring and autonomous response"), unsafe_allow_html=True)

with c_live:
    st.markdown("""
        <div style="height: 100%; display: flex; align-items: center; justify-content: flex-end; padding-top: 1rem;">
            <div class="live-badge" style="padding: 0.8rem 1.5rem;">
                <span class="live-dot"></span>
                LIVE SYSTEM
            </div>
        </div>
    """, unsafe_allow_html=True)


# Calculate metrics
total = len(df)
blocked = (df["access_decision"] == "BLOCK").sum()
restricted = (df["access_decision"] == "RESTRICT").sum()
allowed = (df["access_decision"] == "ALLOW").sum()
avg_risk = df["risk_score"].mean()
critical = (df["risk_score"] >= 80).sum()

# Animated Metric Cards
m1, m2, m3, m4, m5, m6 = st.columns(6)

metrics_data = [
    (m1, total, "Total Events", "#00D4FF"),
    (m2, critical, "Critical", "#FF4444"),
    (m3, blocked, "Blocked", "#FF6B6B"),
    (m4, restricted, "Restricted", "#FF8C00"),
    (m5, allowed, "Allowed", "#00C853"),
    (m6, f"{avg_risk:.1f}", "Avg Risk", "#8B5CF6")
]

for col, value, label, color in metrics_data:
    with col:
        display_value = f"{value:,}" if isinstance(value, (int, np.integer)) else value

    with col:
        display_value = f"{value:,}" if isinstance(value, (int, np.integer)) else value
        
        # Determine color for metric card
        card_color = color
        if label == "Total Events": card_color = "#00f3ff"   # Neon Cyan
        elif label == "Critical": card_color = "#ff003c"     # Neon Red
        elif label == "Blocked": card_color = "#bc13fe"      # Neon Purple
        
        st.markdown(metric_card(display_value, label, card_color), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Charts
chart1, chart2 = st.columns(2)

with chart1:
    st.markdown(section_title("Threat Activity Timeline"), unsafe_allow_html=True)
    if hasattr(df["timestamp"].iloc[0], "hour"):
        df["hour"] = df["timestamp"].apply(lambda x: x.replace(minute=0, second=0, microsecond=0))
        hourly = df.groupby("hour").size().reset_index(name="count")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly["hour"], y=hourly["count"], 
            mode="lines+markers", fill="tozeroy",
            line=dict(color="#00D4FF", width=3, shape='spline'),
            marker=dict(size=8, color="#00D4FF", line=dict(width=2, color="#FFFFFF")),
            fillcolor="rgba(0, 212, 255, 0.15)"
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#FAFAFA",
            xaxis=dict(showgrid=False, showline=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", showline=False),
            margin=dict(l=20, r=20, t=20, b=20), height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Timeline data loading...")

with chart2:
    st.markdown(section_title("Decision Distribution"), unsafe_allow_html=True)
    decision_counts = df["access_decision"].value_counts()
    fig2 = go.Figure(data=[go.Pie(
        labels=decision_counts.index, values=decision_counts.values, hole=0.6,
        marker_colors=["#00C853", "#FF8C00", "#FF4444"],
        textinfo="percent", textfont_size=14, textfont_color="#FFFFFF"
    )])
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FAFAFA", showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1),
        margin=dict(l=20, r=20, t=20, b=60), height=300
    )
    st.plotly_chart(fig2, use_container_width=True)

chart3, chart4 = st.columns(2)

with chart3:
    st.markdown(section_title("Top Attack Types"), unsafe_allow_html=True)
    attack_counts = df[df["attack_type"] != "Normal"]["attack_type"].value_counts().head(6)
    fig3 = go.Figure(go.Bar(
        x=attack_counts.values, y=attack_counts.index, orientation="h",
        marker=dict(
            color=attack_counts.values,
            colorscale=[[0, "#00D4FF"], [0.5, "#8B5CF6"], [1, "#FF4444"]],
            line=dict(width=0)
        )
    ))
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FAFAFA",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(showgrid=False),
        margin=dict(l=20, r=20, t=20, b=20), height=280
    )
    st.plotly_chart(fig3, use_container_width=True)

with chart4:
    st.markdown(section_title("Attack Sources"), unsafe_allow_html=True)
    if "source_country" in df.columns:
        country_counts = df[df["attack_type"] != "Normal"]["source_country"].value_counts().head(6)
        fig4 = go.Figure(go.Bar(
            x=country_counts.index, y=country_counts.values,
            marker=dict(
                color=country_counts.values,
                colorscale=[[0, "#FF8C00"], [1, "#FF4444"]]
            )
        ))
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#FAFAFA",
            xaxis=dict(showgrid=False, tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            margin=dict(l=20, r=20, t=20, b=60), height=280
        )
        st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# Security Score Gauge
st.markdown(section_title("Security Health Score"), unsafe_allow_html=True)

gauge_col1, gauge_col2, gauge_col3 = st.columns([1, 2, 1])

with gauge_col2:
    security_score = max(0, 100 - avg_risk)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=security_score,
        title={'text': "Overall Security", 'font': {'size': 18, 'color': '#FAFAFA'}},
        number={'font': {'size': 48, 'color': '#00D4FF'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "#FAFAFA", 'tickwidth': 2},
            'bar': {'color': "#00D4FF", 'thickness': 0.3},
            'bgcolor': "rgba(26, 31, 46, 0.8)",
            'borderwidth': 2, 'bordercolor': "rgba(255, 255, 255, 0.1)",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.3)'},
                {'range': [40, 70], 'color': 'rgba(255, 140, 0, 0.3)'},
                {'range': [70, 100], 'color': 'rgba(0, 200, 83, 0.3)'}
            ],
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        font={'color': "#FAFAFA", 'family': "Inter"}, 
        height=280
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">AI-Driven Autonomous SOC | Zero Trust Security Platform</p></div>', unsafe_allow_html=True)
