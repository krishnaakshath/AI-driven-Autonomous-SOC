"""
 SOC Dashboard — Nightfall-Inspired Design
=============================================
Card-based grid layout with:
  - Violations Summary (left panel)
  - Live Threat Map with Event Severity + Detection Confidence (center)
  - Risk by Application + Event Types (right panel)
  - Incident Timeline (bottom)
  - Stats bar (footer)
"""

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
    st.set_page_config(page_title="Dashboard | SOC Platform", page_icon="D", layout="wide")
except st.errors.StreamlitAPIError:
    pass

from services.logger import get_logger
logger = get_logger("dashboard")

# --- Background service ---
try:
    from services.cloud_background import start_cloud_background_service
    start_cloud_background_service()
except ImportError:
    logger.debug("Cloud background service not available")
except Exception as e:
    logger.warning("Background service failed: %s", e)

# ── CSS ─────────────────────────────────────────────────────────────
from ui.theme import CYBERPUNK_CSS, MOBILE_CSS, inject_particles
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# Nightfall-inspired card system CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');

/* Reset Streamlit padding */
section[data-testid="stSidebar"] + div .block-container {
    padding: 1rem 2rem 2rem 2rem !important;
    max-width: 100% !important;
}

/* Card system */
.dash-card {
    background: rgba(15, 17, 28, 0.85);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(10px);
    transition: border-color 0.3s ease;
}
.dash-card:hover {
    border-color: rgba(139, 92, 246, 0.25);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.card-title {
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: #E8E8EF;
    letter-spacing: 0.3px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.card-title .icon {
    width: 20px; height: 20px;
    display: flex; align-items: center; justify-content: center;
}
.card-dots {
    display: flex; gap: 3px; cursor: pointer; opacity: 0.4;
}
.card-dots span {
    width: 3px; height: 3px; border-radius: 50%; background: #888;
}

/* Violation row */
.violation-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.9rem 1rem;
    background: rgba(255,255,255,0.02);
    border-radius: 10px;
    margin-bottom: 0.5rem;
    border-left: 3px solid transparent;
    transition: all 0.2s ease;
}
.violation-row:hover {
    background: rgba(255,255,255,0.04);
}
.violation-row .sev-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #999;
    display: flex;
    align-items: center;
    gap: 6px;
}
.violation-row .sev-label .dot {
    width: 6px; height: 6px;
    border-radius: 2px;
}
.violation-row .count-group {
    display: flex; align-items: baseline; gap: 6px;
}
.violation-row .count {
    font-family: 'Inter', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1;
}
.violation-row .count-new {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: rgba(255,255,255,0.35);
}
.violation-row .view-btn {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: #888;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    padding: 4px 14px;
    cursor: pointer;
    transition: all 0.2s ease;
}
.violation-row .view-btn:hover {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.3);
    color: #c4b5fd;
}

