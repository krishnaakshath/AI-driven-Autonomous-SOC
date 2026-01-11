import streamlit as st
import os
import sys
import time
import json
import socket
import uuid
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Security Testing | SOC", page_icon="T", layout="wide")

from ui.theme import PREMIUM_CSS, page_header, section_title
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

from auth.auth_manager import check_auth, show_user_info

user = check_auth()
if not user:
    st.switch_page("pages/0_Login.py")
    st.stop()

show_user_info(user)

st.markdown(page_header("Security Testing", "Attack simulation and penetration testing tools"), unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Attack Simulation", "Pentest Tools"])

with tab1:
    st.markdown(section_title("Attack Simulation Lab"), unsafe_allow_html=True)
    st.warning("**Educational Purpose** - Demonstrates how the SOC detects and responds to threats")
    
    # Device info
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "Unknown"
    
    try:
        public_ip = requests.get("https://api.ipify.org?format=json", timeout=5).json().get("ip", "Unknown")
    except:
        public_ip = "Unknown"
    
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0,48,8)][::-1]).upper()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="glass-card"><span style="color: #8B95A5;">Public IP</span><p style="color: #00D4FF; font-weight: 600; margin: 0.3rem 0 0 0;">{public_ip}</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="glass-card"><span style="color: #8B95A5;">Local IP</span><p style="color: #00C853; font-weight: 600; margin: 0.3rem 0 0 0;">{local_ip}</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="glass-card"><span style="color: #8B95A5;">MAC Address</span><p style="color: #8B5CF6; font-weight: 600; margin: 0.3rem 0 0 0; font-size: 0.85rem;">{mac}</p></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    attacks = {
        "DDoS Attack": {"risk": 95, "color": "#FF4444", "steps": ["Initializing botnet...", "Targeting server...", "Launching SYN flood...", "SOC ALERT: DDoS detected!", "BLOCKED - Rate limiting enabled"]},
        "Port Scan": {"risk": 72, "color": "#FF8C00", "steps": ["Scanning ports...", "Open: 22, 80, 443", "SOC ALERT: Port scan!", "BLOCKED - IP banned"]},
        "Brute Force": {"risk": 78, "color": "#FF8C00", "steps": ["Target: SSH", "Attempt 1: FAILED", "50+ attempts detected", "SOC ALERT: Brute force!", "BLOCKED - Account locked"]},
        "SQL Injection": {"risk": 91, "color": "#FF4444", "steps": ["Payload: ' OR 1=1", "Attempting bypass...", "SOC ALERT: SQLi detected!", "BLOCKED - Session terminated"]},
        "Ransomware": {"risk": 98, "color": "#FF4444", "steps": ["Malware executing...", "Connecting to C2...", "SOC ALERT: Ransomware!", "BLOCKED - Endpoint isolated"]}
    }
    
    attack = st.selectbox("Select Attack Type", list(attacks.keys()))
    
    if st.button("Launch Simulation", type="primary"):
        st.markdown(section_title("Attack Log"), unsafe_allow_html=True)
        
        log_container = st.empty()
        logs = []
        progress = st.progress(0)
        
        for i, step in enumerate(attacks[attack]["steps"]):
            time.sleep(0.5)
            
            if "ALERT" in step or "BLOCKED" in step:
                color = "#FF4444"
            else:
                color = "#00D4FF"
            
            logs.append(f'<div style="padding: 0.5rem; border-left: 3px solid {color}; margin: 0.3rem 0; background: rgba(0,0,0,0.3);"><span style="color: #8B95A5; font-family: monospace;">[{datetime.now().strftime("%H:%M:%S")}]</span> <span style="color: {color};">{step}</span></div>')
            
            log_container.markdown(f'<div style="background: rgba(26, 31, 46, 0.8); padding: 1rem; border-radius: 12px; max-height: 300px; overflow-y: auto;">{"".join(logs)}</div>', unsafe_allow_html=True)
            progress.progress((i + 1) / len(attacks[attack]["steps"]))
        
        st.success(f"Attack blocked! Risk Score: {attacks[attack]['risk']}/100")

