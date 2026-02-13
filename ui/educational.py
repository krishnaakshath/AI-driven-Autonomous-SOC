"""
 Educational Components
=========================
Reusable components for explanations, remediation, and learning content.
"""

import streamlit as st

# Educational content database
EXPLANATIONS = {
    # Dashboard Metrics
    "security_score": {
        "title": "Security Score",
        "what": "A composite metric (0-100) representing your overall security posture based on threats detected, vulnerabilities, compliance status, and response times.",
        "why": "Provides a quick at-a-glance health check of your entire security infrastructure.",
        "how_calculated": "Weighted average: (1 - threat_ratio) × 40 + patch_compliance × 30 + response_efficiency × 30",
        "remediation": [
            "Review and prioritize critical alerts",
            "Ensure all systems are patched",
            "Reduce average response time",
            "Address high-severity vulnerabilities first"
        ]
    },
    "active_threats": {
        "title": "Active Threats",
        "what": "Count of currently unresolved security incidents requiring attention.",
        "why": "Indicates immediate workload and potential risk exposure.",
        "how_calculated": "Sum of all alerts with status ≠ 'resolved' and severity ≥ 'medium'",
        "remediation": [
            "Triage threats by severity",
            "Assign SOC analysts to critical incidents",
            "Execute relevant playbooks",
            "Escalate persistent threats"
        ]
    },
    "blocked_ips": {
        "title": "Blocked IPs",
        "what": "Number of IP addresses currently blocked by your firewall/WAF.",
        "why": "Shows active defense measures and potential attack sources.",
        "how_calculated": "Count of entries in firewall blocklist + automated blocks from IDS/IPS",
        "remediation": [
            "Regularly review blocklist for false positives",
            "Correlate with threat intelligence feeds",
            "Consider geo-blocking for high-risk regions",
            "Set up automatic expiration for temporary blocks"
        ]
    },
    
    # ML Insights
    "isolation_forest": {
        "title": "Isolation Forest",
        "what": "An unsupervised machine learning algorithm that detects anomalies by isolating observations through random feature splitting.",
        "why": "Unlike other ML methods, it doesn't require labeled data and excels at finding rare, unusual patterns that may indicate threats.",
        "how_calculated": "Anomaly score = average path length to isolate a sample. Shorter paths = more anomalous.",
        "remediation": [
            "Investigate high anomaly scores (>0.7) immediately",
            "Cross-reference with other detection methods",
            "Tune contamination parameter based on false positive rate",
            "Add confirmed threats to training data"
        ]
    },
    "fuzzy_c_means": {
        "title": "Fuzzy C-Means Clustering",
        "what": "A soft clustering algorithm where each data point belongs to multiple clusters with varying degrees of membership.",
        "why": "Real-world security data often doesn't fit cleanly into categories. Fuzzy clustering captures this uncertainty.",
        "how_calculated": "Iteratively updates cluster centers and membership degrees until convergence.",
        "remediation": [
            "Focus on points with high membership in 'threat' clusters",
            "Investigate points with split membership (uncertainty)",
            "Use cluster insights to create detection rules",
            "Adjust number of clusters based on data structure"
        ]
    },
    "neural_prediction": {
        "title": "Neural Threat Prediction",
        "what": "LSTM-based deep learning model that forecasts future attack probabilities based on historical patterns.",
        "why": "Enables proactive defense by predicting threats before they occur.",
        "how_calculated": "Time-series analysis of attack patterns → probability forecast for next 24h",
        "remediation": [
            "Increase monitoring during high-probability windows",
            "Pre-position defensive resources",
            "Send preemptive alerts to SOC team",
            "Review and reinforce predicted attack vectors"
        ]
    },
    
    # Alerts
    "brute_force": {
        "title": "Brute Force Attack",
        "what": "Repeated login attempts trying different password combinations to gain unauthorized access.",
        "why": "Indicates credential stuffing or password guessing attacks against your systems.",
        "how_calculated": "Detected when >10 failed logins from same IP within 5 minutes.",
        "remediation": [
            "Block the source IP address",
            "Enforce account lockout policies",
            "Enable MFA for targeted accounts",
            "Check if any accounts were compromised",
            "Review password policies"
        ]
    },
    "data_exfiltration": {
        "title": "Data Exfiltration",
        "what": "Unauthorized transfer of data from your network to external destinations.",
        "why": "Could indicate insider threat, compromised credentials, or active breach.",
        "how_calculated": "Anomaly detection on outbound data volume + destination analysis",
        "remediation": [
            "Immediately isolate the source system",
            "Block the destination IP/domain",
            "Preserve logs for forensic analysis",
            "Notify data protection officer",
            "Assess data classification of leaked content"
        ]
    },
    "malware_detected": {
        "title": "Malware Detection",
        "what": "Malicious software identified on a system through signature or behavioral analysis.",
        "why": "Indicates compromise that could spread or cause further damage.",
        "how_calculated": "Signature match + behavioral heuristics + sandbox analysis",
        "remediation": [
            "Quarantine the affected file/system",
            "Run full system scan",
            "Check for lateral movement",
            "Identify infection vector",
            "Update detection signatures",
            "Consider system reimaging"
        ]
    },
    "phishing": {
        "title": "Phishing Attempt",
        "what": "Social engineering attack attempting to steal credentials or deliver malware via deceptive emails/websites.",
        "why": "Primary attack vector for initial access in most breaches.",
        "how_calculated": "Email content analysis + URL reputation + sender verification",
        "remediation": [
            "Block the sender/domain",
            "Remove email from all mailboxes",
            "Alert users who received it",
            "Check if any users clicked links",
            "Reset credentials if compromise suspected",
            "Report to anti-phishing organizations"
        ]
    },
    "ransomware": {
        "title": "Ransomware Activity",
        "what": "Malware that encrypts files and demands payment for decryption keys.",
        "why": "Critical threat that can halt business operations and cause data loss.",
        "how_calculated": "File entropy changes + mass file modifications + ransom note detection",
        "remediation": [
            "IMMEDIATELY isolate affected systems",
            "Do NOT pay the ransom",
            "Activate incident response plan",
            "Preserve evidence for forensics",
            "Restore from known-good backups",
            "Report to law enforcement"
        ]
    },
    
    # Threat Intel
    "ioc": {
        "title": "Indicator of Compromise (IOC)",
        "what": "Artifacts observed on a network or system that indicate potential intrusion (IPs, hashes, domains, etc.).",
        "why": "Enable detection of known threats and correlation across incidents.",
        "how_calculated": "Aggregated from threat feeds, internal detections, and intelligence sharing",
        "remediation": [
            "Cross-reference with your logs and assets",
            "Add to blocklists if malicious",
            "Hunt for historical presence",
            "Share with threat intelligence community"
        ]
    },
    "apt": {
        "title": "Advanced Persistent Threat (APT)",
        "what": "Sophisticated, long-term cyberattack typically by nation-state actors targeting specific organizations.",
        "why": "Indicates a determined adversary with significant resources.",
        "how_calculated": "Pattern matching against known APT TTPs + attribution analysis",
        "remediation": [
            "Engage incident response team",
            "Conduct thorough threat hunting",
            "Check for persistence mechanisms",
            "Review privileged account activity",
            "Consider engaging external forensics",
            "Notify relevant authorities"
        ]
    },
    
    # Sandbox
    "sandbox_analysis": {
        "title": "Sandbox Analysis",
        "what": "Executing suspicious files/URLs in an isolated environment to observe behavior without risking production systems.",
        "why": "Reveals true malicious behavior that static analysis might miss.",
        "how_calculated": "Dynamic execution monitoring: processes, files, network, registry",
        "remediation": [
            "Block identified IOCs (IPs, domains, hashes)",
            "Hunt for similar files in environment",
            "Update detection signatures",
            "Share findings with threat intel team"
        ]
    }
}


