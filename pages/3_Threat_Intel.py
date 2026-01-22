import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Threat Intelligence | SOC", page_icon="T", layout="wide")

from ui.theme import PREMIUM_CSS, page_header, section_title
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

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
        st.cache_data.clear()
        st.session_state.last_refresh = time.time()
        st.rerun()

with col_time:
    st.markdown(f'''
        <div style="display: flex; align-items: center; gap: 0.5rem; height: 38px;">
            <span style="color: #00C853;">●</span>
            <span style="color: #8B95A5;">Auto-refreshing every 30s</span>
        </div>
    ''', unsafe_allow_html=True)

# Auto-refresh logic
if time.time() - st.session_state.last_refresh > 30:
    st.cache_data.clear()
    st.session_state.last_refresh = time.time()
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Generate threat data
@st.cache_data(ttl=60)
def get_threat_data():
    from services.threat_intel import threat_intel
    
    # Base coordinates for major countries
    coords = {
        "China": {"lat": 35.86, "lon": 104.19},
        "Russia": {"lat": 61.52, "lon": 105.31},
        "United States": {"lat": 37.09, "lon": -95.71},
        "Iran": {"lat": 32.42, "lon": 53.68},
        "North Korea": {"lat": 40.33, "lon": 127.51},
        "Brazil": {"lat": -14.23, "lon": -51.92},
        "India": {"lat": 20.59, "lon": 78.96},
        "Ukraine": {"lat": 48.37, "lon": 31.16},
        "Germany": {"lat": 51.16, "lon": 10.45},
        "Netherlands": {"lat": 52.13, "lon": 5.29},
        "Vietnam": {"lat": 14.05, "lon": 108.27},
        "France": {"lat": 46.22, "lon": 2.21},
        "Israel": {"lat": 31.04, "lon": 34.85},
        "United Kingdom": {"lat": 55.37, "lon": -3.43}
    }
    
    # Fetch real counts
    counts = threat_intel.get_country_threat_counts()
    
    results = {}
    for country, params in coords.items():
        count = counts.get(country, 0)
        # Visual scaling: even 1 result should be visible
        display_threats = count * 10 if count > 0 else 0 
        
        results[country] = {
            "lat": params["lat"],
            "lon": params["lon"], 
            "threats": display_threats,
            "real_count": count
        }
    return results

threats = get_threat_data()

# Stats
total = sum([c["real_count"] for c in threats.values()])
if total == 0:
    top_country = ("None", {"threats": 0, "real_count": 0})
else:
    top_country = max(threats.items(), key=lambda x: x[1]["real_count"])

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF4444;">{total:,}</p><p class="metric-label">Active Threats (OTX)</p></div>', unsafe_allow_html=True)
with c2:
    active_countries = len([c for c in threats.values() if c["real_count"] > 0])
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF8C00;">{active_countries}</p><p class="metric-label">Affected Countries</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00D4FF;">{top_country[0][:10]}</p><p class="metric-label">Top Source</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #8B5CF6;">{top_country[1]["real_count"]}</p><p class="metric-label">Top Threats</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# World Map - Choropleth + Scatter markers
st.markdown(section_title("Global Threat Map"), unsafe_allow_html=True)

# ISO country codes for choropleth
country_codes = {
    "China": "CHN", "Russia": "RUS", "United States": "USA", "Iran": "IRN",
    "North Korea": "PRK", "Brazil": "BRA", "India": "IND", "Ukraine": "UKR",
    "Germany": "DEU", "Netherlands": "NLD", "Vietnam": "VNM", "France": "FRA",
    "Israel": "ISR", "United Kingdom": "GBR"
}

# Prepare data for choropleth
locations = [country_codes.get(c, "") for c in threats.keys()]
z_values = [threats[c]["real_count"] for c in threats.keys()]
country_names = list(threats.keys())

fig = go.Figure()

# Layer 1: Choropleth (colored countries)
fig.add_trace(go.Choropleth(
    locations=locations,
    z=z_values,
    text=country_names,
    colorscale=[
        [0, 'rgba(30, 40, 60, 0.8)'],      # No threats - dark
        [0.2, 'rgba(255, 200, 0, 0.6)'],   # Low - yellow
        [0.5, 'rgba(255, 140, 0, 0.7)'],   # Medium - orange
        [0.8, 'rgba(255, 68, 68, 0.8)'],   # High - red
        [1, 'rgba(139, 0, 0, 0.9)']        # Critical - dark red
    ],
    showscale=True,
    colorbar=dict(
        title="Threats",
        tickfont=dict(color="#8B95A5"),
        titlefont=dict(color="#FAFAFA"),
        bgcolor="rgba(0,0,0,0)",
        x=1.02
    ),
    hovertemplate="<b>%{text}</b><br>Active Threats: %{z}<extra></extra>"
))

