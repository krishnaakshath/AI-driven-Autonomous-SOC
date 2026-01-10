import streamlit as st
import os
import sys
import json
import socket
import subprocess
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Admin Panel | SOC", page_icon="A", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .admin-header {
        background: linear-gradient(135deg, rgba(255, 68, 68, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
        border: 1px solid rgba(255, 68, 68, 0.3);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: rgba(26, 31, 46, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #00D4FF;
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-label {
        color: #8B95A5;
        font-size: 0.85rem;
        text-transform: uppercase;
        margin: 0;
    }
    
    .threat-card {
        background: rgba(26, 31, 46, 0.8);
        border-left: 4px solid;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
    }
    .threat-critical { border-left-color: #FF4444; }
    .threat-high { border-left-color: #FF8C00; }
    .threat-medium { border-left-color: #FFD700; }
    .threat-low { border-left-color: #00C853; }
    
    .user-row {
        background: rgba(26, 31, 46, 0.6);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .blocked-ip {
        background: rgba(255, 68, 68, 0.15);
        border: 1px solid rgba(255, 68, 68, 0.3);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.3rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .scan-result {
        background: rgba(0, 212, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

from auth.auth_manager import check_auth, show_user_info, load_users, save_users, hash_password

user = check_auth()
if not user:
    st.switch_page("pages/0_Login.py")
    st.stop()

if user.get('role') != 'admin':
    st.error("Access Denied - Admin privileges required")
    st.info("Only administrators can access this page.")
    st.stop()

show_user_info(user)

BLOCKED_IPS_FILE = ".blocked_ips.json"
ATTACK_LOGS_FILE = ".attack_logs.json"


def load_blocked_ips():
    if os.path.exists(BLOCKED_IPS_FILE):
        try:
            with open(BLOCKED_IPS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def save_blocked_ips(ips):
    with open(BLOCKED_IPS_FILE, 'w') as f:
        json.dump(ips, f, indent=2)


def load_attack_logs():
    if os.path.exists(ATTACK_LOGS_FILE):
        try:
            with open(ATTACK_LOGS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []


def scan_ip(ip):
    result = {"ip": ip, "status": "unknown", "details": {}}
    
    try:
        response = requests.get(
            f"https://www.virustotal.com/api/v3/ip_addresses/{ip}",
            headers={"x-apikey": get_vt_key()},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json().get('data', {}).get('attributes', {})
            stats = data.get('last_analysis_stats', {})
            result["details"]["malicious"] = stats.get('malicious', 0)
            result["details"]["suspicious"] = stats.get('suspicious', 0)
            result["details"]["country"] = data.get('country', 'Unknown')
            result["details"]["as_owner"] = data.get('as_owner', 'Unknown')
            
            if stats.get('malicious', 0) > 0:
                result["status"] = "malicious"
            elif stats.get('suspicious', 0) > 2:
                result["status"] = "suspicious"
            else:
                result["status"] = "clean"
    except:
        result["status"] = "scan_failed"
    
    return result


def get_vt_key():
    try:
        with open('.soc_config.json', 'r') as f:
            return json.load(f).get('virustotal_api_key', '')
    except:
        return ''


st.markdown("""
    <div class="admin-header">
        <h1 style="margin: 0; color: #FAFAFA;">Admin Control Panel</h1>
        <p style="color: #8B95A5; margin: 0.5rem 0 0 0;">System administration and threat management</p>
    </div>
""", unsafe_allow_html=True)

data = load_users()
users = data.get("users", {})
blocked_ips = load_blocked_ips()
attack_logs = load_attack_logs()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #00D4FF;">{len(users)}</p>
            <p class="metric-label">Total Users</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    admin_count = sum(1 for u in users.values() if u.get('role') == 'admin')
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #FF4444;">{admin_count}</p>
            <p class="metric-label">Administrators</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #FF8C00;">{len(blocked_ips)}</p>
            <p class="metric-label">Blocked IPs</p>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #00C853;">{len(attack_logs)}</p>
            <p class="metric-label">Attack Logs</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Threat Scanner", "Blocked IPs", "User Management", "Attack Logs", "System Config"])

with tab1:
    st.markdown("### Network Threat Scanner")
    st.markdown("Scan IP addresses for threats and take action")
    
    col_scan1, col_scan2 = st.columns([3, 1])
    
    with col_scan1:
        ip_to_scan = st.text_input("Enter IP Address to Scan", placeholder="e.g., 45.33.32.156")
    
    with col_scan2:
        st.markdown("<br>", unsafe_allow_html=True)
        scan_btn = st.button("Scan IP", type="primary", use_container_width=True)
    
    if scan_btn and ip_to_scan:
        with st.spinner("Scanning IP address..."):
            result = scan_ip(ip_to_scan)
            
            if result["status"] == "malicious":
                st.markdown(f"""
                    <div class="scan-result" style="border-color: #FF4444; background: rgba(255, 68, 68, 0.15);">
                        <h3 style="color: #FF4444; margin: 0;">MALICIOUS IP DETECTED</h3>
                        <p style="color: #FAFAFA; font-size: 1.2rem; margin: 0.5rem 0;"><strong>{ip_to_scan}</strong></p>
                        <p style="color: #8B95A5;">Country: {result['details'].get('country', 'Unknown')} | 
                        Owner: {result['details'].get('as_owner', 'Unknown')}</p>
                        <p style="color: #FF4444;">Malicious votes: {result['details'].get('malicious', 0)} | 
                        Suspicious votes: {result['details'].get('suspicious', 0)}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("Block This IP", type="primary", key="block_scanned"):
                    if ip_to_scan not in blocked_ips:
                        blocked_ips.append({
                            "ip": ip_to_scan,
                            "reason": "Malicious - VirusTotal",
                            "blocked_by": user["email"],
                            "blocked_at": datetime.now().isoformat()
                        })
                        save_blocked_ips(blocked_ips)
                        st.success(f"IP {ip_to_scan} has been blocked!")
                        st.rerun()
                        
            elif result["status"] == "suspicious":
                st.markdown(f"""
                    <div class="scan-result" style="border-color: #FF8C00; background: rgba(255, 140, 0, 0.15);">
                        <h3 style="color: #FF8C00; margin: 0;">SUSPICIOUS IP</h3>
                        <p style="color: #FAFAFA; font-size: 1.2rem; margin: 0.5rem 0;"><strong>{ip_to_scan}</strong></p>
                        <p style="color: #8B95A5;">Country: {result['details'].get('country', 'Unknown')}</p>
                    </div>
                """, unsafe_allow_html=True)
                
            elif result["status"] == "clean":
                st.markdown(f"""
                    <div class="scan-result" style="border-color: #00C853; background: rgba(0, 200, 83, 0.15);">
                        <h3 style="color: #00C853; margin: 0;">CLEAN IP</h3>
                        <p style="color: #FAFAFA; font-size: 1.2rem; margin: 0.5rem 0;"><strong>{ip_to_scan}</strong></p>
                        <p style="color: #8B95A5;">Country: {result['details'].get('country', 'Unknown')} | 
                        Owner: {result['details'].get('as_owner', 'Unknown')}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Scan failed. Check your VirusTotal API key in Settings.")

with tab2:
    st.markdown("### Blocked IP Addresses")
    st.markdown("Manage blocked IPs and threats")
    
    col_add1, col_add2, col_add3 = st.columns([2, 2, 1])
    with col_add1:
        new_block_ip = st.text_input("IP Address", placeholder="Enter IP to block", key="new_ip")
    with col_add2:
        block_reason = st.text_input("Reason", placeholder="Why blocking?", key="reason")
    with col_add3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Block IP", type="primary", use_container_width=True):
            if new_block_ip:
                blocked_ips.append({
                    "ip": new_block_ip,
                    "reason": block_reason or "Manual block",
                    "blocked_by": user["email"],
                    "blocked_at": datetime.now().isoformat()
                })
                save_blocked_ips(blocked_ips)
                st.success(f"Blocked {new_block_ip}")
                st.rerun()
    
    st.markdown("---")
    
    if blocked_ips:
        for i, entry in enumerate(blocked_ips):
            ip = entry if isinstance(entry, str) else entry.get('ip', 'Unknown')
            reason = entry.get('reason', 'N/A') if isinstance(entry, dict) else 'N/A'
            blocked_by = entry.get('blocked_by', 'System') if isinstance(entry, dict) else 'System'
            
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                st.markdown(f"**{ip}**")
            with col2:
                st.caption(f"{reason} | By: {blocked_by}")
            with col3:
                if st.button("Unblock", key=f"unblock_{i}"):
                    blocked_ips.pop(i)
                    save_blocked_ips(blocked_ips)
                    st.success(f"Unblocked {ip}")
                    st.rerun()
    else:
        st.info("No blocked IPs. Your network is clean!")

with tab3:
    st.markdown("### User Management")
    
    for email, user_data in users.items():
        role_color = "#FF4444" if user_data.get('role') == 'admin' else "#00D4FF"
        
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{user_data.get('name', 'Unknown')}**")
            st.caption(email)
        
        with col2:
            st.markdown(f"<span style='color: {role_color};'>{user_data.get('role', 'analyst').upper()}</span>", unsafe_allow_html=True)
        
        with col3:
            new_role = st.selectbox(
                "Role",
                ["analyst", "admin"],
                index=1 if user_data.get('role') == 'admin' else 0,
                key=f"role_{email}",
                label_visibility="collapsed"
            )
        
        with col4:
            if new_role != user_data.get('role'):
                if st.button("Save", key=f"save_{email}"):
                    data["users"][email]["role"] = new_role
                    save_users(data)
                    st.success(f"Updated!")
                    st.rerun()
            elif email != user['email']:
                if st.button("Delete", key=f"del_{email}", type="secondary"):
                    del data["users"][email]
                    save_users(data)
                    st.rerun()
        
        st.markdown("---")
    
    st.markdown("### Add New User")
    with st.form("add_user"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Name")
            new_email = st.text_input("Email")
        with col2:
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["analyst", "admin"])
        
        if st.form_submit_button("Create User", type="primary"):
            if new_name and new_email and new_password:
                if new_email.lower() not in users:
                    data["users"][new_email.lower()] = {
                        "password": hash_password(new_password),
                        "name": new_name,
                        "role": new_role,
                        "created": datetime.now().isoformat(),
                        "last_login": None
                    }
                    save_users(data)
                    st.success(f"Created {new_email}")
                    st.rerun()
                else:
                    st.error("Email exists")

with tab4:
    st.markdown("### Attack Simulation Logs")
    
    if attack_logs:
        st.dataframe(
            attack_logs[-50:][::-1],
            use_container_width=True,
            hide_index=True
        )
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Clear All Logs", type="secondary"):
                os.remove(ATTACK_LOGS_FILE)
                st.success("Logs cleared")
                st.rerun()
    else:
        st.info("No attack logs recorded yet.")

with tab5:
    st.markdown("### System Configuration")
    
    config_file = ".soc_config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Security Thresholds")
        alert_threshold = st.slider("Alert Threshold", 0, 100, config.get('alert_threshold', 70))
        block_threshold = st.slider("Auto-Block Threshold", 0, 100, config.get('block_threshold', 70))
        restrict_threshold = st.slider("Restrict Threshold", 0, 100, config.get('restrict_threshold', 30))
    
    with col2:
        st.markdown("#### Notification Settings")
        auto_block = st.checkbox("Auto-block high risk", value=config.get('auto_block', True))
        enable_email = st.checkbox("Email Alerts", value=config.get('notification_email', True))
        enable_telegram = st.checkbox("Telegram Alerts", value=config.get('notification_telegram', True))
    
    if st.button("Save Configuration", type="primary"):
        config['alert_threshold'] = alert_threshold
        config['block_threshold'] = block_threshold
        config['restrict_threshold'] = restrict_threshold
        config['auto_block'] = auto_block
        config['notification_email'] = enable_email
        config['notification_telegram'] = enable_telegram
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        st.success("Configuration saved!")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">AI-Driven Autonomous SOC | Admin Panel</p></div>', unsafe_allow_html=True)
