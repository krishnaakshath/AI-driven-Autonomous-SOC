"""
AI-Driven Autonomous SOC - Main Entry Point
=============================================
A professional Security Operations Center dashboard with ML-powered
threat detection using Isolation Forest and Fuzzy C-Means clustering.
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI-Driven Autonomous SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Redirect to Dashboard
st.switch_page("pages/1_Dashboard.py")
