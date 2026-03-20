import streamlit as st
import os
import sys
import importlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force reload database module to prevent Streamlit caching old versions
try:
    import services.database
    importlib.reload(services.database)
except Exception:
    pass

st.set_page_config(page_title="SOC Platform", page_icon="🛡️", layout="wide")

# Globally enforce the exact aesthetic on the master entrypoint
try:
    import json
    import os
    from services.logger import set_correlation_id
    
    # Bootstrap Observability Pipeline for this execution thread
    set_correlation_id()
    
    CONFIG_FILE = ".soc_config.json"
    if "theme" not in st.session_state:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                cfg = json.load(f)
                st.session_state.theme = cfg.get("theme", "cyberpunk")
        else:
            st.session_state.theme = "cyberpunk"

    from ui.theme import load_css
    load_css()
except Exception:
    pass
# ── ACTIVE FIREWALL (WAF) ──
try:
    from services.firewall_service import firewall
    # Scan session inputs for malicious patterns
    inputs_to_scan = {}
    for key, val in st.query_params.items():
        inputs_to_scan[f"query_{key}"] = val
    
    if not firewall.check_request(inputs_to_scan, source_ip="DYNAMIC_WAF"):
        st.error("⚠️ ACCESS DENIED: Malicious injection detected by Firewall.")
        st.stop()
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE STARTUP (Background Threads)
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def start_active_services():
    """Verify core systems are reachable on startup."""
    try:
        from services.siem_service import get_siem_events
        # Ensure DB is seeded with historical data immediately on startup
        get_siem_events(count=1)
        return True
    except Exception as e:
        print(f"Failed to verify SIEM: {e}")
        return False

# Initialize services once
start_active_services()

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION PERSISTENCE — Restore login from token file on every load
# ═══════════════════════════════════════════════════════════════════════════════
from services.auth_service import is_authenticated, is_admin, check_persistent_session, logout
import time as _time

# Attempt to restore session from saved token
check_persistent_session()

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION TIMEOUT — Auto-logout after 30 minutes of inactivity
# ═══════════════════════════════════════════════════════════════════════════════
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes

if is_authenticated():
    now = _time.time()
    last_activity = st.session_state.get("_last_activity", now)
    
    if now - last_activity > SESSION_TIMEOUT_SECONDS:
        # Session expired
        try:
            logout()
        except Exception:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
        st.toast("Session expired due to inactivity. Please log in again.", icon="🔒")
        st.rerun()
    else:
        st.session_state["_last_activity"] = now

# ═══════════════════════════════════════════════════════════════════════════════
# ROLE-BASED NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════
logged_in = is_authenticated()
user_is_admin = is_admin() if logged_in else False

if not logged_in:
    # ── Not logged in: only show Login & Register ──
    pg = st.navigation({
        "Authentication": [
            st.Page("pages/_Login.py", title="Login", icon=":material/login:"),
            st.Page("pages/_Register.py", title="Register", icon=":material/person_add:"),
        ],
    }, position="sidebar")

