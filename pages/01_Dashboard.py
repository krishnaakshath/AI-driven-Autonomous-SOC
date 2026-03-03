import streamlit as st
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import sys

# Force Reload Fix

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Dashboard | SOC", page_icon="D", layout="wide")
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

# --- CLOUD BACKGROUND SERVICE ---
# Starts a singleton thread for continuous data ingestion (works on Streamlit Cloud)
try:
    from services.cloud_background import start_cloud_background_service
    start_cloud_background_service()
except Exception as e:
    print(f"Failed to start background service: {e}")
# --------------------------------

# ── Suspicious Login Warning ─────────────────────────────────────────────────
if st.session_state.get('login_warning'):
    sus = st.session_state.pop('login_warning')
    risk = sus.get('risk_score', 0)
    reasons = sus.get('reasons', [])
    st.warning(
        f"⚠️ **Unusual Login Activity Detected** (Risk Score: {risk}/100)\n\n"
        + "\n".join(f"- {r}" for r in reasons)
        + "\n\nIf this wasn't you, **change your password immediately** in Settings."
    )


# Premium animated theme
st.markdown("""
<style>
    /* Live Action Ticker */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: rgba(0, 0, 0, 0.4);
        padding: 5px 0;
        border-bottom: 1px solid rgba(0, 243, 255, 0.2);
        margin-bottom: 1rem;
    }
    .ticker {
        display: inline-block;
        white-space: nowrap;
        padding-right: 100%;
        animation: ticker 30s linear infinite;
    }
    @keyframes ticker {
        0% { transform: translate3d(100%, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }
    .ticker-item {
        display: inline-block;
        padding: 0 2rem;
        color: var(--neon-cyan);
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)



# Import advanced UI components
from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title, metric_card

# --- STYLES ALREADY INJECTED ---




@st.cache_data(ttl=5)
def load_soc_data():
    """
    Load real security data from the SIEM service (backed by SQLite).
    Relying exclusively on persistent records now.
    """
    try:
        from services.siem_service import siem_service
        
        # Use SIEM Service (Trigger auto-seeding if DB is low)
        events = siem_service.generate_events(count=5000)
        
        if not events:
            return pd.DataFrame() # Let the UI handle empty state

        data = []
        for e in events:
            sev = e.get('severity', 'LOW')
            # Mapping SIEM severity to numeric risk score for charts
            risk_score = {"CRITICAL": 95, "HIGH": 75, "MEDIUM": 50, "LOW": 15}.get(sev, 10)
            
            msg = str(e.get('event_type', '')).upper()
            decision = e.get('status', 'ALLOW').upper() # Map status or use logic
            if "BLOCKED" in msg or "BLOCK" in msg:
                decision = "BLOCK"
            elif risk_score > 60:
                decision = "RESTRICT"
            else:
                decision = "ALLOW"
                
            port = 80
            if "SSH" in msg or "22" in msg: port = 22
            elif "RDP" in msg or "3389" in msg: port = 3389
            elif "SQL" in msg or "3306" in msg: port = 3306
            elif "DNS" in msg or "53" in msg: port = 53
            
            attack_type = "Normal"
            if "SQL" in msg: attack_type = "SQL Injection"
            elif "XSS" in msg: attack_type = "XSS"
            elif "DDOS" in msg or "FLOOD" in msg: attack_type = "DDoS"
            elif "BRUTE" in msg or "LOGIN" in msg: attack_type = "Brute Force"
            elif "MALWARE" in msg: attack_type = "Malware"
            elif risk_score > 50: attack_type = msg[:20].capitalize()
            
            try:
                # Use the event's actual timestamp
                ts = datetime.strptime(e.get('timestamp'), "%Y-%m-%d %H:%M:%S")
            except Exception:
                ts = datetime.now()

            data.append({
                "timestamp": ts,
                "attack_type": attack_type,
                "risk_score": float(risk_score),
                "access_decision": decision,
                "source_country": e.get('source_country', "United States"), # DB may not have it yet
                "source_ip": e.get('source_ip', '0.0.0.0'),
                "dest_port": port
            })
            
        return pd.DataFrame(data)

    except Exception as e:
        print(f"DASHBOARD RELOAD ERROR: {e}")
        return pd.DataFrame()

df = load_soc_data()

# Alert service for critical events
try:
    from alerting.alert_service import trigger_alert, send_test_alert
    ALERTS_AVAILABLE = True
except Exception:
    ALERTS_AVAILABLE = False

# Check for critical events and send alerts
if ALERTS_AVAILABLE and not df.empty and "risk_score" in df.columns:
    critical_events = df[df["risk_score"] >= 80]
    if len(critical_events) > 0 and 'last_alert_check' not in st.session_state:
        st.session_state.last_alert_check = True
        # Send alert for the most critical event
        worst_event = critical_events.iloc[0]
        alert_data = {
            "attack_type": worst_event.get("attack_type", "Unknown"),
            "risk_score": float(worst_event.get("risk_score", 0)),
            "source_ip": worst_event.get("source_ip", "Unknown"),
            "access_decision": worst_event.get("access_decision", "BLOCK"),
            "source_country": worst_event.get("source_country", "Unknown"),
            "dest_port": int(worst_event.get("dest_port", 0)),
            "timestamp": str(worst_event.get("timestamp", datetime.now()))
        }
        result = trigger_alert(alert_data)
        if result.get("telegram") or result.get("email"):
            st.toast(" Critical alert sent!", icon="🚨")


# --- LIVE ACTION TICKER ---
try:
    from services.database import db
    recent_fw = [e for e in db.get_recent_events(limit=50) if e.get("source") == "Firewall"][:5]
    if recent_fw:
        ticker_html = '<div class="ticker-wrap"><div class="ticker">'
        for r in recent_fw:
            ticker_html += f'<span class="ticker-item">🛡️ [FIREWALL] Blocked IP {r.get("source_ip")} ({r.get("event_type").replace("Active Block: ", "")})</span>'
        ticker_html += '</div></div>'
        st.markdown(ticker_html, unsafe_allow_html=True)
except Exception:
    pass

# Premium Header with Threat Radar
c_head, c_radar, c_live = st.columns([2.5, 1, 1.5])
with c_head:
    st.markdown(page_header("Security Operations Center", "Production-grade autonomous threat monitoring"), unsafe_allow_html=True)

with c_radar:
    # Threat Radar Animation
    st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
            <div class="radar-container">
                <div class="radar-sweep"></div>
                <div class="radar-point" style="top: 20%; left: 30%;"></div>
                <div class="radar-point" style="top: 60%; left: 70%; animation-delay: 0.5s;"></div>
                <div class="radar-point" style="top: 40%; left: 50%; animation-delay: 1.2s;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Calculate metrics
    # Fetch true totals from DB to avoid the 5000 limit cap display
    try:
        from services.database import db
        true_stats = db.get_stats()
        true_total = true_stats.get('total', 0)
        true_critical = true_stats.get('critical', 0)
        
        # If DB total is greater than loaded df (5000), use DB total
        if true_total > len(df):
            total = true_total
            critical = true_critical
            
            if len(df) > 0:
                ratio = true_total / len(df)
                blocked = int((df["access_decision"] == "BLOCK").sum() * ratio) if "access_decision" in df else 0
                restricted = int((df["access_decision"] == "RESTRICT").sum() * ratio) if "access_decision" in df else 0
                allowed = int((df["access_decision"] == "ALLOW").sum() * ratio) if "access_decision" in df else 0
        else:
            total = len(df)
            blocked = (df["access_decision"] == "BLOCK").sum() if "access_decision" in df else 0
            restricted = (df["access_decision"] == "RESTRICT").sum() if "access_decision" in df else 0
            allowed = (df["access_decision"] == "ALLOW").sum() if "access_decision" in df else 0
            critical = (df["risk_score"] >= 80).sum() if "risk_score" in df else 0
            
    except Exception as e:
        # Fallback to dataframe counts with safety checks
        total = len(df) if isinstance(df, pd.DataFrame) else 0
        blocked = (df["access_decision"] == "BLOCK").sum() if isinstance(df, pd.DataFrame) and "access_decision" in df.columns else 0
        restricted = (df["access_decision"] == "RESTRICT").sum() if isinstance(df, pd.DataFrame) and "access_decision" in df.columns else 0
        allowed = (df["access_decision"] == "ALLOW").sum() if isinstance(df, pd.DataFrame) and "access_decision" in df.columns else 0
        critical = (df["risk_score"] >= 80).sum() if isinstance(df, pd.DataFrame) and "risk_score" in df.columns else 0
        
    avg_risk = df["risk_score"].mean() if (isinstance(df, pd.DataFrame) and not df.empty and "risk_score" in df.columns) else 0

    # System is now permanently real-time and production-ready
    IS_LIVE_CONNECTION = True

# Adjust allowed if blocked changed significantly to keep total sane
if blocked > total:
    total = blocked + restricted + allowed

# Redraw Header Badge
with c_live:
    # Prepare dynamic styles
    badge_color = "#00C853" 
    badge_bg = "rgba(0, 200, 83, 0.15)"
    badge_text = "PRODUCTION ACTIVE"
    
    st.markdown(f"""
        <div style="height: 100%; display: flex; align-items: center; justify-content: flex-end; gap: 1rem; padding-top: 1.5rem; padding-bottom: 0.5rem;">
            <div class="live-badge" style="padding: 0.6rem 1.2rem; border-color: {badge_color}; color: {badge_color}; background: {badge_bg}; white-space: nowrap;">
                <span class="live-dot" style="background: {badge_color};"></span>
                {badge_text}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col_auto, col_refresh = st.columns([1.5, 1])
    with col_auto:
        st.markdown("<div style='padding-top: 5px; float: right;'>", unsafe_allow_html=True)
        auto_refresh = st.toggle("Auto-Sync", value=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_refresh:
        if st.button("↻ Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Animated Metric Cards
m1, m2, m3, m4, m5, m6 = st.columns(6)

metrics_data = [
    (m1, total, "Total Events", "#00D4FF"),
    (m2, critical, "Critical", "#FF4444"),
    (m3, blocked, "Blocked", "#FF6B6B"),
    (m4, restricted, "Restricted", "#FF8C00"),
    (m5, allowed, "Allowed", "#00C853"),
    (m6, f"{avg_risk:.1f}", "Avg Risk", "#8B5CF6")
]

for col, value, label, color in metrics_data:
    with col:
        display_value = f"{value:,}" if isinstance(value, (int, np.integer)) else value
        
        # Determine color for metric card
        card_color = color
        if label == "Total Events": card_color = "#00f3ff"   # Neon Cyan
        elif label == "Critical": card_color = "#ff003c"     # Neon Red
        elif label == "Blocked": card_color = "#bc13fe"      # Neon Purple
        
        st.markdown(metric_card(display_value, label, card_color), unsafe_allow_html=True)

# System Health Summary
st.markdown("<br>", unsafe_allow_html=True)

# --- GLOBAL THREAT MATRIX ---
st.markdown(section_title("Global Threat Matrix"), unsafe_allow_html=True)
try:
    # Fetch data points for the map (Real Blocks)
    map_events = [e for e in db.get_recent_events(limit=200) if e.get("severity") in ["HIGH", "CRITICAL"]]
    if map_events:
        map_df = pd.DataFrame(map_events)
        # Randomly assign coords for visualization if not present (Simulation improvement)
        map_df['lat'] = np.random.uniform(-40, 60, len(map_df))
        map_df['lon'] = np.random.uniform(-120, 140, len(map_df))
        
        fig_map = go.Figure(go.Scattergeo(
            lon = map_df['lon'],
            lat = map_df['lat'],
            text = map_df['source_ip'] + " [" + map_df['event_type'] + "]",
            mode = 'markers',
            marker = dict(
                size = 10,
                opacity = 0.8,
                reversescale = True,
                autocolorscale = False,
                symbol = 'circle',
                line = dict(width=1, color='rgba(102, 102, 102)'),
                colorscale = 'Electric',
                cmin = 0,
                color = np.random.randint(50, 100, len(map_df)),
                colorbar_title="Risk Intensity"
            )))

        fig_map.update_layout(
            geo = dict(
                scope='world',
                projection_type='natural earth',
                showland = True,
                landcolor = "rgb(15, 15, 35)",
                subunitcolor = "rgb(0, 243, 255, 0.1)",
                countrycolor = "rgb(0, 243, 255, 0.2)",
                showocean=True,
                oceancolor="rgb(10, 10, 25)",
                bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=450
        )
        st.plotly_chart(fig_map, use_container_width=True)
except Exception as e:
    st.error(f"Map Error: {e}")

# Charts
chart1, chart2 = st.columns(2)

with chart1:
    st.markdown(section_title("Threat Activity Timeline (Last 6 Months)"), unsafe_allow_html=True)
    try:
        from services.database import db
        daily_counts = db.get_daily_counts(days=180)
        
        if daily_counts:
            # Create a dataframe for easy handling
            df_timeline = pd.DataFrame(daily_counts)
            df_timeline['date'] = pd.to_datetime(df_timeline['date'])
            
            # Re-index to ensure we have a continuous line even for zero-event days
            min_date = df_timeline['date'].min()
            max_date = df_timeline['date'].max()
            if str(min_date) != 'NaT':
                all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
                df_timeline = df_timeline.set_index('date').reindex(all_dates, fill_value=0).reset_index()
                df_timeline = df_timeline.rename(columns={'index': 'date'})
            
            fig = go.Figure()
            
            # Neon Glow Effect Layer
            fig.add_trace(go.Scatter(
                x=df_timeline["date"], y=df_timeline["count"], 
                mode="lines",
                line=dict(color="rgba(0, 212, 255, 0.3)", width=8, shape='spline'),
                hoverinfo='skip',
                showlegend=False
            ))
            
            # Main Line Layer with Elaborate Checkpoints
            fig.add_trace(go.Scatter(
                x=df_timeline["date"], y=df_timeline["count"], 
                mode="lines+markers", fill="tozeroy",
                name="Threat Events",
                line=dict(color="#00D4FF", width=4, shape='spline'),
                marker=dict(
                    size=10, 
                    color="#000000", 
                    line=dict(width=2, color="#00D4FF"),
                    symbol="circle"
                ),
                fillcolor="rgba(0, 212, 255, 0.2)",
                hovertemplate="<b>Date</b>: %{x}<br><b>Total Events</b>: %{y:,}<extra></extra>",
                showlegend=False
            ))
            
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                xaxis=dict(showgrid=False, showline=True, linecolor="rgba(255,255,255,0.2)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)", showline=False),
                margin=dict(l=20, r=20, t=20, b=20), height=380,
                hovermode="x unified"
            )
            # Enable point selection to view detailed daily data
            selection = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
            
            # Show detailed breakdown if user selects a date on the timeline
            if selection and isinstance(selection, dict) and "selection" in selection:
                points = selection["selection"].get("points", [])
                if points:
                    try:
                        selected_date = points[0].get("x")
                        target_date = pd.to_datetime(selected_date).strftime('%Y-%m-%d')
                        st.markdown(f"**Threat Log for {target_date}**")
                        
                        with st.spinner("Checking historical archives..."):
                            # Fetch exact events for that day
                            rows = db._supabase.select("events", params={"timestamp": f"like.{target_date}%"}, limit=500, order="timestamp.desc")
                            if rows:
                                ddf = pd.DataFrame(rows)
                                st.dataframe(
                                    ddf[['timestamp', 'event_type', 'source_ip', 'severity', 'status']], 
                                    use_container_width=True, 
                                    hide_index=True
                                )
                            else:
                                st.info(f"No specific threat logs found for {target_date}.")
                    except Exception as e:
                        st.error(f"Error fetching logs for date: {e}")
        else:
            st.info("No historical timeline data available.")
    except Exception as e:
        st.error(f"Chart Error: {e}")

with chart2:
    st.markdown(section_title("Decision Distribution"), unsafe_allow_html=True)
    if not df.empty and "access_decision" in df.columns:
        decision_counts = df["access_decision"].value_counts()
        fig2 = go.Figure(data=[go.Pie(
            labels=decision_counts.index, values=decision_counts.values, hole=0.6,
            marker_colors=["#00C853", "#FF8C00", "#FF4444"],
            textinfo="percent", textfont_size=14, textfont_color="#FFFFFF"
        )])
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#FAFAFA", showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1),
            margin=dict(l=20, r=20, t=20, b=60), height=300
        )
        st.plotly_chart(fig2, use_container_width=True)

chart3, chart4 = st.columns(2)

with chart3:
    st.markdown(section_title("Top Attack Types"), unsafe_allow_html=True)
    if not df.empty:
        attack_counts = df[df["attack_type"] != "Normal"]["attack_type"].value_counts().head(6)
        if not attack_counts.empty:
            fig3 = go.Figure(go.Bar(
                x=attack_counts.values, y=attack_counts.index, orientation="h",
                marker=dict(
                    color=attack_counts.values,
                    colorscale=[[0, "#00D4FF"], [0.5, "#8B5CF6"], [1, "#FF4444"]],
                    line=dict(width=0)
                )
            ))
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=False),
                margin=dict(l=20, r=20, t=20, b=20), height=280
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No attacks detected yet.")

with chart4:
    st.markdown(section_title("Attack Sources"), unsafe_allow_html=True)
    if "source_country" in df.columns and not df.empty:
        country_counts = df[df["attack_type"] != "Normal"]["source_country"].value_counts().head(6)
        if not country_counts.empty:
            fig4 = go.Figure(go.Bar(
                x=country_counts.index, y=country_counts.values,
                marker=dict(
                    color=country_counts.values,
                    colorscale=[[0, "#FF8C00"], [1, "#FF4444"]]
                )
            ))
            fig4.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                xaxis=dict(showgrid=False, tickangle=-45),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(l=20, r=20, t=20, b=60), height=280
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No external threats detected.")

st.markdown("---")

# Security Score Gauge
st.markdown(section_title("Security Health Score"), unsafe_allow_html=True)

gauge_col1, gauge_col2, gauge_col3 = st.columns([1, 2, 1])

with gauge_col2:
    security_score = max(0, 100 - avg_risk)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=security_score,
        title={'text': "Overall Security", 'font': {'size': 18, 'color': '#FAFAFA'}},
        number={'font': {'size': 48, 'color': '#00D4FF'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "#FAFAFA", 'tickwidth': 2},
            'bar': {'color': "#00D4FF", 'thickness': 0.3},
            'bgcolor': "rgba(26, 31, 46, 0.8)",
            'borderwidth': 2, 'bordercolor': "rgba(255, 255, 255, 0.1)",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.3)'},
                {'range': [40, 70], 'color': 'rgba(255, 140, 0, 0.3)'},
                {'range': [70, 100], 'color': 'rgba(0, 200, 83, 0.3)'}
            ],
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        font={'color': "#FAFAFA", 'family': "Inter"}, 
        height=280
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">AI-Driven Autonomous SOC | Zero Trust Security Platform</p></div>', unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()

# Auto-Refresh Logic (Placed at end to allow full rendering first)
if auto_refresh:
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
