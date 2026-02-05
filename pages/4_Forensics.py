import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Forensics | SOC", page_icon="F", layout="wide")

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()


# Authentication removed - public dashboard

st.markdown(page_header("Digital Forensics", "Deep analysis and incident investigation"), unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["Incident Analysis", "Timeline", "Evidence"])

with tab1:
    st.markdown(section_title("Recent Incidents"), unsafe_allow_html=True)
    
    incidents = [
        {"id": "INC-2024-001", "type": "Ransomware", "status": "Active", "severity": "CRITICAL", "time": "2h ago"},
        {"id": "INC-2024-002", "type": "Data Breach", "status": "Investigating", "severity": "HIGH", "time": "5h ago"},
        {"id": "INC-2024-003", "type": "Malware", "status": "Contained", "severity": "MEDIUM", "time": "1d ago"},
    ]
    
    for inc in incidents:
        sev_color = {"CRITICAL": "#FF4444", "HIGH": "#FF8C00", "MEDIUM": "#FFD700"}.get(inc["severity"], "#8B95A5")
        st.markdown(f"""
            <div class="glass-card" style="margin: 0.8rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: {sev_color}; font-weight: 700; font-size: 0.75rem; text-transform: uppercase;">{inc['severity']}</span>
                        <h4 style="color: #FAFAFA; margin: 0.3rem 0;">{inc['id']} - {inc['type']}</h4>
                        <span style="color: #8B95A5;">Status: {inc['status']}</span>
                    </div>
                    <span style="color: #8B95A5;">{inc['time']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(section_title("Analysis Tools"), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="glass-card">
                <h4 style="color: #00D4FF; margin: 0 0 1rem 0;">Memory Analysis</h4>
                <p style="color: #8B95A5; margin: 0;">Analyze memory dumps for malware artifacts</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class="glass-card">
                <h4 style="color: #8B5CF6; margin: 0 0 1rem 0;">Disk Forensics</h4>
                <p style="color: #8B95A5; margin: 0;">Examine file systems and deleted files</p>
            </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown(section_title("Attack Timeline"), unsafe_allow_html=True)
    
    events = [
        {"time": "09:15:32", "event": "Initial access via phishing email", "type": "Initial Access"},
        {"time": "09:18:45", "event": "Malicious payload executed", "type": "Execution"},
        {"time": "09:22:11", "event": "Privilege escalation detected", "type": "Privilege Escalation"},
        {"time": "09:25:00", "event": "Lateral movement to server", "type": "Lateral Movement"},
        {"time": "09:30:22", "event": "Data exfiltration attempt blocked", "type": "Exfiltration"},
    ]
    
    for i, evt in enumerate(events):
        st.markdown(f"""
            <div style="display: flex; margin: 1rem 0;">
                <div style="display: flex; flex-direction: column; align-items: center; margin-right: 1.5rem;">
                    <div style="width: 16px; height: 16px; background: linear-gradient(135deg, #00D4FF, #8B5CF6); border-radius: 50%;"></div>
                    {'<div style="width: 2px; height: 60px; background: rgba(0, 212, 255, 0.3);"></div>' if i < len(events)-1 else ''}
                </div>
                <div class="glass-card" style="flex: 1;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #00D4FF; font-weight: 600;">{evt['type']}</span>
                        <span style="color: #8B95A5; font-family: monospace;">{evt['time']}</span>
                    </div>
                    <p style="color: #FAFAFA; margin: 0.5rem 0 0 0;">{evt['event']}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown(section_title("Evidence Collection"), unsafe_allow_html=True)
    
    evidence = [
        {"name": "memory_dump_001.raw", "size": "4.2 GB", "type": "Memory", "hash": "a1b2c3d4..."},
        {"name": "disk_image_server01.dd", "size": "120 GB", "type": "Disk", "hash": "e5f6g7h8..."},
        {"name": "network_capture.pcap", "size": "850 MB", "type": "Network", "hash": "i9j0k1l2..."},
    ]
    
    for ev in evidence:
        st.markdown(f"""
            <div class="glass-card" style="margin: 0.5rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #FAFAFA; font-weight: 600;">{ev['name']}</span>
                        <div style="display: flex; gap: 1.5rem; margin-top: 0.3rem;">
                            <span style="color: #8B95A5; font-size: 0.85rem;">Size: {ev['size']}</span>
                            <span style="color: #8B95A5; font-size: 0.85rem;">Type: {ev['type']}</span>
                            <span style="color: #00D4FF; font-size: 0.85rem; font-family: monospace;">Hash: {ev['hash']}</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Forensics</p></div>', unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
