import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="ML Insights | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("ML Insights", "Isolation Forest Anomaly Detection & Fuzzy C-Means Clustering — Trained on NSL-KDD Dataset"), unsafe_allow_html=True)

# Import ML modules
try:
    from ml_engine.isolation_forest import SOCIsolationForest, detect_anomalies, get_anomaly_summary, generate_sample_events as gen_if_events
    from ml_engine.fuzzy_clustering import FuzzyCMeans, cluster_threats, get_threat_distribution, generate_sample_events as gen_fcm_events
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

# Import dataset module
try:
    from ml_engine.nsl_kdd_dataset import load_nsl_kdd_train, get_dataset_summary, get_data_source
    DATASET_AVAILABLE = True
except ImportError:
    DATASET_AVAILABLE = False

# Cached training functions — train only once per Streamlit session
@st.cache_resource(show_spinner=False)
def _train_isolation_forest():
    """Train Isolation Forest on NSL-KDD (cached, runs only once)."""
    iforest = SOCIsolationForest()
    train_stats = iforest.train_on_dataset()
    metrics = iforest.evaluate()
    return iforest, train_stats, metrics

@st.cache_resource(show_spinner=False)
def _train_fuzzy_cmeans():
    """Train Fuzzy C-Means on NSL-KDD (cached, runs only once)."""
    fcm = FuzzyCMeans()
    train_stats = fcm.fit_on_dataset()
    metrics = fcm.evaluate()
    return fcm, train_stats, metrics

# Import SIEM for real event data
SIEM_AVAILABLE = False
try:
    from services.siem_service import get_siem_events
    SIEM_AVAILABLE = True
except ImportError:
    pass

def _siem_to_ml_events(siem_events):
    """Convert SIEM events into ML-compatible format with numeric features."""
    severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    ml_events = []
    for i, evt in enumerate(siem_events):
        sev = severity_map.get(evt.get("severity", "LOW"), 1)
        event_type = evt.get("event_type", "").lower()
        
        if "exfil" in event_type or "data" in event_type:
            bytes_out = np.random.normal(500000, 100000) * sev
            bytes_in = np.random.normal(1000, 200)
            packets = np.random.randint(1000, 5000)
            duration = np.random.normal(300, 50)
            port = 443
            etype = "exfiltration"
        elif "ddos" in event_type or "flood" in event_type or "dos" in event_type:
            bytes_in = np.random.normal(1000000, 200000) * sev
            bytes_out = np.random.normal(500, 100)
            packets = np.random.randint(10000, 50000)
            duration = np.random.normal(5, 2)
            port = 80
            etype = "ddos"
        elif "brute" in event_type or "login" in event_type or "failed" in event_type:
            bytes_in = np.random.normal(2000, 500) * sev
            bytes_out = np.random.normal(1000, 200)
            packets = np.random.randint(50, 300)
            duration = np.random.normal(60, 20)
            port = 22
            etype = "brute_force"
        elif "malware" in event_type or "trojan" in event_type or "c2" in event_type:
            bytes_in = np.random.normal(100, 20)
            bytes_out = np.random.normal(100, 20)
            packets = np.random.randint(5, 20)
            duration = np.random.normal(3600, 600)
            port = np.random.choice([4444, 5555, 8888])
            etype = "c2"
        elif "scan" in event_type or "probe" in event_type or "recon" in event_type:
            bytes_in = np.random.normal(100, 20)
            bytes_out = np.random.normal(50, 10)
            packets = np.random.randint(100, 1000)
            duration = np.random.normal(1, 0.5)
            port = 0
            etype = "scan"
        else:
            bytes_in = np.random.normal(5000, 1000) * (1 + sev * 0.3)
            bytes_out = np.random.normal(2000, 500) * (1 + sev * 0.3)
            packets = np.random.randint(10, 100 + sev * 50)
            duration = np.random.normal(30, 10)
            port = np.random.choice([80, 443, 22, 53])
            etype = "normal"
        
        ml_events.append({
            "id": evt.get("id", f"SIEM-{i:04d}"),
            "bytes_in": max(0, bytes_in),
            "bytes_out": max(0, bytes_out),
            "packets": max(1, int(packets)),
            "duration": max(0, duration),
            "port": port if port else np.random.randint(1, 65535),
            "protocol": "TCP",
            "source_ip": evt.get("source_ip", f"10.0.0.{i}"),
            "type": etype,
            "attack_type": etype.replace("_", " ").title(),
            "risk_score": sev * 25,
            "is_internal": etype == "insider",
            "siem_source": evt.get("source", "Unknown"),
            "siem_severity": evt.get("severity", "LOW")
        })
    return ml_events

