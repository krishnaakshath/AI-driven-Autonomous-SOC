"""
AI-Driven Autonomous SOC
Main entry point - redirects to appropriate page.
This file should NOT appear in sidebar.
"""

import streamlit as st

# Page config - using same title as Dashboard to avoid duplicate
st.set_page_config(
    page_title="AI-Driven Autonomous SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Immediate redirect - no content shown
from services.auth_service import is_authenticated

if is_authenticated():
    st.switch_page("pages/1_🛡️_Dashboard.py")
else:
    st.switch_page("pages/_Login.py")
