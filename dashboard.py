import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="SOC Platform", page_icon=":material/shield:", layout="wide")

# ═══════════════════════════════════════════════════════════════════════════════
# NAVIGATION WITH GROUPED SECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Main Dashboards
dashboard_pages = [
    st.Page("pages/01_Dashboard.py", title="Dashboard", icon=":material/dashboard:"),
    st.Page("pages/02_Executive.py", title="Executive", icon=":material/assessment:"),
]

# Monitoring & Detection
monitoring_pages = [
    st.Page("pages/03_Alerts.py", title="Alerts", icon=":material/notification_important:"),
    st.Page("pages/04_Logs.py", title="Logs", icon=":material/description:"),
    st.Page("pages/05_Timeline.py", title="Timeline", icon=":material/timeline:"),
    st.Page("pages/24_SIEM.py", title="SIEM", icon=":material/search:"),
]

# Threat Intelligence
intel_pages = [
    st.Page("pages/06_Threat_Intel.py", title="Threat Intel", icon=":material/public:"),
    st.Page("pages/07_Geo_Predictions.py", title="Geo Predictions", icon=":material/map:"),
    st.Page("pages/08_Kill_Chain.py", title="Kill Chain", icon=":material/link:"),
    st.Page("pages/09_Dark_Web.py", title="Dark Web", icon=":material/language:"),
    st.Page("pages/10_Threat_Hunt.py", title="Threat Hunt", icon=":material/track_changes:"),
]

# Analysis & Investigation
analysis_pages = [
    st.Page("pages/11_Analysis.py", title="Analysis", icon=":material/biotech:"),
    st.Page("pages/12_UBA.py", title="UBA", icon=":material/person_search:"),
    st.Page("pages/13_Forensics.py", title="Forensics", icon=":material/manage_search:"),
    st.Page("pages/14_Sandbox.py", title="Sandbox", icon=":material/inventory_2:"),
]

# Security Operations
operations_pages = [
    st.Page("pages/15_Scanners.py", title="Scanners", icon=":material/radar:"),
    st.Page("pages/16_Security_Testing.py", title="Security Testing", icon=":material/science:"),
    st.Page("pages/17_IP_Block.py", title="IP Block", icon=":material/block:"),
    st.Page("pages/18_Rules.py", title="Rules", icon=":material/rule:"),
    st.Page("pages/19_Reports.py", title="Reports", icon=":material/summarize:"),
    st.Page("pages/20_Playbooks.py", title="Playbooks", icon=":material/auto_stories:"),
]

# AI & Configuration
config_pages = [
    st.Page("pages/21_CORTEX.py", title="CORTEX AI", icon=":material/smart_toy:"),
    st.Page("pages/22_API.py", title="API", icon=":material/api:"),
    st.Page("pages/23_Settings.py", title="Settings", icon=":material/settings:"),
]

# Hidden pages (NOT in navigation - Login/Register)
hidden_pages = [
    st.Page("pages/_Login.py", title="Login"),
    st.Page("pages/_Register.py", title="Register"),
]

# Build navigation with sections
pg = st.navigation({
    "Dashboards": dashboard_pages,
    "Monitoring": monitoring_pages,
    "Threat Intelligence": intel_pages,
    "Investigation": analysis_pages,
    "Operations": operations_pages,
    "AI & Config": config_pages,
}, position="sidebar")

pg.run()
