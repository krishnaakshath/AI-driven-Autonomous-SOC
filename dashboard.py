"""
AI-Driven Autonomous SOC
Simple entry point that works reliably on Streamlit Cloud
"""

import streamlit as st

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="AI-Driven Autonomous SOC",
    page_icon="🛡️",
    layout="wide"
)

# Simple welcome page - this WILL work
st.title("🛡️ AI-Driven Autonomous SOC")
st.markdown("### Welcome to your Security Operations Center")

st.info("👈 **Use the sidebar** to navigate to different modules:")

st.markdown("""
| Page | Description |
|------|-------------|
| **Dashboard** | Real-time threat monitoring |
| **Alerts** | Security alerts and notifications |
| **Threat Intel** | Global threat map |
| **Forensics** | Incident investigation |
| **Reports** | Generate security reports |
| **Scanners** | URL and file scanning |
| **Security Testing** | Penetration testing tools |
| **Settings** | Configure APIs and alerts |
| **ML Insights** | Isolation Forest & Fuzzy C-Means |
""")

st.success("✅ Application loaded successfully!")
