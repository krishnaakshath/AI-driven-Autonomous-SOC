"""
⚔️ MITRE ATT&CK Kill Chain Visualization
=========================================
Interactive kill chain diagram with threat mapping
and countermeasure recommendations.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui.theme import CYBERPUNK_CSS
import random
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Kill Chain | SOC",
    page_icon="⚔️",
    layout="wide"
)

st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)

# Header
st.markdown("""
<div style="text-align: center; padding: 20px 0 30px;">
    <h1 style="font-size: 2.5rem; font-weight: 700; margin: 0; color: #fff;">
        Kill Chain Analysis
    </h1>
    <p style="color: #888; font-size: 0.9rem; letter-spacing: 2px; margin-top: 5px;">
        MITRE ATT&CK FRAMEWORK VISUALIZATION
    </p>
</div>
""", unsafe_allow_html=True)

# MITRE ATT&CK Tactics
KILL_CHAIN_STAGES = [
    {
        "id": "TA0043",
        "name": "Reconnaissance",
        "icon": "🔍",
        "description": "Gathering information to plan attack",
        "techniques": ["Active Scanning", "Phishing for Information", "Search Open Websites"],
        "countermeasures": ["Limit public exposure", "Monitor for scanning activity", "OSINT monitoring"],
        "color": "#00f3ff"
    },
    {
        "id": "TA0042",
        "name": "Resource Development",
        "icon": "🛠️",
        "description": "Establishing infrastructure for attack",
        "techniques": ["Acquire Infrastructure", "Develop Capabilities", "Obtain Credentials"],
        "countermeasures": ["Threat intelligence feeds", "Domain monitoring", "Dark web monitoring"],
        "color": "#00ccff"
    },
    {
        "id": "TA0001",
        "name": "Initial Access",
        "icon": "🚪",
        "description": "Gaining entry into the network",
        "techniques": ["Phishing", "Exploit Public-Facing App", "Supply Chain Compromise"],
        "countermeasures": ["Email security", "Patch management", "Vendor security assessment"],
        "color": "#0099ff"
    },
    {
        "id": "TA0002",
        "name": "Execution",
        "icon": "⚡",
        "description": "Running malicious code",
        "techniques": ["PowerShell", "Command-Line Interface", "Scripting"],
        "countermeasures": ["Application whitelisting", "Script blocking", "EDR monitoring"],
        "color": "#0066ff"
    },
    {
        "id": "TA0003",
        "name": "Persistence",
        "icon": "📌",
        "description": "Maintaining foothold",
        "techniques": ["Registry Run Keys", "Scheduled Tasks", "Web Shell"],
        "countermeasures": ["Registry monitoring", "Task scheduler auditing", "File integrity monitoring"],
        "color": "#3333ff"
    },
    {
        "id": "TA0004",
        "name": "Privilege Escalation",
        "icon": "⬆️",
        "description": "Gaining higher-level permissions",
        "techniques": ["Exploitation for Privilege Escalation", "Valid Accounts", "Token Manipulation"],
        "countermeasures": ["Least privilege principle", "Privileged access management", "Patch management"],
        "color": "#6600ff"
    },
    {
        "id": "TA0005",
        "name": "Defense Evasion",
        "icon": "🥷",
        "description": "Avoiding detection",
        "techniques": ["Obfuscated Files", "Masquerading", "Disabling Security Tools"],
        "countermeasures": ["Behavioral analysis", "EDR solutions", "Integrity monitoring"],
        "color": "#9900ff"
    },
    {
        "id": "TA0006",
        "name": "Credential Access",
        "icon": "🔑",
        "description": "Stealing credentials",
        "techniques": ["Credential Dumping", "Keylogging", "Brute Force"],
        "countermeasures": ["MFA enforcement", "Credential vaulting", "Honeytokens"],
        "color": "#cc00ff"
    },
    {
        "id": "TA0007",
        "name": "Discovery",
        "icon": "🗺️",
        "description": "Learning about the environment",
        "techniques": ["Network Service Scanning", "System Information Discovery", "Permission Groups Discovery"],
        "countermeasures": ["Network segmentation", "Deception technology", "Traffic analysis"],
        "color": "#ff00cc"
    },
    {
        "id": "TA0008",
        "name": "Lateral Movement",
        "icon": "↔️",
        "description": "Moving through the network",
        "techniques": ["Remote Services", "Internal Spearphishing", "Exploitation of Remote Services"],
        "countermeasures": ["Network segmentation", "Zero trust architecture", "Anomaly detection"],
        "color": "#ff0099"
    },
    {
        "id": "TA0009",
        "name": "Collection",
        "icon": "📦",
        "description": "Gathering data of interest",
        "techniques": ["Data from Local System", "Email Collection", "Screen Capture"],
        "countermeasures": ["DLP solutions", "Data classification", "Access controls"],
        "color": "#ff0066"
    },
    {
        "id": "TA0011",
        "name": "Command & Control",
        "icon": "📡",
        "description": "Communicating with compromised systems",
        "techniques": ["Web Protocols", "DNS", "Encrypted Channel"],
        "countermeasures": ["DNS monitoring", "TLS inspection", "Proxy filtering"],
        "color": "#ff0033"
    },
    {
        "id": "TA0010",
        "name": "Exfiltration",
        "icon": "📤",
        "description": "Stealing data",
        "techniques": ["Exfiltration Over C2", "Exfiltration Over Web Service", "Scheduled Transfer"],
        "countermeasures": ["DLP enforcement", "Egress filtering", "Cloud access security"],
        "color": "#ff0000"
    },
    {
        "id": "TA0040",
        "name": "Impact",
        "icon": "💥",
        "description": "Disrupting operations",
        "techniques": ["Data Destruction", "Ransomware", "Service Stop"],
        "countermeasures": ["Backup verification", "Incident response plan", "Business continuity"],
        "color": "#ff3300"
    }
]

# Simulated current threats with kill chain position
def generate_active_threats():
    threats = []
    threat_types = [
        ("APT-29 COZY BEAR", [0, 1, 2, 3, 4], "critical"),
        ("Ransomware Campaign", [2, 3, 5, 10, 13], "high"),
        ("Credential Harvesting", [0, 2, 7], "medium"),
        ("Lateral Movement Detected", [4, 6, 9], "high"),
        ("C2 Beacon Activity", [11], "critical"),
    ]
    
    for name, stages, severity in threat_types:
        threats.append({
            "name": name,
            "stages": stages,
            "severity": severity,
            "first_seen": (datetime.now() - timedelta(hours=random.randint(1, 48))).strftime("%Y-%m-%d %H:%M"),
            "indicators": random.randint(3, 15)
        })
    
    return threats

# Tab layout
tab1, tab2, tab3 = st.tabs(["🔄 Kill Chain View", "⚠️ Active Threats", "📊 Statistics"])

with tab1:
    st.markdown("### MITRE ATT&CK Kill Chain Stages")
    st.markdown("Click on any stage to see techniques and countermeasures.")
    
    # Horizontal kill chain visualization
    st.markdown("""
    <style>
    .kill-chain-container {
        display: flex;
        overflow-x: auto;
        padding: 20px 0;
        gap: 5px;
    }
    .kill-chain-stage {
        flex: 0 0 auto;
        width: 120px;
        text-align: center;
        padding: 15px 10px;
        background: linear-gradient(180deg, rgba(0,0,0,0.5), rgba(0,0,0,0.3));
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        transition: all 0.3s;
        cursor: pointer;
    }
    .kill-chain-stage:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 20px rgba(0,243,255,0.3);
    }
    .stage-icon { font-size: 24px; margin-bottom: 8px; }
    .stage-name { font-size: 11px; font-weight: 600; letter-spacing: 0.5px; }
    .stage-id { font-size: 9px; color: #666; margin-top: 4px; }
    .stage-arrow { 
        flex: 0 0 auto; 
        display: flex; 
        align-items: center; 
        color: #333; 
        font-size: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create horizontal chain
    chain_html = '<div class="kill-chain-container">'
    for i, stage in enumerate(KILL_CHAIN_STAGES):
        chain_html += f"""
        <div class="kill-chain-stage" style="border-color: {stage['color']}40;">
            <div class="stage-icon">{stage['icon']}</div>
            <div class="stage-name" style="color: {stage['color']};">{stage['name']}</div>
            <div class="stage-id">{stage['id']}</div>
        </div>
        """
        if i < len(KILL_CHAIN_STAGES) - 1:
            chain_html += '<div class="stage-arrow">→</div>'
    chain_html += '</div>'
    
    st.markdown(chain_html, unsafe_allow_html=True)
    
    # Detailed stage view
    st.markdown("---")
    st.markdown("### Stage Details")
    
    cols = st.columns(3)
    for i, stage in enumerate(KILL_CHAIN_STAGES):
        with cols[i % 3]:
            with st.expander(f"{stage['icon']} {stage['name']}", expanded=False):
                st.markdown(f"**ID:** `{stage['id']}`")
                st.markdown(f"**Description:** {stage['description']}")
                
                st.markdown("**Techniques:**")
                for tech in stage['techniques']:
                    st.markdown(f"  • {tech}")
                
                st.markdown("**Countermeasures:**")
                for cm in stage['countermeasures']:
                    st.markdown(f"  ✓ {cm}")

with tab2:
    st.markdown("### Active Threats in Kill Chain")
    
    threats = generate_active_threats()
    
    severity_colors = {
        "critical": "#ff0040",
        "high": "#ff6600",
        "medium": "#ffcc00",
        "low": "#00ff88"
    }
    
    for threat in threats:
        sev_color = severity_colors.get(threat['severity'], '#888')
        
        # Build stage progress bar
        stage_indicators = ""
        for i in range(len(KILL_CHAIN_STAGES)):
            if i in threat['stages']:
                stage_indicators += f'<div style="width: 20px; height: 20px; border-radius: 50%; background: {sev_color}; margin: 0 2px; display: inline-block;"></div>'
            else:
                stage_indicators += f'<div style="width: 20px; height: 20px; border-radius: 50%; background: #333; margin: 0 2px; display: inline-block;"></div>'
        
        st.markdown(f"""
        <div style="
            background: rgba(0,0,0,0.3);
            border: 1px solid {sev_color}40;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <div>
                    <span style="
                        background: {sev_color}33;
                        color: {sev_color};
                        padding: 3px 10px;
                        border-radius: 4px;
                        font-size: 0.75rem;
                        font-weight: 600;
                    ">{threat['severity'].upper()}</span>
                    <span style="font-size: 1.2rem; font-weight: 700; margin-left: 10px;">{threat['name']}</span>
                </div>
                <div style="color: #888; font-size: 0.85rem;">
                    First seen: {threat['first_seen']} | {threat['indicators']} IOCs
                </div>
            </div>
            <div style="display: flex; align-items: center; overflow-x: auto;">
                {stage_indicators}
            </div>
            <div style="margin-top: 10px; color: #888; font-size: 0.8rem;">
                Active in: {', '.join([KILL_CHAIN_STAGES[s]['name'] for s in threat['stages']])}
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("### Kill Chain Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Stage Activity (Last 24h)")
        
        # Simulated activity data
        for stage in KILL_CHAIN_STAGES[:7]:
            activity = random.randint(0, 100)
            st.markdown(f"""
            <div style="margin: 8px 0;">
                <div style="display: flex; justify-content: space-between;">
                    <span>{stage['icon']} {stage['name']}</span>
                    <span>{activity}%</span>
                </div>
                <div style="
                    background: #1a1a2e;
                    border-radius: 4px;
                    height: 8px;
                    overflow: hidden;
                ">
                    <div style="
                        width: {activity}%;
                        height: 100%;
                        background: linear-gradient(90deg, {stage['color']}, {stage['color']}88);
                    "></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Top Techniques Detected")
        
        techniques = [
            ("PowerShell Execution", 45),
            ("Credential Dumping", 32),
            ("Remote Service", 28),
            ("Scheduled Task", 21),
            ("DNS Tunneling", 15),
            ("Data Encoding", 12),
            ("Process Injection", 8),
        ]
        
        for tech, count in techniques:
            bar_width = (count / 50) * 100
            st.markdown(f"""
            <div style="margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                    <span style="font-size: 0.9rem;">{tech}</span>
                    <span style="color: #00f3ff;">{count} events</span>
                </div>
                <div style="
                    background: #1a1a2e;
                    border-radius: 4px;
                    height: 6px;
                    overflow: hidden;
                ">
                    <div style="
                        width: {bar_width}%;
                        height: 100%;
                        background: linear-gradient(90deg, #00f3ff, #bc13fe);
                    "></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Inject floating CORTEX orb
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
