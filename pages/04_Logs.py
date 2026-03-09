import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import random
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Log Viewer | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

# Session state for log persistence
if 'log_entries' not in st.session_state:
    st.session_state.log_entries = []
if 'log_refresh_counter' not in st.session_state:
    st.session_state.log_refresh_counter = 0

# Header with Refresh button
h_col1, h_col2 = st.columns([5, 1])
with h_col1:
    st.markdown(page_header("Real-Time Log Viewer", "Live streaming logs from all security sources"), unsafe_allow_html=True)
with h_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Fetch Latest", use_container_width=True):
        st.cache_data.clear()
        st.session_state.log_refresh_counter += 1
        st.rerun()

# Import SIEM service for real data
try:
    from services.siem_service import get_siem_logs, get_siem_stats
    from services.database import db
    HAS_SIEM = True
except ImportError:
    HAS_SIEM = False

# Show data source
if HAS_SIEM:
    try:
        stats = get_siem_stats()
        st.success(f" Connected to SIEM - {stats.get('total_events_24h', 0)} events analyzed | Indexing active")
    except Exception:
        st.success(" Connected to SIEM Infrastructure")
else:
    st.warning(" SIEM not available - Using fallback logging simulation")

# Log sources
LOG_SOURCES = ["Firewall", "IDS/IPS", "WAF", "Endpoint", "Authentication", "Network", "Application", "Cloud"]
SEVERITY_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
SEVERITY_COLORS = {
    "DEBUG": "#8B95A5",
    "INFO": "#00D4FF",
    "WARNING": "#FF8C00",
    "ERROR": "#FF4444",
    "CRITICAL": "#FF0066"
}

# Generate realistic log entries
def generate_log_entry():
    # Deprecated: We now only use real SIEM DB events
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "source": "System",
        "severity": "INFO",
        "message": "Waiting for SIEM database ingestion...",
        "event_id": f"EVT-WAIT"
    }

# Filters
st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])

with col1:
    selected_sources = st.multiselect("Sources", LOG_SOURCES, default=LOG_SOURCES)

with col2:
    selected_severity = st.multiselect("Severity", SEVERITY_LEVELS, default=["WARNING", "ERROR", "CRITICAL"])

with col3:
    search_query = st.text_input("Deep Search", placeholder="Filter by IP, user, or threat pattern...")

with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    use_regex = st.toggle("RegEx", value=False, help="Enable Regular Expression searching")

with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    auto_refresh = st.toggle("Auto-Live", value=False, help="Automatically refreshes every 30 seconds")

# Function to generate logs or fetch from SIEM
@st.cache_data(ttl=1)
def fetch_logs(refresh_id=0):
    if HAS_SIEM:
        # Fetch real logs from DB
        real_logs = db.get_recent_events(limit=500)
        
        if not real_logs:
            # Tell user to trigger ingestion
            return [generate_log_entry()]
            
        # Convert to format expected by UI
        formatted_logs = []
        for log in real_logs:
            formatted_logs.append({
                "timestamp": log.get("timestamp"),
                "source": log.get("source") or "Unknown",
                "severity": log.get("severity") or "INFO",
                "message": f"{log.get('event_type', 'LOG')} - {log.get('details', '') or log.get('source_ip', 'Internal')}",
                "event_id": log.get("id") or f"ID-unknown"
            })
        return formatted_logs
    else:
        # No DB Connection
        return [generate_log_entry()]

st.session_state.log_entries = fetch_logs(st.session_state.log_refresh_counter)

# Filter logs
import re

filtered_logs = []
for log in st.session_state.log_entries:
    if log['source'] not in selected_sources or log['severity'] not in selected_severity:
        continue
        
    if search_query:
        if use_regex:
            try:
                if not re.search(search_query, str(log), re.IGNORECASE):
                    continue
            except re.error:
                # Invalid regex, fallback to nothing or normal search
                pass
        else:
            if search_query.lower() not in str(log).lower():
                continue
                
    filtered_logs.append(log)

# Display live indicator
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 10px; margin: 1rem 0; background: rgba(0,212,255,0.05); padding: 10px; border-radius: 8px; border-left: 2px solid #00D4FF;">
    <span style="width: 10px; height: 10px; background: {('#00FF00' if auto_refresh else '#8B95A5')}; border-radius: 50%; animation: {('pulse 1s infinite' if auto_refresh else 'none')};"></span>
    <span style="color: {('#00FF00' if auto_refresh else '#8B95A5')}; font-family: monospace; font-weight: bold;">{('STREAMING' if auto_refresh else 'PAUSED')}</span>
    <span style="color: #333;">|</span>
    <span style="color: #FAFAFA; font-size: 0.9rem;">{len(filtered_logs)} Events in view</span>
</div>
<style>@keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}</style>
""", unsafe_allow_html=True)

# Log display
st.markdown("""
<div style="
    background: #020617;
    border: 1px solid rgba(0,212,255,0.1);
    border-radius: 12px;
    padding: 5px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.8rem;
    max-height: 600px;
    overflow-y: auto;
">
""", unsafe_allow_html=True)

import json
for log in filtered_logs[:100]:
    color = SEVERITY_COLORS.get(log['severity'], "#FFFFFF")
    log_json = json.dumps(log, indent=2).replace("<", "&lt;").replace(">", "&gt;")
    
    st.markdown(f"""
    <div style="
        padding: 6px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.03);
        display: flex;
        flex-direction: column;
        gap: 4px;
    ">
        <div style="display: flex; gap: 12px; align-items: baseline;">
            <span style="color: #475569; min-width: 100px;">{log['timestamp']}</span>
            <span style="color: #38BDF8; min-width: 110px;">[{log['source']}]</span>
            <span style="color: {color}; min-width: 70px; font-weight: bold;">{log['severity']}</span>
            <span style="color: #CBD5E1; word-break: break-all;">{log['message']}</span>
        </div>
        <details style="cursor: pointer; margin-left: 232px;">
            <summary style="color: #8B95A5; font-size: 0.70rem; outline: none;">View JSON</summary>
            <pre style="background: rgba(0,0,0,0.5); padding: 8px; border-radius: 4px; color: #A78BFA; margin-top: 5px; overflow-x: auto; font-size: 0.75rem; border: 1px solid rgba(139,92,246,0.2);">{log_json}</pre>
        </details>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Export and Actions
st.markdown("<br>", unsafe_allow_html=True)
col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 2])

with col_exp1:
    if filtered_logs:
        df = pd.DataFrame(filtered_logs)
        csv = df.to_csv(index=False)
        st.download_button("💾 Export Current View (CSV)", csv, "security_logs.csv", "text/csv", use_container_width=True)

with col_exp2:
    if st.button("🗑️ Clear Cache", use_container_width=True):
        st.session_state.log_entries = []
        st.cache_data.clear()
        st.rerun()

# Non-blocking auto-refresh simulation
if auto_refresh:
    time.sleep(30)
    st.rerun()

st.markdown("---")
st.markdown('<div style="text-align: center; color: #475569;"><p>AI-Driven Autonomous SOC | Intelligent Log Analyzer | Build 2024.2.1</p></div>', unsafe_allow_html=True)
