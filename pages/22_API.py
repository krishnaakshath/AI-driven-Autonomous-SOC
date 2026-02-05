import streamlit as st
import os
import sys
import json
from datetime import datetime
import hashlib
import hmac

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="API Integration | SOC", page_icon="🔌", layout="wide")

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

st.markdown(page_header("REST API", "External tool integration and programmatic access"), unsafe_allow_html=True)

# Generate API key
if 'api_key' not in st.session_state:
    st.session_state.api_key = hashlib.sha256(os.urandom(32)).hexdigest()[:32]

# API Endpoints documentation
ENDPOINTS = [
    {
        "method": "GET",
        "path": "/api/v1/threats",
        "description": "Get current threat feed",
        "params": "limit, offset, severity",
        "example_response": {"threats": [{"id": "THR-001", "type": "malware", "severity": "high"}]}
    },
    {
        "method": "GET",
        "path": "/api/v1/alerts",
        "description": "Get active alerts",
        "params": "status, from_date, to_date",
        "example_response": {"alerts": [{"id": "ALT-001", "type": "phishing", "status": "active"}]}
    },
    {
        "method": "POST",
        "path": "/api/v1/scan/url",
        "description": "Scan a URL for threats",
        "params": "url (required)",
        "example_response": {"url": "example.com", "risk_score": 85, "threats": ["phishing"]}
    },
    {
        "method": "POST",
        "path": "/api/v1/block/ip",
        "description": "Block an IP address",
        "params": "ip (required), reason, duration",
        "example_response": {"success": True, "ip": "192.168.1.100", "blocked_until": "2024-02-10"}
    },
    {
        "method": "GET",
        "path": "/api/v1/metrics",
        "description": "Get SOC performance metrics",
        "params": "period (day, week, month)",
        "example_response": {"mttr": "2.5h", "mttd": "1.2h", "incidents": 45}
    },
    {
        "method": "POST",
        "path": "/api/v1/incidents",
        "description": "Create a new incident",
        "params": "title, severity, description",
        "example_response": {"id": "INC-2024-0143", "created": "2024-02-05T10:30:00Z"}
    },
    {
        "method": "GET",
        "path": "/api/v1/users/{id}/behavior",
        "description": "Get user behavior analytics",
        "params": "user_id, days",
        "example_response": {"user": "jsmith", "risk_score": 45, "anomalies": 2}
    },
    {
        "method": "POST",
        "path": "/api/v1/webhook/register",
        "description": "Register a webhook for alerts",
        "params": "url, events, secret",
        "example_response": {"webhook_id": "WH-001", "status": "active"}
    }
]

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔑 API Keys", "📖 Endpoints", "🧪 API Tester", "🔗 Webhooks"])

with tab1:
    st.markdown(section_title("API Authentication"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <p style="color: #8B95A5; margin: 0;">
                Use your API key to authenticate all requests. Include it in the header as:
                <code style="background: rgba(0,0,0,0.3); padding: 2px 8px;">Authorization: Bearer YOUR_API_KEY</code>
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Your API Key")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.code(st.session_state.api_key)
    with col2:
        if st.button("🔄 Regenerate", use_container_width=True):
            st.session_state.api_key = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
            st.rerun()
    
    st.warning("⚠️ Keep your API key secure. Never expose it in client-side code.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Rate Limits")
    
    limits = [
        ("Free Tier", "100 requests/hour", "Basic endpoints only"),
        ("Pro Tier", "1,000 requests/hour", "All endpoints"),
        ("Enterprise", "Unlimited", "Priority support + custom endpoints")
    ]
    
    for tier, limit, desc in limits:
        st.markdown(f"""
        <div style="
            background: rgba(26,31,46,0.5);
            border-left: 3px solid #00D4FF;
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
        ">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #00D4FF; font-weight: bold;">{tier}</span>
                <span style="color: #FAFAFA;">{limit}</span>
            </div>
            <div style="color: #8B95A5; font-size: 0.85rem; margin-top: 5px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown(section_title("API Endpoints"), unsafe_allow_html=True)
    
    method_colors = {"GET": "#00C853", "POST": "#FF8C00", "PUT": "#00D4FF", "DELETE": "#FF4444"}
    
    for endpoint in ENDPOINTS:
        color = method_colors.get(endpoint["method"], "#8B95A5")
        
        with st.expander(f"**{endpoint['method']}** {endpoint['path']}", expanded=False):
            st.markdown(f"**Description:** {endpoint['description']}")
            st.markdown(f"**Parameters:** {endpoint['params']}")
            
            st.markdown("**Example Request:**")
            if endpoint["method"] == "GET":
                st.code(f"curl -X GET 'https://api.soc-dashboard.com{endpoint['path']}' \\\n  -H 'Authorization: Bearer YOUR_API_KEY'", language="bash")
            else:
                st.code(f"curl -X POST 'https://api.soc-dashboard.com{endpoint['path']}' \\\n  -H 'Authorization: Bearer YOUR_API_KEY' \\\n  -H 'Content-Type: application/json' \\\n  -d '{{\"param\": \"value\"}}'", language="bash")
            
            st.markdown("**Example Response:**")
            st.json(endpoint["example_response"])

with tab3:
    st.markdown(section_title("API Tester"), unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])
    with col2:
        endpoint = st.text_input("Endpoint", value="/api/v1/threats")
    
    if method in ["POST", "PUT"]:
        body = st.text_area("Request Body (JSON)", value='{\n  "key": "value"\n}', height=150)
    
    headers = st.text_area("Custom Headers (JSON)", value='{\n  "Authorization": "Bearer ' + st.session_state.api_key[:10] + '..."\n}', height=100)
    
    if st.button("🚀 Send Request", type="primary"):
        st.markdown("### Response")
        
        # Simulate API response
        import time
        with st.spinner("Sending request..."):
            time.sleep(1)
        
        response = {
            "status": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Request-ID": hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16],
                "X-RateLimit-Remaining": 95
            },
            "body": ENDPOINTS[0]["example_response"] if "threats" in endpoint else {"success": True}
        }
        
        col1, col2 = st.columns([1, 4])
        with col1:
            st.success(f"**{response['status']}** OK")
        with col2:
            st.caption(f"Request ID: {response['headers']['X-Request-ID']}")
        
        st.json(response["body"])

with tab4:
    st.markdown(section_title("Webhooks"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <p style="color: #8B95A5; margin: 0;">
                Configure webhooks to receive real-time notifications when security events occur.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Webhook registration form
    webhook_url = st.text_input("Webhook URL", placeholder="https://your-app.com/webhook")
    
    events = st.multiselect("Events to Subscribe", [
        "alert.created",
        "alert.resolved",
        "threat.detected",
        "incident.created",
        "incident.updated",
        "user.anomaly",
        "ip.blocked"
    ], default=["alert.created", "threat.detected"])
    
    secret = st.text_input("Webhook Secret", value=hashlib.sha256(b"secret").hexdigest()[:20], type="password")
    
    if st.button("📌 Register Webhook", type="primary"):
        if webhook_url:
            st.success(f"✅ Webhook registered: {webhook_url}")
            st.info("We'll send a test ping to verify the endpoint.")
        else:
            st.warning("Please enter a webhook URL")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Webhook Payload Example")
    st.json({
        "event": "alert.created",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "id": "ALT-1027",
            "type": "phishing",
            "severity": "high",
            "source_ip": "192.168.1.100"
        },
        "signature": "sha256=abc123..."
    })

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | REST API</p></div>', unsafe_allow_html=True)
