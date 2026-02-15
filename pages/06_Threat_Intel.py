import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Threat Intelligence | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

from services.threat_intel import get_latest_threats

# Authentication removed - public dashboard

st.markdown(page_header("Threat Intelligence", "Global threat landscape and geographic analysis"), unsafe_allow_html=True)

# Auto-refresh every 30 seconds
import time
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# Refresh button and auto-refresh indicator
col_refresh, col_time = st.columns([1, 3])
with col_refresh:
    if st.button("Refresh Now", type="primary"):
        st.session_state.force_refresh_next_run = True
        st.session_state.last_refresh = time.time()
        st.rerun()

with col_time:
    st.markdown(f'''
        <div style="display: flex; align-items: center; gap: 0.5rem; height: 38px;">
            <span style="color: #0aff0a;"></span>
            <span style="color: #8B95A5; font-family: 'Share Tech Mono', monospace;">LIVE FEED // AUTO-REFRESH 5min</span>
        </div>
    ''', unsafe_allow_html=True)

# Auto-refresh logic (every 5 minutes)
if time.time() - st.session_state.last_refresh > 300:
    st.session_state.force_refresh_next_run = True
    st.session_state.last_refresh = time.time()
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Generate threat data with attack connections
def get_threat_data(refresh=False):
    from services.threat_intel import threat_intel
    
    # Base coordinates for major threat sources
    coords = {
        "China": {"lat": 35.86, "lon": 104.19, "severity": "critical"},
        "Russia": {"lat": 61.52, "lon": 105.31, "severity": "critical"},
        "United States": {"lat": 37.09, "lon": -95.71, "severity": "medium"},
        "Iran": {"lat": 32.42, "lon": 53.68, "severity": "high"},
        "North Korea": {"lat": 40.33, "lon": 127.51, "severity": "critical"},
        "Brazil": {"lat": -14.23, "lon": -51.92, "severity": "low"},
        "India": {"lat": 20.59, "lon": 78.96, "severity": "medium"},
        "Ukraine": {"lat": 48.37, "lon": 31.16, "severity": "high"},
        "Germany": {"lat": 51.16, "lon": 10.45, "severity": "low"},
        "Netherlands": {"lat": 52.13, "lon": 5.29, "severity": "low"},
        "Vietnam": {"lat": 14.05, "lon": 108.27, "severity": "medium"},
        "France": {"lat": 46.22, "lon": 2.21, "severity": "low"},
        "Israel": {"lat": 31.04, "lon": 34.85, "severity": "medium"},
        "United Kingdom": {"lat": 55.37, "lon": -3.43, "severity": "low"}
    }
    
    # Target location (your SOC - e.g., headquarters)
    target = {"lat": 20.59, "lon": 78.96, "name": "SOC HQ"}  # India as SOC location
    
    # Fetch real counts
    counts = threat_intel.get_country_threat_counts(force_refresh=refresh)
    
    results = {}
    for country, params in coords.items():
        count = counts.get(country, 0)
        
        # Determine severity based on count
        if count > 10:
            severity = "critical"
        elif count > 5:
            severity = "high"
        elif count > 2:
            severity = "medium"
        else:
            severity = "low"
        
        results[country] = {
            "lat": params["lat"],
            "lon": params["lon"], 
            "threats": count * 10 if count > 0 else 0,
            "real_count": count,
            "severity": severity
        }
    
    return results, target

# Call site
refresh_needed = st.session_state.get('force_refresh_next_run', False)
threats, target = get_threat_data(refresh=refresh_needed)
if refresh_needed:
    st.session_state.force_refresh_next_run = False

# Stats
# Fetch SIEM Blocked Count (Real-Time from Background Service)
try:
    from services.database import db
    siem_stats = db.get_stats()
    blocked_today = siem_stats.get('critical', 0) + siem_stats.get('high', 0) # Approximation of blocks
except:
    blocked_today = 0

total = sum([c["real_count"] for c in threats.values()])
if total == 0:
    top_country = ("N/A", {"threats": 0, "real_count": 0})
else:
    top_country = max(threats.items(), key=lambda x: x[1]["real_count"])

