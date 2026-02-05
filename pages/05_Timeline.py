import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Incident Timeline | SOC", page_icon="⏱️", layout="wide")

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("Incident Timeline", "Visual attack progression and MITRE ATT&CK mapping"), unsafe_allow_html=True)

# Sample incidents with timeline
INCIDENTS = [
    {
        "id": "INC-2024-0142",
        "title": "Ransomware Attack - Finance Department",
        "severity": "CRITICAL",
        "status": "Contained",
        "start_time": datetime.now() - timedelta(hours=36),
        "timeline": [
            {"time": -36, "phase": "Initial Access", "technique": "T1566.001", "description": "Phishing email with malicious Excel attachment received", "icon": "📧"},
            {"time": -35, "phase": "Execution", "technique": "T1059.001", "description": "User opened attachment, macro executed PowerShell", "icon": "⚡"},
            {"time": -34, "phase": "Persistence", "technique": "T1053.005", "description": "Scheduled task created for persistence", "icon": "🔄"},
            {"time": -32, "phase": "Discovery", "technique": "T1083", "description": "File and directory discovery performed", "icon": "🔍"},
            {"time": -30, "phase": "Lateral Movement", "technique": "T1021.002", "description": "SMB lateral movement to file server", "icon": "↔️"},
            {"time": -24, "phase": "Collection", "technique": "T1119", "description": "Automated data collection from shares", "icon": "📦"},
            {"time": -12, "phase": "Exfiltration", "technique": "T1041", "description": "Data exfiltration to external C2", "icon": "📤"},
            {"time": -6, "phase": "Impact", "technique": "T1486", "description": "Ransomware encryption initiated", "icon": "🔒"},
            {"time": -4, "phase": "Detection", "technique": "-", "description": "EDR detected mass file encryption", "icon": "🚨"},
            {"time": -3, "phase": "Containment", "technique": "-", "description": "Affected systems isolated from network", "icon": "🛡️"},
        ]
    },
    {
        "id": "INC-2024-0138",
        "title": "Credential Theft Attempt - IT Admin",
        "severity": "HIGH",
        "status": "Resolved",
        "start_time": datetime.now() - timedelta(hours=72),
        "timeline": [
            {"time": -72, "phase": "Initial Access", "technique": "T1078", "description": "Compromised VPN credentials used", "icon": "🔑"},
            {"time": -71, "phase": "Execution", "technique": "T1059.003", "description": "Command shell accessed via RDP", "icon": "💻"},
            {"time": -70, "phase": "Credential Access", "technique": "T1003.001", "description": "Mimikatz detected on endpoint", "icon": "🎭"},
            {"time": -69, "phase": "Detection", "technique": "-", "description": "EDR blocked credential dumping", "icon": "🚨"},
            {"time": -68, "phase": "Response", "technique": "-", "description": "Account disabled, password reset forced", "icon": "✅"},
        ]
    }
]

# Incident selector
incident_options = {f"{inc['id']} - {inc['title']}": inc for inc in INCIDENTS}
selected = st.selectbox("Select Incident", list(incident_options.keys()))
incident = incident_options[selected]

# Incident header
severity_colors = {"CRITICAL": "#FF0066", "HIGH": "#FF4444", "MEDIUM": "#FF8C00", "LOW": "#FFD700"}
status_colors = {"Contained": "#FF8C00", "Resolved": "#00C853", "Active": "#FF4444", "Investigating": "#00D4FF"}

