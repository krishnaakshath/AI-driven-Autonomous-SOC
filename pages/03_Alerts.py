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

h_col1, h_col2 = st.columns([4, 1])
with h_col1:
    st.markdown(page_header("Security Alerts", "Real-time threat detection from SIEM events | Auto-sync active"), unsafe_allow_html=True)

# Auto-refresh
if 'last_alert_refresh' not in st.session_state:
    st.session_state.last_alert_refresh = time.time()

with h_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.session_state.last_alert_refresh = time.time()
        st.rerun()

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
    """Pull alerts from SIEM service (Real DB)."""
    try:
        from services.database import db
        # Fetch real alerts (including those from Threat Intel)
        alerts_data = db.get_alerts(limit=100)
        
        if not alerts_data:
            return pd.DataFrame()
            
        # Parse 'details' JSON into separate columns
        import json
        enriched_data = []
        for alert in alerts_data:
            alert_dict = dict(alert)
            try:
                if 'details' in alert_dict and alert_dict['details']:
                    details = json.loads(alert_dict['details'])
                    alert_dict.update(details)  # Merge details into main dict
            except Exception:
                pass
            
            # Ensure required columns exist with defaults
            defaults = {
                'source': 'SIEM', 'source_ip': 'N/A', 'hostname': 'Unknown',
                'user': 'N/A', 'risk_score': 0, 'type': alert_dict.get('title', 'Unknown'),
                'time': alert_dict.get('timestamp', datetime.now())
            }
            for k, v in defaults.items():
                if k not in alert_dict:
                    alert_dict[k] = v
            
            enriched_data.append(alert_dict)
            
        return pd.DataFrame(enriched_data)
    except Exception as e:
        st.warning(f"DB Connection issue: {e}")
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

# Operational Workbench Layout
tabs = st.tabs(["Active Alerts", "Advanced Filter", "Trends"])

with tabs[0]:
    st.markdown(section_title(f"Operational Workbench ({len(filtered)})"), unsafe_allow_html=True)
    
    # Custom Table Header
    st.markdown("""
        <div style="display: grid; grid-template-columns: 80px 1.5fr 1fr 1fr 100px 100px; gap: 10px; padding: 0.8rem 1.5rem; background: rgba(0, 243, 255, 0.05); border-bottom: 2px solid rgba(0, 243, 255, 0.2); font-family: 'Orbitron', sans-serif; font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">
            <div>Time</div>
            <div>Alert Title / ID</div>
            <div>Source / Target</div>
            <div>Attack Type</div>
            <div>Risk</div>
            <div>Status</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Display alerts in high-density rows
    for _, alert in filtered.head(40).iterrows():
        time_str = alert["time"].strftime("%H:%M") if hasattr(alert["time"], "strftime") else str(alert["time"])[:5]
        
        sev = alert["severity"].lower()
        sev_color = {"critical": "#ff003c", "high": "#ff6b00", "medium": "#f0ff00", "low": "#0aff0a"}.get(sev, "#00f3ff")
        
        status = str(alert["status"]).lower()
        status_color = {"open": "#ff003c", "investigating": "#00f3ff", "resolved": "#0aff0a"}.get(status, "#888")
        
        st.markdown(f"""
            <div class="glass-card" style="margin: 2px 0; padding: 0.6rem 1.5rem; display: grid; grid-template-columns: 80px 1.5fr 1fr 1fr 100px 100px; gap: 10px; align-items: center; border-left: 2px solid {sev_color}; border-radius: 0; background: rgba(5, 5, 10, 0.4);">
                <div style="font-family: 'Share Tech Mono', monospace; font-size: 0.85rem; color: #666;">{time_str}</div>
                <div>
                    <div style="color: #fff; font-weight: 500; font-size: 0.95rem;">{alert['type']}</div>
                    <div style="color: #555; font-size: 0.7rem; font-family: 'Share Tech Mono', monospace;">{alert['id']}</div>
                </div>
                <div style="color: #888; font-size: 0.85rem;">
                    <span style="color: {sev_color}70;">{alert['source_ip']}</span>
                    <div style="font-size: 0.7rem; color: #444;">{alert['hostname']}</div>
                </div>
                <div style="font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; color: #FAFAFA;">{alert.get('attack_type', 'N/A')}</div>
                <div style="font-family: 'Orbitron', sans-serif; color: {sev_color}; font-weight: 700;">{alert['risk_score']}</div>
                <div style="text-align: right;">
                    <span style="padding: 2px 8px; border: 1px solid {status_color}; color: {status_color}; font-size: 0.65rem; text-transform: uppercase; border-radius: 2px; background: {status_color}10;">{alert['status']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

with tabs[1]:
    st.markdown(section_title("Advanced Investigation"), unsafe_allow_html=True)
    st.dataframe(filtered, use_container_width=True)

with tabs[2]:
    st.markdown(section_title("Alert Velocity"), unsafe_allow_html=True)
    import plotly.express as px
    if not filtered.empty:
        fig = px.histogram(filtered, x="time", color="severity", nbins=24, 
                          color_discrete_map={"CRITICAL": "#ff003c", "HIGH": "#ff6b00", "MEDIUM": "#f0ff00", "LOW": "#0aff0a"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | SIEM-Powered Alerts</p></div>', unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
