import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.page_layout import init_page, kpi_row, content_section, section_gap, page_footer, show_empty, show_error

# Import FL engine
FL_LOADED = False
try:
    from ml_engine.federated_learning import (
        FederatedCoordinator,
        run_federated_training,
        get_fl_status,
        get_fl_coordinator,
    )
    FL_LOADED = True
except ImportError as e:
    st.error(f"Federated Learning module not loaded: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .fl-header {
        background: linear-gradient(135deg, #0a0f1c 0%, #1a1040 50%, #0d2137 100%);
        border: 1px solid rgba(100, 70, 255, 0.3);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .fl-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(circle at 20% 50%, rgba(100, 70, 255, 0.08) 0%, transparent 50%),
                    radial-gradient(circle at 80% 50%, rgba(0, 212, 255, 0.06) 0%, transparent 50%);
    }
    .fl-header h1 {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6446ff, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.3rem 0;
        position: relative;
    }
    .fl-header p {
        color: #8892a4;
        font-size: 0.85rem;
        margin: 0;
        position: relative;
    }
    .fl-stat-card {
        background: rgba(20, 25, 45, 0.8);
        border: 1px solid rgba(100, 70, 255, 0.2);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .fl-stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00d4ff;
    }
    .fl-stat-label {
        font-size: 0.7rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .fl-node {
        background: rgba(20, 25, 45, 0.6);
        border: 1px solid rgba(100, 70, 255, 0.15);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .fl-node-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .fl-node-name {
        font-weight: 600;
        color: #c0c8e0;
        font-size: 0.85rem;
    }
    .fl-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 600;
    }
    .fl-badge-active { background: rgba(0,212,255,0.15); color: #00d4ff; }
    .fl-badge-dp { background: rgba(100,70,255,0.15); color: #6446ff; }
    .fl-compare-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1rem;
    }
    .fl-compare-table th {
        background: rgba(100, 70, 255, 0.1);
        color: #8892a4;
        padding: 0.6rem;
        text-align: left;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .fl-compare-table td {
        padding: 0.6rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-size: 0.85rem;
    }
</style>

<div class="fl-header">
    <h1>FEDERATED LEARNING</h1>
    <p>Privacy-Preserving Collaborative Threat Detection — Train across distributed SOC nodes without sharing raw data</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ═══════════════════════════════════════════════════════════════════════════════

tab_overview, tab_train, tab_results, tab_privacy = st.tabs([
    "Overview", "Training", "Results & Comparison", "Privacy Analysis"
])

with tab_overview:
    st.markdown("### How Federated Learning Works in SOC")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="fl-stat-card">
            <div class="fl-stat-value">🔒</div>
            <div class="fl-stat-label">Data Never Leaves</div>
            <div style="color:#8892a4; font-size:0.75rem; margin-top:0.5rem;">
                Raw security logs stay at each SOC node
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="fl-stat-card">
            <div class="fl-stat-value">🌐</div>
            <div class="fl-stat-label">Collaborative Training</div>
            <div style="color:#8892a4; font-size:0.75rem; margin-top:0.5rem;">
                Multiple nodes improve a shared model
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="fl-stat-card">
            <div class="fl-stat-value">📊</div>
            <div class="fl-stat-label">FedAvg Algorithm</div>
            <div style="color:#8892a4; font-size:0.75rem; margin-top:0.5rem;">
                Weighted average of model updates
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="fl-stat-card">
            <div class="fl-stat-value">🛡️</div>
            <div class="fl-stat-label">Differential Privacy</div>
            <div style="color:#8892a4; font-size:0.75rem; margin-top:0.5rem;">
                Optional noise for extra protection
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    #### Federated Learning Pipeline
    
    ```
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  SOC Node 1  │  │  SOC Node 2  │  │  SOC Node 3  │  │  SOC Node N  │
    │  (Private    │  │  (Private    │  │  (Private    │  │  (Private    │
    │   Data)      │  │   Data)      │  │   Data)      │  │   Data)      │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │ Train Local     │ Train Local     │ Train Local     │
           ▼                 ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Local Model  │  │ Local Model  │  │ Local Model  │  │ Local Model  │
    │   Weights    │  │   Weights    │  │   Weights    │  │   Weights    │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                 │                 │
           └────────────┬────┴────────┬────────┘────────┬────────┘
                        ▼                               │
               ┌────────────────────┐                   │
               │   FedAvg Server    │◀──────────────────┘
               │  (Aggregation)     │
               └────────┬───────────┘
                        │ Broadcast Global Model
           ┌────────────┼────────────┬──────────────────┐
           ▼            ▼            ▼                  ▼
    ┌─────────────┐ ┌─────────┐ ┌─────────┐      ┌─────────┐
    │  Updated    │ │ Updated │ │ Updated │      │ Updated │
    │  Node 1     │ │ Node 2  │ │ Node 3  │ ...  │ Node N  │
    └─────────────┘ └─────────┘ └─────────┘      └─────────┘
    ```
    
    **Key Benefits for Security Operations:**
    - **GDPR/Compliance**: Data residency requirements are met automatically
    - **Threat Diversity**: Models learn from threats across all nodes
    - **Resilience**: No single point of data failure
    - **Scalability**: Add new SOC nodes without data migration
    """)

# ═══════════════════════════════════════════════════════════════════════════════
# TRAINING TAB
# ═══════════════════════════════════════════════════════════════════════════════

with tab_train:
    if not FL_LOADED:
        st.error("Federated Learning module is not available.")
        st.stop()

    st.markdown("### Configure Federated Training")

    col_cfg1, col_cfg2 = st.columns(2)

    with col_cfg1:
        n_clients = st.slider("Number of SOC Nodes", min_value=2, max_value=10, value=5,
                              help="Simulated federated clients (SOC sites)")
        n_rounds = st.slider("Training Rounds", min_value=3, max_value=30, value=10,
                             help="Number of federated communication rounds")

    with col_cfg2:
        alpha = st.slider("Data Heterogeneity (α)", min_value=0.1, max_value=5.0, value=0.5, step=0.1,
                          help="Lower α = more non-IID (different threat distributions per node)")
        dp_epsilon = st.slider("Differential Privacy Budget (ε)", min_value=0.0, max_value=10.0,
                               value=0.0, step=0.5,
                               help="0 = no privacy noise. Lower ε = stronger privacy but less accuracy")

    st.markdown("---")

    # Configuration preview
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.metric("Nodes", n_clients)
    with col_p2:
        st.metric("Rounds", n_rounds)
    with col_p3:
        heterogeneity = "High" if alpha < 1 else "Medium" if alpha < 3 else "Low"
        st.metric("Heterogeneity", heterogeneity)
    with col_p4:
        dp_label = "Off" if dp_epsilon == 0 else f"ε={dp_epsilon}"
        st.metric("Diff Privacy", dp_label)

    st.markdown("---")

    # Training button
    if st.button("🚀 Start Federated Training", type="primary", use_container_width=True):
        coordinator = FederatedCoordinator(
            n_clients=n_clients,
            n_rounds=n_rounds,
            alpha=alpha,
            dp_epsilon=dp_epsilon,
        )

        # Prepare data
        with st.spinner("Preparing data partitions across SOC nodes..."):
            data_info = coordinator.prepare_data()

        st.success(f"Data loaded: **{data_info['total_samples']:,}** samples "
                   f"({data_info['n_normal']:,} normal, {data_info['n_anomalies']:,} anomalies)")

        # Progress tracking
        progress_bar = st.progress(0, text="Initializing federated training...")
        status_area = st.empty()
        metrics_area = st.empty()

        round_accuracies = []
        round_f1s = []

        def progress_callback(round_num, total, metrics):
            progress_bar.progress(
                round_num / total,
                text=f"Round {round_num}/{total} — Global Accuracy: {metrics['global_accuracy']:.1f}%"
            )
            round_accuracies.append(metrics["global_accuracy"])
            round_f1s.append(metrics["global_f1"])

            # Live chart
            with metrics_area.container():
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(1, len(round_accuracies) + 1)),
                    y=round_accuracies,
                    mode="lines+markers",
                    name="Accuracy",
                    line=dict(color="#00d4ff", width=2),
                    marker=dict(size=6),
                ))
                fig.add_trace(go.Scatter(
                    x=list(range(1, len(round_f1s) + 1)),
                    y=round_f1s,
                    mode="lines+markers",
                    name="F1 Score",
                    line=dict(color="#6446ff", width=2),
                    marker=dict(size=6),
                ))
                fig.update_layout(
                    title="Live Training Progress",
                    xaxis_title="Round",
                    yaxis_title="Score (%)",
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    margin=dict(l=40, r=20, t=40, b=40),
                    yaxis=dict(range=[0, 105]),
                )
                st.plotly_chart(fig, use_container_width=True, key=f"live_chart_{round_num}")

        # Run training
        results = coordinator.run_federated_training(progress_callback=progress_callback)
        progress_bar.progress(1.0, text="Training complete!")

        # Store results in session state
        st.session_state["fl_results"] = results
        st.session_state["fl_coordinator"] = coordinator

        st.success(f"✅ Federated training complete! Final accuracy: **{results['final_global_accuracy']:.1f}%**")

        # Show gap with centralized
        if results.get("centralized_baseline"):
            gap = results["accuracy_gap"]
            if abs(gap) < 3:
                st.info(f"FL model is within **{abs(gap):.1f}%** of centralized baseline — excellent privacy-utility tradeoff!")
            elif gap > 0:
                st.warning(f"FL model is **{gap:.1f}%** below centralized baseline (expected tradeoff for privacy)")

# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS TAB
# ═══════════════════════════════════════════════════════════════════════════════

with tab_results:
    results = st.session_state.get("fl_results")
    coordinator = st.session_state.get("fl_coordinator")

    if not results or results.get("status") != "completed":
        st.info("No training results yet. Go to the **Training** tab to start federated training.")
    else:
        # ── Summary Cards ──
        st.markdown("### Training Summary")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.markdown(f"""
            <div class="fl-stat-card">
                <div class="fl-stat-value">{results['final_global_accuracy']:.1f}%</div>
                <div class="fl-stat-label">Global Accuracy</div>
            </div>""", unsafe_allow_html=True)
        with col_s2:
            st.markdown(f"""
            <div class="fl-stat-card">
                <div class="fl-stat-value">{results['final_global_f1']:.1f}%</div>
                <div class="fl-stat-label">Global F1 Score</div>
            </div>""", unsafe_allow_html=True)
        with col_s3:
            st.markdown(f"""
            <div class="fl-stat-card">
                <div class="fl-stat-value">{results['convergence_round']}</div>
                <div class="fl-stat-label">Convergence Round</div>
            </div>""", unsafe_allow_html=True)
        with col_s4:
            gap = results.get("accuracy_gap", 0) or 0
            gap_color = "#00ff88" if abs(gap) < 3 else "#ffaa00" if abs(gap) < 5 else "#ff4444"
            st.markdown(f"""
            <div class="fl-stat-card">
                <div class="fl-stat-value" style="color:{gap_color}">{abs(gap):.1f}%</div>
                <div class="fl-stat-label">Gap vs Centralized</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # ── Per-Round Convergence Chart ──
        st.markdown("### Per-Round Convergence")
        rounds_data = results["round_metrics"]
        df_rounds = pd.DataFrame(rounds_data)

        fig_conv = go.Figure()
        fig_conv.add_trace(go.Scatter(
            x=df_rounds["round"], y=df_rounds["global_accuracy"],
            mode="lines+markers", name="Global Accuracy",
            line=dict(color="#00d4ff", width=3),
            marker=dict(size=8, symbol="circle"),
        ))
        fig_conv.add_trace(go.Scatter(
            x=df_rounds["round"], y=df_rounds["global_f1"],
            mode="lines+markers", name="Global F1",
            line=dict(color="#6446ff", width=3),
            marker=dict(size=8, symbol="diamond"),
        ))
        fig_conv.add_trace(go.Scatter(
            x=df_rounds["round"], y=df_rounds["avg_client_accuracy"],
            mode="lines+markers", name="Avg Client Accuracy",
            line=dict(color="#ff6b6b", width=2, dash="dash"),
            marker=dict(size=6),
        ))

        # Add centralized baseline
        if results.get("centralized_baseline"):
            bl = results["centralized_baseline"]["accuracy"]
            fig_conv.add_hline(
                y=bl, line_dash="dot", line_color="#00ff88",
                annotation_text=f"Centralized Baseline: {bl:.1f}%",
                annotation_position="top left",
            )

        fig_conv.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=420,
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis_title="Training Round",
            yaxis_title="Score (%)",
            yaxis=dict(range=[0, 105]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_conv, use_container_width=True)

        st.markdown("---")

        # ── Client Data Distribution ──
        st.markdown("### Client Data Distribution (Non-IID)")
        dist_data = results.get("client_data_distribution", [])
        if dist_data:
            df_dist = pd.DataFrame(dist_data)
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Bar(
                x=[f"Node {d['client_id']}" for d in dist_data],
                y=[d["n_samples"] - d["n_anomalies"] for d in dist_data],
                name="Normal",
                marker_color="#00d4ff",
            ))
            fig_dist.add_trace(go.Bar(
                x=[f"Node {d['client_id']}" for d in dist_data],
                y=[d["n_anomalies"] for d in dist_data],
                name="Anomalies",
                marker_color="#ff6b6b",
            ))
            fig_dist.update_layout(
                barmode="stack",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=320,
                margin=dict(l=40, r=20, t=20, b=40),
                xaxis_title="SOC Node",
                yaxis_title="Number of Events",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_dist, use_container_width=True)

        st.markdown("---")

        # ── FL vs Centralized Comparison ──
        st.markdown("### Federated vs. Centralized Comparison")
        if results.get("centralized_baseline"):
            bl = results["centralized_baseline"]
            comp_data = {
                "Metric": ["Accuracy", "Precision", "Recall", "F1 Score"],
                "Federated Learning": [
                    f"{results['final_global_accuracy']:.1f}%",
                    f"{rounds_data[-1]['global_precision']:.1f}%",
                    f"{rounds_data[-1]['global_recall']:.1f}%",
                    f"{results['final_global_f1']:.1f}%",
                ],
                "Centralized Baseline": [
                    f"{bl['accuracy']:.1f}%",
                    f"{bl['precision']:.1f}%",
                    f"{bl['recall']:.1f}%",
                    f"{bl['f1_score']:.1f}%",
                ],
                "Privacy": ["✅ Data stays local", "✅ Data stays local",
                            "✅ Data stays local", "✅ Data stays local"],
            }
            st.table(pd.DataFrame(comp_data).set_index("Metric"))

            # Radar chart comparison
            categories = ["Accuracy", "Precision", "Recall", "F1 Score"]
            fl_vals = [
                results['final_global_accuracy'],
                rounds_data[-1]['global_precision'],
                rounds_data[-1]['global_recall'],
                results['final_global_f1'],
            ]
            cent_vals = [bl['accuracy'], bl['precision'], bl['recall'], bl['f1_score']]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=fl_vals + [fl_vals[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name='Federated',
                line_color='#00d4ff',
                fillcolor='rgba(0,212,255,0.15)',
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=cent_vals + [cent_vals[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name='Centralized',
                line_color='#00ff88',
                fillcolor='rgba(0,255,136,0.1)',
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100]),
                    bgcolor="rgba(0,0,0,0)",
                ),
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=400,
                margin=dict(l=60, r=60, t=40, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("---")

        # ── Deploy Global Model ──
        st.markdown("### Deploy Global Model")
        st.info("Deploy the federated global model as the active anomaly detector for the SOC platform.")

        if coordinator and st.button("🚀 Deploy FL Model to Production", type="primary"):
            success = coordinator.deploy_global_model()
            if success:
                st.success("✅ Federated model deployed! The Isolation Forest anomaly detector now uses the FL-trained model.")
            else:
                st.error("❌ Deployment failed. Check the logs for details.")

# ═══════════════════════════════════════════════════════════════════════════════
# PRIVACY TAB
# ═══════════════════════════════════════════════════════════════════════════════

with tab_privacy:
    results = st.session_state.get("fl_results")
    coordinator = st.session_state.get("fl_coordinator")

    st.markdown("### Privacy-Preserving Mechanisms")

    # Explain DP
    st.markdown("""
    #### Differential Privacy (DP) in Federated Learning
    
    Differential privacy adds calibrated noise to model updates before sharing,
    ensuring that no individual security event can be reverse-engineered from 
    the shared parameters.
    
    | Privacy Budget (ε) | Privacy Level | Noise Impact |
    |:-:|:-:|:-:|
    | 0 | None | No noise — full accuracy |
    | 0.1 – 1.0 | 🟢 High | Strong noise — significant accuracy cost |
    | 1.0 – 5.0 | 🟡 Medium | Moderate noise — small accuracy cost |
    | 5.0+ | 🔴 Low | Minimal noise — near-original accuracy |
    """)

    if coordinator and coordinator.is_trained:
        privacy = coordinator.get_privacy_analysis()

        col_dp1, col_dp2, col_dp3 = st.columns(3)
        with col_dp1:
            st.metric("DP Enabled", "Yes" if privacy["dp_enabled"] else "No")
        with col_dp2:
            st.metric("Privacy Level", privacy["privacy_level"])
        with col_dp3:
            st.metric("Accuracy with DP", f"{privacy['accuracy_with_dp']:.1f}%")

        st.markdown(f"**Noise Configuration:** {privacy['noise_impact']}")

        st.markdown("---")

        # DP Impact Simulation
        st.markdown("#### DP Impact Simulation")
        st.markdown("See how different privacy budgets affect model accuracy:")

        # Show stored results accuracy as the current data point
        if results and results.get("round_metrics"):
            current_acc = results["final_global_accuracy"]
            current_eps = results.get("dp_epsilon", 0)

            # Simulate different epsilon values
            eps_values = [0, 0.5, 1.0, 2.0, 5.0, 10.0]
            # Approximate accuracy degradation curve
            baseline_acc = results.get("centralized_baseline", {}).get("accuracy", current_acc)
            sim_accs = []
            for eps in eps_values:
                if eps == 0:
                    sim_accs.append(baseline_acc)
                else:
                    # Approximate: accuracy drops as ~1/epsilon
                    noise_penalty = min(15, 5.0 / eps)
                    sim_accs.append(round(baseline_acc - noise_penalty, 1))

            fig_dp = go.Figure()
            fig_dp.add_trace(go.Scatter(
                x=eps_values, y=sim_accs,
                mode="lines+markers",
                name="Estimated Accuracy",
                line=dict(color="#6446ff", width=3),
                marker=dict(size=10),
                fill="tozeroy",
                fillcolor="rgba(100,70,255,0.1)",
            ))
            # Mark current setting
            fig_dp.add_trace(go.Scatter(
                x=[current_eps], y=[current_acc],
                mode="markers",
                name="Current Setting",
                marker=dict(size=16, color="#00d4ff", symbol="star"),
            ))
            fig_dp.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                margin=dict(l=40, r=20, t=20, b=40),
                xaxis_title="Privacy Budget (ε)",
                yaxis_title="Accuracy (%)",
                yaxis=dict(range=[50, 105]),
            )
            st.plotly_chart(fig_dp, use_container_width=True)

    else:
        st.info("Run federated training first to see privacy analysis results.")

    st.markdown("---")
    st.markdown("""
    #### Data Protection Summary

    | Aspect | Protection |
    |:---|:---|
    | Raw Event Data | ✅ Never leaves the SOC node |
    | Model Updates | ✅ Only aggregated parameters shared |
    | Differential Privacy | ✅ Optional Gaussian noise on updates |
    | Compliance | ✅ GDPR / HIPAA / data residency compatible |
    | Reversibility | ✅ Cannot reconstruct individual events from model |
    """)
