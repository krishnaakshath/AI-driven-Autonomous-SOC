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
# IMPORT THEME (same cyberpunk as all other pages)
# ═══════════════════════════════════════════════════════════════════════════════
from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title, metric_card, COLORS, MOBILE_CSS, empty_state
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# Extra spacing overrides for dashboard only
st.markdown("""
<style>
/* Spacious override for dashboard */
.stColumns { gap: 1.5rem !important; }
section[data-testid="stSidebar"] + div .block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
}

/* RL Bar */
.rl-bar {
    background: linear-gradient(90deg, rgba(139,92,246,0.06), rgba(0,212,255,0.03));
    border: 1px solid rgba(139,92,246,0.15);
    border-radius: 8px;
    padding: 0.7rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    margin: 1rem 0 1.5rem 0;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: #A78BFA;
}
.rl-bar .rl-val {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
}

/* More breathing room between sections */
.section-gap { height: 2rem; }

/* Buttons & toggles more spacious */
.stButton > button {
    padding: 0.6rem 1.5rem !important;
    font-size: 0.85rem !important;
    border-radius: 6px !important;
    margin-top: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)


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

# Calculate Probabilistic Security Score
try:
    from services.statistical_engine import statistical_engine
    # Convert dataframe back to dict list for the engine
    if not df.empty:
        events_list = df.to_dict('records')
        alerts_list = [{"severity": "CRITICAL"} for _ in range(critical)]
        security_score = statistical_engine.calculate_probabilistic_risk_score(events_list, alerts_list)
    else:
        security_score = 100.0
except Exception as e:
    print(f"Stats Engine Error: {e}")
    security_score = max(0, min(100, 100 - avg_risk))


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER — uses same page_header as other pages
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(page_header("Security Operations Center", "Autonomous threat detection & response platform"), unsafe_allow_html=True)

# Status + Controls — spread out
st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
h_col1, h_col2, h_col3 = st.columns([2, 1, 1])
with h_col1:
    st.markdown("""
<div style="display:inline-flex; align-items:center; gap:6px; padding:6px 16px; border-radius:20px;
     background:rgba(0,200,83,0.08); border:1px solid rgba(0,200,83,0.2);
     color:#00C853; font-family:'Share Tech Mono',monospace; font-size:0.75rem; font-weight:600; letter-spacing:0.06em;">
    <span style="width:6px;height:6px;border-radius:50%;background:#00C853;box-shadow:0 0 6px #00C853;display:inline-block;"></span>
    PRODUCTION LIVE
</div>
    """, unsafe_allow_html=True)
with h_col2:
    auto_refresh = st.toggle("Auto-Sync", value=True)
with h_col3:
    if st.button("Refresh Data", use_container_width=True):
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
    <span style="color:#8B5CF6;">● RL ENGINE</span>
    <span class="rl-val" style="color:#00C853;">{rl_acc}%</span> <span>accuracy</span>
    <span style="margin-left:auto;">{n_agents} agents</span>
    <span>·</span>
    <span class="rl-val" style="color:#00f3ff;">{total_episodes:,}</span> <span>episodes</span>
    <span>·</span>
    <span>ε = {rl_stats.get('epsilon', 0):.3f}</span>
</div>
    """, unsafe_allow_html=True)
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# KPI CARDS — using theme's metric_card (same as other pages)
# ═══════════════════════════════════════════════════════════════════════════════
def fmt(v):
    return f"{v:,}" if isinstance(v, (int, np.integer)) else v

m1, m2, m3, m4, m5, m6 = st.columns(6)
with m1:
    st.markdown(metric_card("Total Events", fmt(total), "#00f3ff"), unsafe_allow_html=True)
with m2:
    st.markdown(metric_card("Critical", fmt(critical), "#ff003c"), unsafe_allow_html=True)
with m3:
    st.markdown(metric_card("Blocked", fmt(blocked), "#bc13fe"), unsafe_allow_html=True)
with m4:
    st.markdown(metric_card("Restricted", fmt(restricted), "#ff6b00"), unsafe_allow_html=True)
with m5:
    st.markdown(metric_card("Allowed", fmt(allowed), "#00C853"), unsafe_allow_html=True)
with m6:
    st.markdown(metric_card("Avg Risk", f"{avg_risk:.1f}", "#8B5CF6"), unsafe_allow_html=True)

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL THREAT MAP
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(section_title("Global Threat Map"), unsafe_allow_html=True)

