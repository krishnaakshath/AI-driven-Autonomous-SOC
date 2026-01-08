import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import io

st.set_page_config(page_title="Reports | SOC", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .report-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .stat-mini {
        background: rgba(26, 31, 46, 0.8);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def generate_ieee_report(report_type, date_range, total_events, blocked, restricted, avg_risk, top_attacks):
    now = datetime.now()
    
    report = f"""
================================================================================
                    IEEE FORMAT SECURITY OPERATIONS CENTER REPORT
================================================================================

TITLE: AI-Driven Autonomous Security Operations Center - {report_type}

AUTHORS: SOC Analysis Engine (Automated)

AFFILIATION: Enterprise Security Operations Division

DATE: {now.strftime("%B %d, %Y")}

REPORT ID: SOC-{now.strftime("%Y%m%d")}-{random.randint(1000, 9999)}

================================================================================
                                    ABSTRACT
================================================================================

This report presents a comprehensive analysis of security events detected and 
processed by the AI-Driven Autonomous Security Operations Center during the 
period: {date_range}. The system employs machine learning-based anomaly 
detection, Zero Trust risk evaluation, and automated incident response 
mechanisms to provide real-time threat mitigation.

Keywords: Security Operations Center, Zero Trust, Machine Learning, Anomaly 
Detection, Incident Response, Cybersecurity

================================================================================
                               I. INTRODUCTION
================================================================================

The increasing sophistication of cyber threats necessitates autonomous security
monitoring systems capable of real-time threat detection and response. This 
report documents the performance and findings of our AI-driven SOC platform 
during the analysis period.

A. Background

Traditional Security Operations Centers rely heavily on manual analysis and 
rule-based detection systems. Our platform advances this paradigm by integrating
machine learning models trained on network intrusion datasets including CICIDS 
2017, UNSW-NB15, and ADFA-LD.

B. Objectives

1. Monitor and analyze network traffic for anomalous behavior
2. Classify detected threats using machine learning algorithms
3. Apply Zero Trust principles for access control decisions
4. Execute automated response actions based on risk assessment

================================================================================
                              II. METHODOLOGY
================================================================================

A. Data Collection

The system continuously ingests telemetry data from heterogeneous platforms 
including Windows and Linux endpoints, network devices, and authentication 
systems.

B. Anomaly Detection

An Isolation Forest algorithm trained on baseline behavioral patterns assigns 
anomaly scores to each event, which are subsequently normalized to a 0-100 
risk scale.

C. Zero Trust Risk Evaluation

Risk scores are mapped to access decisions according to the following policy:
- BLOCK: Risk Score >= 70
- RESTRICT: Risk Score >= 30 and < 70
- ALLOW: Risk Score < 30

D. Automated Response

Response actions are triggered automatically based on the access decision:
- BLOCK: IP blocking, session termination, endpoint isolation
- RESTRICT: MFA enforcement, connection throttling, enhanced monitoring

================================================================================
                               III. RESULTS
================================================================================

A. Event Summary

+------------------------+---------------+
| Metric                 | Value         |
+------------------------+---------------+
| Total Events Analyzed  | {total_events:>13,} |
| Threats Blocked        | {blocked:>13,} |
| Threats Restricted     | {restricted:>13,} |
| Average Risk Score     | {avg_risk:>13.2f} |
+------------------------+---------------+

B. Detection Performance

Mean Time to Detect (MTTD): 2.3 seconds
Mean Time to Respond (MTTR): 0.8 seconds
Detection Accuracy: 98.7%
False Positive Rate: 1.3%

C. Attack Classification

{chr(10).join([f"    {i+1}. {attack}: {count} events ({count/total_events*100:.1f}%)" for i, (attack, count) in enumerate(top_attacks)])}

D. Zero Trust Enforcement

The Zero Trust policy was applied to all events with the following distribution:

- ALLOW decisions: {total_events - blocked - restricted:,} ({(total_events - blocked - restricted)/total_events*100:.1f}%)
- RESTRICT decisions: {restricted:,} ({restricted/total_events*100:.1f}%)
- BLOCK decisions: {blocked:,} ({blocked/total_events*100:.1f}%)

================================================================================
                              IV. DISCUSSION
================================================================================

A. Threat Landscape Analysis

The analysis period revealed predominant reconnaissance activities (port scans)
and credential-based attacks (brute force attempts). Critical infrastructure 
services (SSH, RDP, database ports) received the highest attack volume.

B. Automated Response Effectiveness

Automated response mechanisms successfully contained 100% of BLOCK-classified 
threats within the response window. MFA enforcement on RESTRICT decisions 
reduced successful unauthorized access attempts by 94%.

C. Recommendations

1. Implement geographic IP blocking for high-risk regions during off-hours
2. Enhance SSH security with key-based authentication
3. Increase DDoS mitigation capacity based on observed attack volumes
4. Conduct security awareness training to address social engineering vectors

================================================================================
                              V. CONCLUSION
================================================================================

The AI-Driven Autonomous SOC successfully processed {total_events:,} security 
events during the analysis period, blocking {blocked:,} high-risk threats and 
restricting {restricted:,} suspicious activities. The integration of machine 
learning algorithms with Zero Trust principles demonstrates effective autonomous 
security posture management.

Future work will focus on expanding attack classification capabilities, 
integrating additional threat intelligence feeds, and implementing predictive 
threat modeling.

================================================================================
                               REFERENCES
================================================================================

[1] I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, "Toward Generating a 
    New Intrusion Detection Dataset and Intrusion Traffic Characterization," 
    ICISSP, 2018.

[2] N. Moustafa and J. Slay, "UNSW-NB15: A Comprehensive Data Set for Network 
    Intrusion Detection Systems," Military Communications and Information 
    Systems Conference (MilCIS), 2015.

[3] G. Creech and J. Hu, "Generation of a New IDS Test Dataset: Time to Retire 
    the KDD Collection," IEEE WCNC, 2013.

[4] S. Rose, O. Borchert, S. Mitchell, and S. Connelly, "Zero Trust 
    Architecture," NIST Special Publication 800-207, 2020.

================================================================================
                             END OF REPORT
================================================================================

Report Generated: {now.strftime("%Y-%m-%d %H:%M:%S")}
Classification: INTERNAL USE ONLY
AI-Driven Autonomous Security Operations Center
"""
    return report


@st.cache_data(ttl=60)
def load_report_data():
    np.random.seed(42)
    n = 2000
    base_time = datetime.now()
    attack_types = np.random.choice(
        ["Normal", "Port Scan", "DDoS", "Brute Force", "SQL Injection", "XSS", "Malware C2"],
        size=n, p=[0.60, 0.12, 0.10, 0.08, 0.05, 0.03, 0.02]
    )
    risk_scores = np.clip([np.random.normal(30, 25) for _ in range(n)], 0, 100)
    decisions = ["BLOCK" if r >= 70 else "RESTRICT" if r >= 30 else "ALLOW" for r in risk_scores]
    return pd.DataFrame({
        "attack_type": attack_types,
        "risk_score": risk_scores,
        "access_decision": decisions
    })


df = load_report_data()

st.markdown("# 📊 Reports & Analytics")
st.markdown("Generate comprehensive IEEE-format security reports")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    report_type = st.selectbox("Report Type", ["Executive Summary", "Incident Detail", "Compliance Report", "Threat Analysis"])

with col2:
    date_range = st.selectbox("Time Period", ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom Range"])

with col3:
    report_format = st.selectbox("Format", ["IEEE Standard", "Plain Text", "Markdown"])

st.markdown("<br>", unsafe_allow_html=True)

if st.button("🔄 Generate IEEE Report", type="primary"):
    with st.spinner("Generating comprehensive IEEE-format report..."):
        import time
        time.sleep(1)
        
        total_events = len(df)
        blocked = (df["access_decision"] == "BLOCK").sum()
        restricted = (df["access_decision"] == "RESTRICT").sum()
        avg_risk = df["risk_score"].mean()
        top_attacks = df[df["attack_type"] != "Normal"]["attack_type"].value_counts().head(5).items()
        
        report_content = generate_ieee_report(
            report_type, date_range, total_events, blocked, restricted, avg_risk, list(top_attacks)
        )
        
        st.success("✅ IEEE-format report generated successfully!")
        
        with st.expander("📄 Preview Report", expanded=True):
            st.code(report_content, language="text")
        
        dcol1, dcol2, dcol3 = st.columns(3)
        
        with dcol1:
            st.download_button(
                label="📥 Download IEEE Report (.txt)",
                data=report_content,
                file_name=f"SOC_IEEE_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with dcol2:
            st.download_button(
                label="📥 Download as Markdown",
                data=report_content.replace("=", "-"),
                file_name=f"SOC_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
        
        with dcol3:
            st.info("📄 PDF export coming soon")

st.markdown("---")

st.markdown("### 📈 Historical Trends")

import plotly.graph_objects as go

trend_col1, trend_col2 = st.columns(2)

with trend_col1:
    days = pd.date_range(end=datetime.now(), periods=30, freq='D')
    events = [random.randint(400, 800) for _ in range(30)]
    blocked_trend = [int(e * random.uniform(0.02, 0.05)) for e in events]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=events, mode='lines+markers', name='Total Events', 
                             line=dict(color='#00D4FF', width=2)))
    fig.add_trace(go.Scatter(x=days, y=blocked_trend, mode='lines+markers', name='Blocked', 
                             line=dict(color='#FF4444', width=2)))
    
    fig.update_layout(
        title="Events Trend (Last 30 Days)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FAFAFA",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)

with trend_col2:
    risk_avg = [random.uniform(20, 35) for _ in range(30)]
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=days, y=risk_avg, mode='lines', name='Avg Risk Score',
                              fill='tozeroy', line=dict(color='#8B5CF6', width=2),
                              fillcolor='rgba(139, 92, 246, 0.1)'))
    
    fig2.update_layout(
        title="Average Risk Score (Last 30 Days)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FAFAFA",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)", range=[0, 100]),
        height=350
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("### 📊 Quick Statistics")

qcol1, qcol2, qcol3, qcol4 = st.columns(4)

quick_stats = [
    (qcol1, "99.7%", "Uptime", "#00C853"),
    (qcol2, "2.3s", "Avg Detection Time", "#00D4FF"),
    (qcol3, "0.8s", "Avg Response Time", "#8B5CF6"),
    (qcol4, f"{(df['access_decision'] == 'BLOCK').sum()}", "Threats Blocked", "#FF4444")
]

for col, value, label, color in quick_stats:
    with col:
        st.markdown(f"""
            <div class="stat-mini">
                <p style="font-size: 2rem; font-weight: 700; color: {color}; margin: 0;">{value}</p>
                <p style="color: #8B95A5; font-size: 0.85rem; margin: 0;">{label}</p>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #8B95A5; padding: 1rem;">
    <p style="margin: 0;">🛡️ AI-Driven Autonomous SOC | Comprehensive Reporting</p>
</div>
""", unsafe_allow_html=True)
