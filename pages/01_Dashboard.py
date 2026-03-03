import streamlit as st
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Dashboard | SOC", page_icon="D", layout="wide")
except st.errors.StreamlitAPIError:
    pass

# --- Background service ---
try:
    from services.cloud_background import start_cloud_background_service
    start_cloud_background_service()
except Exception as e:
    print(f"Failed to start background service: {e}")

# ── Login warning ──
if st.session_state.get('login_warning'):
    sus = st.session_state.pop('login_warning')
    st.warning(
        f"⚠️ **Unusual Login Activity** (Risk: {sus.get('risk_score', 0)}/100)\n\n"
        + "\n".join(f"- {r}" for r in sus.get('reasons', []))
    )

# ═══════════════════════════════════════════════════════════════════════════════
# CLEAN PROFESSIONAL STYLES
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Dashboard KPI Cards */
.kpi-row { display: flex; gap: 12px; margin: 0.5rem 0 1.2rem 0; }
.kpi-card {
    flex: 1;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 1rem 0.8rem;
    text-align: center;
}
.kpi-val {
    font-family: 'Inter', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.3;
}
.kpi-lbl {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6B7280;
    margin-top: 2px;
}

/* Section headers */
.sec-hdr {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #9CA3AF;
    margin: 1.8rem 0 0.8rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

/* Header */
.dash-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #F9FAFB;
    margin: 0 0 0.15rem 0;
    letter-spacing: -0.01em;
}
.dash-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #6B7280;
    margin: 0;
}

/* Status badge */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.status-pill .pulse {
    width: 6px; height: 6px;
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 currentColor; }
    50% { opacity: 0.5; box-shadow: 0 0 0 4px transparent; }
}

/* RL Strip */
.rl-bar {
    background: rgba(99, 102, 241, 0.06);
    border: 1px solid rgba(99, 102, 241, 0.12);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    margin-bottom: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #818CF8;
}
.rl-bar .rl-v { font-weight: 700; font-family: 'Inter', sans-serif; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title, metric_card

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=5)
def load_soc_data():
    try:
        from services.siem_service import siem_service
        events = siem_service.generate_events(count=5000)
        if not events:
            return pd.DataFrame()

        data = []
        for e in events:
            sev = e.get('severity', 'LOW')
            risk_score = {"CRITICAL": 95, "HIGH": 75, "MEDIUM": 50, "LOW": 15}.get(sev, 10)
            msg = str(e.get('event_type', '')).upper()

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
                ts = datetime.strptime(e.get('timestamp'), "%Y-%m-%d %H:%M:%S")
            except Exception:
                ts = datetime.now()

            data.append({
                "timestamp": ts, "attack_type": attack_type,
                "risk_score": float(risk_score), "access_decision": decision,
                "source_country": e.get('source_country', "United States"),
                "source_ip": e.get('source_ip', '0.0.0.0'), "dest_port": port
            })
        return pd.DataFrame(data)
    except Exception as e:
        print(f"DASHBOARD RELOAD ERROR: {e}")
        return pd.DataFrame()

df = load_soc_data()

# Alert service
try:
    from alerting.alert_service import trigger_alert
    ALERTS_AVAILABLE = True
except Exception:
    ALERTS_AVAILABLE = False

if ALERTS_AVAILABLE and not df.empty and "risk_score" in df.columns:
    critical_events = df[df["risk_score"] >= 80]
    if len(critical_events) > 0 and 'last_alert_check' not in st.session_state:
        st.session_state.last_alert_check = True
        worst = critical_events.iloc[0]
        result = trigger_alert({
            "attack_type": worst.get("attack_type", "Unknown"),
            "risk_score": float(worst.get("risk_score", 0)),
            "source_ip": worst.get("source_ip", "Unknown"),
            "access_decision": worst.get("access_decision", "BLOCK"),
            "source_country": worst.get("source_country", "Unknown"),
            "dest_port": int(worst.get("dest_port", 0)),
            "timestamp": str(worst.get("timestamp", datetime.now()))
        })
        if result.get("telegram") or result.get("email"):
            st.toast("Critical alert dispatched", icon="🚨")


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS CALCULATION
# ═══════════════════════════════════════════════════════════════════════════════
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
            blocked = int((df["access_decision"] == "BLOCK").sum() * ratio)
            restricted = int((df["access_decision"] == "RESTRICT").sum() * ratio)
            allowed = int((df["access_decision"] == "ALLOW").sum() * ratio)
    else:
        total = len(df)
        blocked = int((df["access_decision"] == "BLOCK").sum()) if "access_decision" in df else 0
        restricted = int((df["access_decision"] == "RESTRICT").sum()) if "access_decision" in df else 0
        allowed = int((df["access_decision"] == "ALLOW").sum()) if "access_decision" in df else 0
        critical = int((df["risk_score"] >= 80).sum()) if "risk_score" in df else 0
