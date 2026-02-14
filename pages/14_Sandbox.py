"""
 Malware Sandbox
==================
Safely analyze suspicious files and URLs in an isolated environment.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui.theme import CYBERPUNK_CSS

try:
    st.set_page_config(
        page_title="Sandbox | SOC",
        page_icon="",
        layout="wide"
    )
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)

# Header
st.markdown("""
<div style="text-align: center; padding: 20px 0 30px;">
    <h1 style="font-size: 2.5rem; font-weight: 700; margin: 0; color: #fff;">
         Malware Sandbox
    </h1>
    <p style="color: #888; font-size: 0.9rem; letter-spacing: 2px; margin-top: 5px;">
        SAFE DETONATION & BEHAVIORAL ANALYSIS
    </p>
</div>
""", unsafe_allow_html=True)

# Import sandbox service
try:
    from services.sandbox_service import analyze_file, analyze_url, get_analysis_history, get_sandbox_stats
    SANDBOX_LOADED = True
except ImportError as e:
    SANDBOX_LOADED = False
    st.error(f"Sandbox service not available: {e}")

if SANDBOX_LOADED:
    # Stats banner
    stats = get_sandbox_stats()
    
    cols = st.columns(5)
    stat_items = [
        ("Total Analyzed", stats.get("total", 0), "#00f3ff"),
        ("Malicious", stats.get("malicious", 0), "#ff0040"),
        ("Suspicious", stats.get("suspicious", 0), "#ff6600"),
        ("Phishing", stats.get("phishing", 0), "#ffcc00"),
        ("Clean", stats.get("clean", 0), "#00ff88")
    ]
    
    for col, (label, value, color) in zip(cols, stat_items):
        with col:
            st.markdown(f"""
            <div style="
                background: rgba(0,0,0,0.3);
                border: 1px solid {color}40;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="font-size: 1.8rem; font-weight: 700; color: {color};">{value}</div>
                <div style="font-size: 0.75rem; color: #888;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for file and URL analysis
    tab1, tab2, tab3 = st.tabs([" File Analysis", " URL Analysis", " History"])
    
    with tab1:
        st.markdown("### Upload Suspicious File")
        st.markdown("""
        <div class="glass-card" style="margin-bottom: 20px;">
            <p style="color: #888; margin: 0;">
                Upload any suspicious file for safe detonation and behavioral analysis.
                The sandbox will execute the file in isolation and report all activities.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["exe", "dll", "ps1", "bat", "vbs", "js", "doc", "docx", "xls", "xlsx", "pdf", "zip", "rar"],
            help="Upload suspicious files for analysis"
        )
        
        if uploaded_file:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**File:** {uploaded_file.name}")
                st.markdown(f"**Size:** {uploaded_file.size:,} bytes")
            
            with col2:
                if st.button(" Analyze File", type="primary", use_container_width=True):
                    with st.spinner("Detonating in sandbox..."):
                        import time
                        time.sleep(2)  # Simulate analysis time
                        
                        content = uploaded_file.read()
                        result = analyze_file(content, uploaded_file.name)
                        st.session_state.file_result = result
            
            # Display results
            if 'file_result' in st.session_state:
                result = st.session_state.file_result
                
                # Verdict banner
                verdict_colors = {
                    "MALICIOUS": "#ff0040",
                    "SUSPICIOUS": "#ff6600",
                    "CLEAN": "#00ff88"
                }
                verdict_color = verdict_colors.get(result["verdict"], "#888")
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {verdict_color}22, {verdict_color}11);
                    border: 2px solid {verdict_color};
                    border-radius: 12px;
                    padding: 25px;
                    text-align: center;
                    margin: 20px 0;
                ">
                    <div style="font-size: 0.8rem; color: #888; letter-spacing: 2px;">VERDICT</div>
                    <div style="font-size: 2.5rem; font-weight: 800; color: {verdict_color};">
                        {result['verdict']}
                    </div>
                    <div style="color: #888;">
                        Analysis Time: {result['analysis_time']}s | 
                        Severity: <strong style="color: {verdict_color};">{result['severity']}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("####  File Hashes")
                    for hash_type, hash_val in result["hashes"].items():
                        st.code(f"{hash_type.upper()}: {hash_val}")
                    
                    st.markdown("####  Processes Spawned")
                    procs = result["behavior"]["processes_spawned"]
                    if procs:
                        for proc in procs:
                            st.markdown(f"• `{proc}`")
                    else:
                        st.markdown("*No processes spawned*")
                
                with col2:
                    st.markdown("####  Network Connections")
                    conns = result["behavior"]["network_connections"]
                    if conns:
                        for conn in conns:
                            st.markdown(f"""
                            <div style="background: rgba(255,0,64,0.1); padding: 10px; border-radius: 6px; margin: 5px 0;">
                                <strong>{conn['ip']}:{conn['port']}</strong>
                                <span style="color: #ff6600;"> ({conn['type']})</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("*No network activity*")
                    
                    st.markdown("####  Files Modified")
                    st.metric("", result["behavior"]["files_modified"])
                
                # MITRE Techniques
                if result["mitre_techniques"]:
                    st.markdown("####  MITRE ATT&CK Techniques")
                    for tech in result["mitre_techniques"]:
                        st.markdown(f"""
                        <span style="
                            background: #8B5CF6;
                            color: #fff;
                            padding: 4px 10px;
                            border-radius: 4px;
                            margin-right: 8px;
                            font-size: 0.85rem;
                        ">{tech['id']}: {tech['name']}</span>
                        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Analyze Suspicious URL")
        st.markdown("""
        <div class="glass-card" style="margin-bottom: 20px;">
            <p style="color: #888; margin: 0;">
                Paste a suspicious URL to check for phishing, malware downloads, or malicious redirects.
                The sandbox will load the URL and capture behavior.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        url_input = st.text_input(
            "Enter URL to analyze",
            placeholder="https://suspicious-site.example.com/login",
            help="Enter the full URL including http:// or https://"
        )
        
        if st.button(" Analyze URL", type="primary"):
            if url_input:
                with st.spinner("Loading URL in sandbox..."):
                    import time
                    time.sleep(1.5)
                    
                    result = analyze_url(url_input)
                    st.session_state.url_result = result
            else:
                st.warning("Please enter a URL")
        
        # Display URL results
        if 'url_result' in st.session_state:
            result = st.session_state.url_result
            
            verdict_colors = {
                "PHISHING": "#ff0040",
                "MALICIOUS": "#ff0040",
                "SUSPICIOUS": "#ff6600",
                "CLEAN": "#00ff88"
            }
            verdict_color = verdict_colors.get(result["verdict"], "#888")
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {verdict_color}22, {verdict_color}11);
                border: 2px solid {verdict_color};
                border-radius: 12px;
                padding: 25px;
                text-align: center;
                margin: 20px 0;
            ">
                <div style="font-size: 0.8rem; color: #888; letter-spacing: 2px;">VERDICT</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: {verdict_color};">
                    {result['verdict']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("####  URL Info")
                st.markdown(f"**SSL Valid:** {' Yes' if result['ssl_valid'] else ' No'}")
                st.markdown(f"**Redirects:** {result['redirects']}")
                st.markdown(f"**Domain Age:** {result['domain_age_days']} days")
            
            with col2:
                st.markdown("####  Phishing Indicators")
                if result["phishing_indicators"]:
                    for ind in result["phishing_indicators"]:
                        st.markdown(f"• `{ind}`")
                else:
                    st.markdown("*None detected*")
            
            with col3:
                st.markdown("####  Network Activity")
                if result["network_activity"]:
                    for act in result["network_activity"]:
                        st.markdown(f"• {act['ip']}:{act['port']} ({act['type']})")
                else:
                    st.markdown("*No suspicious activity*")
    
    with tab3:
        st.markdown("### Recent Analyses")
        
        history = get_analysis_history(20)
        
        if history:
            for item in history:
                verdict_color = {
                    "MALICIOUS": "#ff0040",
                    "PHISHING": "#ff0040",
                    "SUSPICIOUS": "#ff6600",
                    "CLEAN": "#00ff88"
                }.get(item["verdict"], "#888")
                
                name = item.get("filename") or item.get("url", "Unknown")
                item_type = " File" if "filename" in item else " URL"
                
                st.markdown(f"""
                <div style="
                    background: rgba(0,0,0,0.2);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-left: 3px solid {verdict_color};
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div>
                        <div style="color: #888; font-size: 0.75rem;">{item_type} • {item['submitted_at'][:19]}</div>
                        <div style="color: #fff; font-weight: 600;">{name[:50]}...</div>
                    </div>
                    <div style="
                        background: {verdict_color}22;
                        color: {verdict_color};
                        padding: 5px 15px;
                        border-radius: 4px;
                        font-weight: 700;
                    ">{item['verdict']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No analyses yet. Upload a file or analyze a URL to get started.")

# Inject floating CORTEX orb
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
