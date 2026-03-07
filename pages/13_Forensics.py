"""
 Digital Forensics
====================
Incident investigation powered by SIEM service data.
Shows real incidents from the centralized SIEM with MITRE ATT&CK timelines.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("Digital Forensics", "Deep analysis and incident investigation"), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD LIVE DATA FROM SIEM
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def load_siem_incidents():
    """Load incidents from centralized SIEM service."""
    try:
        from services.siem_service import get_siem_incidents
        return get_siem_incidents()
    except Exception as e:
        st.warning(f"SIEM unavailable: {e}")
        return []

@st.cache_data(ttl=60)
def load_siem_events():
    """Load raw events from SIEM for evidence analysis."""
    try:
        from services.siem_service import get_siem_events
        return get_siem_events(100)
    except Exception:
        return []

incidents = load_siem_incidents()
events = load_siem_events()

if incidents:
    st.success(f" Connected to SIEM — {len(incidents)} active incidents | {len(events)} events")
else:
    st.warning(" No incidents from SIEM")

# Tabs
tab1, tab2, tab3 = st.tabs(["Incident Analysis", "Attack Timeline", "Evidence"])

with tab1:
    st.markdown(section_title(f"Active Incidents ({len(incidents)})"), unsafe_allow_html=True)
    
    if not incidents:
        st.info("No active incidents from SIEM.")
    
    for inc in incidents:
        sev = inc.get("severity", "MEDIUM")
        sev_color = {"CRITICAL": "#FF4444", "HIGH": "#FF8C00", "MEDIUM": "#FFD700"}.get(sev, "#8B95A5")
        status = inc.get("status", "Unknown")
        
        st.markdown(f"""
            <div class="glass-card" style="margin: 0.8rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: {sev_color}; font-weight: 700; font-size: 0.75rem; text-transform: uppercase;">{sev}</span>
                        <h4 style="color: #FAFAFA; margin: 0.3rem 0;">{inc.get('id', 'N/A')} - {inc.get('title', 'Unknown')}</h4>
                        <span style="color: #8B95A5;">Source: {inc.get('source', 'N/A')} | Host: {inc.get('affected_host', 'N/A')} | User: {inc.get('affected_user', 'N/A')}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: {sev_color}; font-weight: 600;">{status}</span><br>
                        <span style="color: #8B95A5; font-size: 0.85rem;">{inc.get('start_time', 'N/A')}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # --- NEURAL LINK INVESTIGATION ---
    selected_inc = st.selectbox("Select Incident for Neural Investigation", [i.get('id') for i in incidents]) if incidents else None
    
    if selected_inc:
        st.markdown(f"### 🧠 CORTEX Neural Analysis: {selected_inc}")
        if st.button("Generate Root Cause Analysis"):
            with st.spinner("Linking neural artifacts..."):
                try:
                    from services.ai_assistant import ai_assistant
                    # Mocking a rich prompt for CORTEX
                    inc_data = next((i for i in incidents if i['id'] == selected_inc), {})
                    analysis = ai_assistant.chat(f"Perform a forensic root cause analysis for incident {selected_inc}: {inc_data.get('title')}. Evidence: {inc_data.get('details')}")
                    st.markdown(f"""
                        <div class="glass-card" style="border-left: 3px solid #bc13fe; padding: 1.5rem;">
                            {analysis}
                        </div>
                    """, unsafe_allow_html=True)
                except Exception:
                    st.info("CORTEX Offline. Please check Settings > AI Configuration.")

        st.markdown("### Visual Attack Sequence")
        # Build dynamic mermaid from incident data
        inc_data_m = next((i for i in incidents if i['id'] == selected_inc), {})
        inc_title_m = str(inc_data_m.get('title', 'Unknown')).replace('"', '')
        inc_source_m = str(inc_data_m.get('source', 'External')).replace('"', '')
        inc_host_m = str(inc_data_m.get('affected_host', 'Target Host')).replace('"', '')
        inc_sev_m = inc_data_m.get('severity', 'MEDIUM')
        sev_fill_m = '#ff4444' if inc_sev_m == 'CRITICAL' else '#FF8C00' if inc_sev_m == 'HIGH' else '#FFD700'
        mermaid_code = f"""graph LR
    A["{inc_source_m}"] -->|Reconnaissance| B["Perimeter"]
    B -->|Exploit| C["{inc_host_m}"]
    C -->|"{inc_title_m}"| D["Impact"]
    style D fill:{sev_fill_m},stroke:#fff,stroke-width:2px
    style A fill:#00f3ff22,stroke:#00f3ff
    style B fill:#8B5CF622,stroke:#8B5CF6
    style C fill:#FF8C0022,stroke:#FF8C00"""
        st.components.v1.html(f"""
            <div style="background: rgba(0,0,0,0.4); padding: 20px; border-radius: 12px; border: 1px solid rgba(0,243,255,0.2);">
                <pre class="mermaid">
                    {mermaid_code}
                </pre>
                <script type="module">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
                </script>
            </div>
        """, height=250)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_title("Analysis Tools"), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="glass-card">
                <h4 style="color: #00D4FF; margin: 0 0 1rem 0;"> Memory Analysis</h4>
                <p style="color: #8B95A5; margin: 0;">Analyze memory dumps for malware artifacts, injected code, and rootkits.</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class="glass-card">
                <h4 style="color: #8B5CF6; margin: 0 0 1rem 0;"> Disk Forensics</h4>
                <p style="color: #8B95A5; margin: 0;">Examine file systems, deleted files, and disk artifacts.</p>
            </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown(section_title("MITRE ATT&CK Attack Timeline"), unsafe_allow_html=True)
    
    # Show timeline from the first incident with timeline data, OR build from events
    timeline_incident = None
    for inc in incidents:
        if inc.get("timeline"):
            timeline_incident = inc
            break
    
    if timeline_incident:
        st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1.5rem;">
                <h4 style="color: #FF4444; margin: 0;">{timeline_incident.get('title', 'Unknown Incident')}</h4>
                <p style="color: #8B95A5; margin: 0.3rem 0;">ID: {timeline_incident.get('id', 'N/A')} | Started: {timeline_incident.get('start_time', 'N/A')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        for i, phase in enumerate(timeline_incident.get("timeline", [])):
            phase_time = (datetime.now() + timedelta(hours=phase.get("time", 0))).strftime("%H:%M")
            st.markdown(f"""
                <div style="display: flex; margin: 1rem 0;">
                    <div style="display: flex; flex-direction: column; align-items: center; margin-right: 1.5rem;">
                        <div style="width: 16px; height: 16px; background: linear-gradient(135deg, #00D4FF, #8B5CF6); border-radius: 50%;"></div>
                        {'<div style="width: 2px; height: 60px; background: rgba(0, 212, 255, 0.3);"></div>' if i < len(timeline_incident.get("timeline", [])) - 1 else ''}
                    </div>
                    <div class="glass-card" style="flex: 1;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #00D4FF; font-weight: 600;">{phase.get('phase', 'Unknown')}</span>
                            <span style="color: #8B95A5; font-family: monospace;">{phase_time} | {phase.get('technique', 'N/A')}</span>
                        </div>
                        <p style="color: #FAFAFA; margin: 0.5rem 0 0 0;">{phase.get('description', 'N/A')}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    elif events:
        # Fallback: build a pseudo-timeline from raw SIEM events
        st.markdown("**Reconstructed from SIEM Event Stream:**")
        critical_evts = [e for e in events if e.get('severity') in ['CRITICAL', 'HIGH']][:8]
        if not critical_evts:
            critical_evts = events[:8]
        for i, evt in enumerate(critical_evts):
            evt_time = str(evt.get('timestamp', 'N/A'))[:19]
            sev_c = '#FF4444' if evt.get('severity') == 'CRITICAL' else '#FF8C00' if evt.get('severity') == 'HIGH' else '#00D4FF'
            st.markdown(f"""
                <div style="display: flex; margin: 0.8rem 0;">
                    <div style="display: flex; flex-direction: column; align-items: center; margin-right: 1.5rem;">
                        <div style="width: 14px; height: 14px; background: {sev_c}; border-radius: 50%;"></div>
                        {'<div style="width: 2px; height: 50px; background: rgba(0, 212, 255, 0.2);"></div>' if i < len(critical_evts) - 1 else ''}
                    </div>
                    <div class="glass-card" style="flex: 1;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: {sev_c}; font-weight: 600;">{evt.get('event_type', 'Event')}</span>
                            <span style="color: #8B95A5; font-family: monospace;">{evt_time}</span>
                        </div>
                        <p style="color: #FAFAFA; margin: 0.3rem 0 0 0; font-size: 0.9rem;">Source: {evt.get('source_ip', 'N/A')} | {evt.get('source', 'N/A')}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No timeline data available. Connect SIEM to populate.")

with tab3:
    st.markdown(section_title("SIEM Event Evidence"), unsafe_allow_html=True)
    
    if events:
        # Group by severity for evidence summary
        sev_counts = {}
        for evt in events:
            s = evt.get("severity", "LOW")
            sev_counts[s] = sev_counts.get(s, 0) + 1
        
        st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <h4 style="color: #00D4FF; margin: 0 0 0.5rem 0;"> Event Evidence Summary</h4>
                <p style="color: #8B95A5; margin: 0;">
                    Total Events: {len(events)} | 
                    Critical: {sev_counts.get('CRITICAL', 0)} | 
                    High: {sev_counts.get('HIGH', 0)} | 
                    Medium: {sev_counts.get('MEDIUM', 0)} | 
                    Low: {sev_counts.get('LOW', 0)}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Show recent critical/high events as evidence items
        critical_events = [e for e in events if e.get("severity") in ["CRITICAL", "HIGH"]][:10]
        
        for evt in critical_events:
            sev_color = "#FF4444" if evt.get("severity") == "CRITICAL" else "#FF8C00"
            st.markdown(f"""
                <div class="glass-card" style="margin: 0.5rem 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: {sev_color}; font-weight: 600; font-size: 0.8rem;">{evt.get('severity', 'N/A')}</span>
                            <span style="color: #FAFAFA; font-weight: 600; margin-left: 0.5rem;">{evt.get('event_type', 'Unknown')}</span>
                            <div style="display: flex; gap: 1.5rem; margin-top: 0.3rem;">
                                <span style="color: #8B95A5; font-size: 0.85rem;">Source: {evt.get('source', 'N/A')}</span>
                                <span style="color: #8B95A5; font-size: 0.85rem;">IP: {evt.get('source_ip', 'N/A')}</span>
                                <span style="color: #8B95A5; font-size: 0.85rem;">Host: {evt.get('hostname', 'N/A')}</span>
                                <span style="color: #00D4FF; font-size: 0.85rem; font-family: monospace;">ID: {evt.get('id', 'N/A')}</span>
                            </div>
                        </div>
                        <span style="color: #8B95A5; font-size: 0.85rem;">{evt.get('timestamp', 'N/A')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No event evidence available from SIEM.")

st.markdown('---')
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | SIEM-Powered Forensics</p></div>', unsafe_allow_html=True)
try:
    from ui.chat_interface import inject_floating_cortex_link
    inject_floating_cortex_link()
except Exception:
    pass