except Exception:
    total = len(df) if isinstance(df, pd.DataFrame) else 0
    blocked = int((df["access_decision"] == "BLOCK").sum()) if isinstance(df, pd.DataFrame) and "access_decision" in df.columns else 0
    restricted = int((df["access_decision"] == "RESTRICT").sum()) if isinstance(df, pd.DataFrame) and "access_decision" in df.columns else 0
    allowed = int((df["access_decision"] == "ALLOW").sum()) if isinstance(df, pd.DataFrame) and "access_decision" in df.columns else 0
    critical = int((df["risk_score"] >= 80).sum()) if isinstance(df, pd.DataFrame) and "risk_score" in df.columns else 0

avg_risk = df["risk_score"].mean() if (isinstance(df, pd.DataFrame) and not df.empty and "risk_score" in df.columns) else 0
if blocked > total:
    total = blocked + restricted + allowed
security_score = max(0, min(100, 100 - avg_risk))


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown("""
<div style="padding: 0.3rem 0 0.8rem 0;">
    <h1 class="dash-title">Security Operations Center</h1>
    <p class="dash-sub">Autonomous threat detection & response platform</p>
</div>
    """, unsafe_allow_html=True)

with h2:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("""
<div style="display:flex; justify-content:flex-end; padding-top:1rem;">
    <span class="status-pill" style="background:rgba(16,185,129,0.1); color:#10B981; border:1px solid rgba(16,185,129,0.2);">
        <span class="pulse" style="background:#10B981;"></span>
        LIVE
    </span>
</div>
        """, unsafe_allow_html=True)
        auto_refresh = st.toggle("Auto-Sync", value=True)
    with c2:
        st.markdown("<div style='padding-top:1rem;'></div>", unsafe_allow_html=True)
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# RL INTELLIGENCE BAR
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from ml_engine.rl_threat_classifier import rl_classifier
    from ml_engine.rl_agents import get_all_agent_stats

    rl_stats = rl_classifier.get_stats()
    domain_stats = get_all_agent_stats()
    total_episodes = rl_stats.get("episodes", 0) + sum(s.get("episodes", 0) for s in domain_stats)
    rl_acc = rl_stats.get("current_accuracy", 0)
    n_agents = 1 + len(domain_stats)

    st.markdown(f"""
<div class="rl-bar">
    <span style="color:#6366F1;">● RL ENGINE</span>
    <span class="rl-v" style="color:#10B981;">{rl_acc}%</span> <span>accuracy</span>
    <span style="margin-left:auto;">{n_agents} agents</span>
    <span>·</span>
    <span class="rl-v" style="color:#E0E7FF;">{total_episodes:,}</span> <span>episodes</span>
    <span>·</span>
    <span>ε {rl_stats.get('epsilon', 0):.3f}</span>
</div>
    """, unsafe_allow_html=True)
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ═══════════════════════════════════════════════════════════════════════════════
def fmt(v):
    return f"{v:,}" if isinstance(v, (int, np.integer)) else v

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card"><div class="kpi-val" style="color:#E0E7FF;">{fmt(total)}</div><div class="kpi-lbl">Total Events</div></div>
    <div class="kpi-card" style="border-color:rgba(239,68,68,0.15);"><div class="kpi-val" style="color:#EF4444;">{fmt(critical)}</div><div class="kpi-lbl">Critical</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#A78BFA;">{fmt(blocked)}</div><div class="kpi-lbl">Blocked</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#F59E0B;">{fmt(restricted)}</div><div class="kpi-lbl">Restricted</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#10B981;">{fmt(allowed)}</div><div class="kpi-lbl">Allowed</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#8B5CF6;">{avg_risk:.1f}</div><div class="kpi-lbl">Avg Risk</div></div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL THREAT MAP
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">Global Threat Map</div>', unsafe_allow_html=True)

