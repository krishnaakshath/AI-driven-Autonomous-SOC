import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Threat Hunting | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
from ui.page_layout import init_page, kpi_row, content_section, section_gap, page_footer, show_empty, show_error
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
from ui.theme import MOBILE_CSS
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
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
    
    # Quick-hunt preset buttons
    st.markdown("##### ⚡ Quick Hunt Presets")
    qh1, qh2, qh3, qh4 = st.columns(4)
    quick_hunt_value = ""
    with qh1:
        if st.button("🔓 SSH Brute Force", use_container_width=True, key="qh_ssh"):
            quick_hunt_value = "ssh"
    with qh2:
        if st.button("🌐 Port Scan", use_container_width=True, key="qh_port"):
            quick_hunt_value = "port_scan"
    with qh3:
        if st.button("💉 SQL Injection", use_container_width=True, key="qh_sqli"):
            quick_hunt_value = "sql_injection"
    with qh4:
        if st.button("🦠 Malware C2", use_container_width=True, key="qh_c2"):
            quick_hunt_value = "malware"
    
    if quick_hunt_value:
        from services.database import db as _hunt_db
        results = _hunt_db.search_events(quick_hunt_value)
        if results:
            st.error(f"🎯 **{len(results)} matches found** for `{quick_hunt_value}`")
            st.dataframe(pd.DataFrame(results).head(10), use_container_width=True, hide_index=True)
        else:
            st.success(f"✅ No matches for `{quick_hunt_value}` in current logs")
    
    st.markdown("---")
    
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
                    except Exception as e:
                        st.warning(f"API error: {e}")
                        result_data = None
                
                # CHECK LOCAL DB (Phase 18)
                from services.database import db
                local_hits = db.search_events(ioc_input)
                
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
                    
                elif local_hits:
                    st.error(f" **IOC Found in Internal Logs!** ({len(local_hits)} matches)")
                    st.dataframe(pd.DataFrame(local_hits), use_container_width=True)
                    
                elif random.random() > 0.8: # Keep small simulation chance if DB empty
                     st.info("Simulating search...")
                     time.sleep(1)
                     st.success("No active threats found.")
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
    
    # Load RL Hunt Recommender
    try:
        from ml_engine.rl_agents import hunt_recommender as rl_hunt
        RL_HUNT = True
    except Exception:
        RL_HUNT = False

    for query in HUNT_QUERIES:
        col1, col2 = st.columns([4, 1])

        # RL Priority badge
        rl_badge = ""
        if RL_HUNT:
            try:
                rl_result = rl_hunt.classify(query)
                rl_hunt.auto_reward(query, rl_result)
                rl_action = rl_result["action"]
                rl_conf = rl_result["confidence"]
                rl_c = {"HUNT-NOW": "#FF0040", "SCHEDULE": "#FF8C00", "SKIP": "#00C853"}.get(rl_action, "#888")
                rl_badge = f'<span style="border:1px solid {rl_c}; color:{rl_c}; padding:1px 6px; border-radius:3px; font-size:0.6rem; font-weight:700; margin-left:8px;">RL:{rl_action}</span>'
            except Exception:
                pass

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
                    <span style="color: #00D4FF; font-weight: bold;">{query['name']}{rl_badge}</span>
                    <span style="background: rgba(139,92,246,0.2); color: #8B5CF6; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{query['category']}</span>
                </div>
                <code style="color: #8B95A5; font-size: 0.85rem;">{query['query']}</code>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button(" Run", key=f"run_{query['name']}", use_container_width=True):
                # Map hunt query categories to meaningful search terms for SIEM DB
                hunt_search_map = {
                    "Suspicious PowerShell": ["powershell", "encoded", "execution", "process"],
                    "Lateral Movement": ["psexec", "wmic", "smb", "lateral", "rdp", "admin"],
                    "Data Exfiltration": ["exfil", "tunnel", "dns", "large", "upload", "443"],
                    "C2 Beaconing": ["beacon", "c2", "http", "callback", "malware", "trojan"],
                    "Credential Dumping": ["credential", "lsass", "mimikatz", "password", "login", "brute"],
                }
                
                search_terms = hunt_search_map.get(query['name'], [query['name'].lower()])
                
                from services.database import db
                all_results = []
                for term in search_terms:
                    results = db.search_events(term)
                    if results:
                        # Deduplicate by event ID
                        existing_ids = {r.get('id') for r in all_results}
                        for r in results:
                            if r.get('id') not in existing_ids:
                                all_results.append(r)
                                existing_ids.add(r.get('id'))
                    if len(all_results) >= 50:
                        break
                
                if all_results:
                    st.success(f"🎯 Found {len(all_results)} matches across {len(search_terms)} search terms")
                    st.session_state[f"hunt_result_{query['name']}"] = all_results
                    # Save to hunt history
                    if 'hunt_execution_log' not in st.session_state:
                        st.session_state.hunt_execution_log = []
                    st.session_state.hunt_execution_log.append({
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "query": query['name'],
                        "results": len(all_results),
                        "status": "Matches Found"
                    })
                else:
                    st.warning("No matches found in current logs")
                    if 'hunt_execution_log' not in st.session_state:
                        st.session_state.hunt_execution_log = []
                    st.session_state.hunt_execution_log.append({
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "query": query['name'],
                        "results": 0,
                        "status": "No Findings"
                    })

    # Display results if available
    for query in HUNT_QUERIES:
        if f"hunt_result_{query['name']}" in st.session_state:
            res = st.session_state[f"hunt_result_{query['name']}"]
            if isinstance(res, list) and res:
                st.write(f"**Results for {query['name']}:**")
                st.dataframe(pd.DataFrame(res).head(10), use_container_width=True)

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
    
    hb_c1, hb_c2 = st.columns(2)
    with hb_c1:
        run_btn = st.button(" Start Hunt", type="primary", use_container_width=True)
    with hb_c2:
        save_btn = st.button("💾 Save Hunt to Workspace", use_container_width=True)

    if save_btn:
        if hypothesis and len(hypothesis) > 5:
            if 'saved_custom_hunts' not in st.session_state:
                st.session_state.saved_custom_hunts = []
            hunt_id = f"Hunt-{random.randint(1000, 9999)}"
            st.session_state.saved_custom_hunts.append({
                "id": hunt_id, "hypothesis": hypothesis, "technique": mitre_technique, "sources": data_sources, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.success(f"✅ Hunt '{hunt_id}' saved successfully to workspace!")
        else:
            st.warning("Please enter a valid hunting hypothesis before saving.")

    if run_btn:
        if hypothesis:
            with st.spinner("Executing hypothesis-driven hunt..."):
                import time
                from services.database import db
                
                tech_keywords = {
                    "PowerShell": "powershell",
                    "Credential Dumping": "mimikatz",
                    "SMB": "smb",
                    "Web C2": "http",
                    "Data Encrypted": "ransom",
                    "Spearphishing": "email"
                }
                
                keyword = "unknown"
                for k, v in tech_keywords.items():
                    if k in mitre_technique:
                        keyword = v
                        break
                
                findings = db.search_events(keyword)
                
                if findings:
                    st.warning(f" **{len(findings)} potential matches found**")
                    st.markdown("Results require analyst review to confirm true positives.")
                    st.dataframe(pd.DataFrame(findings), use_container_width=True)
                else:
                    st.success(" No matches found for this hypothesis in current logs")
        else:
            st.warning("Please enter a hunting hypothesis")

with tab4:
    st.markdown(section_title("Hunt Results & History"), unsafe_allow_html=True)
    
    st.markdown("### 💾 Workspace: Saved Hunts")
    if 'saved_custom_hunts' in st.session_state and st.session_state.saved_custom_hunts:
        for saved in reversed(st.session_state.saved_custom_hunts):
            st.markdown(f"""
            <div style="background: rgba(0,0,0,0.2); border-left: 3px solid #00f3ff; padding: 10px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between;">
                    <strong>{saved['id']}</strong>
                    <span style="color: #666; font-size: 0.8rem;">{saved['date']}</span>
                </div>
                <div style="color: #8B95A5; font-size: 0.9rem; margin: 4px 0;">{saved['hypothesis']}</div>
                <span style="background: rgba(188,19,254,0.1); color: #bc13fe; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">{saved['technique']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No saved hypothesis hunts in the workspace yet. Go to the Hypothesis Hunt tab to create one.")
        
    st.markdown("---")
    st.markdown("###  Historical Execution Log")
    
    # Use dynamic hunt execution log from session state
    if 'hunt_execution_log' in st.session_state and st.session_state.hunt_execution_log:
        history = st.session_state.hunt_execution_log
    else:
        # Fallback: generate initial history from DB search counts
        history = []
        try:
            from services.database import db as _hist_db
            for q in HUNT_QUERIES:
                hunt_search_map = {
                    "Suspicious PowerShell": "powershell",
                    "Lateral Movement": "lateral",
                    "Data Exfiltration": "exfil",
                    "C2 Beaconing": "beacon",
                    "Credential Dumping": "credential",
                }
                term = hunt_search_map.get(q['name'], q['name'].lower())
                results = _hist_db.search_events(term)
                count = len(results) if results else 0
                status = "Matches Found" if count > 0 else "No Findings"
                history.append({
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "query": q['name'],
                    "results": count,
                    "status": status
                })
        except Exception:
            history = [
                {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "query": "System Initialization", "results": 0, "status": "Awaiting First Hunt"}
            ]
    
    df = pd.DataFrame(history)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Export
    csv = df.to_csv(index=False)
    st.download_button(" Export Hunt History", csv, "hunt_history.csv", "text/csv")

page_footer("Threat Hunt")
