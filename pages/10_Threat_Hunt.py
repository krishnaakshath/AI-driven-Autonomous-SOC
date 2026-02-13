import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Threat Hunting | SOC", page_icon="", layout="wide")

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("Threat Hunting", "Proactive threat hunting with IOC queries and hypothesis-driven investigation"), unsafe_allow_html=True)

# Import real threat intel service
try:
    from services.threat_intel import threat_intel, check_ip_reputation
    HAS_REAL_API = True
except ImportError:
    HAS_REAL_API = False

# IOC database (enhanced with real threat intelligence when available)
IOC_DATABASE = {
    "ips": [
        "45.33.32.156", "192.168.1.105", "10.0.0.50", "203.0.113.42", "198.51.100.23",
        "185.220.101.1", "91.219.236.222", "45.155.205.233"
    ],
    "domains": [
        "malware-c2.evil.com", "phishing-kit.xyz", "suspicious-cdn.net", "data-exfil.io",
        "coinminer-pool.com", "emotet-drops.ru", "trickbot-c2.cn"
    ],
    "hashes": [
        "d41d8cd98f00b204e9800998ecf8427e", "e99a18c428cb38d5f260853678922e03",
        "098f6bcd4621d373cade4e832627b4f6", "5d41402abc4b2a76b9719d911017c592"
    ],
    "processes": [
        "powershell.exe -encodedCommand", "cmd.exe /c certutil", "mimikatz.exe",
        "psexec.exe", "cobalt*.exe", "beacon.dll"
    ]
}

# Sample hunt queries
HUNT_QUERIES = [
    {"name": "Suspicious PowerShell", "query": "process.name:powershell.exe AND process.args:(-enc OR -encoded)", "category": "Execution"},
    {"name": "Lateral Movement", "query": "process.name:(psexec.exe OR wmic.exe) AND network.direction:outbound", "category": "Lateral Movement"},
    {"name": "Data Exfiltration", "query": "network.bytes_out:>1000000 AND destination.port:(443 OR 8443)", "category": "Exfiltration"},
    {"name": "C2 Beaconing", "query": "network.protocol:http AND bytes_out:<1000 AND interval:regular", "category": "C2"},
    {"name": "Credential Dumping", "query": "process.name:lsass.exe AND event.type:access", "category": "Credential Access"},
]

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([" IOC Search", " Hunt Queries", " Hypothesis Hunt", " Results"])

with tab1:
    st.markdown(section_title("Search for Indicators of Compromise"), unsafe_allow_html=True)
    
    # Show API status
    if HAS_REAL_API:
        st.success(" Connected to real threat intelligence APIs (AbuseIPDB, VirusTotal, OTX)")
    else:
        st.warning(" Using simulated data - configure API keys in Settings for real intelligence")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ioc_input = st.text_input("Enter IOC (IP, domain, hash, or process name)", placeholder="192.168.1.100 or malware.exe")
    
    with col2:
        ioc_type = st.selectbox("Type", ["Auto-Detect", "IP Address", "Domain", "File Hash", "Process"])
    
    if st.button(" Hunt", type="primary"):
        if ioc_input:
            with st.spinner("Hunting across all data sources..."):
                import time
                import re
                
                # Detect IOC type
                is_ip = bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ioc_input))
                
                result_data = None
                
                # Use real API for IP lookups
                if HAS_REAL_API and is_ip:
                    try:
                        result_data = check_ip_reputation(ioc_input)
                        time.sleep(0.5)
                    except Exception as e:
                        st.warning(f"API error: {e}")
                        result_data = None
                else:
                    time.sleep(1.5)
                
                # Display results
                if result_data and result_data.get('risk_score', 0) > 0:
                    risk = result_data.get('risk_score', 0)
                    st.error(f" **Threat Detected!** Risk Score: {risk}/100")
                    
                    st.markdown(f"""
                    **IP:** {ioc_input}  
                    **Country:** {result_data.get('country', 'Unknown')}  
                    **ISP:** {result_data.get('isp', 'Unknown')}  
                    **Reports:** {result_data.get('reports', 0)} abuse reports  
                    **Categories:** {', '.join(result_data.get('categories', ['Unknown']))}
                    """)
                    
                    st.markdown("###  Recommended Actions")
                    st.markdown("""
                    1. Isolate affected endpoints immediately
                    2. Collect forensic artifacts (memory dump, logs)
                    3. Block IOC at perimeter (firewall, DNS sinkhole)
                    4. Check for lateral movement to other systems
                    5. Reset credentials for affected users
                    """)
                elif random.random() > 0.4:  # Fallback simulation
                    st.error(f" **IOC Found in Environment!** (Simulated)")
                    
                    matches = []
                    for _ in range(random.randint(2, 8)):
                        matches.append({
                            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 72))).strftime("%Y-%m-%d %H:%M"),
                            "source": random.choice(["Firewall", "EDR", "DNS", "Proxy", "SIEM"]),
                            "hostname": random.choice(["WS-001", "SRV-DB-01", "LAPTOP-IT42", "DC-PROD-01"]),
                            "action": random.choice(["Blocked", "Allowed", "Detected"]),
                            "user": random.choice(["jsmith", "admin", "service-account", "SYSTEM"])
                        })
                    
                    df = pd.DataFrame(matches)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.success(f" **IOC not found** - No matches in current data")
                    st.info("Consider expanding time range or checking additional data sources")
        else:
            st.warning("Please enter an IOC to search")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Quick IOC Lists")
    
    cols = st.columns(4)
    with cols[0]:
        st.markdown("**Known Bad IPs**")
        for ip in IOC_DATABASE["ips"][:4]:
            st.code(ip)
    with cols[1]:
        st.markdown("**Malicious Domains**")
        for domain in IOC_DATABASE["domains"][:4]:
            st.code(domain)
    with cols[2]:
        st.markdown("**Malware Hashes**")
        for h in IOC_DATABASE["hashes"][:2]:
            st.code(h[:20] + "...")
    with cols[3]:
        st.markdown("**Suspicious Processes**")
        for proc in IOC_DATABASE["processes"][:2]:
            st.code(proc[:25] + "...")

