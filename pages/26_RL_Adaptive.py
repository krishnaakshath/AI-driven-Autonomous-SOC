import streamlit as st
import os
import sys
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="RL Adaptive | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIError:
    pass

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("RL Adaptive Classifier", "Deep Q-Network Agent — Learns what is dangerous through analyst feedback"), unsafe_allow_html=True)

# ── Load RL Module ──
RL_LOADED = False
try:
    from ml_engine.rl_threat_classifier import rl_classifier, ACTIONS
    RL_LOADED = True
except ImportError as e:
    st.error(f"RL module not loaded: {e}")

# ── Load SIEM for real events ──
SIEM_AVAILABLE = False
try:
    from services.siem_service import get_siem_events
    SIEM_AVAILABLE = True
except ImportError:
    pass


def render_metric(label, value, color):
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


ACTION_COLORS = {"SAFE": "#00C853", "SUSPICIOUS": "#FF8C00", "DANGEROUS": "#FF0040"}
ACTION_ICONS = {"SAFE": "🟢", "SUSPICIOUS": "🟡", "DANGEROUS": "🔴"}

if RL_LOADED:
    stats = rl_classifier.get_stats()

    # ═════════════════════════════════════════════════════════════════════════
    # TOP: Agent Status Cards
    # ═════════════════════════════════════════════════════════════════════════
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric("Episodes", f"{stats['episodes']:,}", "#00D4FF")
    with c2:
        render_metric("Accuracy", f"{stats['current_accuracy']}%", "#00C853")
    with c3:
        render_metric("Epsilon (ε)", f"{stats['epsilon']}", "#8B5CF6")
    with c4:
        render_metric("Total Reward", f"{stats['total_rewards']:+.0f}", "#FF8C00")
    with c5:
        render_metric("Replay Buffer", f"{stats['replay_buffer_size']}", "#FF0066")

    st.markdown("<br>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # TABS
    # ═════════════════════════════════════════════════════════════════════════
    tab1, tab2, tab3 = st.tabs(["Live Classification", "Learning Metrics", "Agent Control"])

    # ── TAB 1: Live Classification + Feedback ──
    with tab1:
        st.markdown(section_title("Classify & Teach"), unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #00D4FF; margin: 0;">How it works</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                Click <strong>Classify Events</strong> to run the RL agent on live SIEM data.
                Then review each classification and click <strong>✅ Correct</strong> or <strong>❌ Wrong</strong>.
                The agent learns from your feedback in real-time — its accuracy improves with every review.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_btn, col_auto = st.columns([1, 1])
        with col_btn:
            classify_clicked = st.button("Classify Events", type="primary", key="classify_btn")
        with col_auto:
            auto_reward_clicked = st.button("Auto-Train (Use IF Scores)", key="auto_btn",
                                            help="Automatically train using Isolation Forest anomaly scores as ground truth")

        if classify_clicked:
            with st.spinner("Classifying events..."):
                events = []
                if SIEM_AVAILABLE:
                    try:
                        siem_events = get_siem_events(20)
                        if siem_events:
                            # Convert SIEM events to ML-compatible format
                            from pages import _siem_to_ml_events_for_rl
                            events = siem_events
                    except Exception:
                        pass

                if not events:
                    # Generate sample events
                    import random
                    events = []
                    for i in range(15):
                        sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
                        events.append({
                            "id": f"EVT-RL-{i:03d}",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "bytes_in": random.randint(100, 500000),
                            "bytes_out": random.randint(100, 300000),
                            "packets": random.randint(1, 10000),
                            "duration": random.uniform(0, 3600),
                            "port": random.choice([22, 80, 443, 3389, 4444, 8080, 8888]),
                            "severity": sev,
                            "source_ip": f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                            "event_type": random.choice(["Connection Blocked", "Port Scan Detected",
                                                          "Login Failure", "Malicious Payload",
                                                          "SQL Injection Attempt", "DNS Tunneling",
                                                          "File Access", "Normal Connection"]),
                            "source": random.choice(["Firewall", "IDS/IPS", "Endpoint", "Web Server"]),
                        })

                # Classify
                classifications = rl_classifier.classify_batch(events)
                st.session_state["rl_classifications"] = list(zip(events, classifications))
                st.session_state["rl_feedback_submitted"] = set()

        if auto_reward_clicked:
            with st.spinner("Auto-training with Isolation Forest scores..."):
                events = []
                if SIEM_AVAILABLE:
                    try:
                        events = get_siem_events(50) or []
                    except Exception:
                        pass

                if not events:
                    import random
                    events = []
                    for i in range(30):
                        sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
                        events.append({
                            "id": f"EVT-AUTO-{i:03d}",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "bytes_in": random.randint(100, 500000),
                            "bytes_out": random.randint(100, 300000),
                            "packets": random.randint(1, 10000),
                            "duration": random.uniform(0, 3600),
                            "port": random.choice([22, 80, 443, 3389, 4444, 8080]),
                            "severity": sev,
                        })

                total_reward = 0
                for evt in events:
                    c = rl_classifier.classify(evt)
                    r = rl_classifier.auto_reward(evt, c)
                    total_reward += r

                rl_classifier._save_to_disk()

                new_stats = rl_classifier.get_stats()
                st.success(
                    f"Auto-trained on {len(events)} events. "
                    f"Total reward: {total_reward:+.1f} | "
                    f"Accuracy: {new_stats['current_accuracy']}% | "
                    f"ε: {new_stats['epsilon']:.4f}"
                )
                st.rerun()

        # Display classifications with feedback buttons
        if "rl_classifications" in st.session_state:
            st.markdown("---")
            st.markdown("### Classification Results")

            feedback_submitted = st.session_state.get("rl_feedback_submitted", set())

            for i, (event, result) in enumerate(st.session_state["rl_classifications"]):
                action = result["action"]
                confidence = result["confidence"]
                color = ACTION_COLORS[action]
                icon = ACTION_ICONS[action]
                event_id = result["event_id"]

                already_reviewed = event_id in feedback_submitted

                st.markdown(f"""
                <div class="glass-card" style="margin: 0.4rem 0; border-left: 3px solid {color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: #8B95A5; font-size: 0.85rem;">{event.get('source', 'Unknown')} | {event.get('event_type', 'N/A')}</span>
                            <span style="color: #555; margin-left: 0.5rem;">IP: {event.get('source_ip', 'N/A')}</span>
                        </div>
                        <div>
                            <span style="color: {color}; font-weight: 700; font-size: 1.1rem;">{icon} {action}</span>
                            <span style="color: #666; margin-left: 0.5rem;">({confidence}% conf)</span>
                        </div>
                    </div>
                    <div style="color: #555; font-size: 0.75rem; margin-top: 0.3rem;">
                        Q-values: Safe={result['q_values'][0]:.2f} | Suspicious={result['q_values'][1]:.2f} | Dangerous={result['q_values'][2]:.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if not already_reviewed:
                    fc1, fc2, fc3 = st.columns([1, 1, 4])
                    with fc1:
                        if st.button("✅ Correct", key=f"correct_{i}"):
                            rl_classifier.submit_feedback(event_id, correct=True)
                            st.session_state["rl_feedback_submitted"].add(event_id)
                            st.rerun()
                    with fc2:
                        if st.button("❌ Wrong", key=f"wrong_{i}"):
                            rl_classifier.submit_feedback(event_id, correct=False)
                            st.session_state["rl_feedback_submitted"].add(event_id)
                            st.rerun()
                else:
                    st.markdown("<span style='color: #00C853; font-size: 0.8rem;'>✔ Feedback submitted</span>",
                                unsafe_allow_html=True)

    # ── TAB 2: Learning Metrics ──
    with tab2:
        st.markdown(section_title("Learning Progress"), unsafe_allow_html=True)

        stats = rl_classifier.get_stats()

        if stats["episodes"] == 0:
            st.info("No training data yet. Classify some events and provide feedback, or use Auto-Train to get started.")
        else:
            # Reward History
            reward_hist = stats.get("reward_history", [])
            if reward_hist:
                col1, col2 = st.columns(2)

                with col1:
                    # Cumulative reward
                    cumulative = np.cumsum(reward_hist).tolist()
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        y=cumulative, mode="lines",
                        line=dict(color="#00D4FF", width=2),
                        fill="tozeroy", fillcolor="rgba(0,212,255,0.1)",
                        name="Cumulative Reward"
                    ))
                    fig.update_layout(
                        title="Cumulative Reward Over Time",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#FAFAFA",
                        height=300,
                        xaxis=dict(title="Episode", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                        yaxis=dict(title="Cumulative Reward", showgrid=True, gridcolor="rgba(255,255,255,0.05)")
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Epsilon Decay
                    eps_hist = stats.get("epsilon_history", [])
                    if eps_hist:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            y=eps_hist, mode="lines",
                            line=dict(color="#8B5CF6", width=2),
                            fill="tozeroy", fillcolor="rgba(139,92,246,0.1)",
                            name="Epsilon"
                        ))
                        fig.update_layout(
                            title="Exploration Rate (ε) Decay",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#FAFAFA",
                            height=300,
                            xaxis=dict(title="Episode", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                            yaxis=dict(title="ε", range=[0, 1.05], showgrid=True, gridcolor="rgba(255,255,255,0.05)")
                        )
                        st.plotly_chart(fig, use_container_width=True)

            # Accuracy over time
            acc_hist = stats.get("accuracy_history", [])
            if acc_hist:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=acc_hist, mode="lines",
                    line=dict(color="#00C853", width=2),
                    fill="tozeroy", fillcolor="rgba(0,200,83,0.1)",
                    name="Accuracy"
                ))
                fig.update_layout(
                    title="Classification Accuracy Over Time",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#FAFAFA",
                    height=300,
                    xaxis=dict(title="Episode", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(title="Accuracy (%)", range=[0, 105], showgrid=True, gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig, use_container_width=True)

            # Action Distribution
            st.markdown("### Action Distribution")
            action_counts = stats.get("action_counts", {})
            total_actions = sum(action_counts.values()) or 1

            ac1, ac2, ac3 = st.columns(3)
            for col, (action, count) in zip([ac1, ac2, ac3], action_counts.items()):
                pct = round(count / total_actions * 100, 1)
                with col:
                    render_metric(f"{ACTION_ICONS.get(action, '')} {action}", f"{count} ({pct}%)", ACTION_COLORS.get(action, "#888"))

            # Q-Value Analysis
            st.markdown("### Q-Value Distribution (Current Network)")
            st.markdown("""
            <div class="glass-card">
                <p style="color: #8B95A5; margin: 0;">
                    Q-values represent the agent's learned value for each action given a state.
                    Higher Q-values indicate the agent is more confident in that classification.
                    As training progresses, these values diverge — meaning the agent becomes more decisive.
                </p>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 3: Agent Control ──
    with tab3:
        st.markdown(section_title("Agent Control Panel"), unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #FF8C00; margin: 0;">Agent Configuration</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                Control the RL agent's behavior. Use <strong>Reset</strong> to start fresh,
                or <strong>Save</strong> to persist the current model to disk.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Agent details
        stats = rl_classifier.get_stats()

        st.markdown("### Agent Status")
        detail_data = {
            "Total Classifications": f"{stats['total_classifications']:,}",
            "Total Episodes (Training Steps)": f"{stats['episodes']:,}",
            "Current Accuracy": f"{stats['current_accuracy']}%",
            "Exploration Rate (ε)": f"{stats['epsilon']}",
            "Replay Buffer Size": f"{stats['replay_buffer_size']:,}",
            "Pending Feedback": f"{stats['pending_feedback_count']}",
            "Total Rewards Earned": f"{stats['total_rewards']:+.1f}",
            "Correct Classifications": f"{stats['correct_count']:,}",
            "Incorrect Classifications": f"{stats['incorrect_count']:,}",
            "Created At": stats.get("created_at", "N/A"),
            "Last Trained": stats.get("last_trained", "Never"),
        }

        for label, value in detail_data.items():
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.4rem 0;
                        border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span style="color: #8B95A5;">{label}</span>
                <span style="color: #FAFAFA; font-weight: 600;">{value}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Control buttons
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            if st.button("💾 Save Model", use_container_width=True, key="save_model"):
                rl_classifier._save_to_disk()
                st.success("Model saved to disk.")
        with bc2:
            if st.button("🔄 Reload Model", use_container_width=True, key="reload_model"):
                rl_classifier._load_from_disk()
                st.success("Model reloaded from disk.")
                st.rerun()
        with bc3:
            if st.button("⚠️ Reset Agent", use_container_width=True, key="reset_agent",
                         type="primary"):
                st.session_state["confirm_reset"] = True

        if st.session_state.get("confirm_reset"):
            st.warning("This will erase all learned knowledge. Are you sure?")
            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button("Yes, Reset Everything", key="confirm_yes"):
                    rl_classifier.reset()
                    st.session_state.pop("confirm_reset", None)
                    st.session_state.pop("rl_classifications", None)
                    st.success("Agent reset to initial state.")
                    st.rerun()
            with rc2:
                if st.button("Cancel", key="confirm_no"):
                    st.session_state.pop("confirm_reset", None)
                    st.rerun()
else:
    st.error("Reinforcement Learning module could not be loaded.")
