import streamlit as st
import os
import sys
import json
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Admin Panel | SOC", page_icon="A", layout="wide")

from ui.theme import PREMIUM_CSS, page_header, section_title
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

from auth.auth_manager import check_auth, show_user_info, get_all_users, update_user_role, delete_user, register_user

user = check_auth()
if not user:
    st.switch_page("pages/0_Login.py")
    st.stop()

if user.get('role') != 'admin':
    st.error("Access Denied - Admin privileges required")
    st.stop()

show_user_info(user)

st.markdown(page_header("Admin Panel", "System administration and security management"), unsafe_allow_html=True)

# Stats
users = get_all_users()
blocked_file = ".blocked_ips.json"
blocked_ips = []
if os.path.exists(blocked_file):
    with open(blocked_file, 'r') as f:
        blocked_ips = json.load(f)

attack_logs_file = ".attack_logs.json"
attack_logs = []
if os.path.exists(attack_logs_file):
    with open(attack_logs_file, 'r') as f:
        attack_logs = json.load(f)

total_users = len(users)
admin_count = sum(1 for u in users.values() if u.get('role') == 'admin')

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00D4FF;">{total_users}</p><p class="metric-label">Total Users</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF4444;">{admin_count}</p><p class="metric-label">Administrators</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF8C00;">{len(blocked_ips)}</p><p class="metric-label">Blocked IPs</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #8B5CF6;">{len(attack_logs)}</p><p class="metric-label">Attack Logs</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Threat Scanner", "Blocked IPs", "User Management", "Attack Logs", "System"])

