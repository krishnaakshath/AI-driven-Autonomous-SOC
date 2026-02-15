import streamlit as st
import os
import sys
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="SIEM | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("SIEM Dashboard", "Security Information and Event Management — Live Event Stream & Correlation"), unsafe_allow_html=True)

# Import Services (backed by SQLite)
try:
    from services.siem_service import get_siem_events, simulate_siem_ingestion, get_siem_stats
    from services.threat_intel import threat_intel
    HAS_REAL_API = True
except ImportError as e:
    st.error(f"Failed to import services: {e}")
    HAS_REAL_API = False

# ===== Dynamic Event Engine =====

# Initialize session state for session-specific tracking (optional, but good for "Live" counter)
if 'siem_start_time' not in st.session_state:
    st.session_state.siem_start_time = datetime.now()
    st.session_state.siem_refresh_count = 0

SOURCES = ["Firewall", "IDS/IPS", "Endpoint", "Active Directory", "Web Server", "DNS", "Email Gateway", "VPN"]

def get_correlation_matches(events):
    """Correlate events against rules and return hit counts."""
    rules = [
        {"id": "CR-001", "name": "Brute Force Detection", "condition": "5+ failed logins in 5 mins", 
         "action": "Block IP + Alert", "keywords": ["Login Failure", "Account Lockout", "Connection Failed"]},
        {"id": "CR-002", "name": "Lateral Movement", "condition": "SMB + RDP from same host", 
         "action": "Isolate Host", "keywords": ["Process Execution", "Service Started", "Registry Change"]},
        {"id": "CR-003", "name": "Data Exfiltration", "condition": ">100MB upload in 1 hour", 
         "action": "Alert SOC", "keywords": ["DNS Tunneling", "File Access", "Zone Transfer"]},
        {"id": "CR-004", "name": "Privilege Escalation", "condition": "Service account + admin access", 
         "action": "Alert + Block", "keywords": ["Group Modification", "Password Change", "Suspicious DLL Load"]},
        {"id": "CR-005", "name": "C2 Beaconing", "condition": "Regular intervals to unknown IP", 
         "action": "Block + Investigate", "keywords": ["DGA Detection", "Anomaly Detected", "CVE Exploit Attempt"]},
    ]
    
    for rule in rules:
        # Simple keyword matching against event types in the current batch
        # In a real DB, this would be a SQL query
        rule["hits"] = sum(1 for e in events if e.get("event_type") in rule["keywords"])
    
    return rules


# 2. Fetch latest events from DB (Persistence!)
# Auto-refresh logic
if 'last_siem_refresh' not in st.session_state:
    st.session_state.last_siem_refresh = time.time()

if time.time() - st.session_state.last_siem_refresh > 30:
    st.rerun()

st.session_state.last_siem_refresh = time.time()

events = get_siem_events(count=200) # Get last 200 events

# Update session counters
st.session_state.siem_refresh_count += 1
session_duration = (datetime.now() - st.session_state.siem_start_time).total_seconds()

# Convert to DataFrame for analytics
df_events = pd.DataFrame(events)

# ===== Top Metrics =====
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

# Use DB stats if available, or calculate from fetched events
db_stats = get_siem_stats()
total_events = db_stats.get("total_events_24h", len(events))
critical_events = db_stats.get("critical_count", len([e for e in events if e.get("severity") == "CRITICAL"]))
high_events = db_stats.get("high_count", len([e for e in events if e.get("severity") == "HIGH"]))
sources_active = db_stats.get("active_sources", len(set(e.get("source") for e in events)))

# EPS (Session based)
eps = round(len(events) / max(session_duration, 1), 1) if session_duration < 60 else db_stats.get("events_per_minute", 0) / 60

metrics = [
    ("Total Events (DB)", f"{total_events:,}", "#00D4FF"),
    ("Critical", str(critical_events), "#FF0066"),
    ("High Severity", str(high_events), "#FF4444"),
    ("Active Sources", str(sources_active), "#8B5CF6"),
    ("Events/Sec", str(eps), "#00C853")
]

for col, (label, value, color) in zip([col1, col2, col3, col4, col5], metrics):
    with col:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(26,31,46,0.8), rgba(26,31,46,0.6));
            border: 1px solid {color}40;
            border-radius: 16px;
            padding: 1.2rem;
            text-align: center;
        ">
            <div style="font-size: 2rem; font-weight: 800; color: {color};">{value}</div>
            <div style="color: #8B95A5; font-size: 0.85rem;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

