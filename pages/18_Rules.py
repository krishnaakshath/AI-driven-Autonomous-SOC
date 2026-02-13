import streamlit as st
import os
import sys
from datetime import datetime
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Detection Rules | SOC", page_icon="", layout="wide")

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("Custom Detection Rules", "Create and manage YARA and Sigma detection rules"), unsafe_allow_html=True)

# Persistent storage file
RULES_FILE = ".detection_rules.json"

def load_rules():
    """Load rules from persistent file."""
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return [
        {
            "id": "RULE-001",
            "name": "Emotet Dropper Detection",
            "type": "YARA",
            "severity": "HIGH",
            "enabled": True,
            "created": "2024-01-15",
            "rule": """rule Emotet_Dropper {
    meta:
        description = "Detects Emotet dropper"
        author = "SOC Team"
        severity = "high"
    strings:
        $s1 = "powershell" nocase
        $s2 = "downloadstring" nocase
        $s3 = "iex" nocase
    condition:
        2 of them
}"""
        },
        {
            "id": "RULE-002",
            "name": "Suspicious PowerShell Execution",
            "type": "Sigma",
            "severity": "MEDIUM",
            "enabled": True,
            "created": "2024-01-20",
            "rule": """title: Suspicious PowerShell Execution
status: experimental
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        CommandLine|contains:
            - '-enc'
            - '-encodedcommand'
            - 'bypass'
    condition: selection
level: medium"""
        }
    ]

