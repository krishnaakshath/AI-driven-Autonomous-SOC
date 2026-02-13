import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="ML Insights | SOC", page_icon="", layout="wide")

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

# Authentication removed - public dashboard

st.markdown(page_header("ML Insights", "Isolation Forest Anomaly Detection & Fuzzy C-Means Clustering"), unsafe_allow_html=True)

# Import ML modules
try:
    from ml_engine.isolation_forest import detect_anomalies, get_anomaly_summary, generate_sample_events as gen_if_events
    from ml_engine.fuzzy_clustering import cluster_threats, get_threat_distribution, generate_sample_events as gen_fcm_events
    ML_LOADED = True
except ImportError as e:
    ML_LOADED = False
    st.error(f"ML modules not loaded: {e}")

# Import Neural Predictor
try:
    from ml_engine.neural_predictor import predict_threats, get_threat_summary
    NEURAL_LOADED = True
except ImportError:
    NEURAL_LOADED = False

if ML_LOADED:
    tab0, tab1, tab2, tab3 = st.tabs([" Neural Prediction", " Isolation Forest", " Fuzzy C-Means", " Combined Analysis"])
    
    with tab0:
        st.markdown(section_title("Neural Threat Prediction Engine"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #00D4FF; margin: 0;">Predictive Threat Intelligence</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                LSTM-style neural engine analyzes <strong>historical attack patterns</strong> to predict 
                future threats <strong>before they happen</strong>. Monitors precursor events to calculate 
                probability scores for each attack type.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if NEURAL_LOADED:
            # Get predictions
            predictions = predict_threats()
            summary = get_threat_summary()
            
            # Summary banner
            if "ALERT" in summary:
                banner_color = "#ff0040"
            elif "WATCH" in summary:
                banner_color = "#ff6600"
            else:
                banner_color = "#00ff88"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {banner_color}22, {banner_color}11);
                border: 1px solid {banner_color}66;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                margin-bottom: 20px;
            ">
                <div style="font-size: 1.3rem; font-weight: 700; color: {banner_color};">{summary}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Threat probability gauges
            st.markdown("### Threat Probability Forecast")
            
            cols = st.columns(5)
            for i, (threat_type, data) in enumerate(sorted(predictions.items(), key=lambda x: x[1]['probability'], reverse=True)):
                with cols[i % 5]:
                    prob = data['probability']
                    color = data['color']
                    risk = data['risk_level']
                    
                    st.markdown(f"""
                    <div style="
                        background: rgba(0,0,0,0.3);
                        border: 1px solid {color}40;
                        border-radius: 12px;
                        padding: 15px;
                        text-align: center;
                        margin: 5px 0;
                    ">
                        <div style="font-size: 2rem; font-weight: 800; color: {color};">{prob}%</div>
                        <div style="font-size: 0.75rem; color: #888; letter-spacing: 1px; text-transform: uppercase;">
                            {threat_type.replace('_', ' ')}
                        </div>
                        <div style="
                            margin-top: 8px;
                            background: {color}33;
                            padding: 3px 8px;
                            border-radius: 4px;
                            font-size: 0.65rem;
                            color: {color};
                            font-weight: 600;
                        ">{risk}</div>
                        <div style="font-size: 0.7rem; color: #666; margin-top: 5px;">ETA: {data['eta_text']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Detailed predictions table
            st.markdown("### Detailed Analysis")
            
            for threat_type, data in sorted(predictions.items(), key=lambda x: x[1]['probability'], reverse=True):
                with st.expander(f"**{threat_type.replace('_', ' ').title()}** — {data['probability']}% ({data['risk_level']})"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**Recommendation:** {data['recommendation']}")
                        st.markdown(f"**Precursor Events Detected:** {data['precursor_count']}")
                        st.markdown(f"**Time Window:** {data['time_window_hours']} hours")
                    with col2:
                        # Mini gauge
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <div style="
                                width: 80px;
                                height: 80px;
                                border-radius: 50%;
                                background: conic-gradient({data['color']} {data['probability']}%, #1a1a2e {data['probability']}%);
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                margin: 0 auto;
                            ">
                                <div style="
                                    width: 60px;
                                    height: 60px;
                                    border-radius: 50%;
                                    background: #0a0a1a;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    font-size: 1.2rem;
                                    font-weight: 700;
                                    color: {data['color']};
                                ">{data['probability']}%</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("Neural Predictor module not available. Please check installation.")
    
    with tab1:
        st.markdown(section_title("Isolation Forest - Anomaly Detection"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #00D4FF; margin: 0;">How Isolation Forest Works</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                Isolation Forest detects anomalies by <strong>isolating observations</strong>. 
                The algorithm randomly selects features and split values, creating trees. 
                <strong>Anomalies are easier to isolate</strong> (shorter path = more anomalous).
            </p>
            <ul style="color: #FAFAFA; margin: 0.5rem 0;">
                <li> <strong>Data Exfiltration:</strong> Very high outbound bytes</li>
                <li> <strong>DDoS:</strong> Very high inbound traffic with many packets</li>
                <li> <strong>C2 Communication:</strong> Long duration beaconing patterns</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Generate sample data
        if st.button("Run Anomaly Detection", type="primary", key="run_if"):
            with st.spinner("Analyzing events with Isolation Forest..."):
                # Generate sample events
                events = gen_if_events(n_normal=100, n_anomalous=15)
                
                # Run detection
                results = detect_anomalies(events)
                summary = get_anomaly_summary(events)
                
                # Display summary metrics
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00D4FF;">{summary["total_events"]}</p><p class="metric-label">Total Events</p></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF4444;">{summary["total_anomalies"]}</p><p class="metric-label">Anomalies Detected</p></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #FF8C00;">{summary["anomaly_rate"]:.1f}%</p><p class="metric-label">Anomaly Rate</p></div>', unsafe_allow_html=True)
                with c4:
                    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #8B5CF6;">{summary["max_anomaly_score"]:.0f}</p><p class="metric-label">Max Score</p></div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Risk distribution chart - FIXED Y-axis
                risk_data = summary['risk_distribution']
                fig = go.Figure(data=[
                    go.Bar(
                        x=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
                        y=[risk_data.get('CRITICAL', 0), risk_data.get('HIGH', 0), risk_data.get('MEDIUM', 0), risk_data.get('LOW', 0)],
                        marker_color=['#FF4444', '#FF8C00', '#FFD700', '#00C853']
                    )
                ])
                fig.update_layout(
                    title="Risk Level Distribution",
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=300,
                    yaxis=dict(range=[0, max(50, max(risk_data.values()) + 5)], dtick=10)  # Fixed Y-axis
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Top anomalies with View Details
                st.markdown(section_title("Top Anomalous Events"), unsafe_allow_html=True)
                anomalies = [r for r in results if r['is_anomaly']]
                top_5 = sorted(anomalies, key=lambda x: x['anomaly_score'], reverse=True)[:5]
                
                # Store in session state for expanders
                if 'anomaly_details' not in st.session_state:
                    st.session_state.anomaly_details = {}
                
                for idx, a in enumerate(top_5):
                    color = "#FF4444" if a['risk_level'] == 'CRITICAL' else "#FF8C00"
                    event_type = a.get('type', 'Unknown')
                    
                    # Generate detailed explanation
                    if event_type == 'exfiltration':
                        why = "Unusually high outbound data transfer detected (500KB+ vs normal 2KB average)"
                        how = "Large volumes of data being sent to external IP addresses, possibly through encrypted channels"
                    elif event_type == 'ddos':
                        why = "Extremely high inbound packet count (10,000+ packets in short burst)"
                        how = "Multiple sources flooding the network with SYN requests or UDP packets"
                    elif event_type == 'c2':
                        why = "Persistent beaconing pattern detected (long-duration connections to unusual ports)"
                        how = "Regular interval connections to command-and-control servers, typical of malware communication"
                    else:
                        why = "Behavior pattern significantly deviates from baseline normal traffic"
                        how = "Statistical features fall outside normal distribution boundaries"
                    
                    st.markdown(f"""<div class="glass-card" style="margin: 0.5rem 0; border-left: 3px solid {color};">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div>
<span style="color: {color}; font-weight: 700;">[{a['risk_level']}]</span>
<span style="color: #FAFAFA; font-weight: 600; margin-left: 0.5rem;">{a['id']}</span>
</div>
<span style="color: {color}; font-weight: 700;">Score: {a['anomaly_score']}</span>
</div>
<p style="color: #8B95A5; margin: 0.3rem 0;">Type: {event_type} | IP: {a.get('source_ip', 'N/A')}</p>
</div>""", unsafe_allow_html=True)
                    
                    with st.expander(f"View Details - {a['id']}"):
                        st.markdown(f"""
** When:** Detected in current analysis batch (real-time monitoring)

** Why (Root Cause):**  
{why}

** How (Technical Details):**  
{how}

** Key Metrics:**
- Bytes In: `{a.get('bytes_in', 0):,.0f}`
- Bytes Out: `{a.get('bytes_out', 0):,.0f}`
- Packets: `{a.get('packets', 0)}`
- Duration: `{a.get('duration', 0):.1f}s`
- Port: `{a.get('port', 'N/A')}`

** Recommended Action:**
{" IMMEDIATE BLOCK - Isolate affected system and investigate data loss" if a['risk_level'] == 'CRITICAL' else " INVESTIGATE - Monitor closely and prepare containment procedures"}
                        """)
    
    with tab2:
        st.markdown(section_title("Fuzzy C-Means - Threat Clustering"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #8B5CF6; margin: 0;">How Fuzzy C-Means Works</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                Unlike K-Means which assigns each event to <strong>exactly one cluster</strong>,
                Fuzzy C-Means provides <strong>membership degrees</strong> to all clusters.
                An event can be 60% Malware and 40% Exfiltration simultaneously.
            </p>
            <p style="color: #00D4FF; margin: 0.5rem 0;">
                <strong>Threat Categories:</strong> Malware/Ransomware, Data Exfiltration, DDoS/DoS, Reconnaissance, Insider Threat
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Run Threat Clustering", type="primary", key="run_fcm"):
            with st.spinner("Clustering events with Fuzzy C-Means..."):
                events = gen_fcm_events(n_events=100)
                results = cluster_threats(events)
                distribution = get_threat_distribution(events)
                
                # Cluster distribution
                c1, c2 = st.columns(2)
                
                with c1:
                    # Pie chart
                    counts = distribution['cluster_counts']
                    fig = go.Figure(data=[go.Pie(
                        labels=list(counts.keys()),
                        values=list(counts.values()),
                        hole=0.4,
                        marker_colors=['#FF4444', '#8B5CF6', '#FF8C00', '#00D4FF', '#00C853']
                    )])
                    fig.update_layout(
                        title="Threat Category Distribution",
                        template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with c2:
                    # Summary stats
                    st.markdown(section_title("Cluster Summary"), unsafe_allow_html=True)
                    for name, count in counts.items():
                        pct = distribution['cluster_percentages'][name]
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span style="color: #FAFAFA;">{name}</span>
                            <span style="color: #00D4FF;">{count} events ({pct}%)</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Sample clustered events
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(section_title("Sample Clustered Events"), unsafe_allow_html=True)
                
                # Category explanations
                category_info = {
                    'Malware/Ransomware': {
                        'why': 'High inbound traffic with executable patterns, file encryption signatures detected',
                        'how': 'Malicious payload delivered via phishing or exploit, encrypts files and demands ransom'
                    },
                    'Data Exfiltration': {
                        'why': 'Unusually high outbound data volume to external destinations',
                        'how': 'Sensitive data being transferred outside the network, possibly compressed/encrypted'
                    },
                    'DDoS/DoS Attack': {
                        'why': 'Massive inbound traffic spike with high packet-per-second rate',
                        'how': 'Distributed attack flooding network resources, causing service unavailability'
                    },
                    'Reconnaissance': {
                        'why': 'Sequential port scanning activity, network enumeration patterns',
                        'how': 'Attacker mapping network topology, identifying vulnerable services'
                    },
                    'Insider Threat': {
                        'why': 'Unusual access patterns from internal IP, off-hours activity',
                        'how': 'Authorized user accessing sensitive resources outside normal behavior'
                    }
                }
                
                for idx, r in enumerate(results[:5]):
                    memberships = r['cluster_memberships']
                    top_cat = r['primary_category']
                    conf = r['primary_confidence']
                    cat_info = category_info.get(top_cat, {'why': 'Pattern matches threat category signature', 'how': 'Behavioral analysis indicates threat characteristics'})
                    
                    # Color based on category
                    cat_colors = {
                        'Malware/Ransomware': '#FF4444',
                        'Data Exfiltration': '#8B5CF6',
                        'DDoS/DoS Attack': '#FF8C00',
                        'Reconnaissance': '#00D4FF',
                        'Insider Threat': '#00C853'
                    }
                    color = cat_colors.get(top_cat, '#8B5CF6')
                    
                    st.markdown(f"""<div class="glass-card" style="margin: 0.5rem 0; border-left: 3px solid {color};">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div>
<span style="color: {color}; font-weight: 700;">[{top_cat}]</span>
<span style="color: #FAFAFA; font-weight: 600; margin-left: 0.5rem;">{r['id']}</span>
</div>
<span style="color: {color}; font-weight: 700;">{conf}% Confidence</span>
</div>
<p style="color: #8B95A5; margin: 0.3rem 0;">IP: {r.get('source_ip', 'N/A')} | Risk Score: {r.get('risk_score', 'N/A')}</p>
</div>""", unsafe_allow_html=True)
                    
                    with st.expander(f"View Details - {r['id']}"):
                        st.markdown(f"""
** Primary Category:** {top_cat} ({conf}%)

** Why This Classification:**  
{cat_info['why']}

** Attack Mechanism:**  
{cat_info['how']}

** Cluster Memberships:**
""")
                        for cat, pct in memberships.items():
                            bar_width = pct
                            bar_color = cat_colors.get(cat, '#8B5CF6')
                            st.markdown(f"`{cat}`: {pct}%")
                        
                        st.markdown(f"""
** Event Metrics:**
- Bytes In: `{r.get('bytes_in', 0):,.0f}`
- Bytes Out: `{r.get('bytes_out', 0):,.0f}`
- Packets: `{r.get('packets', 0)}`
- Duration: `{r.get('duration', 0):.1f}s`

** Recommended Action:**
{" HIGH PRIORITY - Immediate containment required" if conf > 70 else " INVESTIGATE - Verify threat and monitor"}
                        """)
    
    with tab3:
        st.markdown(section_title("Combined ML Analysis"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #00C853; margin: 0;">Real-World SOC Application</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                In a production SOC, these algorithms work together:
            </p>
            <ol style="color: #FAFAFA;">
                <li><strong>Isolation Forest</strong> first identifies which events are anomalous</li>
                <li><strong>Fuzzy C-Means</strong> then categorizes those anomalies by threat type</li>
                <li>SOC analysts prioritize based on anomaly score + threat category</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button(" Run Full ML Pipeline", type="primary", key="run_combined"):
            with st.spinner("Running combined ML analysis..."):
                # Generate events
                events = gen_if_events(n_normal=80, n_anomalous=20)
                
                # Step 1: Anomaly Detection
                st.markdown("### Step 1: Anomaly Detection (Isolation Forest)")
                anomaly_results = detect_anomalies(events)
                anomaly_summary = get_anomaly_summary(events)
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Total Events", anomaly_summary['total_events'])
                with c2:
                    st.metric("Anomalies Found", anomaly_summary['total_anomalies'], delta=f"{anomaly_summary['anomaly_rate']:.1f}%")
                with c3:
                    st.metric("Critical Risk", anomaly_summary['risk_distribution']['CRITICAL'])
                
                # Step 2: Cluster anomalies
                st.markdown("### Step 2: Threat Categorization (Fuzzy C-Means)")
                anomalies_only = [e for e in anomaly_results if e['is_anomaly']]
                
                if anomalies_only:
                    cluster_results = cluster_threats(anomalies_only)
                    
                    # Combined view
                    st.markdown("### Combined Results: Prioritized Threat List")
                    
                    # Sort by anomaly score
                    sorted_results = sorted(cluster_results, key=lambda x: x.get('anomaly_score', 0), reverse=True)
                    
                    for r in sorted_results[:10]:
                        risk_color = {'CRITICAL': '#FF4444', 'HIGH': '#FF8C00', 'MEDIUM': '#FFD700', 'LOW': '#00C853'}.get(r.get('risk_level', 'MEDIUM'), '#8B95A5')
                        
                        st.markdown(f"""
                        <div class="glass-card" style="margin: 0.5rem 0; border-left: 4px solid {risk_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="color: {risk_color}; font-weight: 700;">[{r.get('risk_level', 'N/A')}]</span>
                                    <span style="color: #FAFAFA; font-weight: 600; margin-left: 0.5rem;">{r['id']}</span>
                                </div>
                                <span style="color: #8B5CF6;">{r.get('primary_category', 'Unknown')}</span>
                            </div>
                            <div style="display: flex; gap: 2rem; margin-top: 0.5rem;">
                                <span style="color: #8B95A5;">Anomaly Score: <span style="color: #FF8C00;">{r.get('anomaly_score', 0)}</span></span>
                                <span style="color: #8B95A5;">Confidence: <span style="color: #00D4FF;">{r.get('primary_confidence', 0)}%</span></span>
                                <span style="color: #8B95A5;">IP: {r.get('source_ip', 'N/A')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No anomalies detected to cluster.")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | ML Insights</p></div>', unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
