import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="SOC Platform", page_icon="🛡️", layout="wide")

# ═══════════════════════════════════════════════════════════════════════════════
# NAVIGATION WITH GROUPED SECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Main Dashboards
dashboard_pages = [
    st.Page("pages/01_Dashboard.py", title="Dashboard", icon="📊"),
    st.Page("pages/02_Executive.py", title="Executive", icon="👔"),
]

# Monitoring & Detection
monitoring_pages = [
    st.Page("pages/03_Alerts.py", title="Alerts", icon="🚨"),
    st.Page("pages/04_Logs.py", title="Logs", icon="📋"),
    st.Page("pages/05_Timeline.py", title="Timeline", icon="⏱️"),
    st.Page("pages/24_SIEM.py", title="SIEM", icon="🔍"),
]

# Threat Intelligence
intel_pages = [
    st.Page("pages/06_Threat_Intel.py", title="Threat Intel", icon="🌐"),
    st.Page("pages/07_Geo_Predictions.py", title="Geo Predictions", icon="🗺️"),
    st.Page("pages/08_Kill_Chain.py", title="Kill Chain", icon="⛓️"),
    st.Page("pages/09_Dark_Web.py", title="Dark Web", icon="🕸️"),
    st.Page("pages/10_Threat_Hunt.py", title="Threat Hunt", icon="🎯"),
]

# Analysis & Investigation
analysis_pages = [
    st.Page("pages/11_Analysis.py", title="Analysis", icon="🔬"),
    st.Page("pages/12_UBA.py", title="UBA", icon="👤"),
    st.Page("pages/13_Forensics.py", title="Forensics", icon="🔎"),
    st.Page("pages/14_Sandbox.py", title="Sandbox", icon="📦"),
]

# Security Operations
operations_pages = [
    st.Page("pages/15_Scanners.py", title="Scanners", icon="📡"),
    st.Page("pages/16_Security_Testing.py", title="Security Testing", icon="🧪"),
    st.Page("pages/17_IP_Block.py", title="IP Block", icon="🚫"),
    st.Page("pages/18_Rules.py", title="Rules", icon="📏"),
    st.Page("pages/19_Reports.py", title="Reports", icon="📄"),
    st.Page("pages/20_Playbooks.py", title="Playbooks", icon="📖"),
]

# AI & Configuration
config_pages = [
    st.Page("pages/21_CORTEX.py", title="CORTEX AI", icon="🤖"),
    st.Page("pages/22_API.py", title="API", icon="🔌"),
    st.Page("pages/23_Settings.py", title="Settings", icon="⚙️"),
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
