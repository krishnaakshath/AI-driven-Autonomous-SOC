import streamlit as st
import os
import sys
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="RL Adaptive | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIError:
    pass

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
from ui.page_layout import init_page, kpi_row, content_section, section_gap, page_footer, show_empty, show_error
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
from ui.theme import MOBILE_CSS
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("RL Adaptive Classifier", "Deep Q-Network Agent — Autonomously learns what is dangerous vs safe"), unsafe_allow_html=True)

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
SIGNAL_COLORS = {"isolation_forest": "#00D4FF", "severity": "#FF8C00", "event_type": "#8B5CF6",
                 "port": "#FF0066", "traffic_volume": "#00C853"}


def generate_realistic_events(n=20):
    """Generate diverse security events for classification."""
    templates = [
        {"event_type": "Normal Connection", "severity": "LOW", "port": 443, "bytes_in": 3000, "bytes_out": 1500, "packets": 20, "duration": 5, "source": "Web Server"},
        {"event_type": "SQL Injection Attempt", "severity": "CRITICAL", "port": 3306, "bytes_in": 15000, "bytes_out": 800, "packets": 45, "duration": 2, "source": "WAF"},
        {"event_type": "Port Scan Detected", "severity": "HIGH", "port": 0, "bytes_in": 200, "bytes_out": 100, "packets": 8000, "duration": 10, "source": "IDS/IPS"},
        {"event_type": "Login Failure", "severity": "MEDIUM", "port": 22, "bytes_in": 500, "bytes_out": 200, "packets": 15, "duration": 1, "source": "Endpoint"},
        {"event_type": "Malware Beacon Detected", "severity": "CRITICAL", "port": 4444, "bytes_in": 100, "bytes_out": 100, "packets": 5, "duration": 3600, "source": "IDS/IPS"},
        {"event_type": "DNS Query", "severity": "LOW", "port": 53, "bytes_in": 100, "bytes_out": 50, "packets": 2, "duration": 0.1, "source": "DNS Server"},
        {"event_type": "Data Exfiltration Alert", "severity": "CRITICAL", "port": 443, "bytes_in": 500, "bytes_out": 800000, "packets": 3000, "duration": 120, "source": "DLP"},
        {"event_type": "Brute Force Attack", "severity": "HIGH", "port": 22, "bytes_in": 50000, "bytes_out": 10000, "packets": 500, "duration": 30, "source": "Firewall"},
        {"event_type": "HTTP GET Request", "severity": "LOW", "port": 80, "bytes_in": 2000, "bytes_out": 500, "packets": 8, "duration": 0.5, "source": "Web Server"},
        {"event_type": "C2 Communication Detected", "severity": "CRITICAL", "port": 8888, "bytes_in": 50, "bytes_out": 50, "packets": 3, "duration": 7200, "source": "IDS/IPS"},
        {"event_type": "File Access", "severity": "LOW", "port": 445, "bytes_in": 5000, "bytes_out": 100, "packets": 10, "duration": 1, "source": "Endpoint"},
        {"event_type": "DDoS Flood Detected", "severity": "CRITICAL", "port": 80, "bytes_in": 5000000, "bytes_out": 100, "packets": 50000, "duration": 60, "source": "Firewall"},
        {"event_type": "Ransomware Activity", "severity": "CRITICAL", "port": 5555, "bytes_in": 200, "bytes_out": 100000, "packets": 800, "duration": 300, "source": "Endpoint"},
        {"event_type": "SSL Connection", "severity": "LOW", "port": 443, "bytes_in": 10000, "bytes_out": 5000, "packets": 30, "duration": 15, "source": "Web Server"},
        {"event_type": "DNS Tunneling Suspected", "severity": "HIGH", "port": 53, "bytes_in": 100000, "bytes_out": 80000, "packets": 2000, "duration": 600, "source": "DNS Server"},
        {"event_type": "Privilege Escalation Attempt", "severity": "CRITICAL", "port": 135, "bytes_in": 1000, "bytes_out": 500, "packets": 20, "duration": 3, "source": "Endpoint"},
        {"event_type": "SMTP Connection", "severity": "LOW", "port": 25, "bytes_in": 800, "bytes_out": 20000, "packets": 15, "duration": 5, "source": "Mail Server"},
        {"event_type": "Suspicious Outbound Connection", "severity": "MEDIUM", "port": 31337, "bytes_in": 100, "bytes_out": 50000, "packets": 200, "duration": 60, "source": "Firewall"},
    ]

    events = []
    for i in range(n):
        tmpl = random.choice(templates)
        noise = lambda v, pct=0.2: max(0, v * (1 + random.uniform(-pct, pct)))
        events.append({
            "id": f"EVT-RL-{i:03d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": tmpl["event_type"],
            "severity": tmpl["severity"],
            "port": tmpl["port"],
            "bytes_in": noise(tmpl["bytes_in"]),
            "bytes_out": noise(tmpl["bytes_out"]),
            "packets": max(1, int(noise(tmpl["packets"]))),
            "duration": noise(tmpl["duration"]),
            "source": tmpl["source"],
            "source_ip": f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
        })
    return events


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
    tab1, tab2, tab3 = st.tabs(["Autonomous Learning", "Learning Metrics", "Agent Control"])

    # ── TAB 1: Autonomous Classification & Self-Learning ──
    with tab1:
        st.markdown(section_title("Self-Learning Classifier"), unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #00D4FF; margin: 0;">How it learns by itself</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                The RL agent classifies each event, then <strong>autonomously determines the correct answer</strong>
                using 5 independent intelligence signals: <strong>Isolation Forest anomaly score</strong>, 
                <strong>severity level</strong>, <strong>event type pattern matching</strong>, 
                <strong>port reputation analysis</strong>, and <strong>traffic volume anomalies</strong>.
                It compares its classification against this ground truth, receives a reward or penalty,
                and improves its neural network — all automatically, no human input needed.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_run, col_count = st.columns([2, 1])
        with col_run:
            learn_clicked = st.button("Run Self-Learning Cycle", type="primary", key="learn_btn")
        with col_count:
            n_events = st.slider("Events per cycle", min_value=5, max_value=50, value=20, key="n_slider")

        if learn_clicked:
            with st.spinner(f"Classifying {n_events} events and learning from results..."):
                events = []
                if SIEM_AVAILABLE:
                    try:
                        events = get_siem_events(n_events) or []
                    except Exception:
                        pass
                if not events:
                    events = generate_realistic_events(n_events)

                results = []
                for evt in events:
                    classification = rl_classifier.classify(evt)
                    feedback = rl_classifier.auto_reward(evt, classification)
                    results.append({
                        "event": evt,
                        "classification": classification,
                        "feedback": feedback,
                    })

                rl_classifier._save_to_disk()
                st.session_state["rl_results"] = results

        # Display results
        if "rl_results" in st.session_state:
            results = st.session_state["rl_results"]

            # Summary bar
            correct = sum(1 for r in results if r["feedback"]["is_correct"])
            incorrect = len(results) - correct
            total_reward = sum(r["feedback"]["reward"] for r in results)
            acc = round(correct / len(results) * 100, 1) if results else 0

            st.markdown("---")
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                render_metric("This Cycle", f"{len(results)} events", "#00D4FF")
            with sc2:
                color = "#00C853" if acc >= 60 else "#FF8C00" if acc >= 40 else "#FF0040"
                render_metric("Accuracy", f"{acc}%", color)
            with sc3:
                render_metric("Correct", f"{correct}", "#00C853")
            with sc4:
                render_metric("Reward", f"{total_reward:+.1f}", "#FF8C00")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Classification Results — Agent vs Ground Truth")

            for i, r in enumerate(results):
                evt = r["event"]
                cls = r["classification"]
                fb = r["feedback"]

                agent_action = fb["agent_said"]
                truth_action = fb["ground_truth"]
                is_correct = fb["is_correct"]
                threat_score = fb["threat_score"]
                signals = fb["signals"]
                signal_scores = fb["signal_scores"]

                agent_color = ACTION_COLORS[agent_action]
                truth_color = ACTION_COLORS[truth_action]
                agent_icon = ACTION_ICONS[agent_action]
                truth_icon = ACTION_ICONS[truth_action]

                verdict_text = "✅ CORRECT" if is_correct else "❌ WRONG"
                verdict_color = "#00C853" if is_correct else "#FF0040"
                border_color = "#00C853" if is_correct else "#FF0040"

                st.markdown(f"""
                <div class="glass-card" style="margin: 0.4rem 0; border-left: 4px solid {border_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span style="color: #8B95A5; font-size: 0.85rem;">{evt.get('source', 'Unknown')}</span>
                            <span style="color: #FAFAFA; font-weight: 600; margin-left: 0.5rem;">{evt.get('event_type', 'N/A')}</span>
                            <span style="color: #555; margin-left: 0.5rem;">IP: {evt.get('source_ip', 'N/A')}</span>
                        </div>
                        <div style="display: flex; gap: 1.5rem; align-items: center;">
                            <div style="text-align: center;">
                                <div style="color: #666; font-size: 0.65rem; text-transform: uppercase;">Agent Said</div>
                                <span style="color: {agent_color}; font-weight: 700;">{agent_icon} {agent_action}</span>
                            </div>
                            <div style="color: #444;">→</div>
                            <div style="text-align: center;">
                                <div style="color: #666; font-size: 0.65rem; text-transform: uppercase;">Ground Truth</div>
                                <span style="color: {truth_color}; font-weight: 700;">{truth_icon} {truth_action}</span>
                            </div>
                            <span style="color: {verdict_color}; font-weight: 800; font-size: 0.9rem; min-width: 80px;">{verdict_text}</span>
                        </div>
                    </div>
                    <div style="color: #555; font-size: 0.7rem; margin-top: 0.4rem;">
                        Threat Score: <span style="color: {'#FF0040' if threat_score >= 65 else '#FF8C00' if threat_score >= 35 else '#00C853'}; font-weight: 600;">{threat_score}/100</span>
                        &nbsp;|&nbsp; Reward: <span style="color: {'#00C853' if fb['reward'] > 0 else '#FF0040'};">{fb['reward']:+.1f}</span>
                        &nbsp;|&nbsp; Confidence: {cls['confidence']}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"Signal Intelligence — {evt.get('event_type', 'Event')} [{evt['id']}]"):
                    # Signal breakdown bars
                    for sig_name, sig_score in signal_scores.items():
                        sig_label = sig_name.replace("_", " ").title()
                        sig_color = SIGNAL_COLORS.get(sig_name, "#888")
                        bar_width = min(sig_score, 100)
                        st.markdown(f"""
                        <div style="margin: 0.3rem 0;">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: #8B95A5; font-size: 0.8rem;">{sig_label}</span>
                                <span style="color: {sig_color}; font-weight: 600; font-size: 0.8rem;">{sig_score}/100</span>
                            </div>
                            <div style="background: rgba(255,255,255,0.05); border-radius: 4px; height: 6px; margin-top: 2px;">
                                <div style="background: {sig_color}; width: {bar_width}%; height: 100%; border-radius: 4px;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Signal reasoning
                    st.markdown("**Intelligence Signals:**")
                    for sig in signals:
                        st.markdown(f"- {sig}")

    # ── TAB 2: Learning Metrics ──
    with tab2:
        st.markdown(section_title("Learning Progress"), unsafe_allow_html=True)

        stats = rl_classifier.get_stats()

        if stats["episodes"] == 0:
            st.info("No training data yet. Click **Run Self-Learning Cycle** on the first tab to start.")
        else:
            reward_hist = stats.get("reward_history", [])
            if reward_hist:
                col1, col2 = st.columns(2)

                with col1:
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
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#FAFAFA", height=300,
                        xaxis=dict(title="Episode", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                        yaxis=dict(title="Cumulative Reward", showgrid=True, gridcolor="rgba(255,255,255,0.05)")
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
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
                            title="Exploration → Exploitation (ε Decay)",
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#FAFAFA", height=300,
                            xaxis=dict(title="Episode", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                            yaxis=dict(title="ε", range=[0, 1.05], showgrid=True, gridcolor="rgba(255,255,255,0.05)")
                        )
                        st.plotly_chart(fig, use_container_width=True)

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
                    title="Classification Accuracy Over Time (Agent Improving)",
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#FAFAFA", height=300,
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
                    render_metric(f"{ACTION_ICONS.get(action, '')} {action}", f"{count} ({pct}%)",
                                  ACTION_COLORS.get(action, "#888"))

    # ── TAB 3: Agent Control ──
    with tab3:
        st.markdown(section_title("Agent Control Panel"), unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #FF8C00; margin: 0;">How the RL Agent Decides on Its Own</h4>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                The agent uses <strong>5 independent intelligence signals</strong> to build its own ground truth:
            </p>
            <ol style="color: #8B95A5; margin: 0.5rem 0;">
                <li><strong>Isolation Forest</strong> (30%) — ML anomaly detection score</li>
                <li><strong>Severity Level</strong> (25%) — CRITICAL/HIGH/MEDIUM/LOW rating</li>
                <li><strong>Event Type Patterns</strong> (25%) — Keyword matching against known attack types</li>
                <li><strong>Port Reputation</strong> (10%) — Known malware/C2 ports vs normal service ports</li>
                <li><strong>Traffic Volume</strong> (10%) — Unusual data transfer patterns</li>
            </ol>
            <p style="color: #8B95A5; margin: 0.5rem 0;">
                These signals create a <strong>composite threat score (0-100)</strong>. The agent compares its
                classification against this score, gets rewarded or penalized, and improves its Q-network.
                Over time, epsilon (ε) decays from 1.0 → 0.05, shifting from random exploration to confident exploitation.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        stats = rl_classifier.get_stats()
        st.markdown("### Agent Status")
        detail_data = {
            "Total Classifications": f"{stats['total_classifications']:,}",
            "Total Episodes (Training Steps)": f"{stats['episodes']:,}",
            "Current Accuracy": f"{stats['current_accuracy']}%",
            "Exploration Rate (ε)": f"{stats['epsilon']} {'← Exploring' if stats['epsilon'] > 0.5 else '← Exploiting learned knowledge'}",
            "Replay Buffer Size": f"{stats['replay_buffer_size']:,}",
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

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            if st.button("Save Model", use_container_width=True, key="save_model"):
                rl_classifier._save_to_disk()
                st.success("Model saved to disk.")
        with bc2:
            if st.button("Reload Model", use_container_width=True, key="reload_model"):
                rl_classifier._load_from_disk()
                st.success("Model reloaded from disk.")
                st.rerun()
        with bc3:
            if st.button("Reset Agent", use_container_width=True, key="reset_agent", type="primary"):
                st.session_state["confirm_reset"] = True

        if st.session_state.get("confirm_reset"):
            st.warning("This will erase all learned knowledge. Are you sure?")
            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button("Yes, Reset Everything", key="confirm_yes"):
                    rl_classifier.reset()
                    st.session_state.pop("confirm_reset", None)
                    st.session_state.pop("rl_results", None)
                    st.success("Agent reset to initial state.")
                    st.rerun()
            with rc2:
                if st.button("Cancel", key="confirm_no"):
                    st.session_state.pop("confirm_reset", None)
                    st.rerun()
else:
    st.error("Reinforcement Learning module could not be loaded.")
