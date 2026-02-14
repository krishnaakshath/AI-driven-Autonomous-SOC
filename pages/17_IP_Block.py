import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime
import random
import io
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Bulk IP Blocking | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("Bulk IP Blocking", "Upload and manage IP blocklists for automated threat blocking"), unsafe_allow_html=True)

# Persistent storage via FirewallShim
from services.firewall_shim import firewall

st.success(" Persistent Firewal Service Connected")

# Tabs
tab1, tab2, tab3 = st.tabs([" Upload Blocklist", " Current Blocklist", " Statistics"])

with tab1:
    st.markdown(section_title("Upload IP Blocklist"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <p style="color: #8B95A5; margin: 0;">
                Upload a CSV or TXT file containing IP addresses to block. 
                Supported formats: one IP per line, or CSV with 'ip' column.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "txt"])
    
    col1, col2 = st.columns(2)
    with col1:
        default_reason = st.text_input("Default Reason", value="Bulk Import", placeholder="Reason for blocking")
    with col2:
        block_duration = st.selectbox("Block Duration", ["Permanent", "24 Hours", "7 Days", "30 Days"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
                if 'ip' in df.columns:
                    ips = df['ip'].tolist()
                else:
                    ips = df.iloc[:, 0].tolist()
            else:
                content = uploaded_file.read().decode('utf-8')
                ips = [line.strip() for line in content.split('\n') if line.strip()]
            
            st.success(f"Found **{len(ips)}** IP addresses in file")
            
            # Preview
            with st.expander("Preview IPs"):
                st.code('\n'.join(ips[:20]))
                if len(ips) > 20:
                    st.caption(f"...and {len(ips) - 20} more")
            
            if st.button(" Block All IPs", type="primary"):
                added_count = 0
                for ip in ips:
                    if firewall.block_ip(ip, reason=default_reason, source="Bulk Upload"):
                        added_count += 1
                
                st.success(f" Added **{added_count}** IPs to blocklist")
                time.sleep(1)
                st.rerun()
                
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Add Single IP")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        single_ip = st.text_input("IP Address", placeholder="192.168.1.100")
    with col2:
        single_reason = st.text_input("Reason", placeholder="Malicious activity", key="single_reason")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", use_container_width=True):
            if single_ip:
                if firewall.block_ip(single_ip, reason=single_reason or "Manual block", source="Dashboard"):
                    st.success(f"Added {single_ip} to blocklist")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Failed to block IP")

with tab2:
    st.markdown(section_title("Current Blocklist"), unsafe_allow_html=True)
    
    # Load from Shim
    blocklist = firewall.get_all_blocked_ips()
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("Search IP", placeholder="Filter by IP address...")
    with col2:
        status_filter = st.selectbox("Status", ["All", "Active", "Disabled"])
    
    # Filter blocklist
    filtered = blocklist
    if search:
        filtered = [b for b in filtered if search in b['ip']]
    if status_filter != "All":
        filtered = [b for b in filtered if b['status'] == status_filter]
    
    st.markdown(f"**{len(filtered)}** entries")
    
    # Display blocklist
    for i, entry in enumerate(filtered):
        status_color = "#00C853" if entry['status'] == "Active" else "#8B95A5"
        
        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 1, 1])
        
        with col1:
            st.code(entry['ip'])
        with col2:
            st.markdown(f"<span style='color: #8B95A5;'>{entry['reason']}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color: #8B95A5;'>{entry.get('added', 'N/A')}</span>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<span style='color: {status_color};'></span> {entry['status']}", unsafe_allow_html=True)
        with col5:
            if st.button("", key=f"remove_{i}"):
                firewall.unblock_ip(entry['ip'])
                st.rerun()
    
    # Bulk actions
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        df = pd.DataFrame(blocklist)
        csv = df.to_csv(index=False)
        st.download_button(" Export Blocklist", csv, "ip_blocklist.csv", "text/csv", use_container_width=True)
    
    with col2:
        if st.button(" Sync to Firewall", use_container_width=True):
            st.info("Firewall sync simulated - would push to iptables/firewall API")
    
    with col3:
        if st.button(" Clear All", use_container_width=True):
            # Not implemented in Shim yet, but we can loop unblock or clear file?
            # Safe option: Loop
            for entry in blocklist:
                firewall.unblock_ip(entry['ip'])
            st.rerun()

with tab3:
    st.markdown(section_title("Blocking Statistics"), unsafe_allow_html=True)
    
    blocklist = firewall.get_all_blocked_ips()
    
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(blocklist)
    active = len([b for b in blocklist if b['status'] == 'Active'])
    today_str = datetime.now().strftime("%Y-%m-%d")
    blocked_today = len([b for b in blocklist if b.get('added', '').startswith(today_str)])
    prevention_rate = f"{int(active / total * 100)}%" if total > 0 else "0%"
    
    metrics = [
        ("Total Blocked IPs", total, "#FF4444"),
        ("Active Blocks", active, "#00C853"),
        ("Blocked Today", blocked_today, "#FF8C00"),
        ("Attack Prevention", prevention_rate, "#00D4FF")
    ]
    
    for col, (label, value, color) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(26,31,46,0.8), rgba(26,31,46,0.6));
                border: 1px solid {color}40;
                border-radius: 16px;
                padding: 1.5rem;
                text-align: center;
            ">
                <div style="font-size: 2rem; font-weight: 800; color: {color};">{value}</div>
                <div style="color: #8B95A5;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Top blocked reasons
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Top Block Reasons")
    
    reasons = {}
    for entry in blocklist:
        reasons[entry['reason']] = reasons.get(entry['reason'], 0) + 1
    
    for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
        pct = (count / total * 100) if total > 0 else 0
        st.markdown(f"""
        <div style="margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="color: #FAFAFA;">{reason}</span>
                <span style="color: #8B95A5;">{count} ({pct:.1f}%)</span>
            </div>
            <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 8px;">
                <div style="background: #00D4FF; width: {pct}%; height: 100%; border-radius: 4px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Bulk IP Blocking</p></div>', unsafe_allow_html=True)