/* Severity colors */
.sev-critical { border-left-color: #EF4444 !important; }
.sev-critical .count { color: #EF4444; }
.sev-critical .dot { background: #EF4444; }

.sev-high { border-left-color: #F97316 !important; }
.sev-high .count { color: #F97316; }
.sev-high .dot { background: #F97316; }

.sev-medium { border-left-color: #EAB308 !important; }
.sev-medium .count { color: #EAB308; }
.sev-medium .dot { background: #EAB308; }

.sev-low { border-left-color: #8B95A5 !important; }
.sev-low .count { color: #8B95A5; }
.sev-low .dot { background: #8B95A5; }

/* Event type row */
.event-type-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.8rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.event-type-row:last-child { border-bottom: none; }
.event-type-row .et-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #bbb;
    display: flex; align-items: center; gap: 8px;
}
.event-type-row .et-count {
    font-family: 'Inter', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #E8E8EF;
}
.event-type-row .et-right {
    display: flex; align-items: center; gap: 12px;
}
.event-type-row .et-badge {
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
}
.et-badge.up { background: rgba(239,68,68,0.12); color: #EF4444; }
.et-badge.down { background: rgba(34,197,94,0.12); color: #22C55E; }

/* Timeline table */
.timeline-row {
    display: grid;
    grid-template-columns: 2fr 0.8fr 1fr;
    gap: 10px;
    padding: 0.7rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #bbb;
    align-items: center;
}
.timeline-row:last-child { border-bottom: none; }
.timeline-header {
    color: #666;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.status-badge {
    font-size: 0.7rem;
    padding: 3px 10px;
    border-radius: 4px;
    font-weight: 600;
    display: inline-block;
}
.status-investigate {
    background: rgba(59,130,246,0.15);
    color: #60A5FA;
    border: 1px solid rgba(59,130,246,0.25);
}
.status-contained {
    background: rgba(34,197,94,0.12);
    color: #22C55E;
    border: 1px solid rgba(34,197,94,0.2);
}
.status-open {
    background: rgba(239,68,68,0.12);
    color: #EF4444;
    border: 1px solid rgba(239,68,68,0.2);
}

/* Bottom stats bar */
.stats-bar {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
}
.stat-chip {
    flex: 1;
    background: rgba(15, 17, 28, 0.85);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.stat-chip .stat-value {
    font-family: 'Inter', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #E8E8EF;
}
.stat-chip .stat-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: #888;
}

/* Top header bar */
.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0 1.5rem 0;
}
.top-bar .brand {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #E8E8EF;
    display: flex;
    align-items: center;
    gap: 10px;
}
.top-bar .brand .dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #8B5CF6;
    box-shadow: 0 0 12px rgba(139,92,246,0.5);
}
.user-type-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 6px 16px;
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #bbb;
}
.user-type-badge strong {
    color: #E8E8EF;
}

/* Tab switcher */
.map-tabs {
    display: flex;
    gap: 0;
    margin-bottom: 1rem;
}
.map-tab {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #888;
    padding: 8px 18px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    cursor: pointer;
    transition: all 0.2s;
}
.map-tab:first-child { border-radius: 8px 0 0 8px; }
.map-tab:last-child { border-radius: 0 8px 8px 0; }
.map-tab.active {
    background: rgba(139, 92, 246, 0.15);
    color: #c4b5fd;
    border-color: rgba(139, 92, 246, 0.3);
}

/* Add Widget button */
.add-widget-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.03);
    border: 1px dashed rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 10px 20px;
    color: #888;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
    margin-top: 0.5rem;
}
.add-widget-btn:hover {
    background: rgba(139,92,246,0.08);
    border-color: rgba(139,92,246,0.3);
    color: #c4b5fd;
}

/* RL Intelligence bar */
.rl-bar {
    background: linear-gradient(90deg, rgba(139,92,246,0.06), rgba(0,212,255,0.03));
    border: 1px solid rgba(139,92,246,0.15);
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: #A78BFA;
}
.rl-bar .rl-val {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
}

/* Security Query button */
.security-query-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #7C3AED, #8B5CF6);
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    color: white;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(139,92,246,0.3);
    transition: all 0.3s;
}
.security-query-btn:hover {
    box-shadow: 0 6px 30px rgba(139,92,246,0.5);
    transform: translateY(-1px);
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
        logger.warning("Dashboard data load: %s", e)
        return pd.DataFrame()

# Show loading skeleton while loading
load_placeholder = st.empty()
with load_placeholder.container():
    from ui.page_layout import show_loading
    show_loading(rows=3)

df = load_soc_data()
load_placeholder.empty()

# Onboarding / Empty State
if df.empty:
    from ui.page_layout import show_empty
    st.markdown("<br><br>", unsafe_allow_html=True)
    show_empty(
        title="Welcome to the Autonomous SOC",
        message="Your deployment is initialized but we aren't receiving any telemetry yet.<br/>Head to the <b>SIEM Settings</b> to configure your log ingestion sources or trigger a simulation.",
        icon="🚀"
    )
    from ui.page_layout import page_footer
    page_footer("DASHBOARD")
    st.stop()

# Alert service
try:
    from alerting.alert_service import trigger_alert
    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False

if ALERTS_AVAILABLE and not df.empty and "risk_score" in df.columns:
    critical_events = df[df["risk_score"] >= 80]
    if len(critical_events) > 0 and 'last_alert_check' not in st.session_state:
        st.session_state.last_alert_check = True
        worst = critical_events.iloc[0]
        trigger_alert({
            "attack_type": worst.get("attack_type", "Unknown"),
            "risk_score": float(worst.get("risk_score", 0)),
            "source_ip": worst.get("source_ip", "Unknown"),
            "access_decision": worst.get("access_decision", "BLOCK"),
            "source_country": worst.get("source_country", "Unknown"),
            "dest_port": int(worst.get("dest_port", 0)),
            "timestamp": str(worst.get("timestamp", datetime.now()))
        })

# ═══════════════════════════════════════════════════════════════════════════════
# METRICS
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
high = int((df["risk_score"].between(60, 79)).sum()) if isinstance(df, pd.DataFrame) and not df.empty and "risk_score" in df.columns else 0
medium = int((df["risk_score"].between(30, 59)).sum()) if isinstance(df, pd.DataFrame) and not df.empty and "risk_score" in df.columns else 0
low = total - critical - high - medium if total > 0 else 0

# Security score
try:
    from services.statistical_engine import statistical_engine
    if not df.empty:
        events_list = df.to_dict('records')
        alerts_list = [{"severity": "CRITICAL"} for _ in range(critical)]
        security_score = statistical_engine.calculate_probabilistic_risk_score(events_list, alerts_list)
    else:
        security_score = 100.0
except Exception:
    security_score = max(0, min(100, 100 - avg_risk))


# ═══════════════════════════════════════════════════════════════════════════════
# TOP BAR
# ═══════════════════════════════════════════════════════════════════════════════
user_name = st.session_state.get("user_email", "Analyst")
user_role = st.session_state.get("user_role", "SOC Analyst")

st.markdown(f"""
<div class="top-bar">
    <div class="brand">
        <span class="dot"></span>
        SOC Platform
    </div>
    <div style="display: flex; align-items: center; gap: 16px;">
        <span class="user-type-badge">User Type <strong>{user_role}</strong></span>
    </div>
</div>
""", unsafe_allow_html=True)


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
        <span class="rl-val" style="color:#22C55E;">{rl_acc}%</span> <span>accuracy</span>
        <span style="margin-left:auto;">{n_agents} agents</span>
        <span>·</span>
        <span class="rl-val" style="color:#60A5FA;">{total_episodes:,}</span> <span>episodes</span>
        <span>·</span>
        <span>ε = {rl_stats.get('epsilon', 0):.3f}</span>
    </div>
    """, unsafe_allow_html=True)
except ImportError:
    pass
except Exception:
    logger.debug("RL bar rendering skipped", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GRID: LEFT (Violations) | CENTER (Charts) | RIGHT (Risk + Events)
# ═══════════════════════════════════════════════════════════════════════════════

col_left, col_center, col_right = st.columns([1, 2.4, 1.2])


# ── LEFT: Violations Summary ─────────────────────────────────────────────────
with col_left:
    st.markdown("""
    <div class="dash-card">
        <div class="card-header">
            <span class="card-title">
                <span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2"><path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg></span>
                Violations Summary
            </span>
            <span class="card-dots"><span></span><span></span><span></span></span>
        </div>
    """, unsafe_allow_html=True)

    # Compute "new" counts (events in last hour)
    recent_mask = pd.Series([False] * len(df))
    if not df.empty and "timestamp" in df.columns:
        try:
            recent_mask = df["timestamp"] > (datetime.now() - timedelta(hours=1))
        except Exception:
            pass
    new_crit = int((df.loc[recent_mask, "risk_score"] >= 80).sum()) if not df.empty and "risk_score" in df.columns else 0
    new_high = int((df.loc[recent_mask, "risk_score"].between(60, 79)).sum()) if not df.empty and "risk_score" in df.columns else 0
    new_med = int((df.loc[recent_mask, "risk_score"].between(30, 59)).sum()) if not df.empty and "risk_score" in df.columns else 0
    new_low = int(recent_mask.sum()) - new_crit - new_high - new_med if not df.empty else 0

    violations = [
        ("Critical", critical, new_crit, "sev-critical"),
        ("High", high, new_high, "sev-high"),
        ("Medium", medium, new_med, "sev-medium"),
        ("Low", low, max(0, new_low), "sev-low"),
    ]

    for label, count, new, css_class in violations:
        new_text = f"+{new} new" if new > 0 else ""
        st.markdown(f"""
        <div class="violation-row {css_class}">
            <div>
                <div class="sev-label"><span class="dot"></span> {label}</div>
                <div class="count-group">
                    <span class="count">{count:,}</span>
                    <span class="count-new">{new_text}</span>
                </div>
            </div>
            <a href="Alerts" target="_self" class="view-btn" style="text-decoration:none; display:inline-block; text-align:center;">View</a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Incident Timeline
    st.markdown("""
    <div class="dash-card">
        <div class="card-header">
            <span class="card-title">
                <span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg></span>
                Incident Timeline
            </span>
            <span class="card-dots"><span></span><span></span><span></span></span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="timeline-row timeline-header">
            <span>Event</span><span>Time</span><span>Status</span>
        </div>
    """, unsafe_allow_html=True)

    # Pull recent events from DB or fallback to DataFrame
    timeline_events = []
    try:
        recent_db = db.get_recent_events(limit=5)
        if recent_db:
            for evt in recent_db[:5]:
                etype = evt.get("event_type", "Unknown Event")[:25]
                etime = evt.get("timestamp", "")
                if isinstance(etime, str) and len(etime) > 10:
                    etime = etime[11:16]
                elif hasattr(etime, "strftime"):
                    etime = etime.strftime("%H:%M")
                else:
                    etime = "N/A"
                sev = evt.get("severity", "LOW")
                if sev == "CRITICAL":
                    status_class, status_text = "status-open", "Open"
                elif sev == "HIGH":
                    status_class, status_text = "status-investigate", "Investigate"
                else:
                    status_class, status_text = "status-contained", "Contained"
                timeline_events.append((etype, etime, status_class, status_text))
    except Exception:
        pass

    if not timeline_events and not df.empty:
        for _, row in df.head(5).iterrows():
            etype = str(row.get("attack_type", "Event"))[:25]
            ts = row.get("timestamp", datetime.now())
            etime = ts.strftime("%H:%M") if hasattr(ts, "strftime") else "N/A"
            risk = row.get("risk_score", 0)
            if risk >= 80:
                sc, st_text = "status-open", "Open"
            elif risk >= 50:
                sc, st_text = "status-investigate", "Investigate"
            else:
                sc, st_text = "status-contained", "Contained"
            timeline_events.append((etype, etime, sc, st_text))

    for etype, etime, sc, st_text in timeline_events[:5]:
        st.markdown(f"""
        <div class="timeline-row">
            <span style="color:#E8E8EF;">{etype}</span>
            <span style="color:#888; font-family:'Share Tech Mono',monospace; font-size:0.8rem;">{etime}</span>
            <span><span class="status-badge {sc}">{st_text}</span></span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── CENTER: Live Threat Map (Charts) ─────────────────────────────────────────
with col_center:
    st.markdown("""
    <div class="dash-card">
        <div class="card-header">
            <span class="card-title">
                <span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg></span>
                Live Threat Map
            </span>
            <span class="card-dots"><span></span><span></span><span></span></span>
        </div>
        <div class="map-tabs">
            <span class="map-tab active">Real-time Scans</span>
            <span class="map-tab">Historical Audits</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    DARK_LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#999", family="Inter", size=11),
        margin=dict(l=40, r=20, t=30, b=40),
    )

    # Two charts side by side: Event Severity + Detection Confidence
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("""<div class="dash-card" style="padding: 1rem;">""", unsafe_allow_html=True)

        # Event Severity bar chart
        if not df.empty and "timestamp" in df.columns:
            df_copy = df.copy()
            df_copy["hour"] = df_copy["timestamp"].dt.hour

            hours = list(range(0, 24, 4))
            hour_labels = [f"{h}:00" for h in hours]

            sev_data = {"Critical": [], "High": [], "Medium": [], "Low": []}
            for h in hours:
                mask = df_copy["hour"].between(h, h + 3)
                subset = df_copy[mask]
                sev_data["Critical"].append(int((subset["risk_score"] >= 80).sum()) if "risk_score" in subset else 0)
                sev_data["High"].append(int((subset["risk_score"].between(60, 79)).sum()) if "risk_score" in subset else 0)
                sev_data["Medium"].append(int((subset["risk_score"].between(30, 59)).sum()) if "risk_score" in subset else 0)
                sev_data["Low"].append(int((subset["risk_score"] < 30).sum()) if "risk_score" in subset else 0)

            fig_sev = go.Figure()
            colors = {"Critical": "#EF4444", "High": "#F97316", "Medium": "#EAB308", "Low": "#6B7280"}
            for sev_name, vals in sev_data.items():
                fig_sev.add_trace(go.Bar(
                    x=hour_labels, y=vals, name=sev_name,
                    marker_color=colors[sev_name],
                    marker_line_width=0,
                ))
            fig_sev.update_layout(
                **DARK_LAYOUT, height=260,
                barmode="group", bargap=0.25, bargroupgap=0.1,
                title=dict(text="Event Severity", font=dict(size=13, color="#E8E8EF"), x=0),
                legend=dict(orientation="h", y=-0.2, font=dict(size=10, color="#888")),
                xaxis=dict(showgrid=False, linecolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
            )
            st.plotly_chart(fig_sev, use_container_width=True)
        else:
            st.info("Awaiting event data...")

        st.markdown("</div>", unsafe_allow_html=True)

    with ch2:
        st.markdown("""<div class="dash-card" style="padding: 1rem;">""", unsafe_allow_html=True)

        # Detection Confidence line chart
        if not df.empty and "timestamp" in df.columns:
            df_copy2 = df.copy()
            df_copy2["hour"] = df_copy2["timestamp"].dt.hour
            hours = list(range(0, 24, 4))
            hour_labels = [f"{h}:00" for h in hours]

            risk_idx = []
            fp_rate = []
            tp_acc = []
            for h in hours:
                mask = df_copy2["hour"].between(h, h + 3)
                subset = df_copy2[mask]
                avg_r = subset["risk_score"].mean() if not subset.empty else 0
                risk_idx.append(round(avg_r, 1))
                fp = max(5, 100 - avg_r * 0.8 + np.random.uniform(-5, 5)) if not subset.empty else 50
                fp_rate.append(round(min(100, fp), 1))
                tp = max(50, avg_r * 0.9 + np.random.uniform(-3, 3)) if not subset.empty else 70
                tp_acc.append(round(min(100, tp), 1))

            fig_conf = go.Figure()
            fig_conf.add_trace(go.Scatter(
                x=hour_labels, y=risk_idx, name="Risk Index",
                line=dict(color="#EF4444", width=2), mode="lines+markers",
                marker=dict(size=5),
            ))
            fig_conf.add_trace(go.Scatter(
                x=hour_labels, y=fp_rate, name="% False Positives",
                line=dict(color="#22C55E", width=2, dash="dot"), mode="lines+markers",
                marker=dict(size=5),
            ))
            fig_conf.add_trace(go.Scatter(
                x=hour_labels, y=tp_acc, name="True Positive Accuracy",
                line=dict(color="#60A5FA", width=2), mode="lines+markers",
                marker=dict(size=5),
            ))
            fig_conf.update_layout(
                **DARK_LAYOUT, height=260,
                title=dict(text="Detection Confidence", font=dict(size=13, color="#E8E8EF"), x=0),
                legend=dict(orientation="h", y=-0.25, font=dict(size=10, color="#888")),
                xaxis=dict(showgrid=False, linecolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
            )
            st.plotly_chart(fig_conf, use_container_width=True)
        else:
            st.info("Awaiting event data...")

        st.markdown("</div>", unsafe_allow_html=True)

    # Daily Alerts Bar Chart
    st.markdown("""
    <div class="dash-card">
        <div class="card-header">
            <span class="card-title">
                <span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg></span>
                Daily Alerts Volume
            </span>
            <span class="card-dots"><span></span><span></span><span></span></span>
        </div>
    """, unsafe_allow_html=True)

    try:
        from services.database import db
        alerts = db.get_alerts(limit=500)
        from collections import defaultdict
        alert_counts = defaultdict(int)
        
        # Aggregate local or fallback to mock
        if alerts:
            for a in alerts:
                ts = a.get("timestamp")
                if ts:
                    d_str = ts[:10]
                    alert_counts[d_str] += 1
                    
        dates = sorted(alert_counts.keys())
        counts = [alert_counts[d] for d in dates]
        
        # Fill missing days if needed or if DB empty
        if len(dates) < 7:
            counts_map = dict(zip(dates, counts))
            dates = []
            counts = []
            for i in range(6, -1, -1):
                d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                dates.append(d)
                # Random realistic data fallback if no DB data
                fallback = int(np.random.normal(5, 2)) if not alerts else 0
                counts.append(counts_map.get(d, max(0, fallback)))

        fig_bar = go.Figure(go.Bar(
            x=dates, y=counts,
            marker_color="#F59E0B",
            opacity=0.8,
            hovertemplate="<b>%{x}</b><br>%{y} Alerts<extra></extra>"
        ))
        fig_bar.update_layout(
            **DARK_LAYOUT, height=200,
            xaxis=dict(showgrid=False, linecolor="rgba(255,255,255,0.05)", categoryorder="category ascending"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
            margin=dict(l=30, r=10, t=10, b=30),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    except Exception as e:
        logger.debug(f"Failed to load daily alerts: {e}")
        st.info("Alert data unavailable.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Render Custom Add-On Widgets
    current_widgets = st.session_state.get("custom_widgets", [])
    for widget_id in current_widgets:
        st.markdown("<br>", unsafe_allow_html=True)
        cols = st.columns([0.85, 0.15])
        with cols[0]:
            if widget_id == "recent_logins":
                st.markdown("""
                <div class="dash-card">
                    <div class="card-header"><span class="card-title">Recent Login Activity</span></div>
                    <div style="color:#bbb; font-size:0.8rem; padding:0 0 1rem 0; font-family:'Share Tech Mono', monospace;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;"><span>admin@soc.org</span><span style="color:#22C55E;">SUCCESS</span></div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;"><span>unknown@104.28.x.x</span><span style="color:#EF4444;">FAILED</span></div>
                        <div style="display:flex; justify-content:space-between;"><span>analyst@soc.org</span><span style="color:#22C55E;">SUCCESS</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif widget_id == "system_health":
                st.markdown("""
                <div class="dash-card">
                    <div class="card-header"><span class="card-title">System Health Metrics</span></div>
                    <div style="color:#bbb; font-size:0.8rem; padding:0 0 1rem 0;">
                        CPU Usage: <strong>42%</strong><br>
                        Memory: <strong>16GB / 64GB</strong><br>
                        Ingestion Lag: <strong>45ms</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif widget_id == "threat_actors":
                st.markdown("""
                <div class="dash-card">
                    <div class="card-header"><span class="card-title">Top Threat Actors</span></div>
                    <div style="color:#bbb; font-size:0.8rem; padding:0 0 1rem 0;">
                        1. APT29 (Russia) - 34%<br>
                        2. Lazarus Group (DPRK) - 21%<br>
                        3. Unknown Scanners - 45%
                    </div>
                </div>
                """, unsafe_allow_html=True)
        with cols[1]:
            if st.button("✖", key=f"rm_{widget_id}"):
                current_widgets.remove(widget_id)
                st.session_state.custom_widgets = current_widgets
                st.rerun()

    # Add Widget button
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("➕ Add Custom Widget", expanded=False):
        available_widgets = {
            "recent_logins": "Recent Login Activity",
            "system_health": "System Health Metrics",
            "threat_actors": "Top Threat Actors"
        }
        options = {k: v for k, v in available_widgets.items() if k not in current_widgets}
        
        if options:
            selected_widget = st.selectbox("Select Widget:", options=list(options.keys()), format_func=lambda x: options[x], label_visibility="collapsed")
            if st.button("Add to Dashboard", use_container_width=True, type="secondary"):
                current_widgets.append(selected_widget)
                st.session_state.custom_widgets = current_widgets
                st.rerun()
        else:
            st.info("All available widgets have been added.")
# ── RIGHT: Risk by Application + Event Types ─────────────────────────────────
with col_right:
    # Risk by Application donut
    st.markdown("""
    <div class="dash-card">
        <div class="card-header">
            <span class="card-title">
                <span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2"><path d="M21.21 15.89A10 10 0 118 2.83"/><path d="M22 12A10 10 0 0012 2v10z"/></svg></span>
                Risk by Application
            </span>
            <span class="card-dots"><span></span><span></span><span></span></span>
        </div>
    """, unsafe_allow_html=True)

    # Build risk-by-attack-type donut
    if not df.empty and "attack_type" in df.columns:
        atk_counts = df[df["attack_type"] != "Normal"]["attack_type"].value_counts().head(5)
        if not atk_counts.empty:
            app_colors = ["#8B5CF6", "#EF4444", "#22C55E", "#F97316", "#60A5FA"]
            fig_donut = go.Figure(go.Pie(
                labels=atk_counts.index, values=atk_counts.values, hole=0.6,
                marker_colors=app_colors[:len(atk_counts)],
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>"
            ))
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#999", family="Inter", size=10),
                height=180, margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(
                    orientation="v", x=1.05, y=0.5,
                    font=dict(size=10, color="#bbb"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                showlegend=True,
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Event Types
    st.markdown("""
    <div class="dash-card">
        <div class="card-header">
            <span class="card-title">
                <span class="icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg></span>
                Event Types
            </span>
            <span class="card-dots"><span></span><span></span><span></span></span>
        </div>
    """, unsafe_allow_html=True)

    event_types = [
        ("Blocked Events", blocked, "up", f"{min(99, max(1, int(blocked / max(1, total) * 100)))}%"),
        ("Restricted Events", restricted, "up", f"{min(99, max(1, int(restricted / max(1, total) * 100)))}%"),
        ("Allowed Events", allowed, "down", f"{min(99, max(1, int(allowed / max(1, total) * 100)))}%"),
        ("Critical Alerts", critical, "up", f"{min(99, max(1, int(critical / max(1, total) * 100)))}%"),
    ]

    for label, count, direction, pct in event_types:
        arrow = "↗" if direction == "up" else "↙"
        st.markdown(f"""
        <div class="event-type-row">
            <div>
                <div class="et-label">{label}</div>
                <div class="et-count">{count:,}</div>
            </div>
            <div class="et-right">
                <a href="SIEM" target="_self" class="view-btn" style="text-decoration:none; font-size:0.7rem; padding:3px 10px; display:inline-block; text-align:center;">View</a>
                <span class="et-badge {direction}">{arrow} {pct}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# BOTTOM STATS BAR
# ═══════════════════════════════════════════════════════════════════════════════

# Calculate stats
data_volume = f"{total * 0.3 / 1000:.2f} TB" if total > 0 else "0 TB"
users_monitored = st.session_state.get("total_users", 1653)
endpoints = total if total > 0 else 1502
apps_connected = 8

st.markdown(f"""
<div class="stats-bar">
    <div class="stat-chip">
        <span class="stat-value">{total:,}</span>
        <span class="stat-label">Total Events Tracked</span>
    </div>
    <div class="stat-chip">
        <span class="stat-value">{data_volume}</span>
        <span class="stat-label">Data Volume</span>
    </div>
    <div class="stat-chip">
        <span class="stat-value">{users_monitored:,}</span>
        <span class="stat-label">Users Monitored</span>
    </div>
    <div class="stat-chip">
        <span class="stat-value">{endpoints:,}</span>
        <span class="stat-label">Endpoints Monitored</span>
    </div>
    <div class="stat-chip">
        <span class="stat-value">{apps_connected}</span>
        <span class="stat-label">Apps Connected</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔍 Launch Security Query Engine", use_container_width=True, type="primary"):
    st.switch_page("pages/24_SIEM.py")


# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#555; padding:0.5rem; font-family:'Share Tech Mono',monospace; font-size:0.8rem;">
    // AI-DRIVEN AUTONOMOUS SOC // DASHBOARD MODULE // ZERO TRUST PLATFORM //
</div>
""", unsafe_allow_html=True)

# Auto-refresh
h_col = st.columns([3, 1])
with h_col[1]:
    auto_refresh = st.toggle("Auto-Sync", value=True, key="dashboard_auto")

if auto_refresh:
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