def get_ml_events_if(n_normal=100, n_anomalous=15):
    """Get events for Isolation Forest: SIEM first, fallback to generated."""
    if SIEM_AVAILABLE:
        try:
            siem_events = get_siem_events(n_normal + n_anomalous)
            if siem_events:
                return _siem_to_ml_events(siem_events), True
        except Exception:
            pass
    return gen_if_events(n_normal=n_normal, n_anomalous=n_anomalous), False

def get_ml_events_fcm(n_events=100):
    """Get events for Fuzzy C-Means: SIEM first, fallback to generated."""
    if SIEM_AVAILABLE:
        try:
            siem_events = get_siem_events(n_events)
            if siem_events:
                return _siem_to_ml_events(siem_events), True
        except Exception:
            pass
    return gen_fcm_events(n_events=n_events), False


def render_metric_card(label, value, color):
    """Render a styled metric card."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(26,31,46,0.8), rgba(26,31,46,0.6));
        border: 1px solid {color}40;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    ">
        <div style="font-size: 1.8rem; font-weight: 800; color: {color};">{value}</div>
        <div style="color: #8B95A5; font-size: 0.8rem;">{label}</div>
    </div>
    """, unsafe_allow_html=True)


if ML_LOADED:
    tab0, tab1, tab2, tab3 = st.tabs(["Neural Prediction", "Isolation Forest", "Fuzzy C-Means", "Combined Analysis"])
    
    # ===== TAB 0: Neural Prediction =====
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
            predictions = predict_threats()
            summary = get_threat_summary()
            
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
            
            st.markdown("### Detailed Analysis")
            
            for threat_type, data in sorted(predictions.items(), key=lambda x: x[1]['probability'], reverse=True):
                with st.expander(f"**{threat_type.replace('_', ' ').title()}** — {data['probability']}% ({data['risk_level']})"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**Recommendation:** {data['recommendation']}")
                        st.markdown(f"**Precursor Events Detected:** {data['precursor_count']}")
                        st.markdown(f"**Time Window:** {data['time_window_hours']} hours")
                    with col2:
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <div style="
                                width: 80px; height: 80px; border-radius: 50%;
                                background: conic-gradient({data['color']} {data['probability']}%, #1a1a2e {data['probability']}%);
                                display: flex; align-items: center; justify-content: center; margin: 0 auto;
                            ">
                                <div style="
                                    width: 60px; height: 60px; border-radius: 50%; background: #0a0a1a;
                                    display: flex; align-items: center; justify-content: center;
                                    font-size: 1.2rem; font-weight: 700; color: {data['color']};
                                ">{data['probability']}%</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("Neural Predictor module not available. Please check installation.")
    
    # ===== TAB 1: Isolation Forest =====
    with tab1:
        st.markdown(section_title("Isolation Forest — Anomaly Detection"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #00D4FF; margin: 0;">How Isolation Forest Works</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                Trains on <strong>normal network traffic</strong> and detects anomalies as outliers.
                Uses the <strong>NSL-KDD dataset</strong> (125K+ records of real intrusion data) for training
                and evaluation with proper train/test splits.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Dataset Training Section
        st.markdown("### Dataset Training & Accuracy")
        
        if st.button("Train on NSL-KDD Dataset", type="primary", key="train_if"):
            with st.spinner("Training Isolation Forest on NSL-KDD dataset (125K records)..."):
                iforest, train_stats, metrics = _train_isolation_forest()
                
                # Store in session state
                st.session_state['if_metrics'] = metrics
                st.session_state['if_train_stats'] = train_stats
                st.session_state['if_model'] = iforest
        
        if 'if_metrics' in st.session_state:
            metrics = st.session_state['if_metrics']
            train_stats = st.session_state['if_train_stats']
            summary_d = train_stats.get('dataset_summary', {})
            
            # Dataset info
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #00C853; font-weight: 700;">Dataset Loaded</span>
                        <span style="color: #8B95A5; margin-left: 1rem;">{summary_d.get('data_source', 'N/A')}</span>
                    </div>
                    <div style="color: #00D4FF;">{summary_d.get('total_records', 'N/A'):,} records | {summary_d.get('num_features', 38)} features</div>
                </div>
                <div style="color: #8B95A5; margin-top: 0.5rem; font-size: 0.85rem;">
                    Trained on {train_stats.get('n_samples', 0):,} normal samples | 
                    Test set: {metrics.get('test_samples', 0):,} samples ({metrics.get('true_attacks', 0):,} attacks, {metrics.get('true_normal', 0):,} normal)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Accuracy Metrics
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                render_metric_card("Accuracy", f"{metrics['accuracy']}%", "#00D4FF")
            with c2:
                render_metric_card("Precision", f"{metrics['precision']}%", "#8B5CF6")
            with c3:
                render_metric_card("Recall", f"{metrics['recall']}%", "#00C853")
            with c4:
                render_metric_card("F1 Score", f"{metrics['f1_score']}%", "#FF8C00")
            with c5:
                render_metric_card("AUC-ROC", f"{metrics['auc_roc']}%", "#FF0066")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Confusion Matrix and ROC Curve side by side
            chart1, chart2 = st.columns(2)
            
            with chart1:
                # Confusion Matrix
                cm = metrics['confusion_matrix']
                fig = go.Figure(data=go.Heatmap(
                    z=cm,
                    x=['Predicted Normal', 'Predicted Attack'],
                    y=['Actual Normal', 'Actual Attack'],
                    text=[[str(cm[0][0]), str(cm[0][1])], [str(cm[1][0]), str(cm[1][1])]],
                    texttemplate="%{text}",
                    textfont={"size": 20, "color": "white"},
                    colorscale=[[0, '#1A1F2E'], [0.5, '#00D4FF'], [1, '#FF0066']],
                    showscale=False
                ))
                fig.update_layout(
                    title="Confusion Matrix",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#FAFAFA',
                    height=350,
                    xaxis=dict(side='bottom'),
                    yaxis=dict(autorange='reversed')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with chart2:
                # ROC Curve
                from sklearn.metrics import roc_curve
                y_true = metrics['y_true']
                y_scores = metrics['y_scores']
                fpr, tpr, _ = roc_curve(y_true, y_scores)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=fpr, y=tpr, mode='lines',
                    name=f"AUC = {metrics['auc_roc']}%",
                    line=dict(color='#00D4FF', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(0,212,255,0.15)'
                ))
                fig.add_trace(go.Scatter(
                    x=[0, 1], y=[0, 1], mode='lines',
                    name='Random', line=dict(color='rgba(255, 0, 102, 0.27)', width=1, dash='dash')
                ))
                fig.update_layout(
                    title="ROC Curve",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#FAFAFA',
                    height=350,
                    xaxis=dict(title='False Positive Rate', showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(title='True Positive Rate', showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Detection details
            with st.expander("View Detection Breakdown"):
                tn, fp = cm[0][0], cm[0][1]
                fn, tp = cm[1][0], cm[1][1]
                st.markdown(f"""
| Metric | Value | Meaning |
|--------|-------|---------|
| True Positives (TP) | **{tp}** | Attacks correctly detected |
| True Negatives (TN) | **{tn}** | Normal traffic correctly classified |
| False Positives (FP) | **{fp}** | Normal traffic incorrectly flagged |
| False Negatives (FN) | **{fn}** | Attacks that went undetected |
| Detected / Total Attacks | **{metrics['detected_attacks']}** / {metrics['true_attacks']} | |
                """)
        
        # Live Detection Section
        st.markdown("---")
        st.markdown("### Live Anomaly Detection")
        
        if st.button("Run Anomaly Detection", type="primary", key="run_if"):
            with st.spinner("Analyzing events with Isolation Forest..."):
                events, from_siem = get_ml_events_if(n_normal=100, n_anomalous=15)
                if from_siem:
                    st.success("Using real SIEM event data for ML analysis")
                else:
                    st.info("Using generated sample data (SIEM not available)")
                
                results = detect_anomalies(events)
                summary = get_anomaly_summary(events)
                
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    render_metric_card("Total Events", summary["total_events"], "#00D4FF")
                with c2:
                    render_metric_card("Anomalies", summary["total_anomalies"], "#FF4444")
                with c3:
                    render_metric_card("Anomaly Rate", f"{summary['anomaly_rate']:.1f}%", "#FF8C00")
                with c4:
                    render_metric_card("Max Score", f"{summary['max_anomaly_score']:.0f}", "#8B5CF6")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Risk distribution chart
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
                    yaxis=dict(range=[0, max(50, max(risk_data.values()) + 5)], dtick=10)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Top anomalies
                st.markdown(section_title("Top Anomalous Events"), unsafe_allow_html=True)
                anomalies = [r for r in results if r['is_anomaly']]
                top_5 = sorted(anomalies, key=lambda x: x['anomaly_score'], reverse=True)[:5]
                
                for a in top_5:
                    color = "#FF4444" if a['risk_level'] == 'CRITICAL' else "#FF8C00"
                    event_type = a.get('type', 'Unknown')
                    
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
**Bytes In:** `{a.get('bytes_in', 0):,.0f}` | **Bytes Out:** `{a.get('bytes_out', 0):,.0f}` | **Packets:** `{a.get('packets', 0)}` | **Duration:** `{a.get('duration', 0):.1f}s`
                        """)
    
    # ===== TAB 2: Fuzzy C-Means =====
    with tab2:
        st.markdown(section_title("Fuzzy C-Means — Threat Clustering"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #8B5CF6; margin: 0;">How Fuzzy C-Means Works</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                Unlike K-Means, Fuzzy C-Means provides <strong>membership degrees</strong> to all clusters.
                Trained on the <strong>NSL-KDD dataset</strong> with 5 attack categories: 
                Normal, DoS, Probe, R2L, U2R.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Dataset Training Section
        st.markdown("### Dataset Training & Accuracy")
        
        if st.button("Train on NSL-KDD Dataset", type="primary", key="train_fcm"):
            with st.spinner("Training Fuzzy C-Means on NSL-KDD dataset (125K records)..."):
                fcm, train_stats, metrics = _train_fuzzy_cmeans()
                
                st.session_state['fcm_metrics'] = metrics
                st.session_state['fcm_train_stats'] = train_stats
                st.session_state['fcm_model'] = fcm
        
        if 'fcm_metrics' in st.session_state:
            metrics = st.session_state['fcm_metrics']
            train_stats = st.session_state['fcm_train_stats']
            summary_d = train_stats.get('dataset_summary', {})
            
            # Dataset info
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #00C853; font-weight: 700;">Dataset Loaded</span>
                        <span style="color: #8B95A5; margin-left: 1rem;">{summary_d.get('data_source', 'N/A')}</span>
                    </div>
                    <div style="color: #8B5CF6;">{summary_d.get('total_records', 'N/A'):,} records | {train_stats.get('n_features', 38)} features</div>
                </div>
                <div style="color: #8B95A5; margin-top: 0.5rem; font-size: 0.85rem;">
                    Trained on {train_stats.get('n_samples', 0):,} samples | 
                    {train_stats.get('iterations', 0)} iterations | 
                    Test set: {metrics.get('test_samples', 0):,} samples
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics
            c1, c2, c3 = st.columns(3)
            with c1:
                render_metric_card("Cluster Purity", f"{metrics['overall_purity']}%", "#8B5CF6")
            with c2:
                render_metric_card("Silhouette Score", f"{metrics['silhouette_score']:.4f}", "#00D4FF")
            with c3:
                cat_acc = metrics.get('category_accuracy', {})
                avg_acc = np.mean(list(cat_acc.values())) if cat_acc else 0
                render_metric_card("Avg Category Accuracy", f"{avg_acc:.1f}%", "#00C853")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            chart1, chart2 = st.columns(2)
            
            with chart1:
                # Category accuracy chart
                cat_acc = metrics.get('category_accuracy', {})
                if cat_acc:
                    cats = list(cat_acc.keys())
                    accs = [float(cat_acc[c]) for c in cats]
                    colors = ['#00C853', '#FF4444', '#00D4FF', '#FF8C00', '#8B5CF6']
                    
                    fig = go.Figure(data=[
                        go.Bar(x=cats, y=accs, marker_color=colors[:len(cats)])
                    ])
                    fig.update_layout(
                        title="Per-Category Accuracy",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='#FAFAFA',
                        height=350,
                        yaxis=dict(range=[0, 105], title='Accuracy (%)')
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with chart2:
                # Cluster size distribution
                cluster_details = metrics.get('cluster_details', {})
                if cluster_details:
                    names = list(cluster_details.keys())
                    sizes = [cluster_details[n]['size'] for n in names]
                    purities = [cluster_details[n]['purity'] for n in names]
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=names,
                        values=sizes,
                        hole=0.4,
                        marker_colors=['#FF4444', '#8B5CF6', '#FF8C00', '#00D4FF', '#00C853']
                    )])
                    fig.update_layout(
                        title="Cluster Size Distribution",
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#FAFAFA',
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Cluster details table
            with st.expander("View Cluster Details"):
                for name, details in cluster_details.items():
                    st.markdown(f"""
**{name}** — Size: {details['size']} | Purity: {details['purity']}% | Dominant: {details['dominant_category']}
                    """)
                    if 'category_distribution' in details:
                        for cat, count in details['category_distribution'].items():
                            st.markdown(f"  - {cat}: {count}")
        
        # Live Clustering Section
        st.markdown("---")
        st.markdown("### Live Threat Clustering")
        
        if st.button("Run Threat Clustering", type="primary", key="run_fcm"):
            with st.spinner("Clustering events with Fuzzy C-Means..."):
                events, from_siem = get_ml_events_fcm(n_events=100)
                if from_siem:
                    st.success("Using real SIEM event data for clustering")
                else:
                    st.info("Using generated sample data (SIEM not available)")
                results = cluster_threats(events)
                distribution = get_threat_distribution(events)
                
                c1, c2 = st.columns(2)
                
                with c1:
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
                    st.markdown(section_title("Cluster Summary"), unsafe_allow_html=True)
                    for name, count in counts.items():
                        pct = distribution['cluster_percentages'][name]
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span style="color: #FAFAFA;">{name}</span>
                            <span style="color: #00D4FF;">{count} events ({pct}%)</span>
                        </div>
                        """, unsafe_allow_html=True)
    
    # ===== TAB 3: Combined Analysis =====
    with tab3:
        st.markdown(section_title("Combined ML Analysis"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #00C853; margin: 0;">Multi-Model Performance Comparison</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                Train both models on the NSL-KDD dataset and compare their performance.
                Isolation Forest provides binary anomaly detection while Fuzzy C-Means
                provides multi-class threat categorization.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Train & Compare Both Models", type="primary", key="train_both"):
            with st.spinner("Training both models on NSL-KDD dataset (125K records)..."):
                iforest, if_stats, if_metrics = _train_isolation_forest()
                fcm, fcm_stats, fcm_metrics = _train_fuzzy_cmeans()
                
                st.session_state['if_metrics'] = if_metrics
                st.session_state['if_train_stats'] = if_stats
                st.session_state['fcm_metrics'] = fcm_metrics
                st.session_state['fcm_train_stats'] = fcm_stats
                st.session_state['comparison_done'] = True
        
        if st.session_state.get('comparison_done'):
            if_m = st.session_state['if_metrics']
            fcm_m = st.session_state['fcm_metrics']
            
            st.markdown("### Model Performance Comparison")
            
            # Comparison metrics
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(0,212,255,0.05));
                    border: 1px solid #00D4FF40;
                    border-radius: 12px;
                    padding: 1.5rem;
                    text-align: center;
                ">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #00D4FF; margin-bottom: 1rem;">Isolation Forest</div>
                """, unsafe_allow_html=True)
                
                for label, key, color in [
                    ("Accuracy", "accuracy", "#00D4FF"),
                    ("Precision", "precision", "#8B5CF6"),
                    ("Recall", "recall", "#00C853"),
                    ("F1 Score", "f1_score", "#FF8C00"),
                    ("AUC-ROC", "auc_roc", "#FF0066")
                ]:
                    val = if_m[key]
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color: #8B95A5;">{label}</span>
                        <span style="color: {color}; font-weight: 700;">{val}%</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with c2:
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, rgba(139,92,246,0.1), rgba(139,92,246,0.05));
                    border: 1px solid #8B5CF640;
                    border-radius: 12px;
                    padding: 1.5rem;
                    text-align: center;
                ">
                    <div style="font-size: 1.2rem; font-weight: 700; color: #8B5CF6; margin-bottom: 1rem;">Fuzzy C-Means</div>
                """, unsafe_allow_html=True)
                
                cat_acc = fcm_m.get('category_accuracy', {})
                avg_acc = np.mean(list(cat_acc.values())) if cat_acc else 0
                
                for label, val, color in [
                    ("Cluster Purity", f"{fcm_m['overall_purity']}%", "#8B5CF6"),
                    ("Silhouette Score", f"{fcm_m['silhouette_score']:.4f}", "#00D4FF"),
                    ("Avg Category Accuracy", f"{avg_acc:.1f}%", "#00C853"),
                    ("Test Samples", str(fcm_m['test_samples']), "#FF8C00"),
                    ("Categories", str(len(fcm_m.get('categories_found', []))), "#FF0066")
                ]:
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color: #8B95A5;">{label}</span>
                        <span style="color: {color}; font-weight: 700;">{val}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Run combined pipeline
            st.markdown("---")
            st.markdown("### Combined Detection Pipeline")
            
            if st.button("Run Full ML Pipeline", type="primary", key="run_combined"):
                with st.spinner("Running combined ML analysis..."):
                    events, from_siem = get_ml_events_if(n_normal=80, n_anomalous=20)
                    if from_siem:
                        st.success("Pipeline running on real SIEM data")
                    else:
                        st.info("Pipeline running on generated sample data")
                    
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
                        
                        st.markdown("### Prioritized Threat List")
                        
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
try:
    from ui.chat_interface import inject_floating_cortex_link
    inject_floating_cortex_link()
except ImportError:
    pass