try:
    map_events = [e for e in db.get_recent_events(limit=200) if e.get("severity") in ["HIGH", "CRITICAL"]]
    if map_events:
        map_df = pd.DataFrame(map_events)
        np.random.seed(42)
        map_df['lat'] = np.random.uniform(-40, 60, len(map_df))
        map_df['lon'] = np.random.uniform(-120, 140, len(map_df))
        np.random.seed(None)

        risk_map = {"CRITICAL": 95, "HIGH": 75, "MEDIUM": 50, "LOW": 25}
        map_df['risk'] = map_df['severity'].map(risk_map).fillna(50)

        fig_map = go.Figure(go.Scattergeo(
            lon=map_df['lon'], lat=map_df['lat'],
            text=map_df['source_ip'] + " — " + map_df['event_type'],
            mode='markers',
            marker=dict(
                size=map_df['risk'] / 10,
                opacity=0.6,
                color=map_df['risk'],
                colorscale=[[0, "#6366F1"], [0.5, "#F59E0B"], [1, "#EF4444"]],
                cmin=20, cmax=100,
                colorbar=dict(
                    title=dict(text="Risk", font=dict(color="#6B7280", size=10)),
                    tickfont=dict(color="#6B7280", size=9),
                    thickness=10, len=0.4,
                ),
                line=dict(width=0),
            )))

        fig_map.update_layout(
            geo=dict(
                scope='world', projection_type='natural earth',
                showland=True, landcolor="rgb(17, 24, 39)",
                countrycolor="rgba(75, 85, 99, 0.3)",
                showocean=True, oceancolor="rgb(11, 15, 25)",
                bgcolor="rgba(0,0,0,0)", showframe=False,
                coastlinecolor="rgba(75, 85, 99, 0.2)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0), height=380
        )
        st.plotly_chart(fig_map, use_container_width=True)
except Exception as e:
    st.error(f"Map Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS ROW 1
# ═══════════════════════════════════════════════════════════════════════════════
chart1, chart2 = st.columns([2, 1])

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#9CA3AF", family="Inter"),
    margin=dict(l=10, r=10, t=10, b=10),
)

with chart1:
    st.markdown('<div class="sec-hdr">Threat Activity · 6 Months</div>', unsafe_allow_html=True)
    try:
        daily_counts = db.get_daily_counts(days=180)
        if daily_counts:
            df_t = pd.DataFrame(daily_counts)
            df_t['date'] = pd.to_datetime(df_t['date'])
            mn, mx = df_t['date'].min(), df_t['date'].max()
            if str(mn) != 'NaT':
                df_t = df_t.set_index('date').reindex(pd.date_range(mn, mx, freq='D'), fill_value=0).reset_index().rename(columns={'index': 'date'})

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_t["date"], y=df_t["count"],
                mode="lines", fill="tozeroy",
                line=dict(color="#6366F1", width=2, shape='spline'),
                fillcolor="rgba(99, 102, 241, 0.06)",
                hovertemplate="<b>%{x|%b %d}</b><br>%{y:,} events<extra></extra>",
                showlegend=False
            ))
            fig.update_layout(
                **CHART_LAYOUT, height=300, hovermode="x unified",
                xaxis=dict(showgrid=False, linecolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
            )
            selection = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")

            if selection and isinstance(selection, dict) and "selection" in selection:
                points = selection["selection"].get("points", [])
                if points:
                    try:
                        target_date = pd.to_datetime(points[0].get("x")).strftime('%Y-%m-%d')
                        st.markdown(f"**Events on {target_date}**")
                        rows = db._supabase.select("events", params={"timestamp": f"like.{target_date}%"}, limit=500, order="timestamp.desc")
                        if rows:
                            st.dataframe(pd.DataFrame(rows)[['timestamp', 'event_type', 'source_ip', 'severity', 'status']], use_container_width=True, hide_index=True)
                        else:
                            st.info("No records found for this date.")
                    except Exception as e:
                        st.error(f"Lookup error: {e}")
        else:
            st.info("No timeline data yet.")
    except Exception as e:
        st.error(f"Timeline error: {e}")

with chart2:
    st.markdown('<div class="sec-hdr">Decision Distribution</div>', unsafe_allow_html=True)
    if not df.empty and "access_decision" in df.columns:
        dc = df["access_decision"].value_counts()
        colors_map = {"ALLOW": "#10B981", "RESTRICT": "#F59E0B", "BLOCK": "#EF4444"}

        fig2 = go.Figure(go.Pie(
            labels=dc.index, values=dc.values, hole=0.6,
            marker_colors=[colors_map.get(d, "#6B7280") for d in dc.index],
            textinfo="percent", textfont=dict(size=12, color="#E5E7EB"),
            hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>"
        ))
        fig2.update_layout(
            **CHART_LAYOUT, height=300, showlegend=True,
            legend=dict(orientation="h", y=-0.12, font=dict(size=10, color="#9CA3AF")),
        )
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS ROW 2
# ═══════════════════════════════════════════════════════════════════════════════
chart3, chart4 = st.columns(2)

with chart3:
    st.markdown('<div class="sec-hdr">Top Attack Vectors</div>', unsafe_allow_html=True)
    if not df.empty:
        ac = df[df["attack_type"] != "Normal"]["attack_type"].value_counts().head(6)
        if not ac.empty:
            fig3 = go.Figure(go.Bar(
                x=ac.values, y=ac.index, orientation="h",
                marker=dict(color="#6366F1", line=dict(width=0)),
                hovertemplate="<b>%{y}</b>: %{x:,}<extra></extra>"
            ))
            fig3.update_layout(
                **CHART_LAYOUT, height=260,
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
                yaxis=dict(showgrid=False, tickfont=dict(size=11)),
            )
            st.plotly_chart(fig3, use_container_width=True)

with chart4:
    st.markdown('<div class="sec-hdr">Attack Origins</div>', unsafe_allow_html=True)
    if "source_country" in df.columns and not df.empty:
        cc = df[df["attack_type"] != "Normal"]["source_country"].value_counts().head(6)
        if not cc.empty:
            fig4 = go.Figure(go.Bar(
                x=cc.index, y=cc.values,
                marker=dict(color="#F59E0B", line=dict(width=0)),
                hovertemplate="<b>%{x}</b>: %{y:,}<extra></extra>"
            ))
            fig4.update_layout(
                **CHART_LAYOUT, height=260,
                xaxis=dict(showgrid=False, tickangle=-25, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
            )
            st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY SCORE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">Security Health</div>', unsafe_allow_html=True)

_, gc, _ = st.columns([1, 2, 1])
with gc:
    if security_score >= 70:
        g_color = "#10B981"
    elif security_score >= 40:
        g_color = "#F59E0B"
    else:
        g_color = "#EF4444"

    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=security_score,
        number={'font': {'size': 44, 'color': g_color, 'family': 'Inter'}, 'suffix': ''},
        title={'text': "Overall Score", 'font': {'size': 13, 'color': '#6B7280', 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "#374151", 'tickwidth': 1, 'tickfont': {'size': 9, 'color': '#6B7280'}},
            'bar': {'color': g_color, 'thickness': 0.2},
            'bgcolor': "rgba(31, 41, 55, 0.4)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': 'rgba(239,68,68,0.06)'},
                {'range': [40, 70], 'color': 'rgba(245,158,11,0.06)'},
                {'range': [70, 100], 'color': 'rgba(16,185,129,0.06)'}
            ],
        }
    ))
    fig_g.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "#E5E7EB", 'family': "Inter"},
        height=230, margin=dict(l=30, r=30, t=30, b=0)
    )
    st.plotly_chart(fig_g, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#4B5563; padding:0.3rem; font-family:'Inter',sans-serif; font-size:0.75rem; letter-spacing:0.04em;">
    AI-Driven Autonomous SOC · Zero Trust · RL-Powered Intelligence
</div>
""", unsafe_allow_html=True)

try:
    from ui.chat_interface import inject_floating_cortex_link
    inject_floating_cortex_link()
except Exception:
    pass

if auto_refresh:
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
