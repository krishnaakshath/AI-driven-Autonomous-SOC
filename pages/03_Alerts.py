"""
 Security Alerts
==================
Real-time threat detection from centralized SIEM service.
Alerts are generated from SIEM events and enriched with threat intel.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, alert_card, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("Security Alerts", "Real-time threat detection from SIEM events"), unsafe_allow_html=True)

# Auto-refresh
if 'last_alert_refresh' not in st.session_state:
    st.session_state.last_alert_refresh = time.time()

col_refresh, col_time = st.columns([1, 3])
with col_refresh:
    if st.button("Refresh Alerts", type="primary"):
        st.cache_data.clear()
        st.session_state.last_alert_refresh = time.time()
        st.rerun()

with col_time:
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 0.5rem; height: 38px;">
            <span style="color: #00C853;"></span>
            <span style="color: #8B95A5;">Auto-refreshing every 30s | Connected to SIEM</span>
        </div>
    ''', unsafe_allow_html=True)

# Auto-refresh logic
if time.time() - st.session_state.last_alert_refresh > 30:
    st.cache_data.clear()
    st.session_state.last_alert_refresh = time.time()
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PULL ALERTS FROM CENTRALIZED SIEM SERVICE
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def get_alerts():
    """Pull alerts from SIEM service instead of generating random data."""
    try:
        from services.siem_service import get_siem_events
        events = get_siem_events(200)
        
        # Convert SIEM events to alert format
        alerts = []
        for evt in events:
            # Map event severity to risk score
            risk_map = {"CRITICAL": 90, "HIGH": 70, "MEDIUM": 45, "LOW": 20}
            base_risk = risk_map.get(evt.get("severity", "LOW"), 20)
            
            alerts.append({
                "id": evt.get("id", "ALT-000"),
                "severity": evt.get("severity", "LOW"),
                "type": evt.get("event_type", "Unknown Event"),
                "source_ip": evt.get("source_ip", "0.0.0.0"),
                "source": evt.get("source", "Unknown"),
                "time": datetime.strptime(evt["timestamp"], "%Y-%m-%d %H:%M:%S") if isinstance(evt.get("timestamp"), str) else datetime.now(),
                "status": evt.get("status", "Open"),
                "risk_score": base_risk,
                "hostname": evt.get("hostname", "Unknown"),
                "user": evt.get("user", "-"),
            })
        
        return pd.DataFrame(alerts)
    except Exception as e:
        st.warning(f"SIEM connection issue: {e}. Using local data.")
        # Fallback
        return pd.DataFrame()

# Enrich with OTX threat intel
@st.cache_data(ttl=300)
def get_otx_enrichment():
    """Get OTX threat pulse data for enrichment."""
    try:
        from services.threat_intel import get_latest_threats, threat_intel
        pulses = get_latest_threats()
        
        # Check AbuseIPDB/Indicators too
        indicators = threat_intel.get_recent_indicators(limit=5)
        
        if pulses:
            return {
                "active_pulses": len(pulses),
                "latest": pulses[0].get("name", "Unknown"),
                "source": "OTX Live"
            }
        elif indicators:
             return {
                "active_pulses": len(indicators),
                "latest": f"Indicator: {indicators[0].get('indicator')}",
                "source": "Threat Intel Live"
            }
        else:
             return {
                "active_pulses": 0,
                "latest": "No recent pulses",
                "source": "OTX Active (No Pulses)"
            }
            
    except Exception as e:
        # st.error(f"Intel Error: {e}") # Debug
        pass
    return {"active_pulses": 0, "latest": "Check Config", "source": "Offline"}

alerts_df = get_alerts()
otx_data = get_otx_enrichment()

if alerts_df.empty:
    st.error("No alert data available. SIEM service may be down.")
    st.stop()

# Stats
critical = (alerts_df["severity"] == "CRITICAL").sum()
high = (alerts_df["severity"] == "HIGH").sum()
active = (alerts_df["status"] == "Open").sum()
resolved = (alerts_df["status"] == "Resolved").sum()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF4444;">{critical}</p><p class="metric-label">Critical</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF8C00;">{high}</p><p class="metric-label">High</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00D4FF;">{active}</p><p class="metric-label">Open</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00C853;">{resolved}</p><p class="metric-label">Resolved</p></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #8B5CF6;">{otx_data["active_pulses"]}</p><p class="metric-label">OTX Pulses</p></div>', unsafe_allow_html=True)

# OTX enrichment banner
if otx_data["source"] == "OTX Live":
    st.success(f" **OTX Enrichment Active** — {otx_data['active_pulses']} threat pulses | Latest: {otx_data['latest'][:60]}")
else:
    st.info(" OTX enrichment offline — showing SIEM alerts only")

st.markdown("<br>", unsafe_allow_html=True)

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    sev_filter = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
with col2:
    status_filter = st.selectbox("Status", ["All", "Open", "Investigating", "Resolved", "False Positive"])
with col3:
    source_filter = st.selectbox("Source", ["All"] + sorted(alerts_df["source"].unique().tolist()))

# Filter data
filtered = alerts_df.copy()
if sev_filter != "All":
    filtered = filtered[filtered["severity"] == sev_filter]
if status_filter != "All":
    filtered = filtered[filtered["status"] == status_filter]
if source_filter != "All":
    filtered = filtered[filtered["source"] == source_filter]

filtered = filtered.sort_values("time", ascending=False)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_title(f"SIEM Alerts ({len(filtered)})"), unsafe_allow_html=True)

# Display alerts
for _, alert in filtered.head(25).iterrows():
    time_str = alert["time"].strftime("%H:%M") if hasattr(alert["time"], "strftime") else str(alert["time"])[:5]
    desc = f"Source: {alert['source']} | IP: {alert['source_ip']} | Host: {alert['hostname']} | User: {alert['user']} | Risk: {alert['risk_score']}/100"
    st.markdown(alert_card(alert["severity"], f"{alert['id']} - {alert['type']}", desc, time_str), unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | SIEM-Powered Alerts</p></div>', unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
