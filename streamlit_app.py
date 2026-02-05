"""
AI-Driven Autonomous SOC
Entry point that redirects to Login or Dashboard based on auth status.
"""

import streamlit as st

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="AI-Driven Autonomous SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Check authentication and redirect
from services.auth_service import is_authenticated

if is_authenticated():
    # Already logged in - go to Dashboard
    st.switch_page("pages/1_Dashboard.py")
else:
    # Not logged in - go to Login
    st.switch_page("pages/_Login.py")
