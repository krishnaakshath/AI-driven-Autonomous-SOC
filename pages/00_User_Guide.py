import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("Command Manual", "Official Guide to the Autonomous SOC Platform"), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE GUIDE SECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

sections = {
    "🚀 Getting Started": {
        "icon": "auto_awesome",
        "content": """
        ### Welcome, Commander.
        This platform is a fully autonomous **Security Operations Center**. 
        
        **Your Mission:**
        1. **Monitor**: Use the main Dashboard to oversee the global threat landscape.
        2. **Analyze**: Use CORTEX AI to investigate suspicious indicators.
        3. **Respond**: Use the Alerts workbench to triage and resolve incidents.
        """,
        "tip": "The platform is 100% data-authentic. Every alert you see represents a real persistent event."
    },
    "📊 Global Dashboard": {
        "icon": "dashboard",
        "content": """
        ### Real-Time Intelligence
        The Dashboard provides a high-level view of your security posture.
        
        - **Threat Radar**: Shows active monitoring status.
        - **KPI Metrics**: Real-time counts of Critical and High severity events.
        - **Visual Analytics**: Trends and distributions across your infrastructure.
        """,
        "tip": "Click the 'Refresh' button in the sidebar or toggle 'Auto-refresh' on specific pages for live updates."
    },
    "🚨 Alerts Workbench": {
        "icon": "notifications_active",
        "content": """
        ### Triage & Response
        Located in the 'Monitoring' category, the Alerts page is your operational hub.
        
        - **Active Alerts**: Latest threats requiring attention.
        - **Filtering**: Search by Severity, Source IP, or Status.
        - **Investigation**: Each alert includes a 'Risk Score' derived from ML clusters.
        """,
        "tip": "Always prioritize **CRITICAL** severity alerts first."
    },
    "🧠 CORTEX AI": {
        "icon": "psychology",
        "content": """
        ### Neural-Link Investigation
        CORTEX is your intelligent assistant. It is directly connected to the SIEM and Threat Intel feeds.
        
        **Try asking:**
        - "What are the latest critical threats?"
        - "Analyze the reputation of IP 8.8.8.8"
        - "Suggest a playbook for SQL Injection"
        """,
        "tip": "CORTEX uses real-world data from VirusTotal, AbuseIPDB, and AlienVault OTX."
    },
    "🛡️ Active Firewall": {
        "icon": "verified_user",
        "content": """
        ### Integrated Defense
        The platform features an active **Web Application Firewall (WAF)**.
        
        - **Payload Scanning**: Automatically blocks SQL Injection and XSS attempts.
        - **IP Reputation**: Blocks known malicious IPs dynamically.
        - **Audit Logs**: Every block is recorded in the SIEM for full transparency.
        """,
        "tip": "Manage active blocks and overrides in the 'Firewall Control' page (Admin only)."
    }
}

# Render Sidebar Navigation for Guide
st.sidebar.markdown("### Guide Contents")
selected_section = st.sidebar.radio("Jump to Section", list(sections.keys()))

# Main Content Area
if selected_section:
    data = sections[selected_section]
    
    st.markdown(f"""
    <div class="glass-card" style="padding: 2.5rem; border-radius: 12px; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 1.5rem;">
            <span class="material-icons" style="color: #00D4FF; font-size: 2.5rem;">{data['icon']}</span>
            <h2 style="margin: 0; font-family: 'Orbitron', sans-serif; letter-spacing: 2px;">{selected_section.split(' ', 1)[1]}</h2>
        </div>
        <div style="color: #FAFAFA; line-height: 1.8; font-size: 1.1rem;">
            {data['content']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info(f"💡 **PRO TIP:** {data['tip']}")

# Navigation Footer
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("⬅️ Home Dashboard"):
        st.switch_page("pages/01_Dashboard.py")
with col2:
    if st.button("🧠 Consult CORTEX"):
        st.switch_page("pages/21_CORTEX.py")