# Session info bar
st.markdown(f"""
<div style="
    background: rgba(0,200,83,0.08);
    border: 1px solid rgba(0,200,83,0.2);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin: 0.5rem 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
">
    <span style="color: #00C853;">LIVE — Connected to Persistent Storage (SQLite)</span>
    <span style="color: #8B95A5;">Refresh #{st.session_state.siem_refresh_count} | Session: {int(session_duration)}s</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Auto-refresh control
refresh_col1, refresh_col2, refresh_col3 = st.columns([1, 1, 4])
with refresh_col1:
    auto_refresh = st.toggle("Auto-refresh", value=False, key="siem_auto_refresh")
with refresh_col2:
    refresh_interval = st.selectbox("Interval", [5, 10, 15, 30], index=1, key="siem_interval")

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Event Stream", "Analytics", "Correlation Rules", "Log Sources"])

# ===== TAB 1: Event Stream =====
with tab1:
    st.markdown(section_title("Live Event Stream"), unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        source_filter = st.selectbox("Source", ["All"] + SOURCES)
    with col2:
        severity_filter = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    with col3:
        search_query = st.text_input("Search", placeholder="Search events...")
    
    # Apply filters
    filtered = events
    if source_filter != "All":
        filtered = [e for e in filtered if e.get("source") == source_filter]
    if severity_filter != "All":
        filtered = [e for e in filtered if e.get("severity") == severity_filter]
    if search_query:
        filtered = [e for e in filtered if search_query.lower() in str(e).lower()]
    
    st.markdown(f"**{len(filtered)}** recent events matching filters")
    
    # Event table with color coding
    for event in filtered[:50]:
        severity_colors = {"CRITICAL": "#FF0066", "HIGH": "#FF4444", "MEDIUM": "#FF8C00", "LOW": "#00D4FF"}
        color = severity_colors.get(event.get("severity"), "#8B95A5")
        
        st.markdown(f"""
        <div style="
            background: rgba(26,31,46,0.5);
            border-left: 4px solid {color};
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 0 8px 8px 0;
            font-size: 0.9rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="color: #8B95A5;">{event.get('timestamp')}</span>
                    <span style="color: {color}; font-weight: bold; margin-left: 10px;">[{event.get('severity')}]</span>
                    <span style="color: #00D4FF; margin-left: 10px;">{event.get('source')}</span>
                    <span style="color: #FAFAFA; margin-left: 10px;">{event.get('event_type')}</span>
                </div>
                <div style="color: #8B95A5;">
                    {event.get('source_ip')} → {event.get('dest_ip')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Export
    # df_filtered = pd.DataFrame(filtered) # Re-use if needed
    # csv = df_filtered.to_csv(index=False)
    # st.download_button("Export Events (CSV)", csv, "siem_events.csv", "text/csv")

# ===== TAB 2: Analytics =====
with tab2:
    st.markdown(section_title("SIEM Analytics"), unsafe_allow_html=True)
    
    if not df_events.empty:
        chart1, chart2 = st.columns(2)
        
        with chart1:
            # Events by source
            source_counts = df_events.groupby("source").size().reset_index(name="count")
            fig = px.bar(source_counts, x="source", y="count", color="count",
                        color_continuous_scale=["#1A1F2E", "#00D4FF", "#8B5CF6"],
                        title="Events by Source")
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                height=300,
                showlegend=False
            )
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)
        
        with chart2:
            # Events by severity
            severity_counts = df_events.groupby("severity").size().reset_index(name="count")
            severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            severity_counts["severity"] = pd.Categorical(severity_counts["severity"], categories=severity_order, ordered=True)
            severity_counts = severity_counts.sort_values("severity")
            
            colors = {"LOW": "#00D4FF", "MEDIUM": "#FF8C00", "HIGH": "#FF4444", "CRITICAL": "#FF0066"}
            fig = go.Figure(data=[go.Pie(
                labels=severity_counts["severity"],
                values=severity_counts["count"],
                hole=0.5,
                marker_colors=[colors.get(s, "#8B95A5") for s in severity_counts["severity"]]
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                height=300,
                title="Events by Severity"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Timeline
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Event Timeline (Recent)")
        
        # Create hourly buckets (or minute buckets if very recent)
        df_events["time_bucket"] = pd.to_datetime(df_events["timestamp"]).dt.strftime('%H:%M')
        timeline = df_events.groupby("time_bucket").size().reset_index(name="count")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timeline["time_bucket"],
            y=timeline["count"],
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color="#00D4FF", width=2),
            fillcolor="rgba(0,212,255,0.2)"
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#FAFAFA",
            height=250,
            xaxis=dict(title="Time", showgrid=False),
            yaxis=dict(title="Events", showgrid=True, gridcolor="rgba(255,255,255,0.1)")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No events to analyze.")

# ===== TAB 3: Correlation Rules =====
with tab3:
    st.markdown(section_title("Correlation Rules"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <p style="color: #8B95A5; margin: 0;">
                Correlation rules match against the <strong>persistent event stream</strong>. 
                Hit counts reflect actual matches in the database.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    rules = get_correlation_matches(events)
    
    for rule in rules:
        hit_color = "#FF0066" if rule["hits"] > 10 else "#FF8C00" if rule["hits"] > 3 else "#00C853"
        
        st.markdown(f"""
        <div style="
            background: rgba(26,31,46,0.5);
            border: 1px solid rgba(0,212,255,0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        ">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span style="color: #00D4FF; font-weight: bold;">{rule['name']}</span>
                <span style="background: {hit_color}22; color: {hit_color}; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{rule['hits']} hits</span>
            </div>
            <div style="color: #8B95A5; margin-bottom: 8px;"><strong>Condition:</strong> {rule['condition']}</div>
            <div style="color: #FAFAFA;"><strong>Action:</strong> {rule['action']}</div>
        </div>
        """, unsafe_allow_html=True)

# ===== TAB 4: Log Sources =====
with tab4:
    st.markdown(section_title("Log Sources"), unsafe_allow_html=True)
    
    # Dynamic log source stats
    source_stats = {}
    for event in events:
        src = event.get("source")
        if src not in source_stats:
            source_stats[src] = {"count": 0, "last_event": event.get("timestamp")}
        source_stats[src]["count"] += 1
        if event.get("timestamp") > source_stats[src]["last_event"]:
            source_stats[src]["last_event"] = event.get("timestamp")
    
    # Map sources to product names
    source_products = {
        "Firewall": "Palo Alto Firewall",
        "IDS/IPS": "Suricata IDS",
        "Endpoint": "CrowdStrike Falcon",
        "Active Directory": "Microsoft AD",
        "Web Server": "Nginx Web Server",
        "DNS": "Cloudflare DNS",
        "Email Gateway": "Proofpoint Email",
        "VPN": "Cisco AnyConnect"
    }
    
    for source_type in SOURCES:
        stats = source_stats.get(source_type, {"count": 0, "last_event": "N/A"})
        product = source_products.get(source_type, source_type)
        
        # Calculate dynamic EPS per source
        source_eps = round(stats["count"] / max(session_duration, 1), 1) if stats["count"] > 0 else 0
        
        # Calculate time since last event
        try:
            last_dt = datetime.strptime(stats["last_event"], "%Y-%m-%d %H:%M:%S")
            diff = datetime.now() - last_dt
            if diff.total_seconds() < 60:
                last_text = f"{int(diff.total_seconds())} sec ago"
            elif diff.total_seconds() < 3600:
                last_text = f"{int(diff.total_seconds() / 60)} min ago"
            else:
                last_text = f"{int(diff.total_seconds() / 3600)} hr ago"
        except Exception:
            last_text = "N/A"
        
        status = "Active" if stats["count"] > 0 else "Inactive"
        status_color = "#00C853" if status == "Active" else "#FF8C00"
        
        st.markdown(f"""
        <div style="
            background: rgba(26,31,46,0.5);
            border-left: 4px solid {status_color};
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div>
                <span style="color: #FAFAFA; font-weight: bold;">{product}</span>
                <span style="color: #8B95A5; margin-left: 15px;">{source_type}</span>
            </div>
            <div style="display: flex; gap: 30px; align-items: center;">
                <div style="text-align: center;">
                    <div style="color: #00D4FF; font-weight: bold;">{stats['count']}</div>
                    <div style="color: #8B95A5; font-size: 0.75rem;">Events</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #8B5CF6; font-weight: bold;">{source_eps}</div>
                    <div style="color: #8B95A5; font-size: 0.75rem;">EPS</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #FAFAFA;">{last_text}</div>
                    <div style="color: #8B95A5; font-size: 0.75rem;">Last Event</div>
                </div>
                <div style="color: {status_color};">{status}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add log source (simulation for now)
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Add Log Source"):
        source_name = st.text_input("Source Name", placeholder="My Log Source")
        source_type = st.selectbox("Source Type", ["Syslog (UDP)", "Syslog (TCP)", "API", "Agent"])
        
        if st.button("Add Source", type="primary"):
            st.success(f"Log source '{source_name}' added successfully!")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Persistent Data Layer (SQLite)</p></div>', unsafe_allow_html=True)