try:
    map_events = [e for e in db.get_recent_events(limit=200) if e.get("severity") in ["HIGH", "CRITICAL"]]
    if map_events:
        map_df = pd.DataFrame(map_events)

        # Deterministic geo-mapping: hash each IP to consistent lat/lon
        import hashlib
        def ip_to_coords(ip):
            h = int(hashlib.md5(str(ip).encode()).hexdigest(), 16)
            lat = (h % 10000) / 10000 * 120 - 50   # Range: -50 to 70
            lon = ((h >> 16) % 10000) / 10000 * 300 - 140  # Range: -140 to 160
            return lat, lon

        coords = map_df['source_ip'].apply(lambda ip: ip_to_coords(ip))
        map_df['lat'] = [c[0] for c in coords]
        map_df['lon'] = [c[1] for c in coords]

        risk_map = {"CRITICAL": 95, "HIGH": 75, "MEDIUM": 50, "LOW": 25}
        map_df['risk'] = map_df['severity'].map(risk_map).fillna(50)

        fig_map = go.Figure(go.Scattergeo(
            lon=map_df['lon'], lat=map_df['lat'],
            text=map_df['source_ip'] + " — " + map_df['event_type'],
            mode='markers',
            marker=dict(
                size=map_df['risk'] / 10, opacity=0.6,
                color=map_df['risk'],
                colorscale=[[0, "#00f3ff"], [0.5, "#bc13fe"], [1, "#ff003c"]],
                cmin=20, cmax=100,
                colorbar=dict(
                    title=dict(text="Risk", font=dict(color="#8B95A5", size=10)),
                    tickfont=dict(color="#8B95A5", size=9),
                    thickness=10, len=0.4,
                ),
                line=dict(width=0),
            )))

        fig_map.update_layout(
            geo=dict(
                scope='world', projection_type='natural earth',
                showland=True, landcolor="rgb(12, 14, 28)",
                countrycolor="rgba(0, 200, 255, 0.12)",
                showocean=True, oceancolor="rgb(8, 10, 20)",
                bgcolor="rgba(0,0,0,0)", showframe=False,
                coastlinecolor="rgba(0,200,255,0.08)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0), height=380
        )
        st.plotly_chart(fig_map, use_container_width=True)
except Exception as e:
    st.error(f"Map Error: {e}")

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PROBABILISTIC THREAT FORECAST MATRIX
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(section_title("Threat Forecast Matrix (7-Day Outlook)"), unsafe_allow_html=True)

try:
    from services.statistical_engine import statistical_engine
    if not df.empty:
        # Generate live forecasts based on current events dataframe
        forecasts = statistical_engine.forecast_threats(df.to_dict('records'), days_ahead=7)
        if forecasts:
            st.markdown("""
            <div style="background: rgba(0,243,255,0.05); border-left: 3px solid #8B5CF6; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem;">
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">
                    <strong>Markov-Poisson Probability Engine:</strong> Live mathematical forecasts of incoming attacks based on current network momentum.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            f_cols = st.columns(len(forecasts[:4])) # Show top 4
            for i, col in enumerate(f_cols):
                f = forecasts[i]
                r_color = "#ff003c" if f["risk_level"] == "High" else "#FF8C00" if f["risk_level"] == "Medium" else "#00C853"
                
                col.markdown(f"""
                <div style="background: rgba(0,0,0,0.4); border: 1px solid rgba(139,92,246,0.2); border-radius: 12px; padding: 1.2rem; text-align: center;">
                    <h5 style="color: #FAFAFA; margin: 0 0 0.5rem 0; font-size: 1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{f['threat_type']}</h5>
                    <div style="font-family: 'Orbitron', sans-serif; font-size: 2rem; font-weight: 700; color: {r_color}; margin: 0.5rem 0;">
                        {f['probability_pct']}%
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #8B95A5; margin-top: 1rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.5rem;">
                        <span>Risk: <span style="color: {r_color};">{f['risk_level']}</span></span>
                        <span>Momentum: {f['momentum_multiplier']}x</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            empty_state("Insufficient Data", "Waiting for more events to calculate statistical momentum.", height=150)
    else:
        empty_state("No Events", "Telemetry feed is empty.", height=150)
except Exception as e:
    empty_state("Forecast Error", str(e), height=150)

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS — Shared dark layout
# ═══════════════════════════════════════════════════════════════════════════════
DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#FAFAFA", family="Rajdhani"),
    margin=dict(l=10, r=10, t=10, b=10),
)

# Row 1: Timeline + Decision Split
chart1, spc1, chart2 = st.columns([2.2, 0.1, 1])

with chart1:
    st.markdown(section_title("Threat Activity Timeline"), unsafe_allow_html=True)
    try:
        daily_counts = db.get_daily_counts(days=180)
        if daily_counts:
            df_t = pd.DataFrame(daily_counts)
            df_t['date'] = pd.to_datetime(df_t['date'])
            mn, mx = df_t['date'].min(), df_t['date'].max()
            if str(mn) != 'NaT':
                df_t = df_t.set_index('date').reindex(pd.date_range(mn, mx, freq='D'), fill_value=0).reset_index().rename(columns={'index': 'date'})

            fig = go.Figure()
            # Bar chart — clear daily breakdown
            fig.add_trace(go.Bar(
                x=df_t["date"], y=df_t["count"],
                marker=dict(
                    color=df_t["count"],
                    colorscale=[[0, "#00f3ff"], [0.5, "#8B5CF6"], [1, "#ff003c"]],
                    line=dict(width=0),
                ),
                hovertemplate="<b>%{x|%b %d}</b><br>%{y:,} events<extra></extra>",
                showlegend=False
            ))
            fig.update_layout(
                **DARK_LAYOUT, height=320, hovermode="x unified",
                xaxis=dict(showgrid=False, linecolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
                bargap=0.15,
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
                            st.info("No records for this date.")
                    except Exception as e:
                        st.error(f"Lookup error: {e}")
        else:
            st.info("No timeline data yet.")
    except Exception as e:
        st.error(f"Timeline error: {e}")

with chart2:
    st.markdown(section_title("Decision Split"), unsafe_allow_html=True)
    if not df.empty and "access_decision" in df.columns:
        dc = df["access_decision"].value_counts()
        colors_map = {"ALLOW": "#00C853", "RESTRICT": "#ff6b00", "BLOCK": "#ff003c"}

        fig2 = go.Figure(go.Pie(
            labels=dc.index, values=dc.values, hole=0.65,
            marker_colors=[colors_map.get(d, "#888") for d in dc.index],
            textinfo="percent", textfont=dict(size=12, color="#FAFAFA"),
            hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>"
        ))
        fig2.update_layout(
            **DARK_LAYOUT, height=320, showlegend=True,
            legend=dict(orientation="h", y=-0.12, font=dict(size=10, color="#8B95A5")),
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

# Row 2: Attack Vectors + Origins
chart3, spc2, chart4 = st.columns([1, 0.1, 1])

with chart3:
    st.markdown(section_title("Top Attack Vectors"), unsafe_allow_html=True)
    if not df.empty:
        ac = df[df["attack_type"] != "Normal"]["attack_type"].value_counts().head(6)
        if not ac.empty:
            fig3 = go.Figure(go.Bar(
                x=ac.values, y=ac.index, orientation="h",
                marker=dict(
                    color=ac.values,
                    colorscale=[[0, "#00f3ff"], [0.5, "#bc13fe"], [1, "#ff003c"]],
                    line=dict(width=0),
                ),
                hovertemplate="<b>%{y}</b>: %{x:,}<extra></extra>"
            ))
            fig3.update_layout(
                **DARK_LAYOUT, height=280,
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
                yaxis=dict(showgrid=False, tickfont=dict(size=11)),
            )
            st.plotly_chart(fig3, use_container_width=True)

with chart4:
    st.markdown(section_title("Attack Origins"), unsafe_allow_html=True)
    if "source_country" in df.columns and not df.empty:
        cc = df[df["attack_type"] != "Normal"]["source_country"].value_counts().head(6)
        if not cc.empty:
            fig4 = go.Figure(go.Bar(
                x=cc.index, y=cc.values,
                marker=dict(
                    color=cc.values,
                    colorscale=[[0, "#ff6b00"], [1, "#ff003c"]],
                ),
                hovertemplate="<b>%{x}</b>: %{y:,}<extra></extra>"
            ))
            fig4.update_layout(
                **DARK_LAYOUT, height=280,
                xaxis=dict(showgrid=False, tickangle=-25, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
            )
            st.plotly_chart(fig4, use_container_width=True)

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY HEALTH GAUGE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(section_title("Security Health Score"), unsafe_allow_html=True)

_, gc, _ = st.columns([1.2, 2, 1.2])
with gc:
    if security_score >= 70:
        g_color = "#00C853"
    elif security_score >= 40:
        g_color = "#ff6b00"
    else:
        g_color = "#ff003c"

    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=security_score,
        number={'font': {'size': 48, 'color': g_color, 'family': 'Orbitron'}},
        title={'text': "Overall Score", 'font': {'size': 14, 'color': '#8B95A5', 'family': 'Rajdhani'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "#555", 'tickwidth': 1, 'tickfont': {'size': 9}},
            'bar': {'color': g_color, 'thickness': 0.2},
            'bgcolor': "rgba(26, 31, 46, 0.5)",
            'borderwidth': 1, 'bordercolor': "rgba(255, 255, 255, 0.06)",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 0, 60, 0.08)'},
                {'range': [40, 70], 'color': 'rgba(255, 107, 0, 0.08)'},
                {'range': [70, 100], 'color': 'rgba(0, 200, 83, 0.08)'}
            ],
        }
    ))
    fig_g.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "#FAFAFA", 'family': "Rajdhani"},
        height=250, margin=dict(l=30, r=30, t=30, b=10)
    )
    st.plotly_chart(fig_g, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#555; padding:0.5rem; font-family:'Share Tech Mono',monospace; font-size:0.8rem;">
    // AI-DRIVEN AUTONOMOUS SOC // ZERO TRUST PLATFORM // RL-POWERED INTELLIGENCE //
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
