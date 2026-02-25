import streamlit as st
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="OSINT Feeds | SOC", page_icon="📡", layout="wide")
except st.errors.StreamlitAPIException:
    pass

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("OSINT Threat Feeds", "Real-time actionable threat intelligence from global sources"), unsafe_allow_html=True)

import requests

@st.cache_data(ttl=300)
def fetch_urlhaus_recent():
    """Fetch recent malware URLs from abuse.ch URLhaus (free, no key)."""
    try:
        r = requests.post("https://urlhaus-api.abuse.ch/v1/urls/recent/", 
                          data={"limit": 25}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("urls", [])[:25]
    except Exception as e:
        print(f"URLhaus error: {e}")
    return []

@st.cache_data(ttl=300)
def fetch_threatfox_recent():
    """Fetch recent IoCs from abuse.ch ThreatFox (free, no key)."""
    try:
        r = requests.post("https://threatfox-api.abuse.ch/api/v1/",
                          json={"query": "get_iocs", "days": 1}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("data", [])[:25]
    except Exception as e:
        print(f"ThreatFox error: {e}")
    return []

st.markdown(section_title("Live OSINT Threat Feed"), unsafe_allow_html=True)

st.markdown("""
    <div class="glass-card" style="margin-bottom: 1.5rem;">
        <p style="color: #8B95A5; margin: 0;">
            Real-time intelligence from <strong>abuse.ch URLhaus</strong> and <strong>ThreatFox</strong>. 
            These are live malware URLs and Indicators of Compromise (IoCs) reported in the last 24 hours.
            <span style="color: #00C853;">No API key required — fully automated.</span>
        </p>
    </div>
""", unsafe_allow_html=True)

feed_tab1, feed_tab2 = st.tabs(["URLhaus (Malware URLs)", "ThreatFox (IoCs)"])

with feed_tab1:
    with st.spinner("Fetching live malware URLs from abuse.ch..."):
        urls = fetch_urlhaus_recent()
    
    if urls:
        st.success(f"**{len(urls)}** live malware URLs retrieved from URLhaus")
        for u in urls:
            status = u.get("url_status", "unknown")
            status_color = {"online": "#FF4444", "offline": "#00C853", "unknown": "#FF8C00"}.get(status, "#8B95A5")
            threat = u.get("threat", "Malware")
            
            st.markdown(f'''
            <div style="
                background: rgba(26,31,46,0.5);
                border-left: 4px solid {status_color};
                padding: 12px 15px;
                border-radius: 0 8px 8px 0;
                margin: 6px 0;
                font-size: 0.9rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <code style="color: #FF6B6B; font-size: 0.85rem;">{u.get("url", "N/A")[:80]}</code>
                        <div style="color: #8B95A5; font-size: 0.75rem; margin-top: 4px;">
                            {u.get("date_added", "N/A")} | Threat: <strong style="color: #00D4FF;">{threat}</strong>
                        </div>
                    </div>
                    <span style="background: {status_color}; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">{status.upper()}</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("Unable to reach URLhaus API. Try again in a moment.")

with feed_tab2:
    with st.spinner("Fetching live IoCs from ThreatFox..."):
        iocs = fetch_threatfox_recent()
    
    if iocs:
        st.success(f"**{len(iocs)}** live IoCs retrieved from ThreatFox")
        for ioc in iocs:
            ioc_type = ioc.get("ioc_type", "unknown")
            malware = ioc.get("malware_printable", "Unknown")
            confidence = ioc.get("confidence_level", 0)
            conf_color = "#FF4444" if confidence > 75 else "#FF8C00" if confidence > 50 else "#00C853"
            
            st.markdown(f'''
            <div style="
                background: rgba(26,31,46,0.5);
                border: 1px solid rgba(255,255,255,0.1);
                padding: 12px 15px;
                border-radius: 8px;
                margin: 6px 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <code style="color: #00D4FF; font-size: 0.85rem;">{ioc.get("ioc", "N/A")[:80]}</code>
                        <div style="color: #8B95A5; font-size: 0.75rem; margin-top: 4px;">
                            Type: <strong>{ioc_type}</strong> | Malware: <strong style="color: #FF6B6B;">{malware}</strong>
                        </div>
                    </div>
                    <span style="background: {conf_color}; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">{confidence}%</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("Unable to reach ThreatFox API. Try again in a moment.")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | OSINT Feeds</p></div>', unsafe_allow_html=True)