with tab2:
    st.markdown(section_title("Predefined Hunt Queries"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <p style="color: #8B95A5; margin: 0;">
                Execute predefined hunting queries aligned with MITRE ATT&CK techniques.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    for query in HUNT_QUERIES:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"""
            <div style="
                background: rgba(26,31,46,0.5);
                border: 1px solid rgba(0,212,255,0.2);
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
            ">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #00D4FF; font-weight: bold;">{query['name']}</span>
                    <span style="background: rgba(139,92,246,0.2); color: #8B5CF6; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{query['category']}</span>
                </div>
                <code style="color: #8B95A5; font-size: 0.85rem;">{query['query']}</code>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button(" Run", key=f"run_{query['name']}", use_container_width=True):
                st.session_state[f"hunt_result_{query['name']}"] = random.randint(0, 50)
                st.rerun()

with tab3:
    st.markdown(section_title("Hypothesis-Driven Hunting"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <p style="color: #8B95A5; margin: 0;">
                Create custom hunting hypotheses based on threat intelligence or suspicious activity.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    hypothesis = st.text_area("Describe your hunting hypothesis", 
                               placeholder="e.g., 'An attacker may be using encoded PowerShell to download and execute malicious payloads'",
                               height=100)
    
    mitre_technique = st.selectbox("Related MITRE ATT&CK Technique", [
        "T1059.001 - PowerShell",
        "T1003 - Credential Dumping",
        "T1021.002 - SMB/Windows Admin Shares",
        "T1071.001 - Web C2",
        "T1486 - Data Encrypted for Impact",
        "T1566.001 - Spearphishing Attachment"
    ])
    
    data_sources = st.multiselect("Data Sources to Query", 
                                   ["EDR Logs", "Firewall Logs", "DNS Logs", "Proxy Logs", "Windows Event Logs", "Authentication Logs"],
                                   default=["EDR Logs", "Windows Event Logs"])
    
    if st.button(" Start Hunt", type="primary"):
        if hypothesis:
            with st.spinner("Executing hypothesis-driven hunt..."):
                import time
                time.sleep(2)
                
                findings = random.randint(0, 25)
                
                if findings > 0:
                    st.warning(f" **{findings} potential matches found**")
                    st.markdown("Results require analyst review to confirm true positives.")
                else:
                    st.success(" No matches found for this hypothesis")
        else:
            st.warning("Please enter a hunting hypothesis")

with tab4:
    st.markdown(section_title("Hunt Results & History"), unsafe_allow_html=True)
    
    # Sample hunt history
    history = [
        {"date": "2024-02-05 14:30", "query": "Suspicious PowerShell", "results": 12, "status": "Reviewed"},
        {"date": "2024-02-05 10:15", "query": "C2 Beaconing Detection", "results": 3, "status": "Investigating"},
        {"date": "2024-02-04 16:45", "query": "Lateral Movement Scan", "results": 0, "status": "No Findings"},
        {"date": "2024-02-04 09:00", "query": "Credential Dumping Hunt", "results": 5, "status": "Escalated"},
    ]
    
    df = pd.DataFrame(history)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Export
    csv = df.to_csv(index=False)
    st.download_button(" Export Hunt History", csv, "hunt_history.csv", "text/csv")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Threat Hunting</p></div>', unsafe_allow_html=True)
