import streamlit as st
import os
import sys
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Network Monitor | SOC", page_icon="N", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .monitor-header {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
        border: 1px solid rgba(0, 212, 255, 0.4);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 2rem;
    }
    
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 68, 68, 0.2);
        border: 1px solid #FF4444;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #FF4444;
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: #FF4444;
        border-radius: 50%;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    
    .stat-card {
        background: rgba(26, 31, 46, 0.9);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    
    .traffic-row {
        background: rgba(26, 31, 46, 0.6);
        border-left: 3px solid #00D4FF;
        padding: 0.8rem 1rem;
        margin: 0.3rem 0;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
    }
    
    .threat-alert {
        background: rgba(255, 68, 68, 0.15);
        border: 1px solid rgba(255, 68, 68, 0.4);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

from auth.auth_manager import check_auth, show_user_info

user = check_auth()
if not user:
    st.switch_page("pages/0_Login.py")
    st.stop()

show_user_info(user)

from services.live_monitor import (
    check_wireshark, get_interfaces, start_live_capture,
    stop_live_capture, analyze_traffic, detect_network_threats
)

st.markdown("""
    <div class="monitor-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin: 0; color: #FAFAFA;">Live Network Monitor</h1>
                <p style="color: #8B95A5; margin: 0.5rem 0 0 0;">Real-time network traffic analysis with Wireshark/tshark</p>
            </div>
            <div class="live-badge">
                <div class="live-dot"></div>
                LIVE
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

tshark_available = check_wireshark()

if tshark_available:
    st.success("Wireshark/tshark detected - Live capture available")
else:
    st.warning("tshark not found. Install Wireshark to enable live capture. Using file-based analysis.")

tab1, tab2, tab3 = st.tabs(["Live Capture", "Traffic Analysis", "Threat Detection"])

with tab1:
    st.markdown("### Live Network Capture")
    
    if tshark_available:
        interfaces = get_interfaces()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if interfaces:
                interface = st.selectbox("Network Interface", interfaces)
            else:
                interface = st.text_input("Interface Name", value="en0")
        
        with col2:
            duration = st.number_input("Duration (seconds)", min_value=5, max_value=300, value=30)
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Start Capture", type="primary", use_container_width=True):
                with st.spinner(f"Capturing traffic on {interface} for {duration} seconds..."):
                    result = start_live_capture(interface, duration)
                    
                    if result.get("status") == "started":
                        progress = st.progress(0)
                        for i in range(duration):
                            time.sleep(1)
                            progress.progress((i + 1) / duration)
                        
                        stop_live_capture()
                        st.success(f"Capture complete! {duration} seconds of traffic recorded.")
                        st.session_state["capture_ready"] = True
                    else:
                        st.error(f"Capture failed: {result.get('message', 'Unknown error')}")
        
        with col_btn2:
            if st.button("Stop Capture", use_container_width=True):
                stop_live_capture()
                st.info("Capture stopped")
    else:
        st.info("To enable live capture, install Wireshark and add tshark to your PATH")
        st.code("brew install wireshark  # macOS", language="bash")
    
    st.markdown("---")
    st.markdown("### Manual File Analysis")
    st.markdown("Upload PCAP file for analysis (works without Wireshark)")
    
    uploaded = st.file_uploader("Upload PCAP file", type=["pcap", "pcapng"])
    
    if uploaded:
        file_path = f"uploaded_{uploaded.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"File uploaded: {uploaded.name}")
        st.session_state["uploaded_file"] = file_path
        
        if st.button("Analyze Uploaded PCAP", type="primary"):
            from services.live_monitor import analyze_pcap_file
            
            with st.spinner("Analyzing PCAP file with Python..."):
                analysis = analyze_pcap_file(file_path)
                
                if "error" in analysis and analysis.get("total_packets", 0) == 0:
                    st.error(f"Analysis error: {analysis.get('error')}")
                else:
                    st.session_state["last_analysis"] = analysis
                    
                    st.markdown("### Analysis Results")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Packets", f"{analysis.get('total_packets', 0):,}")
                    with col2:
                        st.metric("Unique Sources", len(analysis.get('unique_sources', [])))
                    with col3:
                        st.metric("Destinations", len(analysis.get('unique_destinations', [])))
                    with col4:
                        st.metric("Threats Found", len(analysis.get('threats', [])))
                    
                    st.markdown("#### Protocol Distribution")
                    protocols = analysis.get("protocols", {})
                    if protocols:
                        st.bar_chart(protocols)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Top Talkers")
                        for ip, count in analysis.get("top_talkers", {}).items():
                            st.markdown(f"**{ip}** - {count:,} packets")
                    
                    with col2:
                        st.markdown("#### Top Ports")
                        for port, count in analysis.get("port_stats", {}).items():
                            st.markdown(f"**Port {port}** - {count:,} packets")
                    
                    threats = analysis.get("threats", [])
                    if threats:
                        st.markdown("---")
                        st.error(f"### {len(threats)} Threats Detected!")
                        for threat in threats:
                            severity_color = "#FF4444" if threat.get("severity") in ["CRITICAL", "HIGH"] else "#FF8C00"
                            st.markdown(f"""
                                <div class="threat-alert">
                                    <strong style="color: {severity_color};">[{threat.get('severity')}] {threat.get('type')}</strong>
                                    <p style="color: #FAFAFA; margin: 0.5rem 0;">{threat.get('detail')}</p>
                                    <p style="color: #00D4FF; margin: 0;">{threat.get('recommendation')}</p>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("No threats detected in this capture.")

with tab2:
    st.markdown("### Traffic Analysis")
    
    if st.button("Analyze Captured Traffic", type="primary"):
        with st.spinner("Analyzing network traffic..."):
            analysis = analyze_traffic()
            
            if "error" in analysis:
                st.error(f"Analysis error: {analysis['error']}")
            else:
                st.session_state["last_analysis"] = analysis
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                        <div class="stat-card">
                            <p style="color: #00D4FF; font-size: 2rem; font-weight: 700; margin: 0;">{analysis.get('total_packets', 0):,}</p>
                            <p style="color: #8B95A5; margin: 0;">Total Packets</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="stat-card">
                            <p style="color: #00C853; font-size: 2rem; font-weight: 700; margin: 0;">{len(analysis.get('unique_sources', []))}</p>
                            <p style="color: #8B95A5; margin: 0;">Unique Sources</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                        <div class="stat-card">
                            <p style="color: #FF8C00; font-size: 2rem; font-weight: 700; margin: 0;">{len(analysis.get('unique_destinations', []))}</p>
                            <p style="color: #8B95A5; margin: 0;">Destinations</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                        <div class="stat-card">
                            <p style="color: #8B5CF6; font-size: 2rem; font-weight: 700; margin: 0;">{len(analysis.get('protocols', {}))}</p>
                            <p style="color: #8B95A5; margin: 0;">Protocols</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Top Talkers")
                    for ip, count in analysis.get("top_talkers", {}).items():
                        pct = (count / max(analysis.get('total_packets', 1), 1)) * 100
                        st.markdown(f"""
                            <div class="traffic-row">
                                <span style="font-family: monospace;">{ip}</span>
                                <span style="color: #00D4FF;">{count:,} ({pct:.1f}%)</span>
                            </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("#### Top Ports")
                    port_names = {
                        "80": "HTTP", "443": "HTTPS", "22": "SSH", "53": "DNS",
                        "21": "FTP", "25": "SMTP", "3306": "MySQL", "3389": "RDP"
                    }
                    for port, count in analysis.get("port_stats", {}).items():
                        service = port_names.get(str(port), "")
                        st.markdown(f"""
                            <div class="traffic-row">
                                <span>Port {port} {f'({service})' if service else ''}</span>
                                <span style="color: #00D4FF;">{count:,}</span>
                            </div>
                        """, unsafe_allow_html=True)

with tab3:
    st.markdown("### Threat Detection")
    
    if st.button("Run Threat Analysis", type="primary"):
        with st.spinner("Analyzing for threats..."):
            analysis = st.session_state.get("last_analysis") or analyze_traffic()
            threats = detect_network_threats(analysis)
            
            if threats:
                st.error(f"⚠️ {len(threats)} potential threats detected!")
                
                for threat in threats:
                    severity_color = "#FF4444" if threat.get("severity") == "HIGH" else "#FF8C00"
                    st.markdown(f"""
                        <div class="threat-alert">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong style="color: {severity_color};">[{threat.get('severity')}] {threat.get('type')}</strong>
                            </div>
                            <p style="color: #FAFAFA; margin: 0.5rem 0;">{threat.get('detail')}</p>
                            <p style="color: #00D4FF; margin: 0; font-size: 0.9rem;">Recommendation: {threat.get('recommendation')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                if user.get('role') == 'admin':
                    st.markdown("---")
                    st.markdown("#### Admin Actions")
                    
                    for threat in threats:
                        if threat.get("source"):
                            if st.button(f"Block {threat.get('source')}", key=f"block_{threat.get('source')}"):
                                blocked_file = ".blocked_ips.json"
                                blocked = []
                                if os.path.exists(blocked_file):
                                    with open(blocked_file, 'r') as f:
                                        blocked = json.load(f)
                                
                                blocked.append({
                                    "ip": threat.get("source"),
                                    "reason": threat.get("type"),
                                    "blocked_by": user.get("email"),
                                    "blocked_at": datetime.now().isoformat()
                                })
                                
                                with open(blocked_file, 'w') as f:
                                    json.dump(blocked, f, indent=2)
                                
                                st.success(f"Blocked {threat.get('source')}")
            else:
                st.success("No threats detected in the analyzed traffic.")
    
    st.markdown("---")
    st.markdown("#### Real-Time Monitoring")
    
    auto_refresh = st.checkbox("Enable auto-refresh (every 30s)")
    
    if auto_refresh:
        st.info("Auto-refresh enabled. Page will analyze traffic every 30 seconds.")
        time.sleep(30)
        st.rerun()

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">AI-Driven Autonomous SOC | Live Network Monitor</p></div>', unsafe_allow_html=True)
