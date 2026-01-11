import streamlit as st
import os
import sys
import json
import tempfile
import requests
import base64
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Scanners | SOC", page_icon="S", layout="wide")

from ui.theme import PREMIUM_CSS, page_header, section_title
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

from auth.auth_manager import check_auth, show_user_info

user = check_auth()
if not user:
    st.switch_page("pages/0_Login.py")
    st.stop()

show_user_info(user)

st.markdown(page_header("Security Scanners", "File, URL, and network analysis tools"), unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["File Scanner", "URL Scanner", "Network Monitor"])

with tab1:
    st.markdown(section_title("PDF File Scanner"), unsafe_allow_html=True)
    st.markdown('<p style="color: #8B95A5;">Scan PDF files for malware, JavaScript, and phishing indicators.</p>', unsafe_allow_html=True)
    
    uploaded = st.file_uploader("Upload PDF", type=['pdf'], key="pdf_upload")
    
    if uploaded:
        st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #FAFAFA; font-weight: 600;">{uploaded.name}</span>
                    <span style="color: #8B95A5;">{uploaded.size:,} bytes</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Scan PDF", type="primary", key="scan_pdf"):
            with st.spinner("Scanning for threats..."):
                try:
                    from services.pdf_scanner import scan_pdf_file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        tmp.write(uploaded.getvalue())
                        tmp_path = tmp.name
                    
                    result = scan_pdf_file(tmp_path)
                    os.unlink(tmp_path)
                    
                    verdict = result.get('verdict', 'UNKNOWN')
                    risk = result.get('risk_score', 0)
                    verdict_color = {"CLEAN": "#00C853", "SUSPICIOUS": "#FF8C00", "MALICIOUS": "#FF4444"}.get(verdict, "#8B95A5")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: {verdict_color};">{verdict}</p><p class="metric-label">Verdict</p></div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF8C00;">{risk}</p><p class="metric-label">Risk Score</p></div>', unsafe_allow_html=True)
                    with c3:
                        st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF4444;">{len(result.get("threats_found", []))}</p><p class="metric-label">Threats</p></div>', unsafe_allow_html=True)
                    
                    if result.get('threats_found'):
                        st.markdown("<br>", unsafe_allow_html=True)
                        for t in result['threats_found']:
                            st.markdown(f'<div class="alert-card alert-high">{t}</div>', unsafe_allow_html=True)
                    else:
                        st.success("No threats detected in this file.")
                except Exception as e:
                    st.error(f"Scan error: {e}")

with tab2:
    st.markdown(section_title("URL Scanner"), unsafe_allow_html=True)
    st.markdown('<p style="color: #8B95A5;">Check URLs for malicious content using VirusTotal.</p>', unsafe_allow_html=True)
    
    config = {}
    if os.path.exists('.soc_config.json'):
        with open('.soc_config.json', 'r') as f:
            config = json.load(f)
    
    VT_KEY = config.get('virustotal_api_key', '')
    
    if not VT_KEY:
        st.warning("Add VirusTotal API key in Settings to enable URL scanning.")
    else:
        st.success("VirusTotal API connected")
        
        url = st.text_input("Enter URL", placeholder="https://example.com")
        
        if st.button("Scan URL", type="primary", key="scan_url") and url:
            if not url.startswith('http'):
                url = 'https://' + url
            
            with st.spinner("Scanning with 70+ vendors..."):
                try:
                    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip('=')
                    resp = requests.get(
                        f'https://www.virustotal.com/api/v3/urls/{url_id}',
                        headers={'x-apikey': VT_KEY},
                        timeout=15
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()['data']['attributes']
                        stats = data.get('last_analysis_stats', {})
                        
                        mal = stats.get('malicious', 0)
                        sus = stats.get('suspicious', 0)
                        clean = stats.get('harmless', 0)
                        
                        if mal > 0:
                            verdict, color = "MALICIOUS", "#FF4444"
                        elif sus > 2:
                            verdict, color = "SUSPICIOUS", "#FF8C00"
                        else:
                            verdict, color = "SAFE", "#00C853"
                        
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: {color};">{verdict}</p><p class="metric-label">Verdict</p></div>', unsafe_allow_html=True)
                        with c2:
                            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF4444;">{mal}</p><p class="metric-label">Malicious</p></div>', unsafe_allow_html=True)
                        with c3:
                            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF8C00;">{sus}</p><p class="metric-label">Suspicious</p></div>', unsafe_allow_html=True)
                        with c4:
                            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00C853;">{clean}</p><p class="metric-label">Clean</p></div>', unsafe_allow_html=True)
                    else:
                        st.info("URL not in database. Submitting for analysis...")
                except Exception as e:
                    st.error(f"Error: {e}")

with tab3:
    st.markdown(section_title("Network Monitor"), unsafe_allow_html=True)
    st.markdown('<p style="color: #8B95A5;">Upload PCAP files for traffic analysis and threat detection.</p>', unsafe_allow_html=True)
    
    pcap = st.file_uploader("Upload PCAP", type=['pcap', 'pcapng'], key="pcap_upload")
    
    if pcap:
        path = f"uploaded_{pcap.name}"
        with open(path, 'wb') as f:
            f.write(pcap.getbuffer())
        
        st.markdown(f"""
            <div class="glass-card">
                <span style="color: #FAFAFA; font-weight: 600;">{pcap.name}</span>
                <span style="color: #8B95A5; margin-left: 1rem;">{pcap.size:,} bytes</span>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Analyze PCAP", type="primary", key="analyze_pcap"):
            with st.spinner("Analyzing network traffic..."):
                try:
                    from services.live_monitor import analyze_pcap_file
                    result = analyze_pcap_file(path)
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00D4FF;">{result.get("total_packets", 0):,}</p><p class="metric-label">Packets</p></div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00C853;">{len(result.get("unique_sources", []))}</p><p class="metric-label">Sources</p></div>', unsafe_allow_html=True)
                    with c3:
                        st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #8B5CF6;">{len(result.get("unique_destinations", []))}</p><p class="metric-label">Destinations</p></div>', unsafe_allow_html=True)
                    with c4:
                        st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF4444;">{len(result.get("threats", []))}</p><p class="metric-label">Threats</p></div>', unsafe_allow_html=True)
                    
                    if result.get('threats'):
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(section_title("Detected Threats"), unsafe_allow_html=True)
                        for t in result['threats']:
                            sev_color = {"CRITICAL": "#FF4444", "HIGH": "#FF8C00"}.get(t.get('severity'), "#FFD700")
                            st.markdown(f"""
                                <div class="alert-card" style="border-left-color: {sev_color};">
                                    <span style="color: {sev_color}; font-weight: 700;">[{t.get('severity')}] {t.get('type')}</span>
                                    <p style="color: #FAFAFA; margin: 0.3rem 0;">{t.get('detail')}</p>
                                    <p style="color: #00D4FF; font-size: 0.85rem;">{t.get('recommendation')}</p>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("No threats detected in this capture.")
                except Exception as e:
                    st.error(f"Analysis error: {e}")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Scanners</p></div>', unsafe_allow_html=True)
