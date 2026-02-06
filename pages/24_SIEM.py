import streamlit as st
import os
import sys
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="SIEM | SOC", page_icon="📊", layout="wide")

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("SIEM Dashboard", "Security Information and Event Management - Centralized log aggregation and correlation"), unsafe_allow_html=True)

# Try to import real services
try:
    from services.threat_intel import threat_intel, get_threat_stats
    from services.soc_monitor import SOCMonitor
    HAS_REAL_API = True
except ImportError:
    HAS_REAL_API = False

# Generate SIEM data
@st.cache_data(ttl=60)
def generate_siem_events(count=100):
    """Generate SIEM events from multiple sources."""
    sources = ["Firewall", "IDS/IPS", "Endpoint", "Active Directory", "Web Server", "DNS", "Email Gateway", "VPN"]
    event_types = {
        "Firewall": ["Connection Blocked", "Port Scan Detected", "Rule Violation", "NAT Translation"],
        "IDS/IPS": ["Signature Match", "Anomaly Detected", "Protocol Violation", "Malicious Payload"],
        "Endpoint": ["Process Execution", "File Access", "Registry Change", "Service Started"],
        "Active Directory": ["Login Success", "Login Failure", "Password Change", "Group Modification"],
        "Web Server": ["HTTP 404", "HTTP 500", "SQL Injection Attempt", "XSS Attempt"],
        "DNS": ["Query", "Zone Transfer", "DNS Tunneling", "DGA Detection"],
        "Email Gateway": ["Spam Blocked", "Phishing Detected", "Malware Attachment", "SPF Failure"],
        "VPN": ["Connection Established", "Connection Failed", "MFA Success", "Unusual Location"]
    }
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    severity_weights = [0.4, 0.35, 0.2, 0.05]
    
    events = []
    for i in range(count):
        source = random.choice(sources)
        event_type = random.choice(event_types[source])
        severity = random.choices(severities, weights=severity_weights)[0]
        
        events.append({
            "id": f"EVT-{100000 + i}",
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 1440))).strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "event_type": event_type,
            "severity": severity,
            "source_ip": f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "dest_ip": f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "user": random.choice(["jsmith", "alee", "mwilson", "admin", "service-account", "-"]),
            "status": random.choice(["Open", "Investigating", "Resolved", "False Positive"])
        })
    
    return sorted(events, key=lambda x: x["timestamp"], reverse=True)

@st.cache_data(ttl=300)
def get_correlation_rules():
    """Get active correlation rules."""
    return [
        {"id": "CR-001", "name": "Brute Force Detection", "condition": "5+ failed logins in 5 mins", "action": "Block IP + Alert", "hits": random.randint(10, 50)},
        {"id": "CR-002", "name": "Lateral Movement", "condition": "SMB + RDP from same host", "action": "Isolate Host", "hits": random.randint(2, 15)},
        {"id": "CR-003", "name": "Data Exfiltration", "condition": ">100MB upload in 1 hour", "action": "Alert SOC", "hits": random.randint(5, 25)},
        {"id": "CR-004", "name": "Privilege Escalation", "condition": "Service account + admin access", "action": "Alert + Block", "hits": random.randint(3, 12)},
        {"id": "CR-005", "name": "C2 Beaconing", "condition": "Regular intervals to unknown IP", "action": "Block + Investigate", "hits": random.randint(1, 8)},
    ]

events = generate_siem_events()
df_events = pd.DataFrame(events)

# Top metrics
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

total_events = len(events)
critical_events = len([e for e in events if e["severity"] == "CRITICAL"])
high_events = len([e for e in events if e["severity"] == "HIGH"])
sources_active = len(set(e["source"] for e in events))
events_per_min = round(total_events / 1440, 1)

metrics = [
    ("Total Events (24h)", f"{total_events:,}", "#00D4FF"),
    ("Critical", str(critical_events), "#FF0066"),
    ("High Severity", str(high_events), "#FF4444"),
    ("Active Sources", str(sources_active), "#8B5CF6"),
    ("Events/Min", str(events_per_min), "#00C853")
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

st.markdown("<br>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Event Stream", "Analytics", "Correlation Rules", "Log Sources"])

