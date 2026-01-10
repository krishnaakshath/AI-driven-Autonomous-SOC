import streamlit as st
import time
import random
import os
import sys
import socket
import uuid
import requests
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Attack Simulation | SOC", page_icon="A", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .sim-card {
        background: linear-gradient(135deg, rgba(255, 68, 68, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%);
        border: 1px solid rgba(255, 68, 68, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .sim-card:hover {
        border-color: #FF4444;
        transform: translateY(-3px);
    }
    .attack-log {
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        max-height: 400px;
        overflow-y: auto;
    }
    .log-entry { margin: 0.3rem 0; }
    .log-time { color: #8B95A5; }
    .log-info { color: #00D4FF; }
    .log-warning { color: #FF8C00; }
    .log-danger { color: #FF4444; }
    .log-success { color: #00C853; }
    .stat-box {
        background: rgba(26, 31, 46, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .device-info {
        background: rgba(0, 212, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
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

LOGS_FILE = ".attack_logs.json"


def get_device_info():
    info = {
        "timestamp": datetime.now().isoformat(),
        "user_email": user.get("email", "unknown"),
        "user_name": user.get("name", "unknown"),
        "hostname": socket.gethostname(),
        "local_ip": "Unknown",
        "public_ip": "Unknown",
        "mac_address": "Unknown",
        "user_agent": "Streamlit App"
    }
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["local_ip"] = s.getsockname()[0]
        s.close()
    except:
        pass
    
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0,2*6,2)][::-1])
        info["mac_address"] = mac.upper()
    except:
        pass
    
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        if response.status_code == 200:
            info["public_ip"] = response.json().get("ip", "Unknown")
    except:
        pass
    
    return info


def log_attack_event(attack_type, device_info, risk_score):
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r') as f:
                logs = json.load(f)
        except:
            pass
    
    log_entry = {
        "id": len(logs) + 1,
        "timestamp": datetime.now().isoformat(),
        "attack_type": attack_type,
        "risk_score": risk_score,
        "user": device_info.get("user_email"),
        "user_name": device_info.get("user_name"),
        "hostname": device_info.get("hostname"),
        "local_ip": device_info.get("local_ip"),
        "public_ip": device_info.get("public_ip"),
        "mac_address": device_info.get("mac_address"),
        "status": "BLOCKED"
    }
    
    logs.append(log_entry)
    
    with open(LOGS_FILE, 'w') as f:
        json.dump(logs[-100:], f, indent=2)
    
    return log_entry


st.markdown("# Attack Simulation Lab")
st.markdown("Simulate cyber attacks to test SOC detection and response capabilities")
st.markdown("---")

device_info = get_device_info()

st.markdown("### Device Information Captured")
col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.markdown(f"""
        <div class="device-info">
            <p style="color: #8B95A5; margin: 0; font-size: 0.8rem;">PUBLIC IP</p>
            <p style="color: #00D4FF; font-size: 1.2rem; font-weight: 600; margin: 0;">{device_info['public_ip']}</p>
        </div>
    """, unsafe_allow_html=True)

with col_d2:
    st.markdown(f"""
        <div class="device-info">
            <p style="color: #8B95A5; margin: 0; font-size: 0.8rem;">LOCAL IP</p>
            <p style="color: #00D4FF; font-size: 1.2rem; font-weight: 600; margin: 0;">{device_info['local_ip']}</p>
        </div>
    """, unsafe_allow_html=True)

with col_d3:
    st.markdown(f"""
        <div class="device-info">
            <p style="color: #8B95A5; margin: 0; font-size: 0.8rem;">MAC ADDRESS</p>
            <p style="color: #00D4FF; font-size: 1.2rem; font-weight: 600; margin: 0;">{device_info['mac_address']}</p>
        </div>
    """, unsafe_allow_html=True)

col_d4, col_d5 = st.columns(2)
with col_d4:
    st.markdown(f"""
        <div class="device-info">
            <p style="color: #8B95A5; margin: 0; font-size: 0.8rem;">HOSTNAME</p>
            <p style="color: #FAFAFA; font-size: 1rem; font-weight: 500; margin: 0;">{device_info['hostname']}</p>
        </div>
    """, unsafe_allow_html=True)

with col_d5:
    st.markdown(f"""
        <div class="device-info">
            <p style="color: #8B95A5; margin: 0; font-size: 0.8rem;">LOGGED IN USER</p>
            <p style="color: #FAFAFA; font-size: 1rem; font-weight: 500; margin: 0;">{device_info['user_name']} ({device_info['user_email']})</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

attack_types = {
    "DDoS Attack": {
        "icon": "DDoS",
        "description": "Distributed Denial of Service - flood target with traffic",
        "severity": "CRITICAL",
        "risk": 95,
        "steps": [
            ("Initializing botnet nodes...", "info"),
            (f"Source Device: {device_info['hostname']} ({device_info['public_ip']})", "info"),
            (f"MAC Address: {device_info['mac_address']}", "info"),
            ("Connecting to 500+ compromised hosts...", "warning"),
            ("Targeting server: srv-web-01", "danger"),
            ("Launching SYN flood attack...", "danger"),
            ("Traffic volume: 10 Gbps", "danger"),
            ("SOC ALERT: DDoS detected!", "danger"),
            ("ML Risk Score: 95/100", "warning"),
            ("Zero Trust Decision: BLOCK", "danger"),
            ("Automated Response: Rate limiting enabled", "success"),
            ("Attack mitigated successfully", "success")
        ]
    },
    "Port Scan": {
        "icon": "SCAN",
        "description": "Reconnaissance scan to discover open ports and services",
        "severity": "HIGH",
        "risk": 72,
        "steps": [
            (f"Attacker Device: {device_info['hostname']}", "info"),
            (f"Source IP: {device_info['public_ip']}", "info"),
            (f"MAC: {device_info['mac_address']}", "info"),
            ("Scanning port range: 1-65535", "warning"),
            ("Open port found: 22 (SSH)", "warning"),
            ("Open port found: 80 (HTTP)", "warning"),
            ("Open port found: 443 (HTTPS)", "warning"),
            ("Open port found: 3306 (MySQL)", "danger"),
            ("SOC ALERT: Port scan detected!", "danger"),
            ("ML Risk Score: 72/100", "warning"),
            ("Zero Trust Decision: BLOCK", "danger"),
            ("Automated Response: IP blocked", "success")
        ]
    },
    "Brute Force": {
        "icon": "BRUTE",
        "description": "Password guessing attack on authentication systems",
        "severity": "HIGH",
        "risk": 78,
        "steps": [
            ("Target: SSH authentication srv-auth-01", "info"),
            (f"Attacker: {device_info['public_ip']} ({device_info['hostname']})", "warning"),
            (f"Device MAC: {device_info['mac_address']}", "info"),
            ("Attempt 1: admin:password123 - FAILED", "warning"),
            ("Attempt 2: admin:admin - FAILED", "warning"),
            ("Attempt 3: root:toor - FAILED", "warning"),
            ("50+ failed attempts detected", "danger"),
            ("SOC ALERT: Brute force attack!", "danger"),
            ("ML Risk Score: 78/100", "warning"),
            ("Zero Trust Decision: BLOCK", "danger"),
            ("Automated Response: Account locked, IP banned", "success")
        ]
    },
    "SQL Injection": {
        "icon": "SQLi",
        "description": "Database attack via malicious SQL queries",
        "severity": "CRITICAL",
        "risk": 91,
        "steps": [
            ("Target: /api/users endpoint", "info"),
            (f"Attacker IP: {device_info['public_ip']}", "info"),
            (f"Device: {device_info['hostname']} (MAC: {device_info['mac_address']})", "info"),
            ("Payload: ' OR '1'='1' --", "danger"),
            ("Attempting to bypass authentication...", "warning"),
            ("Injecting DROP TABLE users;", "danger"),
            ("WAF Alert: SQL injection detected!", "danger"),
            ("SOC ALERT: Critical SQL injection!", "danger"),
            ("ML Risk Score: 91/100", "warning"),
            ("Zero Trust Decision: BLOCK", "danger"),
            ("Automated Response: Session terminated", "success"),
            ("Database protected, attack blocked", "success")
        ]
    },
    "Ransomware": {
        "icon": "RANSOM",
        "description": "Malware that encrypts files and demands payment",
        "severity": "CRITICAL",
        "risk": 98,
        "steps": [
            (f"Infected Device: {device_info['hostname']}", "danger"),
            (f"Device IP: {device_info['public_ip']} / {device_info['local_ip']}", "info"),
            (f"MAC Address: {device_info['mac_address']}", "info"),
            ("Malicious email attachment opened", "warning"),
            ("Payload executing: cryptolocker.exe", "danger"),
            ("Connecting to C2 server: evil.onion", "danger"),
            ("Generating encryption keys...", "danger"),
            ("SOC ALERT: Ransomware behavior detected!", "danger"),
            ("ML Risk Score: 98/100", "danger"),
            ("Zero Trust Decision: BLOCK", "danger"),
            ("Automated Response: Endpoint isolated", "success"),
            ("Process terminated, files protected", "success"),
            ("Threat neutralized before encryption", "success")
        ]
    }
}

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Select Attack Type")
    
    selected_attack = st.selectbox(
        "Choose an attack to simulate",
        options=list(attack_types.keys()),
        format_func=lambda x: f"[{attack_types[x]['icon']}] {x}"
    )
    
    attack = attack_types[selected_attack]
    
    st.markdown(f"""
        <div class="sim-card">
            <h3 style="color: #FF6B6B; margin: 0;">[{attack['icon']}] {selected_attack}</h3>
            <p style="color: #8B95A5; margin: 0.5rem 0;">{attack['description']}</p>
            <div style="display: flex; gap: 2rem; margin-top: 1rem;">
                <div>
                    <span style="color: #8B95A5;">Severity:</span>
                    <span style="color: #FF4444; font-weight: 600;"> {attack['severity']}</span>
                </div>
                <div>
                    <span style="color: #8B95A5;">Risk Score:</span>
                    <span style="color: #FF4444; font-weight: 600;"> {attack['risk']}/100</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### Simulation Stats")
    st.markdown(f"""
        <div class="stat-box">
            <p style="color: #8B95A5; margin: 0; font-size: 0.8rem;">ATTACKS SIMULATED</p>
            <p style="color: #00D4FF; font-size: 2rem; font-weight: 700; margin: 0;">{st.session_state.get('sim_count', 0)}</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="stat-box">
            <p style="color: #8B95A5; margin: 0; font-size: 0.8rem;">THREATS BLOCKED</p>
            <p style="color: #00C853; font-size: 2rem; font-weight: 700; margin: 0;">{st.session_state.get('blocked_count', 0)}</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

send_alerts = st.checkbox("Send real Telegram/Gmail alerts", value=False)

if st.button("Launch Attack Simulation", type="primary", use_container_width=True):
    st.session_state['sim_count'] = st.session_state.get('sim_count', 0) + 1
    
    log_entry = log_attack_event(selected_attack, device_info, attack['risk'])
    
    st.markdown("### Attack Log")
    log_container = st.empty()
    
    logs = []
    progress_bar = st.progress(0)
    
    for i, (message, level) in enumerate(attack['steps']):
        time.sleep(0.4)
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        level_class = f"log-{level}"
        
        logs.append(f'<div class="log-entry"><span class="log-time">[{timestamp}]</span> <span class="{level_class}">{message}</span></div>')
        
        log_html = '<div class="attack-log">' + ''.join(logs) + '</div>'
        log_container.markdown(log_html, unsafe_allow_html=True)
        
        progress_bar.progress((i + 1) / len(attack['steps']))
    
    st.session_state['blocked_count'] = st.session_state.get('blocked_count', 0) + 1
    
    st.success(f"Attack simulation complete! SOC successfully detected and blocked the {selected_attack}.")
    
    if send_alerts:
        try:
            from alerting.alert_service import trigger_alert
            
            event = {
                'attack_type': f"[SIMULATION] {selected_attack}",
                'risk_score': attack['risk'],
                'source_ip': device_info['public_ip'],
                'mac_address': device_info['mac_address'],
                'hostname': device_info['hostname'],
                'target_host': 'srv-web-01',
                'access_decision': 'BLOCK',
                'automated_response': 'Attack simulated and blocked',
                'user': device_info['user_email']
            }
            
            result = trigger_alert(event)
            if result.get('telegram') or result.get('email'):
                st.info("Alert sent to your Telegram/Gmail!")
        except Exception as e:
            st.warning(f"Alert not sent: {str(e)}")

    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.metric("Risk Score", f"{attack['risk']}/100", delta=None)
    with col_r2:
        st.metric("Decision", "BLOCK", delta=None)
    with col_r3:
        st.metric("Response Time", f"{random.uniform(0.1, 0.5):.2f}s", delta=None)

if user.get('role') == 'admin':
    st.markdown("---")
    st.markdown("### Attack Logs (Admin Only)")
    
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r') as f:
                logs = json.load(f)
            
            if logs:
                st.dataframe(
                    logs[-20:][::-1],
                    use_container_width=True,
                    hide_index=True
                )
                
                if st.button("Clear Logs"):
                    os.remove(LOGS_FILE)
                    st.success("Logs cleared")
                    st.rerun()
            else:
                st.info("No attack logs yet.")
        except:
            st.info("No attack logs yet.")
    else:
        st.info("No attack logs yet.")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">AI-Driven Autonomous SOC | Attack Simulation Lab</p></div>', unsafe_allow_html=True)
