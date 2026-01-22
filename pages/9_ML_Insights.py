import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="ML Insights | SOC", page_icon="🧠", layout="wide")

from ui.theme import PREMIUM_CSS, page_header, section_title
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

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

if ML_LOADED:
    tab1, tab2, tab3 = st.tabs(["🌲 Isolation Forest", "🔮 Fuzzy C-Means", "📊 Combined Analysis"])
    
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
                <li>🔴 <strong>Data Exfiltration:</strong> Very high outbound bytes</li>
                <li>🟠 <strong>DDoS:</strong> Very high inbound traffic with many packets</li>
                <li>🟡 <strong>C2 Communication:</strong> Long duration beaconing patterns</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Generate sample data
        if st.button("🔄 Run Anomaly Detection", type="primary", key="run_if"):
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
                
                # Risk distribution chart
                risk_data = summary['risk_distribution']
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(risk_data.keys()),
                        y=list(risk_data.values()),
                        marker_color=['#FF4444', '#FF8C00', '#FFD700', '#00C853']
                    )
                ])
                fig.update_layout(
                    title="Risk Level Distribution",
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Top anomalies table
                st.markdown(section_title("Top Anomalous Events"), unsafe_allow_html=True)
                anomalies = [r for r in results if r['is_anomaly']]
                top_5 = sorted(anomalies, key=lambda x: x['anomaly_score'], reverse=True)[:5]
                
                for a in top_5:
                    color = "#FF4444" if a['risk_level'] == 'CRITICAL' else "#FF8C00"
                    st.markdown(f"""
                    <div class="glass-card" style="margin: 0.5rem 0; border-left: 3px solid {color};">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #FAFAFA; font-weight: 600;">{a['id']}</span>
                            <span style="color: {color}; font-weight: 700;">Score: {a['anomaly_score']}</span>
                        </div>
                        <p style="color: #8B95A5; margin: 0.3rem 0;">Type: {a.get('type', 'Unknown')} | IP: {a.get('source_ip', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
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
        
        if st.button("🔄 Run Threat Clustering", type="primary", key="run_fcm"):
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
                
                for r in results[:5]:
                    memberships = r['cluster_memberships']
                    top_cat = r['primary_category']
                    conf = r['primary_confidence']
                    
                    st.markdown(f"""
                    <div class="glass-card" style="margin: 0.5rem 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #FAFAFA; font-weight: 600;">{r['id']}</span>
                            <span style="color: #8B5CF6;">{top_cat} ({conf}%)</span>
                        </div>
                        <div style="display: flex; gap: 1rem; margin-top: 0.5rem; flex-wrap: wrap;">
                            {' '.join([f'<span style="color: #8B95A5; font-size: 0.8rem;">{k}: {v}%</span>' for k, v in memberships.items()])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
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
        
        if st.button("🚀 Run Full ML Pipeline", type="primary", key="run_combined"):
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