elif user_is_admin:
    # ── Admin: full access to all pages ──
    pg = st.navigation({
        "Platform Entrypoint": [
            st.Page("pages/00_User_Guide.py", title="User Guide", icon=":material/menu_book:", default=True),
        ],
        "🚨 CORE WORKFLOW 🚨": [
            st.Page("pages/01_Dashboard.py", title="SOC Dashboard", icon=":material/dashboard:"),
            st.Page("pages/02_Alert_Triage.py", title="Alert Triage", icon=":material/warning:"),
            st.Page("pages/03_Investigation.py", title="Investigation", icon=":material/policy:"),
            st.Page("pages/04_SOAR_Response.py", title="SOAR Response", icon=":material/bolt:"),
            st.Page("pages/05_Executive_Report.py", title="Executive Report", icon=":material/summarize:"),
        ],
        "Dashboards & Monitoring": [
            st.Page("pages/02_Executive.py", title="Executive Overview", icon=":material/trending_up:"),
            st.Page("pages/04_Logs.py", title="Raw Logs", icon=":material/receipt_long:"),
            st.Page("pages/05_Timeline.py", title="Global Timeline", icon=":material/schedule:"),
            st.Page("pages/24_SIEM.py", title="SIEM Console", icon=":material/security:"),
        ],
        "Threat Intelligence": [
            st.Page("pages/06_Threat_Intel.py", title="Threat Intel Feed", icon=":material/bug_report:"),
            st.Page("pages/07_Geo_Predictions.py", title="Geo Predictions", icon=":material/map:"),
            st.Page("pages/08_Kill_Chain.py", title="MITRE Kill Chain", icon=":material/link:"),
            st.Page("pages/09_OSINT_Feeds.py", title="OSINT Sources", icon=":material/satellite:"),
            st.Page("pages/10_Threat_Hunt.py", title="Threat Hunting", icon=":material/radar:"),
        ],
        "Advanced AI Analysis": [
            st.Page("pages/11_Analysis.py", title="ML Insights", icon=":material/psychology:"),
            st.Page("pages/26_RL_Adaptive.py", title="RL Adaptive Defense", icon=":material/smart_toy:"),
            st.Page("pages/27_Federated_Learning.py", title="Federated Learning", icon=":material/hub:"),
        ],
        "Operations & Settings": [
            st.Page("pages/15_Scanners.py", title="Network Scanners", icon=":material/wifi_find:"),
            st.Page("pages/21_CORTEX.py", title="CORTEX Assistant", icon=":material/forum:"),
            st.Page("pages/25_Firewall_Control.py", title="Firewall Control", icon=":material/gitea:"),
            st.Page("pages/06_Settings.py", title="Platform Settings", icon=":material/settings:"),
        ],
    }, position="sidebar")

else:
    # ── Regular user: clean, limited sidebar ──
    pg = st.navigation({
        "Platform Entrypoint": [
            st.Page("pages/00_User_Guide.py", title="User Guide", icon=":material/menu_book:", default=True),
        ],
        "🚨 CORE WORKFLOW 🚨": [
            st.Page("pages/01_Dashboard.py", title="SOC Dashboard", icon=":material/dashboard:"),
            st.Page("pages/02_Alert_Triage.py", title="Alert Triage", icon=":material/warning:"),
            st.Page("pages/03_Investigation.py", title="Investigation", icon=":material/policy:"),
            st.Page("pages/04_SOAR_Response.py", title="SOAR Response", icon=":material/bolt:"),
        ],
        "Additional Context": [
            st.Page("pages/04_Logs.py", title="Raw Logs", icon=":material/receipt_long:"),
            st.Page("pages/10_Threat_Hunt.py", title="Threat Hunting", icon=":material/radar:"),
            st.Page("pages/11_Analysis.py", title="ML Insights", icon=":material/psychology:"),
        ],
    }, position="sidebar")

# SIDEBAR LOGOUT BUTTON
# ═══════════════════════════════════════════════════════════════════════════════
if logged_in:
    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        # ── SYSTEM HEALTH HEARTBEAT ──
        _latency = "N/A"
        try:
            import time as _t
            _start = _t.time()
            from services.database import db, SUPABASE_URL
            # Actually hit the database to verify connectivity
            db.get_stats()
            _latency = f"{int((_t.time() - _start) * 1000)}ms"
            status = "online"
        except Exception:
            status = "offline"
            
        from ui.theme import status_indicator
        st.markdown(status_indicator(status), unsafe_allow_html=True)
        st.markdown(f"<div style='color: #444; font-size: 0.6rem; font-family: monospace; margin-top: -5px;'>LATENCY: {_latency}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("🔒 Logout", use_container_width=True):
            try:
                from services.auth_service import logout
                logout()
            except Exception:
                # Manual fallback: clear session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
            st.rerun()

pg.run()
