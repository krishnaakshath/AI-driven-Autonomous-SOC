import streamlit as st
import time
import random
from datetime import datetime

def render_autonomous_defense_log(risk_score):
    """
    Renders a scrolling 'Matrix-style' log of autonomous actions based on risk score.
    """
    st.markdown("""
    <style>
    .defense-log {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.8rem;
        background: rgba(5, 5, 10, 0.9);
        border: 1px solid #333;
        border-left: 3px solid #00f3ff;
        padding: 10px;
        height: 150px;
        overflow-y: hidden;
        position: relative;
    }
    .log-entry {
        margin-bottom: 4px;
        opacity: 0;
        animation: fadeIn 0.3s forwards;
    }
    @keyframes fadeIn {
        to { opacity: 1; }
    }
    .log-timestamp { color: #666; margin-right: 8px; }
    .log-action { color: #00f3ff; font-weight: bold; }
    .log-success { color: #0aff0a; }
    .log-warning { color: #ff6b00; }
    .log-critical { color: #ff003c; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h4 style="font-family: Orbitron; color: #00f3ff; font-size: 0.9rem; margin-bottom: 5px;"> AUTONOMOUS DEFENSE PROTOCOL</h4>', unsafe_allow_html=True)
    
    # Generate fake log entries based on risk
    actions = []
    
    if risk_score > 70:
        actions = [
            ("CRITICAL_THREAT_DETECTED", "critical"),
            ("INITIATING_CONTAINMENT_PROTOCOL_ALPHA", "warning"),
            (f"BLOCKING_IP_RANGE_{random.randint(10,99)}.X.X.X", "action"),
            ("TERMINATING_ACTIVE_SESSIONS", "warning"),
            ("ISOLATING_AFFECTED_HOSTS", "action"),
            ("DEPLOYING_COUNTER_MEASURES", "action"),
            ("THREAT_NEUTRALIZED", "success")
        ]
    elif risk_score > 40:
        actions = [
            ("ANOMALY_DETECTED", "warning"),
            ("INCREASING_LOG_VERBOSITY", "action"),
            ("INITIATING_DEEP_PACKET_INSPECTION", "action"),
            ("SANDBOXING_SUSPICIOUS_FILE", "action"),
            ("ANALYSIS_COMPLETE_NO_THREAT_FOUND", "success")
        ]
    else:
        actions = [
            ("SYSTEM_NOMINAL", "success"),
            ("ROUTINE_TRAFFIC_ANALYSIS", "action"),
            ("UPDATING_SIGNATURE_DB", "action"),
            ("HEARTBEAT_CHECK_PASSED", "success")
        ]

    # Render container
    log_html = '<div class="defense-log">'
    
    # Show the last 5 actions for the visual effect
    display_actions = actions # In a real app we'd queue these, here we just show the set
    
    for action, level in display_actions:
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_class = f"log-{level}"
        log_html += f'<div class="log-entry"><span class="log-timestamp">[{timestamp}]</span> <span class="{color_class}">{action}</span></div>'
    
    log_html += '</div>'
    st.markdown(log_html, unsafe_allow_html=True)