def render_explanation(key: str, collapsed: bool = True):
    """
    Render an educational dropdown for a given topic.
    
    Args:
        key: The key for the explanation in EXPLANATIONS dict
        collapsed: Whether the expander should be collapsed by default
    """
    if key not in EXPLANATIONS:
        return
    
    info = EXPLANATIONS[key]
    
    with st.expander(f" **Learn: {info['title']}**", expanded=not collapsed):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**What is it?**")
            st.markdown(f"<p style='color: #a8b2c1; font-size: 0.9rem;'>{info['what']}</p>", unsafe_allow_html=True)
            
            st.markdown("**Why it matters:**")
            st.markdown(f"<p style='color: #a8b2c1; font-size: 0.9rem;'>{info['why']}</p>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("**How it's calculated:**")
            st.markdown(f"<p style='color: #a8b2c1; font-size: 0.9rem;'>{info['how_calculated']}</p>", unsafe_allow_html=True)
            
            st.markdown("** Remediation Steps:**")
            for i, step in enumerate(info['remediation'], 1):
                st.markdown(f"<p style='color: #00D4FF; font-size: 0.85rem; margin: 3px 0;'>{i}. {step}</p>", unsafe_allow_html=True)


def render_alert_explanation(alert_type: str):
    """Render explanation for a specific alert type."""
    type_mapping = {
        "brute_force": "brute_force",
        "data_exfiltration": "data_exfiltration",
        "malware": "malware_detected",
        "phishing": "phishing",
        "ransomware": "ransomware",
        "apt": "apt"
    }
    
    key = type_mapping.get(alert_type.lower().replace(" ", "_"))
    if key:
        render_explanation(key)


def render_quick_tip(tip_text: str, tip_type: str = "info"):
    """Render a quick tip banner."""
    colors = {
        "info": ("#00D4FF", "rgba(0,212,255,0.1)"),
        "warning": ("#FF8C00", "rgba(255,140,0,0.1)"),
        "danger": ("#FF4444", "rgba(255,68,68,0.1)"),
        "success": ("#00FF88", "rgba(0,255,136,0.1)")
    }
    
    border_color, bg_color = colors.get(tip_type, colors["info"])
    
    st.markdown(f"""
    <div style="
        background: {bg_color};
        border-left: 4px solid {border_color};
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 10px 0;
    ">
        <div style="color: {border_color}; font-weight: 600; font-size: 0.85rem;"> Tip</div>
        <div style="color: #a8b2c1; font-size: 0.9rem; margin-top: 5px;">{tip_text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_with_explanation(
    label: str,
    value: str,
    delta: str = None,
    explanation_key: str = None
):
    """Render a metric with an optional expandable explanation."""
    st.metric(label, value, delta)
    if explanation_key:
        render_explanation(explanation_key, collapsed=True)
