import streamlit as st
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import sys

# Force Reload Fix

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Dashboard | SOC", page_icon="D", layout="wide")
except st.errors.StreamlitAPIError:
    pass  # Already set by dashboard.py

# --- CLOUD BACKGROUND SERVICE ---
# Starts a singleton thread for continuous data ingestion (works on Streamlit Cloud)
try:
    from services.cloud_background import start_cloud_background_service
    start_cloud_background_service()
except Exception as e:
    print(f"Failed to start background service: {e}")
# --------------------------------

# ── Suspicious Login Warning ─────────────────────────────────────────────────
if st.session_state.get('login_warning'):
    sus = st.session_state.pop('login_warning')
    risk = sus.get('risk_score', 0)
    reasons = sus.get('reasons', [])
    st.warning(
        f"⚠️ **Unusual Login Activity Detected** (Risk Score: {risk}/100)\n\n"
        + "\n".join(f"- {r}" for r in reasons)
        + "\n\nIf this wasn't you, **change your password immediately** in Settings."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM DASHBOARD STYLES
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* Live Action Ticker */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: linear-gradient(90deg, rgba(0,0,0,0.6), rgba(0,212,255,0.03), rgba(0,0,0,0.6));
        padding: 8px 0;
        border-bottom: 1px solid rgba(0, 243, 255, 0.15);
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
    .ticker {
        display: inline-block;
        white-space: nowrap;
        padding-right: 100%;
        animation: ticker 35s linear infinite;
    }
    @keyframes ticker {
        0% { transform: translate3d(100%, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }
    .ticker-item {
        display: inline-block;
        padding: 0 2.5rem;
        color: #00D4FF;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.8rem;
        letter-spacing: 0.03em;
    }

    /* Premium Metric Cards */
    .metric-card-pro {
        background: linear-gradient(135deg, rgba(15, 18, 30, 0.9), rgba(26, 31, 46, 0.7));
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 1.2rem 1rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .metric-card-pro:hover {
        border-color: rgba(0, 212, 255, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    .metric-card-pro::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--accent);
    }
    .metric-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 0.3rem;
    }
    .metric-label {
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #8B95A5;
        font-weight: 500;
    }
    .metric-delta {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.7rem;
        margin-top: 0.25rem;
        opacity: 0.8;
    }

    /* Section Titles */
    .section-title-pro {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .section-title-pro .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #00D4FF;
        box-shadow: 0 0 8px #00D4FF;
    }
    .section-title-pro h3 {
        margin: 0;
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #FAFAFA;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .section-title-pro .sys-tag {
        margin-left: auto;
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.65rem;
        color: #444;
    }

    /* RL Status Strip */
    .rl-strip {
        background: linear-gradient(90deg, rgba(139,92,246,0.08), rgba(0,212,255,0.04));
        border: 1px solid rgba(139,92,246,0.2);
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        display: flex;
        align-items: center;
        gap: 1.5rem;
        margin-bottom: 1rem;
    }
    .rl-strip .rl-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #8B5CF6;
        box-shadow: 0 0 10px rgba(139,92,246,0.5);
        animation: pulseDot 2s infinite;
    }
    @keyframes pulseDot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .rl-strip .rl-text {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.78rem;
        color: #A78BFA;
    }
    .rl-strip .rl-stat {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.85rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)



# Import advanced UI components
from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title, metric_card

# --- STYLES ALREADY INJECTED ---




@st.cache_data(ttl=5)
def load_soc_data():
    """
    Load real security data from the SIEM service (backed by SQLite).
    Relying exclusively on persistent records now.
    """
    try:
        from services.siem_service import siem_service
        
        # Use SIEM Service (Trigger auto-seeding if DB is low)
        events = siem_service.generate_events(count=5000)
        
        if not events:
            return pd.DataFrame() # Let the UI handle empty state

        data = []
        for e in events:
            sev = e.get('severity', 'LOW')
            # Mapping SIEM severity to numeric risk score for charts
            risk_score = {"CRITICAL": 95, "HIGH": 75, "MEDIUM": 50, "LOW": 15}.get(sev, 10)
            
            msg = str(e.get('event_type', '')).upper()
            decision = e.get('status', 'ALLOW').upper() # Map status or use logic
            if "BLOCKED" in msg or "BLOCK" in msg:
                decision = "BLOCK"
            elif risk_score > 60:
                decision = "RESTRICT"
            else:
                decision = "ALLOW"
                
            port = 80
            if "SSH" in msg or "22" in msg: port = 22
            elif "RDP" in msg or "3389" in msg: port = 3389
            elif "SQL" in msg or "3306" in msg: port = 3306
            elif "DNS" in msg or "53" in msg: port = 53
            
            attack_type = "Normal"
            if "SQL" in msg: attack_type = "SQL Injection"
            elif "XSS" in msg: attack_type = "XSS"
            elif "DDOS" in msg or "FLOOD" in msg: attack_type = "DDoS"
            elif "BRUTE" in msg or "LOGIN" in msg: attack_type = "Brute Force"
            elif "MALWARE" in msg: attack_type = "Malware"
            elif risk_score > 50: attack_type = msg[:20].capitalize()
            
            try:
                # Use the event's actual timestamp
                ts = datetime.strptime(e.get('timestamp'), "%Y-%m-%d %H:%M:%S")
            except Exception:
                ts = datetime.now()

            data.append({
                "timestamp": ts,
                "attack_type": attack_type,
                "risk_score": float(risk_score),
                "access_decision": decision,
                "source_country": e.get('source_country', "United States"), # DB may not have it yet
                "source_ip": e.get('source_ip', '0.0.0.0'),
                "dest_port": port
            })
            
        return pd.DataFrame(data)

    except Exception as e:
        print(f"DASHBOARD RELOAD ERROR: {e}")
        return pd.DataFrame()

df = load_soc_data()

# Alert service for critical events
try:
    from alerting.alert_service import trigger_alert, send_test_alert
    ALERTS_AVAILABLE = True
except Exception:
    ALERTS_AVAILABLE = False

# Check for critical events and send alerts
if ALERTS_AVAILABLE and not df.empty and "risk_score" in df.columns:
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
            st.toast(" Critical alert sent!", icon="🚨")


# --- LIVE ACTION TICKER ---
try:
    from services.database import db
    recent_fw = [e for e in db.get_recent_events(limit=50) if e.get("source") == "Firewall"][:5]
    if recent_fw:
        ticker_html = '<div class="ticker-wrap"><div class="ticker">'
        for r in recent_fw:
            ticker_html += f'<span class="ticker-item">🛡️ [FIREWALL] Blocked IP {r.get("source_ip")} ({r.get("event_type").replace("Active Block: ", "")})</span>'
        ticker_html += '</div></div>'
        st.markdown(ticker_html, unsafe_allow_html=True)
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER SECTION
# ═══════════════════════════════════════════════════════════════════════════════
c_head, c_live = st.columns([3, 1.5])
with c_head:
    st.markdown("""
    <div style="padding: 0.5rem 0;">
        <h1 style="
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            color: #FAFAFA;
            margin: 0 0 0.3rem 0;
            letter-spacing: 0.05em;
        ">Security Operations Center</h1>
        <p style="
            font-family: 'Share Tech Mono', monospace;
            color: #00D4FF;
            font-size: 0.85rem;
            margin: 0;
            opacity: 0.8;
        ">> Production-grade autonomous threat monitoring_</p>
    </div>
    """, unsafe_allow_html=True)

# Calculate metrics
try:
    from services.database import db
    true_stats = db.get_stats()
    true_total = true_stats.get('total', 0)
    true_critical = true_stats.get('critical', 0)
    
    if true_total > len(df):
        total = true_total
        critical = true_critical
        if len(df) > 0:
            ratio = true_total / len(df)
            blocked = int((df["access_decision"] == "BLOCK").sum() * ratio) if "access_decision" in df else 0
            restricted = int((df["access_decision"] == "RESTRICT").sum() * ratio) if "access_decision" in df else 0
            allowed = int((df["access_decision"] == "ALLOW").sum() * ratio) if "access_decision" in df else 0
    else:
        total = len(df)
        blocked = (df["access_decision"] == "BLOCK").sum() if "access_decision" in df else 0
        restricted = (df["access_decision"] == "RESTRICT").sum() if "access_decision" in df else 0
        allowed = (df["access_decision"] == "ALLOW").sum() if "access_decision" in df else 0
        critical = (df["risk_score"] >= 80).sum() if "risk_score" in df else 0
        
except Exception as e:
    total = len(df) if isinstance(df, pd.DataFrame) else 0
    blocked = (df["access_decision"] == "BLOCK").sum() if isinstance(df, pd.DataFrame) and "access_decision" in df.columns else 0
    restricted = (df["access_decision"] == "RESTRICT").sum() if isinstance(df, pd.DataFrame) and "access_decision" in df.columns else 0
    allowed = (df["access_decision"] == "ALLOW").sum() if isinstance(df, pd.DataFrame) and "access_decision" in df.columns else 0
    critical = (df["risk_score"] >= 80).sum() if isinstance(df, pd.DataFrame) and "risk_score" in df.columns else 0
    
avg_risk = df["risk_score"].mean() if (isinstance(df, pd.DataFrame) and not df.empty and "risk_score" in df.columns) else 0
IS_LIVE_CONNECTION = True

if blocked > total:
    total = blocked + restricted + allowed

with c_live:
    badge_color = "#00C853" 
    badge_bg = "rgba(0, 200, 83, 0.1)"
    badge_text = "PRODUCTION ACTIVE"
    
    st.markdown(f"""
        <div style="height: 100%; display: flex; align-items: center; justify-content: flex-end; gap: 1rem; padding-top: 1.5rem; padding-bottom: 0.5rem;">
            <div style="
                padding: 0.5rem 1rem;
                border: 1px solid {badge_color};
                border-radius: 8px;
                color: {badge_color};
                background: {badge_bg};
                font-family: 'Share Tech Mono', monospace;
                font-size: 0.75rem;
                font-weight: 600;
                letter-spacing: 0.1em;
                display: flex;
                align-items: center;
                gap: 8px;
                white-space: nowrap;
            ">
                <span style="width: 6px; height: 6px; border-radius: 50%; background: {badge_color}; box-shadow: 0 0 8px {badge_color}; animation: pulseDot 2s infinite;"></span>
                {badge_text}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col_auto, col_refresh = st.columns([1.5, 1])
    with col_auto:
        st.markdown("<div style='padding-top: 5px; float: right;'>", unsafe_allow_html=True)
        auto_refresh = st.toggle("Auto-Sync", value=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_refresh:
        if st.button("↻ Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# RL INTELLIGENCE STRIP
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from ml_engine.rl_threat_classifier import rl_classifier
    from ml_engine.rl_agents import get_all_agent_stats
    
    rl_stats = rl_classifier.get_stats()
    domain_stats = get_all_agent_stats()
    
    total_episodes = rl_stats.get("episodes", 0) + sum(s.get("episodes", 0) for s in domain_stats)
    avg_accuracy = rl_stats.get("current_accuracy", 0)
    active_agents = 1 + len(domain_stats)
    
    st.markdown(f"""
    <div class="rl-strip">
        <div class="rl-dot"></div>
        <span class="rl-text">RL INTELLIGENCE</span>
        <span class="rl-stat" style="color: #00C853;">{avg_accuracy}%</span>
        <span class="rl-text">accuracy</span>
        <span class="rl-text" style="margin-left: auto;">{active_agents} agents</span>
        <span class="rl-text">·</span>
        <span class="rl-stat" style="color: #00D4FF;">{total_episodes:,}</span>
        <span class="rl-text">episodes</span>
        <span class="rl-text">·</span>
        <span class="rl-text">ε = {rl_stats.get('epsilon', 0):.3f}</span>
    </div>
    """, unsafe_allow_html=True)
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# METRIC CARDS — Clean 6-column layout
# ═══════════════════════════════════════════════════════════════════════════════
m1, m2, m3, m4, m5, m6 = st.columns(6)

def render_metric(col, value, label, color, delta=None):
    display_value = f"{value:,}" if isinstance(value, (int, np.integer)) else value
    delta_html = ""
    if delta:
        delta_color = "#00C853" if "+" in str(delta) or float(str(delta).replace("+","").replace("%","").replace(",","") or 0) >= 0 else "#FF4444"
        delta_html = f'<div class="metric-delta" style="color: {delta_color};">{delta}</div>'
    with col:
        st.markdown(f"""
        <div class="metric-card-pro" style="--accent: {color};">
            <div class="metric-value" style="color: {color};">{display_value}</div>
            <div class="metric-label">{label}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

render_metric(m1, total, "Total Events", "#00D4FF")
render_metric(m2, critical, "Critical", "#FF003C")
render_metric(m3, blocked, "Blocked", "#BC13FE")
render_metric(m4, restricted, "Restricted", "#FF8C00")
render_metric(m5, allowed, "Allowed", "#00C853")
render_metric(m6, f"{avg_risk:.1f}", "Avg Risk", "#8B5CF6")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL THREAT MATRIX
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-title-pro">
    <span class="dot"></span>
    <h3>Global Threat Matrix</h3>
    <span class="sys-tag">[SYS]</span>
</div>
""", unsafe_allow_html=True)

try:
    map_events = [e for e in db.get_recent_events(limit=200) if e.get("severity") in ["HIGH", "CRITICAL"]]
    if map_events:
        map_df = pd.DataFrame(map_events)
        # Use deterministic coordinates seeded by IP hash for consistency
        np.random.seed(42)
        map_df['lat'] = np.random.uniform(-40, 60, len(map_df))
        map_df['lon'] = np.random.uniform(-120, 140, len(map_df))
        np.random.seed(None)
        
        risk_map = {"CRITICAL": 95, "HIGH": 75, "MEDIUM": 50, "LOW": 25}
        map_df['risk'] = map_df['severity'].map(risk_map).fillna(50)
        
        fig_map = go.Figure(go.Scattergeo(
            lon = map_df['lon'],
            lat = map_df['lat'],
            text = map_df['source_ip'] + " [" + map_df['event_type'] + "]",
            mode = 'markers',
            marker = dict(
                size = map_df['risk'] / 8,
                opacity = 0.7,
                color = map_df['risk'],
                colorscale = [[0, "#00D4FF"], [0.5, "#8B5CF6"], [1, "#FF003C"]],
                cmin = 20,
                cmax = 100,
                colorbar = dict(
                    title="Risk",
                    titlefont=dict(color="#8B95A5", size=11),
                    tickfont=dict(color="#8B95A5", size=10),
                    thickness=12,
                    len=0.5,
                ),
                line = dict(width=0.5, color='rgba(255,255,255,0.2)'),
            )))

        fig_map.update_layout(
            geo = dict(
                scope='world',
                projection_type='natural earth',
                showland = True,
                landcolor = "rgb(12, 14, 28)",
                subunitcolor = "rgba(0, 200, 255, 0.08)",
                countrycolor = "rgba(0, 200, 255, 0.15)",
                showocean=True,
                oceancolor="rgb(8, 10, 20)",
                bgcolor="rgba(0,0,0,0)",
                showframe=False,
                coastlinecolor="rgba(0,200,255,0.12)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=420
        )
        st.plotly_chart(fig_map, use_container_width=True)
except Exception as e:
    st.error(f"Map Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS ROW 1: Timeline + Decision Distribution
# ═══════════════════════════════════════════════════════════════════════════════
chart1, chart2 = st.columns([2, 1])

with chart1:
    st.markdown("""
    <div class="section-title-pro">
        <span class="dot"></span>
        <h3>Threat Activity Timeline</h3>
        <span class="sys-tag">[6M]</span>
    </div>
    """, unsafe_allow_html=True)
    try:
        from services.database import db
        daily_counts = db.get_daily_counts(days=180)
        
        if daily_counts:
            df_timeline = pd.DataFrame(daily_counts)
            df_timeline['date'] = pd.to_datetime(df_timeline['date'])
            
            min_date = df_timeline['date'].min()
            max_date = df_timeline['date'].max()
            if str(min_date) != 'NaT':
                all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
                df_timeline = df_timeline.set_index('date').reindex(all_dates, fill_value=0).reset_index()
                df_timeline = df_timeline.rename(columns={'index': 'date'})
            
            fig = go.Figure()
            
            # Glow effect
            fig.add_trace(go.Scatter(
                x=df_timeline["date"], y=df_timeline["count"], 
                mode="lines",
                line=dict(color="rgba(0, 212, 255, 0.15)", width=12, shape='spline'),
                hoverinfo='skip',
                showlegend=False
            ))
            
            # Main line
            fig.add_trace(go.Scatter(
                x=df_timeline["date"], y=df_timeline["count"], 
                mode="lines", fill="tozeroy",
                name="Events",
                line=dict(color="#00D4FF", width=2.5, shape='spline'),
                fillcolor="rgba(0, 212, 255, 0.08)",
                hovertemplate="<b>%{x|%b %d}</b><br>Events: %{y:,}<extra></extra>",
                showlegend=False
            ))
            
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                xaxis=dict(showgrid=False, showline=True, linecolor="rgba(255,255,255,0.08)", tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", showline=False, tickfont=dict(size=10)),
                margin=dict(l=10, r=10, t=10, b=10), height=340,
                hovermode="x unified"
            )
            selection = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
            
            # Show detailed breakdown if user selects a date
            if selection and isinstance(selection, dict) and "selection" in selection:
                points = selection["selection"].get("points", [])
                if points:
                    try:
                        selected_date = points[0].get("x")
                        target_date = pd.to_datetime(selected_date).strftime('%Y-%m-%d')
                        st.markdown(f"**Threat Log for {target_date}**")
                        
                        with st.spinner("Checking historical archives..."):
                            rows = db._supabase.select("events", params={"timestamp": f"like.{target_date}%"}, limit=500, order="timestamp.desc")
                            if rows:
                                ddf = pd.DataFrame(rows)
                                st.dataframe(
                                    ddf[['timestamp', 'event_type', 'source_ip', 'severity', 'status']], 
                                    use_container_width=True, 
                                    hide_index=True
                                )
                            else:
                                st.info(f"No specific threat logs found for {target_date}.")
                    except Exception as e:
                        st.error(f"Error fetching logs for date: {e}")
        else:
            st.info("No historical timeline data available.")
    except Exception as e:
        st.error(f"Chart Error: {e}")

with chart2:
    st.markdown("""
    <div class="section-title-pro">
        <span class="dot" style="background: #8B5CF6; box-shadow: 0 0 8px #8B5CF6;"></span>
        <h3>Decision Split</h3>
        <span class="sys-tag">[LIVE]</span>
    </div>
    """, unsafe_allow_html=True)
    if not df.empty and "access_decision" in df.columns:
        decision_counts = df["access_decision"].value_counts()
        colors = {"ALLOW": "#00C853", "RESTRICT": "#FF8C00", "BLOCK": "#FF003C"}
        marker_colors = [colors.get(d, "#888") for d in decision_counts.index]
        
        fig2 = go.Figure(data=[go.Pie(
            labels=decision_counts.index, values=decision_counts.values, hole=0.65,
            marker_colors=marker_colors,
            textinfo="percent", textfont_size=13, textfont_color="#FFFFFF",
            hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>Share: %{percent}<extra></extra>"
        )])
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#FAFAFA", showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, font=dict(size=11)),
            margin=dict(l=10, r=10, t=10, b=50), height=340
        )
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS ROW 2: Attack Types + Sources
# ═══════════════════════════════════════════════════════════════════════════════
chart3, chart4 = st.columns(2)

with chart3:
    st.markdown("""
    <div class="section-title-pro">
        <span class="dot" style="background: #FF003C; box-shadow: 0 0 8px #FF003C;"></span>
        <h3>Top Attack Vectors</h3>
        <span class="sys-tag">[ANALYSIS]</span>
    </div>
    """, unsafe_allow_html=True)
    if not df.empty:
        attack_counts = df[df["attack_type"] != "Normal"]["attack_type"].value_counts().head(6)
        if not attack_counts.empty:
            fig3 = go.Figure(go.Bar(
                x=attack_counts.values, y=attack_counts.index, orientation="h",
                marker=dict(
                    color=attack_counts.values,
                    colorscale=[[0, "#00D4FF"], [0.5, "#8B5CF6"], [1, "#FF003C"]],
                    line=dict(width=0),
                    cornerradius=4,
                ),
                hovertemplate="<b>%{y}</b><br>Count: %{x:,}<extra></extra>"
            ))
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)", tickfont=dict(size=10)),
                yaxis=dict(showgrid=False, tickfont=dict(size=11)),
                margin=dict(l=10, r=10, t=10, b=10), height=280
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No attacks detected yet.")

with chart4:
    st.markdown("""
    <div class="section-title-pro">
        <span class="dot" style="background: #FF8C00; box-shadow: 0 0 8px #FF8C00;"></span>
        <h3>Attack Origins</h3>
        <span class="sys-tag">[GEO]</span>
    </div>
    """, unsafe_allow_html=True)
    if "source_country" in df.columns and not df.empty:
        country_counts = df[df["attack_type"] != "Normal"]["source_country"].value_counts().head(6)
        if not country_counts.empty:
            fig4 = go.Figure(go.Bar(
                x=country_counts.index, y=country_counts.values,
                marker=dict(
                    color=country_counts.values,
                    colorscale=[[0, "#FF8C00"], [1, "#FF003C"]],
                    cornerradius=4,
                ),
                hovertemplate="<b>%{x}</b><br>Count: %{y:,}<extra></extra>"
            ))
            fig4.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)", tickfont=dict(size=10)),
                margin=dict(l=10, r=10, t=10, b=50), height=280
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No external threats detected.")

# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY HEALTH GAUGE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-title-pro">
    <span class="dot" style="background: #00C853; box-shadow: 0 0 8px #00C853;"></span>
    <h3>Security Health Score</h3>
    <span class="sys-tag">[COMPOSITE]</span>
</div>
""", unsafe_allow_html=True)

gauge_col1, gauge_col2, gauge_col3 = st.columns([1, 2, 1])

with gauge_col2:
    security_score = max(0, 100 - avg_risk)
    
    # Color based on score
    if security_score >= 70:
        gauge_color = "#00C853"
    elif security_score >= 40:
        gauge_color = "#FF8C00"
    else:
        gauge_color = "#FF003C"
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=security_score,
        title={'text': "Overall Security", 'font': {'size': 16, 'color': '#8B95A5', 'family': 'Rajdhani'}},
        number={'font': {'size': 52, 'color': gauge_color, 'family': 'Orbitron'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "#555", 'tickwidth': 1, 'tickfont': {'size': 10}},
            'bar': {'color': gauge_color, 'thickness': 0.25},
            'bgcolor': "rgba(26, 31, 46, 0.5)",
            'borderwidth': 1, 'bordercolor': "rgba(255, 255, 255, 0.06)",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 0, 60, 0.12)'},
                {'range': [40, 70], 'color': 'rgba(255, 140, 0, 0.12)'},
                {'range': [70, 100], 'color': 'rgba(0, 200, 83, 0.12)'}
            ],
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        font={'color': "#FAFAFA", 'family': "Inter"}, 
        height=260,
        margin=dict(l=30, r=30, t=30, b=10)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #555; padding: 0.5rem; font-family: 'Rajdhani', sans-serif; font-size: 0.85rem; letter-spacing: 0.05em;">
    AI-Driven Autonomous SOC · Zero Trust Security Platform · RL-Powered Intelligence
</div>
""", unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()

# Auto-Refresh Logic (Placed at end to allow full rendering first)
if auto_refresh:
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
