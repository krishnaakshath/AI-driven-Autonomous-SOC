"""
🎯 Autonomous Response Playbooks
================================
Visual playbook editor/viewer with execution logs and status tracking.
Zero-touch incident response with predefined security workflows.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui.theme import CYBERPUNK_CSS
from services.playbook_engine import playbook_engine, list_playbooks, get_playbook_details, execute_playbook

st.set_page_config(
    page_title="Playbooks | SOC",
    page_icon="🎯",
    layout="wide"
)

st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)

# Header
st.markdown("""
<div style="text-align: center; padding: 20px 0 30px;">
    <h1 style="font-size: 2.5rem; font-weight: 700; margin: 0; color: #fff;">
        Response Playbooks
    </h1>
    <p style="color: #888; font-size: 0.9rem; letter-spacing: 2px; margin-top: 5px;">
        AUTONOMOUS INCIDENT RESPONSE WORKFLOWS
    </p>
</div>
""", unsafe_allow_html=True)

# Get all playbooks
playbooks = list_playbooks()

# Severity color mapping
severity_colors = {
    "critical": "#ff0040",
    "high": "#ff6600",
    "medium": "#ffcc00",
    "low": "#00ff88"
}

# Create tabs
tab1, tab2, tab3 = st.tabs(["📋 Playbook Library", "▶️ Execute Playbook", "📜 Execution History"])

with tab1:
    st.markdown("### Available Playbooks")
    
    for pb in playbooks:
        severity_color = severity_colors.get(pb['severity'], '#888')
        auto_badge = "🤖 AUTO" if pb['auto_execute'] else "👤 MANUAL"
        
        with st.expander(f"**{pb['name']}** — {pb['severity'].upper()}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Description:** {pb['description']}")
                st.markdown(f"**Triggers:** `{'`, `'.join(pb['triggers'])}`")
                st.markdown(f"**Actions:** {pb['action_count']} steps")
            
            with col2:
                st.markdown(f"""
                <div style="
                    background: {severity_color}22;
                    border: 1px solid {severity_color};
                    border-radius: 8px;
                    padding: 10px;
                    text-align: center;
                ">
                    <div style="font-size: 0.7rem; color: #888;">SEVERITY</div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: {severity_color};">
                        {pb['severity'].upper()}
                    </div>
                    <div style="font-size: 0.7rem; margin-top: 5px; color: {'#00f3ff' if pb['auto_execute'] else '#ff6600'};">
                        {auto_badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Show detailed actions
            details = get_playbook_details(pb['key'])
            if details:
                st.markdown("---")
                st.markdown("**Execution Steps:**")
                for i, action in enumerate(details.get('actions', []), 1):
                    st.markdown(f"""
                    <div style="
                        background: rgba(0,0,0,0.3);
                        border-left: 3px solid #00f3ff;
                        padding: 10px 15px;
                        margin: 5px 0;
                        border-radius: 0 8px 8px 0;
                    ">
                        <strong>Step {i}:</strong> {action['name']}<br>
                        <span style="color: #888; font-size: 0.85rem;">{action['description']}</span>
                    </div>
                    """, unsafe_allow_html=True)

with tab2:
    st.markdown("### Execute Response Playbook")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pb_options = {pb['name']: pb['key'] for pb in playbooks}
        selected_pb_name = st.selectbox(
            "Select Playbook",
            options=list(pb_options.keys())
        )
        selected_pb_key = pb_options.get(selected_pb_name)
    
    with col2:
        target_ip = st.text_input(
            "Target (IP/Hostname)",
            placeholder="e.g., 192.168.1.100"
        )
    
    # Show selected playbook details
    if selected_pb_key:
        details = get_playbook_details(selected_pb_key)
        if details:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(0,243,255,0.1), rgba(188,19,254,0.05));
                border: 1px solid rgba(0,243,255,0.2);
                border-radius: 12px;
                padding: 20px;
                margin: 15px 0;
            ">
                <div style="font-size: 0.8rem; color: #00f3ff; letter-spacing: 1px;">SELECTED PLAYBOOK</div>
                <div style="font-size: 1.5rem; font-weight: 700; margin: 5px 0;">{details['name']}</div>
                <div style="color: #888;">{details['description']}</div>
                <div style="margin-top: 10px;">
                    <span style="
                        background: {severity_colors.get(details['severity'], '#888')}33;
                        border: 1px solid {severity_colors.get(details['severity'], '#888')};
                        padding: 3px 10px;
                        border-radius: 4px;
                        font-size: 0.75rem;
                        color: {severity_colors.get(details['severity'], '#888')};
                    ">{details['severity'].upper()}</span>
                    <span style="
                        background: rgba(0,243,255,0.1);
                        border: 1px solid rgba(0,243,255,0.3);
                        padding: 3px 10px;
                        border-radius: 4px;
                        font-size: 0.75rem;
                        color: #00f3ff;
                        margin-left: 8px;
                    ">{len(details.get('actions', []))} STEPS</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_btn = st.button("▶️ Execute Playbook", type="primary", use_container_width=True)
    
    if execute_btn:
        if not target_ip:
            st.error("Please specify a target IP or hostname")
        else:
            with st.spinner(f"Executing {selected_pb_name}..."):
                result = execute_playbook(selected_pb_key, target_ip)
                
                if result.get('success'):
                    st.success(f"✅ Playbook executed successfully!")
                    
                    st.markdown("### Execution Results")
                    for action_result in result.get('results', []):
                        icon = "✅" if action_result['status'] == 'success' else "❌"
                        st.markdown(f"{icon} **{action_result['action']}**: {action_result.get('result', action_result.get('error', 'Completed'))}")
                else:
                    st.error(f"Playbook execution failed: {result.get('error', 'Unknown error')}")

with tab3:
    st.markdown("### Recent Executions")
    
    execution_log = playbook_engine.get_execution_log(limit=10)
    
    if not execution_log:
        st.info("No playbook executions recorded yet. Execute a playbook to see history here.")
    else:
        for log in reversed(execution_log):
            success_count = sum(1 for r in log.get('results', []) if r.get('status') == 'success')
            total_count = len(log.get('results', []))
            
            st.markdown(f"""
            <div style="
                background: rgba(0,0,0,0.3);
                border: 1px solid rgba(0,243,255,0.2);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 700; font-size: 1.1rem;">{log.get('playbook_name', 'Unknown')}</div>
                        <div style="color: #888; font-size: 0.85rem;">Target: {log.get('target', 'N/A')}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #00ff88; font-weight: 600;">{success_count}/{total_count} Actions</div>
                        <div style="color: #666; font-size: 0.75rem;">{log.get('completed_at', 'Unknown time')[:19]}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Inject floating CORTEX orb
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