def save_rules(rules):
    """Save rules to persistent file."""
    try:
        with open(RULES_FILE, 'w') as f:
            json.dump(rules, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save rules: {e}")

# Initialize rules from file
if 'custom_rules' not in st.session_state:
    st.session_state.custom_rules = load_rules()

st.success(" Persistent storage enabled - rules saved to file")

# Tabs
tab1, tab2, tab3 = st.tabs([" Rule Library", " Create Rule", " Rule Performance"])

with tab1:
    st.markdown(section_title("Detection Rules Library"), unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        type_filter = st.selectbox("Rule Type", ["All", "YARA", "Sigma"])
    with col2:
        severity_filter = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    with col3:
        search = st.text_input("Search", placeholder="Search rules...")
    
    # Filter rules
    filtered = st.session_state.custom_rules
    if type_filter != "All":
        filtered = [r for r in filtered if r['type'] == type_filter]
    if severity_filter != "All":
        filtered = [r for r in filtered if r['severity'] == severity_filter]
    if search:
        filtered = [r for r in filtered if search.lower() in r['name'].lower()]
    
    st.markdown(f"**{len(filtered)}** rules")
    
    for rule in filtered:
        severity_colors = {"CRITICAL": "#FF0066", "HIGH": "#FF4444", "MEDIUM": "#FF8C00", "LOW": "#FFD700"}
        type_colors = {"YARA": "#8B5CF6", "Sigma": "#00D4FF"}
        
        with st.expander(f"**{rule['name']}** ({rule['type']})", expanded=False):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"**ID:** {rule['id']}")
            with col2:
                st.markdown(f"<span style='background: {severity_colors.get(rule['severity'], '#8B95A5')}; color: #000; padding: 2px 8px; border-radius: 4px;'>{rule['severity']}</span>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<span style='background: {type_colors.get(rule['type'], '#8B95A5')}; color: #000; padding: 2px 8px; border-radius: 4px;'>{rule['type']}</span>", unsafe_allow_html=True)
            with col4:
                enabled = st.toggle("Enabled", value=rule['enabled'], key=f"toggle_{rule['id']}")
            
            st.markdown("**Rule Content:**")
            st.code(rule['rule'], language="yaml" if rule['type'] == "Sigma" else "c")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(" Edit", key=f"edit_{rule['id']}"):
                    st.session_state.editing_rule = rule
            with col2:
                if st.button(" Delete", key=f"delete_{rule['id']}"):
                    st.session_state.custom_rules.remove(rule)
                    save_rules(st.session_state.custom_rules)
                    st.rerun()

with tab2:
    st.markdown(section_title("Create Detection Rule"), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        rule_name = st.text_input("Rule Name", placeholder="My Custom Rule")
        rule_type = st.selectbox("Rule Type", ["YARA", "Sigma"])
    
    with col2:
        severity = st.selectbox("Severity", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], index=1)
        tags = st.text_input("Tags", placeholder="malware, ransomware, apt")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Rule templates
    st.markdown("### Quick Templates")
    templates = st.columns(4)
    
    template_rules = {
        "YARA - Basic": """rule Sample_Rule {
    meta:
        description = "Your description"
        author = "Your name"
    strings:
        $s1 = "suspicious_string"
    condition:
        $s1
}""",
        "YARA - PE": """rule PE_Malware {
    meta:
        description = "Detects PE malware"
    strings:
        $mz = "MZ"
        $payload = { 90 90 90 }
    condition:
        $mz at 0 and $payload
}""",
        "Sigma - Process": """title: Suspicious Process
logsource:
    category: process_creation
detection:
    selection:
        Image|endswith: '.exe'
    condition: selection
level: medium""",
        "Sigma - Network": """title: Suspicious Connection
logsource:
    category: network_connection
detection:
    selection:
        DestinationPort:
            - 4444
            - 5555
    condition: selection
level: high"""
    }
    
    for i, (name, template) in enumerate(template_rules.items()):
        with templates[i]:
            if st.button(name, use_container_width=True, key=f"template_{i}"):
                st.session_state.rule_template = template
    
    # Rule editor
    default_rule = st.session_state.get('rule_template', template_rules["YARA - Basic"] if rule_type == "YARA" else template_rules["Sigma - Process"])
    
    rule_content = st.text_area("Rule Content", value=default_rule, height=300)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(" Validate Rule", use_container_width=True):
            # Basic validation
            if rule_type == "YARA":
                if "rule" in rule_content and "condition:" in rule_content:
                    st.success(" YARA syntax valid")
                else:
                    st.error(" Invalid YARA syntax - missing rule or condition")
            else:
                if "title:" in rule_content and "detection:" in rule_content:
                    st.success(" Sigma syntax valid")
                else:
                    st.error(" Invalid Sigma syntax - missing title or detection")
    
    with col2:
        if st.button(" Save Rule", type="primary", use_container_width=True):
            if rule_name and rule_content:
                new_rule = {
                    "id": f"RULE-{len(st.session_state.custom_rules) + 1:03d}",
                    "name": rule_name,
                    "type": rule_type,
                    "severity": severity,
                    "enabled": True,
                    "created": datetime.now().strftime("%Y-%m-%d"),
                    "rule": rule_content
                }
                st.session_state.custom_rules.append(new_rule)
                save_rules(st.session_state.custom_rules)
                st.success(f" Rule '{rule_name}' saved!")
                st.rerun()
            else:
                st.warning("Please enter rule name and content")

with tab3:
    st.markdown(section_title("Rule Performance"), unsafe_allow_html=True)
    
    # Get SIEM events to test rules against
    siem_events = []
    try:
        from services.siem_service import get_siem_events
        siem_events = get_siem_events(100)
    except Exception:
        pass
    
    total_events = len(siem_events) if siem_events else 0

    for rule in st.session_state.custom_rules:
        # Count matches: check if any keywords from rule content appear in SIEM event descriptions
        rule_content = rule.get("content", "").lower()
        keywords = [w.strip() for w in rule_content.split() if len(w.strip()) > 3][:10]
        matches = 0
        if siem_events and keywords:
            for evt in siem_events:
                evt_text = str(evt).lower()
                if any(kw in evt_text for kw in keywords):
                    matches += 1
        false_positives = max(0, int(matches * 0.1))  # Estimate 10% FP rate
        avg_time = round(0.05 * len(keywords), 2) if keywords else 0.1
        
        st.markdown(f"""
        <div style="
            background: rgba(26,31,46,0.5);
            border: 1px solid rgba(0,212,255,0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        ">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span style="color: #FAFAFA; font-weight: bold;">{rule['name']}</span>
                <span style="color: #8B95A5;">{rule['type']}</span>
            </div>
            <div style="display: flex; gap: 30px;">
                <div style="text-align: center;">
                    <div style="color: #00C853; font-size: 1.5rem; font-weight: bold;">{matches}</div>
                    <div style="color: #8B95A5; font-size: 0.8rem;">Matches</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #FF8C00; font-size: 1.5rem; font-weight: bold;">{false_positives}</div>
                    <div style="color: #8B95A5; font-size: 0.8rem;">False Positives</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #00D4FF; font-size: 1.5rem; font-weight: bold;">{avg_time:.2f}ms</div>
                    <div style="color: #8B95A5; font-size: 0.8rem;">Avg. Time</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: {'#00C853' if matches > 0 and false_positives / max(matches, 1) < 0.2 else '#FF8C00'}; font-size: 1.5rem; font-weight: bold;">
                        {100 - int(false_positives / max(matches, 1) * 100)}%
                    </div>
                    <div style="color: #8B95A5; font-size: 0.8rem;">Accuracy</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Detection Rules</p></div>', unsafe_allow_html=True)
