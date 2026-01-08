import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random

st.set_page_config(page_title="Threat Map | SOC", page_icon="🌍", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stat-card { background: rgba(26, 31, 46, 0.8); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 12px; padding: 1.2rem; text-align: center; }
    .country-row { background: rgba(26, 31, 46, 0.6); border-radius: 8px; padding: 0.8rem 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; transition: all 0.3s ease; }
    .country-row:hover { background: rgba(0, 212, 255, 0.1); transform: translateX(5px); }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_geo_data():
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    countries_data = [
        {"country": "China", "code": "CHN", "lat": 35.86, "lon": 104.19, "attacks": 1250},
        {"country": "Russia", "code": "RUS", "lat": 61.52, "lon": 105.31, "attacks": 980},
        {"country": "United States", "code": "USA", "lat": 37.09, "lon": -95.71, "attacks": 620},
        {"country": "Iran", "code": "IRN", "lat": 32.42, "lon": 53.68, "attacks": 480},
        {"country": "North Korea", "code": "PRK", "lat": 40.33, "lon": 127.51, "attacks": 350},
        {"country": "Ukraine", "code": "UKR", "lat": 48.37, "lon": 31.16, "attacks": 290},
        {"country": "Brazil", "code": "BRA", "lat": -14.23, "lon": -51.92, "attacks": 230},
        {"country": "India", "code": "IND", "lat": 20.59, "lon": 78.96, "attacks": 210},
        {"country": "Germany", "code": "DEU", "lat": 51.16, "lon": 10.45, "attacks": 180},
        {"country": "Netherlands", "code": "NLD", "lat": 52.13, "lon": 5.29, "attacks": 150},
        {"country": "Vietnam", "code": "VNM", "lat": 14.05, "lon": 108.27, "attacks": 120},
        {"country": "Indonesia", "code": "IDN", "lat": -0.78, "lon": 113.92, "attacks": 95},
        {"country": "Turkey", "code": "TUR", "lat": 38.96, "lon": 35.24, "attacks": 85},
        {"country": "France", "code": "FRA", "lat": 46.22, "lon": 2.21, "attacks": 75},
        {"country": "United Kingdom", "code": "GBR", "lat": 55.37, "lon": -3.43, "attacks": 65}
    ]
    for c in countries_data:
        c["attacks"] = int(c["attacks"] * random.uniform(0.8, 1.2))
        c["blocked"] = int(c["attacks"] * random.uniform(0.2, 0.4))
        c["critical"] = int(c["attacks"] * random.uniform(0.05, 0.15))
    return pd.DataFrame(countries_data)

df = load_geo_data()

st.markdown("# 🌍 Global Threat Map")
st.markdown("Geographic visualization of attack sources")
st.markdown("---")

total_attacks = df["attacks"].sum()
total_blocked = df["blocked"].sum()
total_critical = df["critical"].sum()
total_countries = len(df)

stat1, stat2, stat3, stat4 = st.columns(4)
with stat1:
    st.markdown(f'<div class="stat-card"><p style="font-size: 2.5rem; font-weight: 700; color: #00D4FF; margin: 0;">{total_attacks:,}</p><p style="color: #8B95A5; margin: 0;">Total Attacks</p></div>', unsafe_allow_html=True)
with stat2:
    st.markdown(f'<div class="stat-card" style="border-color: #FF4444;"><p style="font-size: 2.5rem; font-weight: 700; color: #FF4444; margin: 0;">{total_blocked:,}</p><p style="color: #8B95A5; margin: 0;">Blocked</p></div>', unsafe_allow_html=True)
with stat3:
    st.markdown(f'<div class="stat-card" style="border-color: #FF8C00;"><p style="font-size: 2.5rem; font-weight: 700; color: #FF8C00; margin: 0;">{total_critical:,}</p><p style="color: #8B95A5; margin: 0;">Critical</p></div>', unsafe_allow_html=True)
with stat4:
    st.markdown(f'<div class="stat-card" style="border-color: #8B5CF6;"><p style="font-size: 2.5rem; font-weight: 700; color: #8B5CF6; margin: 0;">{total_countries}</p><p style="color: #8B95A5; margin: 0;">Countries</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

map_col, list_col = st.columns([2, 1])

with map_col:
    st.markdown("### 🗺️ Attack Heatmap")
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lat=df["lat"], lon=df["lon"], mode="markers",
        marker=dict(size=df["attacks"] / 30, color=df["attacks"],
                    colorscale=[[0, "#00D4FF"], [0.5, "#FF8C00"], [1, "#FF4444"]], opacity=0.8,
                    line=dict(width=1, color="#FFFFFF")),
        text=df.apply(lambda x: f"{x['country']}<br>Attacks: {x['attacks']:,}<br>Blocked: {x['blocked']:,}", axis=1),
        hoverinfo="text", name="Attack Sources"
    ))
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True, coastlinecolor="#3D4A5C", showland=True, landcolor="#1A1F2E",
                 showocean=True, oceancolor="#0E1117", showcountries=True, countrycolor="#3D4A5C",
                 showlakes=False, projection_type="natural earth", bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=0, b=0), height=500
    )
    st.plotly_chart(fig, use_container_width=True)