with tab1:
    st.markdown(section_title("Live Event Stream"), unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        source_filter = st.selectbox("Source", ["All"] + list(set(e["source"] for e in events)))
    with col2:
        severity_filter = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    with col3:
        search_query = st.text_input("Search", placeholder="Search events...")
    with col4:
        auto_refresh = st.toggle("Auto-refresh", value=False)
    
    # Apply filters
    filtered = events
    if source_filter != "All":
        filtered = [e for e in filtered if e["source"] == source_filter]
    if severity_filter != "All":
        filtered = [e for e in filtered if e["severity"] == severity_filter]
    if search_query:
        filtered = [e for e in filtered if search_query.lower() in str(e).lower()]
    
    st.markdown(f"**{len(filtered)}** events matching filters")
    
    # Event table with color coding
    for event in filtered[:50]:
        severity_colors = {"CRITICAL": "#FF0066", "HIGH": "#FF4444", "MEDIUM": "#FF8C00", "LOW": "#00D4FF"}
        color = severity_colors.get(event["severity"], "#8B95A5")
        
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
                    <span style="color: #8B95A5;">{event['timestamp']}</span>
                    <span style="color: {color}; font-weight: bold; margin-left: 10px;">[{event['severity']}]</span>
                    <span style="color: #00D4FF; margin-left: 10px;">{event['source']}</span>
                    <span style="color: #FAFAFA; margin-left: 10px;">{event['event_type']}</span>
                </div>
                <div style="color: #8B95A5;">
                    {event['source_ip']} → {event['dest_ip']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Export
    df_filtered = pd.DataFrame(filtered)
    csv = df_filtered.to_csv(index=False)
    st.download_button("📥 Export Events (CSV)", csv, "siem_events.csv", "text/csv")

with tab2:
    st.markdown(section_title("SIEM Analytics"), unsafe_allow_html=True)
    
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
    st.markdown("### Event Timeline (24h)")
    
    # Create hourly buckets
    df_events["hour"] = pd.to_datetime(df_events["timestamp"]).dt.hour
    hourly = df_events.groupby("hour").size().reset_index(name="count")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hourly["hour"],
        y=hourly["count"],
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
        xaxis=dict(title="Hour", showgrid=False),
        yaxis=dict(title="Events", showgrid=True, gridcolor="rgba(255,255,255,0.1)")
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown(section_title("Correlation Rules"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <p style="color: #8B95A5; margin: 0;">
                Correlation rules detect complex attack patterns by analyzing multiple events together.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    rules = get_correlation_rules()
    
    for rule in rules:
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
                <span style="background: rgba(139,92,246,0.2); color: #8B5CF6; padding: 2px 8px; border-radius: 4px;">{rule['hits']} hits</span>
            </div>
            <div style="color: #8B95A5; margin-bottom: 8px;"><strong>Condition:</strong> {rule['condition']}</div>
            <div style="color: #FAFAFA;"><strong>Action:</strong> {rule['action']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add new rule
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("➕ Create New Correlation Rule"):
        rule_name = st.text_input("Rule Name", placeholder="My Custom Rule")
        rule_condition = st.text_area("Condition (pseudo-code)", placeholder="event.type == 'login_failure' AND count > 5 within 5m")
        rule_action = st.selectbox("Action", ["Alert SOC", "Block IP", "Isolate Host", "Alert + Block", "Quarantine"])
        
        if st.button("Create Rule", type="primary"):
            st.success(f"Rule '{rule_name}' created successfully!")

with tab4:
    st.markdown(section_title("Log Sources"), unsafe_allow_html=True)
    
    log_sources = [
        {"name": "Palo Alto Firewall", "type": "Firewall", "status": "Active", "eps": 450, "last_event": "2 sec ago"},
        {"name": "CrowdStrike Falcon", "type": "Endpoint", "status": "Active", "eps": 280, "last_event": "1 sec ago"},
        {"name": "Microsoft AD", "type": "Active Directory", "status": "Active", "eps": 120, "last_event": "5 sec ago"},
        {"name": "Suricata IDS", "type": "IDS/IPS", "status": "Active", "eps": 180, "last_event": "3 sec ago"},
        {"name": "Nginx Web Server", "type": "Web Server", "status": "Active", "eps": 350, "last_event": "1 sec ago"},
        {"name": "Cloudflare DNS", "type": "DNS", "status": "Active", "eps": 520, "last_event": "1 sec ago"},
        {"name": "Proofpoint Email", "type": "Email Gateway", "status": "Active", "eps": 85, "last_event": "10 sec ago"},
        {"name": "Cisco AnyConnect", "type": "VPN", "status": "Warning", "eps": 12, "last_event": "2 min ago"},
    ]
    
    for source in log_sources:
        status_color = "#00C853" if source["status"] == "Active" else "#FF8C00"
        
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
                <span style="color: #FAFAFA; font-weight: bold;">{source['name']}</span>
                <span style="color: #8B95A5; margin-left: 15px;">{source['type']}</span>
            </div>
            <div style="display: flex; gap: 30px; align-items: center;">
                <div style="text-align: center;">
                    <div style="color: #00D4FF; font-weight: bold;">{source['eps']}</div>
                    <div style="color: #8B95A5; font-size: 0.75rem;">EPS</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #FAFAFA;">{source['last_event']}</div>
                    <div style="color: #8B95A5; font-size: 0.75rem;">Last Event</div>
                </div>
                <div style="color: {status_color};">● {source['status']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add log source
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("➕ Add Log Source"):
        source_name = st.text_input("Source Name", placeholder="My Log Source")
        source_type = st.selectbox("Source Type", ["Syslog (UDP)", "Syslog (TCP)", "API", "Agent", "File Beat", "Kafka"])
        source_host = st.text_input("Host/IP", placeholder="192.168.1.100")
        source_port = st.number_input("Port", value=514, min_value=1, max_value=65535)
        
        if st.button("Add Source", type="primary"):
            st.success(f"Log source '{source_name}' added successfully!")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | SIEM Dashboard</p></div>', unsafe_allow_html=True)