# Layer 2: Scatter markers for visual impact
lats = [c["lat"] for c in threats.values()]
lons = [c["lon"] for c in threats.values()]
sizes = [max(10, c["real_count"] * 3) for c in threats.values()]
real_counts = [c["real_count"] for c in threats.values()]

fig.add_trace(go.Scattergeo(
    lat=lats, lon=lons,
    mode='markers',
    marker=dict(
        size=sizes,
        color='#FF4444',
        opacity=0.7,
        line=dict(width=2, color='white'),
        sizemode='diameter'
    ),
    text=[f"<b>{n}</b><br>{c} active threats" for n, c in zip(country_names, real_counts)],
    hoverinfo='text',
    showlegend=False
))

fig.update_layout(
    geo=dict(
        bgcolor='rgba(10, 14, 23, 1)',
        showland=True, landcolor='rgba(30, 40, 60, 0.6)',
        showocean=True, oceancolor='rgba(15, 25, 45, 0.9)',
        showlakes=False,
        showcountries=True, countrycolor='rgba(100, 120, 140, 0.4)',
        showcoastlines=True, coastlinecolor='rgba(100, 120, 140, 0.3)',
        projection_type='natural earth',
        showframe=False
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, t=0, b=0),
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Threat Sources
col1, col2 = st.columns(2)

with col1:
    st.markdown(section_title("Top Threat Sources"), unsafe_allow_html=True)
    sorted_threats = sorted(threats.items(), key=lambda x: x[1]["real_count"], reverse=True)
    for country, data in sorted_threats[:6]:
        if total > 0:
            pct = (data["real_count"] / total) * 100
        else:
            pct = 0
        st.markdown(f"""
            <div class="glass-card" style="margin: 0.5rem 0; padding: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #FAFAFA; font-weight: 600;">{country}</span>
                    <span style="color: #FF8C00; font-weight: 700;">{data['real_count']:,}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 6px; margin-top: 0.5rem; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #FF8C00, #FF4444); width: {pct}%; height: 100%;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown(section_title("Threat Types"), unsafe_allow_html=True)
    types = ["Port Scanning", "Brute Force", "Malware", "DDoS", "Phishing", "Exploitation"]
    for t in types:
        count = random.randint(50, 300)
        pct = count / 3
        st.markdown(f"""
            <div class="glass-card" style="margin: 0.5rem 0; padding: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #FAFAFA; font-weight: 600;">{t}</span>
                    <span style="color: #00D4FF; font-weight: 700;">{count}</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 6px; margin-top: 0.5rem; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #00D4FF, #8B5CF6); width: {pct}%; height: 100%;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_title("Live Threat Feed (AlienVault OTX)"), unsafe_allow_html=True)

try:
    pulses = get_latest_threats()
    if pulses:
        # Show top 5
        for pulse in pulses[:5]:
            tags_html = "".join([f'<span style="background:rgba(139, 92, 246, 0.2); border: 1px solid rgba(139, 92, 246, 0.3); padding:0.1rem 0.5rem; border-radius:12px; font-size:0.75rem; margin-right:0.5rem; color:#D8B4FE;">{tag}</span>' for tag in pulse.get('tags', [])])
            desc = pulse.get('description', '')[:150] + "..." if pulse.get('description') else "No description available."
            
            st.markdown(f"""
                <div class="glass-card" style="margin-bottom: 0.8rem; border-left: 3px solid #8B5CF6; transition: transform 0.2s;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <h4 style="color: #FAFAFA; margin: 0 0 0.3rem 0; font-size: 1.05rem;">{pulse.get('name', 'Unknown Threat')}</h4>
                            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                                <span style="color: #00D4FF; font-size: 0.8rem;">👤 {pulse.get('author') or 'AlienVault'}</span>
                                <span style="color: #8B95A5; font-size: 0.8rem;">📅 {pulse.get('created', '')[:10]}</span>
                            </div>
                            <div style="margin-bottom: 0.6rem;">{tags_html}</div>
                            <p style="color: #B0B8C3; margin: 0; font-size: 0.9rem; line-height: 1.5;">{desc}</p>
                        </div>
                        <div style="text-align: right; min-width: 80px; padding-left: 1rem;">
                            <div style="background: rgba(255, 68, 68, 0.1); border-radius: 8px; padding: 0.5rem;">
                                <span style="color: #FF4444; font-weight: 700; font-size: 1.2rem; display: block;">{pulse.get('indicators', 0)}</span>
                                <span style="color: #FF8C00; font-size: 0.7rem; text-transform: uppercase;">Indicators</span>
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
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Threat Intelligence</p></div>', unsafe_allow_html=True)