with tab2:
    if user.get('role') != 'admin':
        st.error("Admin access required for penetration testing tools")
        st.stop()
    
    st.markdown(section_title("Penetration Testing"), unsafe_allow_html=True)
    st.warning("**Authorized Use Only** - Only test systems you own or have permission to test")
    
    target = st.text_input("Target IP Address", placeholder="192.168.1.1")
    
    scan_type = st.selectbox("Scan Type", [
        "Quick Scan (22 common ports)",
        "Web Ports (80, 443, 8080)",
        "Full Scan (1-1024)"
    ])
    
    port_lists = {
        "Quick Scan (22 common ports)": [21,22,23,25,53,80,110,139,143,443,445,993,1433,3306,3389,5432,5900,8080,8443,27017,6379,11211],
        "Web Ports (80, 443, 8080)": [80, 443, 8080, 8443, 8000, 3000],
        "Full Scan (1-1024)": list(range(1, 1025))
    }
    
    if st.button("Start Port Scan", type="primary") and target:
        ports = port_lists[scan_type]
        
        def check_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((target, port))
                sock.close()
                return port if result == 0 else None
            except:
                return None
        
        st.markdown(section_title(f"Scanning {len(ports)} ports..."), unsafe_allow_html=True)
        
        progress = st.progress(0)
        open_ports = []
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(check_port, p): p for p in ports}
            done = 0
            for future in as_completed(futures):
                done += 1
                progress.progress(done / len(ports))
                result = future.result()
                if result:
                    open_ports.append(result)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00D4FF;">{len(open_ports)}</p><p class="metric-label">Open Ports</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00C853;">{len(ports) - len(open_ports)}</p><p class="metric-label">Closed/Filtered</p></div>', unsafe_allow_html=True)
        
        if open_ports:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(section_title("Open Ports"), unsafe_allow_html=True)
            
            services = {21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS", 80:"HTTP", 110:"POP3", 139:"NetBIOS", 143:"IMAP", 443:"HTTPS", 445:"SMB", 993:"IMAPS", 1433:"MSSQL", 3306:"MySQL", 3389:"RDP", 5432:"PostgreSQL", 5900:"VNC", 8080:"HTTP-Proxy"}
            
            for p in sorted(open_ports):
                svc = services.get(p, "Unknown")
                risk_color = "#FF4444" if p in [23, 445, 3389, 21] else "#00C853"
                st.markdown(f"""
                    <div class="glass-card" style="margin: 0.3rem 0; padding: 0.8rem 1.2rem; border-left: 3px solid {risk_color};">
                        <span style="color: #FAFAFA; font-weight: 600;">Port {p}</span>
                        <span style="color: #8B95A5; margin-left: 1rem;">{svc}</span>
                        <span style="color: {risk_color}; float: right;">OPEN</span>
                    </div>
                """, unsafe_allow_html=True)
            
            # Vulnerability check
            vulns = []
            if 23 in open_ports: vulns.append(("CRITICAL", "Telnet", "Unencrypted protocol - use SSH instead"))
            if 445 in open_ports: vulns.append(("CRITICAL", "SMB", "Vulnerable to ransomware attacks"))
            if 3389 in open_ports: vulns.append(("HIGH", "RDP", "Exposed to brute force attacks"))
            if 21 in open_ports: vulns.append(("HIGH", "FTP", "Unencrypted file transfer"))
            
            if vulns:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(section_title("Vulnerabilities Found"), unsafe_allow_html=True)
                for sev, svc, desc in vulns:
                    sev_color = "#FF4444" if sev == "CRITICAL" else "#FF8C00"
                    st.markdown(f"""
                        <div class="alert-card" style="border-left-color: {sev_color};">
                            <span style="color: {sev_color}; font-weight: 700;">[{sev}] {svc}</span>
                            <p style="color: #FAFAFA; margin: 0.3rem 0 0 0;">{desc}</p>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No open ports found on target")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Security Testing</p></div>', unsafe_allow_html=True)
