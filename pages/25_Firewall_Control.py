import streamlit as st
import os
import sys
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("Firewall Control", "Real-Time Defense & Policy Management"), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FIREWALL STATS
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from services.database import db
    # Fetch firewall events from SIEM
    fw_events = [e for e in db.get_recent_events(limit=500) if e.get("source") == "Firewall"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Blocks (24h)", len(fw_events), delta=f"+{len([e for e in fw_events if 'Active' in e.get('event_type', '')])}")
    with col2:
        top_threat = "N/A"
        if fw_events:
            threats = [e.get("event_type") for e in fw_events]
            top_threat = max(set(threats), key=threats.count).replace("Active Block: ", "")
        st.metric("Top Attack Vector", top_threat)
    with col3:
        st.metric("Defense Status", "ACTIVE", delta_color="normal")

    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Block Log", "WAF Policy"])
    
    with tab1:
        st.markdown(section_title("Real-Time Block History"), unsafe_allow_html=True)
        if fw_events:
            df_fw = pd.DataFrame(fw_events)
            st.dataframe(
                df_fw[["timestamp", "event_type", "source_ip", "status"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No firewall blocks recorded yet.")
            
    with tab2:
        st.markdown(section_title("Active WAF Policies"), unsafe_allow_html=True)
        
        policies = [
            {"Rule": "SQL Injection Protection", "Enabled": True, "Level": "CRITICAL"},
            {"Rule": "Cross-Site Scripting (XSS)", "Enabled": True, "Level": "CRITICAL"},
            {"Rule": "Path Traversal Detection", "Enabled": True, "Level": "HIGH"},
            {"Rule": "Rate Limiting (100 req/min)", "Enabled": False, "Level": "MEDIUM"},
        ]
        
        for p in policies:
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.write(f"**{p['Rule']}** ({p['Level']})")
            with col_b:
                st.toggle("Active", value=p['Enabled'], key=p['Rule'])
                
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Manual IP Block"):
            st.text_input("Enter IP Address")
            st.button("Confirm Block", type="primary")

except Exception as e:
    st.error(f"Failed to load Firewall stats: {e}")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>Active Protection Engine v1.0 | SOC-WAF Ready</p></div>', unsafe_allow_html=True)