with tab1:
    st.markdown(section_title("IP Threat Scanner"), unsafe_allow_html=True)
    
    config = {}
    if os.path.exists('.soc_config.json'):
        with open('.soc_config.json', 'r') as f:
            config = json.load(f)
    
    VT_KEY = config.get('virustotal_api_key', '')
    
    if not VT_KEY:
        st.warning("Add VirusTotal API key in Settings to enable threat scanning")
    else:
        ip_to_scan = st.text_input("Enter IP Address", placeholder="1.2.3.4")
        
        if st.button("Scan IP", type="primary") and ip_to_scan:
            with st.spinner("Scanning with VirusTotal..."):
                try:
                    resp = requests.get(
                        f'https://www.virustotal.com/api/v3/ip_addresses/{ip_to_scan}',
                        headers={'x-apikey': VT_KEY},
                        timeout=15
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()['data']['attributes']
                        stats = data.get('last_analysis_stats', {})
                        
                        mal = stats.get('malicious', 0)
                        sus = stats.get('suspicious', 0)
                        
                        if mal > 0:
                            verdict, color = "MALICIOUS", "#FF4444"
                        elif sus > 2:
                            verdict, color = "SUSPICIOUS", "#FF8C00"
                        else:
                            verdict, color = "CLEAN", "#00C853"
                        
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: {color};">{verdict}</p><p class="metric-label">Verdict</p></div>', unsafe_allow_html=True)
                        with c2:
                            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF4444;">{mal}</p><p class="metric-label">Malicious</p></div>', unsafe_allow_html=True)
                        with c3:
                            st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00C853;">{stats.get("harmless", 0)}</p><p class="metric-label">Clean</p></div>', unsafe_allow_html=True)
                        
                        if mal > 0:
                            if st.button(f"Block {ip_to_scan}", type="primary"):
                                blocked_ips.append({
                                    "ip": ip_to_scan,
                                    "reason": f"VirusTotal: {mal} malicious detections",
                                    "blocked_by": user.get('email'),
                                    "blocked_at": datetime.now().isoformat()
                                })
                                with open(blocked_file, 'w') as f:
                                    json.dump(blocked_ips, f, indent=2)
                                st.success(f"Blocked {ip_to_scan}")
                                st.rerun()
                    else:
                        st.error("IP not found in database")
                except Exception as e:
                    st.error(f"Scan error: {e}")

with tab2:
    st.markdown(section_title("Blocked IP Addresses"), unsafe_allow_html=True)
    
    if blocked_ips:
        for i, ip in enumerate(blocked_ips):
            st.markdown(f"""
                <div class="glass-card" style="margin: 0.5rem 0; border-left: 3px solid #FF4444;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: #FAFAFA; font-weight: 600; font-family: monospace;">{ip.get('ip')}</span>
                            <p style="color: #8B95A5; margin: 0.3rem 0 0 0; font-size: 0.85rem;">{ip.get('reason', 'Manual block')}</p>
                            <p style="color: #8B95A5; margin: 0; font-size: 0.75rem;">By: {ip.get('blocked_by', 'Unknown')}</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Unblock", key=f"unblock_{i}"):
                blocked_ips.pop(i)
                with open(blocked_file, 'w') as f:
                    json.dump(blocked_ips, f, indent=2)
                st.success("IP unblocked")
                st.rerun()
    else:
        st.info("No blocked IPs")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_title("Block New IP"), unsafe_allow_html=True)
    
    new_ip = st.text_input("IP Address", key="new_block_ip")
    new_reason = st.text_input("Reason", key="new_block_reason")
    
    if st.button("Block IP", type="primary"):
        if new_ip:
            blocked_ips.append({
                "ip": new_ip,
                "reason": new_reason or "Manual block",
                "blocked_by": user.get('email'),
                "blocked_at": datetime.now().isoformat()
            })
            with open(blocked_file, 'w') as f:
                json.dump(blocked_ips, f, indent=2)
            st.success(f"Blocked {new_ip}")
            st.rerun()

with tab3:
    st.markdown(section_title("User Management"), unsafe_allow_html=True)
    
    for email, u in users.items():
        role_color = "#FF4444" if u.get('role') == 'admin' else "#00D4FF"
        st.markdown(f"""
            <div class="glass-card" style="margin: 0.5rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #FAFAFA; font-weight: 600;">{u.get('name', 'Unknown')}</span>
                        <span style="color: #8B95A5; margin-left: 1rem;">{email}</span>
                        <span style="color: {role_color}; margin-left: 1rem; text-transform: uppercase; font-size: 0.75rem;">{u.get('role', 'analyst')}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            new_role = st.selectbox("Role", ["analyst", "admin"], key=f"role_{email}", index=0 if u.get('role') == 'analyst' else 1)
            if st.button("Update", key=f"update_{email}"):
                update_user_role(email, new_role)
                st.success(f"Updated {email}")
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_title("Create New User"), unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        new_name = st.text_input("Name", key="new_user_name")
    with c2:
        new_email = st.text_input("Email", key="new_user_email")
    with c3:
        new_password = st.text_input("Password", type="password", key="new_user_pass")
    
    if st.button("Create User", type="primary"):
        if new_name and new_email and new_password:
            success, msg = register_user(new_email, new_password, new_name)
            if success:
                st.success("User created!")
                st.rerun()
            else:
                st.error(msg)

with tab4:
    st.markdown(section_title("Attack Simulation Logs"), unsafe_allow_html=True)
    
    if attack_logs:
        for log in attack_logs[-10:]:
            st.markdown(f"""
                <div class="glass-card" style="margin: 0.5rem 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #FF8C00; font-weight: 600;">{log.get('attack_type', 'Unknown')}</span>
                        <span style="color: #8B95A5;">{log.get('timestamp', '')[:19]}</span>
                    </div>
                    <p style="color: #8B95A5; margin: 0.3rem 0 0 0; font-size: 0.85rem;">
                        User: {log.get('user', 'Unknown')} | IP: {log.get('public_ip', 'Unknown')} | Risk: {log.get('risk_score', 0)}
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("Clear All Logs", type="secondary"):
            with open(attack_logs_file, 'w') as f:
                json.dump([], f)
            st.success("Logs cleared")
            st.rerun()
    else:
        st.info("No attack logs")

with tab5:
    st.markdown(section_title("System Information"), unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="glass-card">
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                <div>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">Platform</p>
                    <p style="color: #FAFAFA; margin: 0.2rem 0 0 0; font-weight: 600;">AI-Driven SOC v2.0</p>
                </div>
                <div>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">Environment</p>
                    <p style="color: #FAFAFA; margin: 0.2rem 0 0 0; font-weight: 600;">Production</p>
                </div>
                <div>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">Server Time</p>
                    <p style="color: #FAFAFA; margin: 0.2rem 0 0 0; font-weight: 600;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div>
                    <p style="color: #8B95A5; margin: 0; font-size: 0.85rem;">Status</p>
                    <p style="color: #00C853; margin: 0.2rem 0 0 0; font-weight: 600;">● Operational</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Admin Panel</p></div>', unsafe_allow_html=True)