with list_col:
    st.markdown("### 📊 Top Threat Sources")
    sorted_df = df.sort_values("attacks", ascending=False)
    for idx, row in sorted_df.iterrows():
        pct = row["attacks"] / total_attacks * 100
        bar_color = "#FF4444" if pct > 15 else "#FF8C00" if pct > 10 else "#00D4FF"
        st.markdown(f'<div class="country-row"><div><span style="font-weight: 600; color: #FAFAFA;">{row["country"]}</span><span style="color: #8B95A5; font-size: 0.8rem; margin-left: 0.5rem;">{row["code"]}</span></div><div style="text-align: right;"><span style="font-weight: 700; color: {bar_color};">{row["attacks"]:,}</span><span style="color: #8B95A5; font-size: 0.8rem;"> ({pct:.1f}%)</span></div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🌐 Regional Analysis")

import plotly.express as px
region_col1, region_col2 = st.columns(2)

with region_col1:
    regions = {
        "Asia Pacific": ["China", "North Korea", "India", "Vietnam", "Indonesia"],
        "Europe": ["Russia", "Ukraine", "Germany", "Netherlands", "France", "United Kingdom", "Turkey"],
        "Americas": ["United States", "Brazil"],
        "Middle East": ["Iran"]
    }
    region_data = [{"region": region, "attacks": df[df["country"].isin(countries)]["attacks"].sum()} for region, countries in regions.items()]
    region_df = pd.DataFrame(region_data)
    fig2 = px.pie(region_df, values="attacks", names="region", hole=0.5, color_discrete_sequence=["#FF4444", "#FF8C00", "#00D4FF", "#8B5CF6"])
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA", showlegend=True,
                       legend=dict(orientation="h", yanchor="bottom", y=-0.2), margin=dict(l=20, r=20, t=40, b=40), height=350)
    fig2.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig2, use_container_width=True)

with region_col2:
    hours = list(range(24))
    attack_trend = [int(total_attacks / 24 * random.uniform(0.5, 1.5)) for _ in hours]
    trend_df = pd.DataFrame({"hour": hours, "attacks": attack_trend})
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=trend_df["hour"], y=trend_df["attacks"], mode="lines+markers", fill="tozeroy",
                              line=dict(color="#00D4FF", width=2), fillcolor="rgba(0, 212, 255, 0.1)", marker=dict(size=6)))
    fig3.update_layout(title="24-Hour Attack Trend", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA",
                       xaxis=dict(title="Hour (UTC)", showgrid=False, tickmode="array", tickvals=list(range(0, 24, 4))),
                       yaxis=dict(title="Attacks", showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
                       margin=dict(l=40, r=20, t=60, b=40), height=350)
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">🛡️ AI-Driven Autonomous SOC | Geographic Threat Intelligence</p></div>', unsafe_allow_html=True)
