import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title, metric_card
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("SOAR Workbench", "Security Orchestration, Automation, and Response"), unsafe_allow_html=True)

# --- LOAD DATA ---
try:
    from services.database import db
    from services.siem_service import get_siem_incidents
    incidents = get_siem_incidents()
except Exception:
    incidents = []

# --- SOAR METRICS ---
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(metric_card("142", "Auto-Remediated", "#00C853"), unsafe_allow_html=True)
with m2:
    st.markdown(metric_card("4.2m", "Avg Response Time", "#00D4FF"), unsafe_allow_html=True)
with m3:
    st.markdown(metric_card("850+", "Hours Saved", "#8B5CF6"), unsafe_allow_html=True)
with m4:
    st.markdown(metric_card("98%", "Playbook Success", "#FFD700"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- WORKBENCH LAYOUT ---
col_play, col_exec = st.columns([1, 1.5])

with col_play:
    st.markdown(section_title("Defensive Playbooks"), unsafe_allow_html=True)
    
    playbooks = [
        {"name": "Full Network Quarantine", "icon": "🛡️", "desc": "Isolate affected VLANs and trigger global firewall block.", "risk": "CRITICAL"},
        {"name": "Credential Revocation", "icon": "🔑", "desc": "Force password reset and invalidate all active session tokens.", "risk": "HIGH"},
        {"name": "Process Termination", "icon": "🚫", "desc": "Kill suspicious child processes across all enpoints.", "risk": "MEDIUM"},
        {"name": "Snapshot & Forensic Lock", "icon": "🧊", "desc": "Capture memory state and lock disk for investigation.", "risk": "LOW"},
    ]
    
    for pb in playbooks:
        with st.expander(f"{pb['icon']} {pb['name']}"):
            st.markdown(f"**Target:** {pb['risk']} Threat Patterns")
            st.info(pb['desc'])
            if st.button(f"⚡ Execute {pb['name'].split()[0]}", key=pb['name']):
                st.toast(f"Execution started: {pb['name']}", icon="🚀")
                import time
                time.sleep(1)
                st.success("Playbook Deployed Successfully")

with col_exec:
    st.markdown(section_title("Active Investigations & Auto-Triggers"), unsafe_allow_html=True)
    
    if incidents:
        for inc in incidents[:5]:
            status = inc.get("status", "Active")
            btn_label = "Re-validate" if status == "Resolved" else "Deploy Defense"
            
            st.markdown(f"""
                <div class="glass-card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <h4 style="margin:0; color:#FAFAFA;">{inc.get('title')}</h4>
                        <span style="color:#00D4FF; font-family:monospace;">{inc.get('id')}</span>
                    </div>
                    <p style="color:#8B95A5; font-size:0.85rem; margin:0.5rem 0;">{inc.get('details')[:80]}...</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size:0.75rem; color:{'#00C853' if status=='Resolved' else '#FF4444'};">STATUS: {status.upper()}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if status != "Resolved":
                if st.button(f"⚡ {btn_label}", key=f"btn_{inc.get('id')}"):
                    # Update DB status to Resolved locally
                    try:
                        db.update_alert_status(inc.get('id'), "Resolved")
                        st.success(f"Response Automated for {inc.get('id')}")
                        st.rerun()
                    except Exception:
                        st.toast("Automation Engine Timeout", icon="")
    else:
        st.info("No active incidents requiring SOAR intervention.")

st.markdown("---")
# Automation ROI Chart
st.markdown(section_title("Automation ROI (Last 30 Days)"), unsafe_allow_html=True)
roi_data = pd.DataFrame({
    'Day': range(1, 31),
    'Manual': np.random.normal(50, 5, 30).cumsum(),
    'Autonomous': np.random.normal(10, 2, 30).cumsum()
})

fig = go.Figure()
fig.add_trace(go.Scatter(x=roi_data['Day'], y=roi_data['Manual'], name="Manual Effort (Hrs)", fill='tozeroy', line=dict(color='#FF4444')))
fig.add_trace(go.Scatter(x=roi_data['Day'], y=roi_data['Autonomous'], name="Autonomous Effort (Hrs)", fill='tozeroy', line=dict(color='#00C853')))
fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA", height=300, margin=dict(l=20,r=20,t=20,b=20))
st.plotly_chart(fig, use_container_width=True)

# Live Refresh Logic
st.sidebar.markdown("---")
auto_refresh = st.sidebar.toggle("SOAR Live Link", value=True)
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()

from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