critical_count = len([c for c in threats.values() if c["severity"] == "critical"])
high_count = len([c for c in threats.values() if c["severity"] == "high"])

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #ff003c;">{total:,}</p><p class="metric-label">Global Threats (OTX)</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #ff6b00;">{blocked_today}</p><p class="metric-label">Blocked Today (SIEM)</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00f3ff;">{top_country[0][:10]}</p><p class="metric-label">Top Global Source</p></div>', unsafe_allow_html=True)
with c4:
    active_countries = len([c for c in threats.values() if c["real_count"] > 0])
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #bc13fe;">{active_countries}</p><p class="metric-label">Active Regions</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 3D HOLOGRAPHIC THREAT GLOBE
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('''
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 1.5rem;">
        <span style="font-size: 1.5rem;"></span>
        <h3 style="
            margin: 0; 
            color: #00f3ff; 
            font-family: 'Orbitron', sans-serif;
            font-size: 1rem;
            text-transform: uppercase; 
            letter-spacing: 4px;
            text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
        ">GLOBAL THREAT HOLOGRAPH</h3>
    </div>
''', unsafe_allow_html=True)

# Severity colors matching the reference image
severity_colors = {
    "critical": "#ff003c",  # Red
    "high": "#ff6b00",      # Orange
    "medium": "#f0ff00",    # Yellow
    "low": "#0aff0a"        # Green
}

fig = go.Figure()

# Layer 1: The Globe Base (Dark, Holographic)
fig.add_trace(go.Scattergeo(
    lon=[], lat=[],
    mode='markers',
    marker=dict(size=0, color='rgba(0,0,0,0)')
))

# Layer 2: Attack Arcs (3D Trajectories)
for country, data in threats.items():
    if data["real_count"] > 0:
        color = severity_colors.get(data["severity"], "#00f3ff")
        
        # Add 3D Arcs (Great Circle)
        fig.add_trace(go.Scattergeo(
            lat=[data["lat"], target["lat"]],
            lon=[data["lon"], target["lon"]],
            mode='lines',
            line=dict(
                width=2,
                color=color,
            ),
            opacity=0.7,
            hoverinfo='skip',
            showlegend=False
        ))

# Layer 3: Source Markers (Pulsing Orbs)
for country, data in threats.items():
    if data["real_count"] > 0:
        color = severity_colors.get(data["severity"], "#00f3ff")
        
        fig.add_trace(go.Scattergeo(
            lat=[data["lat"]],
            lon=[data["lon"]],
            mode='markers+text',
            marker=dict(
                size=10 + (data["real_count"] / 5),
                color=color,
                opacity=0.9,
                line=dict(width=2, color='white'),
                symbol='circle'
            ),
            text=country if data["severity"] == "critical" else "",
            textposition="top center",
            textfont=dict(family="Orbitron", size=10, color=color),
            hovertemplate=f"<b>{country}</b><br>Threats: {data['real_count']}<br>Severity: {data['severity'].upper()}<extra></extra>",
            showlegend=False
        ))

# Layer 4: Target Marker (SOC HQ)
fig.add_trace(go.Scattergeo(
    lat=[target["lat"]],
    lon=[target["lon"]],
    mode='markers',
    marker=dict(
        size=20,
        color='#0aff0a',
        opacity=1,
        symbol='diamond-tall',
        line=dict(width=3, color='white')
    ),
    hovertemplate="<b>SOC HEADQUARTERS</b><br>Status: ONLINE<extra></extra>",
    showlegend=False
))

# 3D Orthographic Layout (The "Iron Man" Look)
fig.update_geos(
    projection_type="orthographic",
    showland=True,
    landcolor="rgba(10, 20, 40, 0.8)",
    showocean=True,
    oceancolor="rgba(2, 5, 10, 0.8)",
    showcountries=True,
    countrycolor="rgba(0, 243, 255, 0.3)",
    showlakes=False,
    showcoastlines=True,
    coastlinecolor="rgba(0, 243, 255, 0.5)",
    projection_rotation=dict(lon=time.time() % 360, lat=20), # Auto-rotation handled by Streamlit rerun
    bgcolor='rgba(0,0,0,0)'
)

fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    height=600,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    showlegend=False,
    scene=dict(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        zaxis=dict(visible=False)
    )
)

# Render with FULL INTERACTIVE CONTROLS
st.plotly_chart(
    fig, 
    use_container_width=True, 
    config={
        'displayModeBar': True,  # Show the toolbar
        'scrollZoom': True,       # Enable scroll to zoom
        'displaylogo': False,     # Hide plotly logo
        'modeBarButtonsToRemove': ['toImage', 'sendDataToCloud', 'pan2d', 'select2d', 'lasso2d']
    }
)

# Legend matching reference image
st.markdown('''
<div style="display: flex; justify-content: flex-end; gap: 2rem; padding: 1rem 2rem; margin-top: -1rem;">
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="width: 12px; height: 12px; border-radius: 50%; background: #ff003c; box-shadow: 0 0 10px #ff003c;"></span>
        <span style="color: #8B95A5; font-family: 'Share Tech Mono', monospace; font-size: 0.85rem;">Critical</span>
    </div>
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="width: 12px; height: 12px; border-radius: 50%; background: #ff6b00; box-shadow: 0 0 10px #ff6b00;"></span>
        <span style="color: #8B95A5; font-family: 'Share Tech Mono', monospace; font-size: 0.85rem;">High</span>
    </div>
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="width: 12px; height: 12px; border-radius: 50%; background: #f0ff00; box-shadow: 0 0 10px #f0ff00;"></span>
        <span style="color: #8B95A5; font-family: 'Share Tech Mono', monospace; font-size: 0.85rem;">Medium</span>
    </div>
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="width: 12px; height: 12px; border-radius: 50%; background: #0aff0a; box-shadow: 0 0 10px #0aff0a;"></span>
        <span style="color: #8B95A5; font-family: 'Share Tech Mono', monospace; font-size: 0.85rem;">Low</span>
    </div>
</div>
''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Threat Sources with cyberpunk styling
col1, col2 = st.columns(2)

with col1:
    st.markdown(section_title("Top Threat Sources"), unsafe_allow_html=True)
    sorted_threats = sorted(threats.items(), key=lambda x: x[1]["real_count"], reverse=True)
    for country, data in sorted_threats[:6]:
        color = severity_colors.get(data["severity"], "#00f3ff")
        if total > 0:
            pct = (data["real_count"] / total) * 100
        else:
            pct = 0
        st.markdown(f"""
            <div class="glass-card" style="margin: 0.5rem 0; padding: 1rem; border-left: 3px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: {color}; box-shadow: 0 0 8px {color};"></span>
                        <span style="color: #FAFAFA; font-weight: 600; font-family: 'Rajdhani', sans-serif;">{country}</span>
                    </div>
                    <span style="color: {color}; font-weight: 700; font-family: 'Orbitron', sans-serif;">{data['real_count']:,}</span>
                </div>
                <div style="background: rgba(255,255,255,0.05); border-radius: 2px; height: 4px; margin-top: 0.5rem; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, {color}, {color}80); width: {pct}%; height: 100%; box-shadow: 0 0 10px {color};"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown(section_title("Attack Vectors"), unsafe_allow_html=True)
    # Get attack vector counts from SIEM events
    siem_attack_counts = {}
    try:
        from services.siem_service import get_siem_events
        siem_events = get_siem_events(200)
        attack_keywords = {
            "Port Scanning": ["scan", "port", "nmap", "probe"],
            "Brute Force": ["brute", "login", "failed", "password", "ssh"],
            "Malware C2": ["malware", "c2", "beacon", "trojan", "ransomware"],
            "DDoS": ["ddos", "flood", "dos", "syn"],
            "Phishing": ["phish", "spoof", "email", "credential"],
            "Exploitation": ["exploit", "vuln", "cve", "injection", "rce"]
        }
        for evt in siem_events:
            evt_text = str(evt).lower()
            for attack, keywords in attack_keywords.items():
                if any(kw in evt_text for kw in keywords):
                    siem_attack_counts[attack] = siem_attack_counts.get(attack, 0) + 1
    except Exception:
        pass
    
    attack_types = [
        ("Port Scanning", "#00f3ff", siem_attack_counts.get("Port Scanning", 0)),
        ("Brute Force", "#ff6b00", siem_attack_counts.get("Brute Force", 0)),
        ("Malware C2", "#ff003c", siem_attack_counts.get("Malware C2", 0)),
        ("DDoS", "#bc13fe", siem_attack_counts.get("DDoS", 0)),
        ("Phishing", "#f0ff00", siem_attack_counts.get("Phishing", 0)),
        ("Exploitation", "#ff003c", siem_attack_counts.get("Exploitation", 0))
    ]
    max_count = max([a[2] for a in attack_types]) if any(a[2] > 0 for a in attack_types) else 1
    
    for attack_type, color, count in attack_types:
        pct = (count / max_count) * 100
        st.markdown(f"""
            <div class="glass-card" style="margin: 0.5rem 0; padding: 1rem; border-left: 3px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: {color}; box-shadow: 0 0 8px {color};"></span>
                        <span style="color: #FAFAFA; font-weight: 600; font-family: 'Rajdhani', sans-serif;">{attack_type}</span>
                    </div>
                    <span style="color: {color}; font-weight: 700; font-family: 'Orbitron', sans-serif;">{count}</span>
                </div>
                <div style="background: rgba(255,255,255,0.05); border-radius: 2px; height: 4px; margin-top: 0.5rem; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, {color}, {color}80); width: {pct}%; height: 100%; box-shadow: 0 0 10px {color};"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_title("Live Threat Feed (AlienVault OTX)"), unsafe_allow_html=True)

try:
    pulses = get_latest_threats()
    if pulses:
        for pulse in pulses[:5]:
            tags_html = "".join([f'<span style="background:rgba(0, 243, 255, 0.1); border: 1px solid rgba(0, 243, 255, 0.3); padding:0.1rem 0.5rem; border-radius:2px; font-size:0.7rem; margin-right:0.5rem; color:#00f3ff; font-family: Share Tech Mono, monospace;">{tag}</span>' for tag in pulse.get('tags', [])[:4]])
            desc = pulse.get('description', '')[:120] + "..." if pulse.get('description') else "No description available."
            
            st.markdown(f"""
                <div class="glass-card" style="margin-bottom: 0.8rem; border-left: 3px solid #bc13fe;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <h4 style="color: #FAFAFA; margin: 0 0 0.3rem 0; font-size: 1rem; font-family: 'Rajdhani', sans-serif;">{pulse.get('name', 'Unknown Threat')[:60]}</h4>
                            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                                <span style="color: #00f3ff; font-size: 0.75rem; font-family: 'Share Tech Mono', monospace;">// {pulse.get('author') or 'AlienVault'}</span>
                                <span style="color: #666; font-size: 0.75rem; font-family: 'Share Tech Mono', monospace;">{pulse.get('created', '')[:10]}</span>
                            </div>
                            <div style="margin-bottom: 0.5rem;">{tags_html}</div>
                            <p style="color: #8B95A5; margin: 0; font-size: 0.85rem; line-height: 1.4;">{desc}</p>
                        </div>
                        <div style="text-align: center; min-width: 70px; padding-left: 1rem;">
                            <div style="background: rgba(255, 0, 60, 0.1); border: 1px solid rgba(255, 0, 60, 0.3); border-radius: 2px; padding: 0.5rem;">
                                <span style="color: #ff003c; font-weight: 700; font-size: 1.1rem; display: block; font-family: 'Orbitron', sans-serif;">{pulse.get('indicators', 0)}</span>
                                <span style="color: #ff6b00; font-size: 0.6rem; text-transform: uppercase; font-family: 'Share Tech Mono', monospace;">IOCs</span>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent OTX data available. Check your API key in Settings.")
except Exception as e:
    st.error(f"Error connecting to AlienVault OTX: {e}")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #666; font-family: Share Tech Mono, monospace; font-size: 0.8rem;">// AI-DRIVEN AUTONOMOUS SOC // THREAT INTELLIGENCE MODULE //</div>', unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
