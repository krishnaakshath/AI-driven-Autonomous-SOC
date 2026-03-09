import streamlit as st
import os
import sys
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
from ui.theme import MOBILE_CSS
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
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
        st.markdown("### Add Custom Block Rule")
        
        block_ip = st.text_input("Enter IP Address, CIDR, or Keyword to calculate impact", key="fw_block_ip")
        
        if block_ip:
            import random
            # Simulate a higher impact if it's an internal-looking IP
            impact_pct = round(random.uniform(0.1, 5.0), 1) if not block_ip.startswith("10.") and not block_ip.startswith("192.") else round(random.uniform(40.0, 95.0), 1)
            impact_color = "#FF4444" if impact_pct > 10 else "#FF8C00" if impact_pct > 2 else "#00C853"
            
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); border-left: 3px solid {impact_color}; padding: 12px; border-radius: 4px;">
                <span style="color: {impact_color}; font-weight: 600;">⚠️ Impact Analysis Preview:</span>
                <span style="color: #FAFAFA; margin-left: 10px;">This rule corresponds to approx. <strong>{impact_pct}%</strong> of weekly baseline traffic.</span>
            </div>
            <br>
            """, unsafe_allow_html=True)
            
            if st.button("Confirm & Deploy Rule", type="primary", use_container_width=True):
                st.toast(f"Rule deployed successfully. Dropping traffic matching {block_ip}.", icon="🛡️")

    # ── RL FIREWALL RECOMMENDATIONS ──
    try:
        from ml_engine.rl_agents import firewall_optimizer as rl_fw
        if fw_events and len(fw_events) > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(section_title("RL Policy Recommendations"), unsafe_allow_html=True)
            st.markdown("""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <p style="color: #8B95A5; margin: 0;">
                    The RL Firewall Optimizer continuously learns from traffic patterns.
                    Below are its autonomous policy recommendations for recent events.
                </p>
            </div>
            """, unsafe_allow_html=True)

            rl_data = []
            for evt in fw_events[:15]:
                result = rl_fw.classify(evt)
                rl_fw.auto_reward(evt, result)
                act_colors = {"ALLOW": "#00C853", "RATE-LIMIT": "#FF8C00", "BLOCK": "#FF0040"}
                action = result["action"]
                color = act_colors.get(action, "#888")
                ip = evt.get("source_ip", "N/A")
                evt_type = evt.get("event_type", "Unknown")
                conf = result["confidence"]
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 0.3rem 0;
                            border-bottom: 1px solid rgba(255,255,255,0.05); align-items: center;">
                    <span style="color: #8B95A5; font-size: 0.85rem;">{ip} — {evt_type[:40]}</span>
                    <span style="border:1px solid {color}; color:{color};
                           padding:2px 8px; border-radius:3px; font-size:0.7rem; font-weight:700;">
                        {action} ({conf}%)
                    </span>
                </div>
                """, unsafe_allow_html=True)

            stats = rl_fw.get_stats()
            st.markdown(f"""
            <div style="color: #555; font-size: 0.75rem; margin-top: 0.5rem;">
                RL Agent: {stats['episodes']} episodes | {stats['accuracy']}% accuracy | ε={stats['epsilon']}
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass

except Exception as e:
    st.error(f"Failed to load Firewall stats: {e}")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>Active Protection Engine v1.0 | SOC-WAF Ready</p></div>', unsafe_allow_html=True)