st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(26,31,46,0.8), rgba(26,31,46,0.6));
    border: 1px solid {severity_colors.get(incident['severity'], '#FF4444')}40;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h2 style="color: #FAFAFA; margin: 0;">{incident['title']}</h2>
            <p style="color: #8B95A5; margin: 5px 0 0 0;">ID: {incident['id']} | Started: {incident['start_time'].strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        <div style="display: flex; gap: 10px;">
            <span style="background: {severity_colors.get(incident['severity'], '#FF4444')}; color: #000; padding: 8px 16px; border-radius: 20px; font-weight: bold;">{incident['severity']}</span>
            <span style="background: {status_colors.get(incident['status'], '#8B95A5')}; color: #000; padding: 8px 16px; border-radius: 20px; font-weight: bold;">{incident['status']}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Timeline visualization
st.markdown(section_title("Attack Timeline"), unsafe_allow_html=True)

for i, event in enumerate(incident["timeline"]):
    event_time = incident["start_time"] + timedelta(hours=event["time"] + 36)
    
    # Color based on phase type
    phase_colors = {
        "Initial Access": "#FF8C00",
        "Execution": "#FF4444",
        "Persistence": "#8B5CF6",
        "Discovery": "#00D4FF",
        "Lateral Movement": "#FF0066",
        "Collection": "#FFD700",
        "Exfiltration": "#FF4444",
        "Impact": "#FF0066",
        "Detection": "#00C853",
        "Containment": "#00C853",
        "Response": "#00C853",
        "Credential Access": "#FF4444"
    }
    
    color = phase_colors.get(event["phase"], "#8B95A5")
    
    st.markdown(f"""
    <div style="display: flex; margin: 0;">
        <div style="width: 150px; text-align: right; padding-right: 20px; color: #8B95A5; font-size: 0.85rem;">
            {event_time.strftime('%H:%M')}
            <br>
            <span style="font-size: 0.75rem;">{event_time.strftime('%Y-%m-%d')}</span>
        </div>
        <div style="width: 40px; display: flex; flex-direction: column; align-items: center;">
            <div style="
                width: 30px; height: 30px;
                background: {color};
                border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                font-size: 1rem;
            ">{event['icon']}</div>
            {"<div style='width: 2px; flex: 1; background: rgba(255,255,255,0.1);'></div>" if i < len(incident["timeline"]) - 1 else ""}
        </div>
        <div style="flex: 1; padding: 0 20px 30px;">
            <div style="
                background: rgba(26,31,46,0.5);
                border-left: 3px solid {color};
                padding: 15px;
                border-radius: 0 8px 8px 0;
            ">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: {color}; font-weight: bold;">{event['phase']}</span>
                    {f'<code style="background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 4px; color: #00D4FF;">{event["technique"]}</code>' if event["technique"] != "-" else ""}
                </div>
                <div style="color: #FAFAFA;">{event['description']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# MITRE ATT&CK Mapping
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_title("MITRE ATT&CK Coverage"), unsafe_allow_html=True)

techniques = [e for e in incident["timeline"] if e["technique"] != "-"]
if techniques:
    cols = st.columns(len(techniques))
    for i, tech in enumerate(techniques):
        with cols[i]:
            st.markdown(f"""
            <div style="
                background: rgba(0,212,255,0.1);
                border: 1px solid rgba(0,212,255,0.3);
                border-radius: 8px;
                padding: 10px;
                text-align: center;
            ">
                <div style="color: #00D4FF; font-weight: bold;">{tech['technique']}</div>
                <div style="color: #8B95A5; font-size: 0.8rem;">{tech['phase']}</div>
            </div>
            """, unsafe_allow_html=True)

# Export
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    df = pd.DataFrame(incident["timeline"])
    csv = df.to_csv(index=False)
    st.download_button("📥 Export Timeline (CSV)", csv, f"{incident['id']}_timeline.csv", "text/csv", use_container_width=True)

with col2:
    import json
    json_data = json.dumps({
        "incident_id": incident["id"],
        "title": incident["title"],
        "severity": incident["severity"],
        "timeline": incident["timeline"]
    }, indent=2, default=str)
    st.download_button("📋 Export (JSON)", json_data, f"{incident['id']}_timeline.json", "application/json", use_container_width=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Incident Timeline</p></div>', unsafe_allow_html=True)
