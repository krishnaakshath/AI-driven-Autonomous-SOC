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
        "Account": [
            st.Page("pages/_Login.py", title="Login"),
            st.Page("pages/_Register.py", title="Register"),
        ],
    }, position="sidebar")

else:
    # ── Authenticated User Streamlined Hero Workflow ──
    workspace_pages = [
        st.Page("pages/01_Dashboard.py", title="SOC Dashboard", default=True),
        st.Page("pages/02_Alert_Triage.py", title="Alert Triage"),
        st.Page("pages/03_Investigation.py", title="Forensic Investigation"),
        st.Page("pages/04_SOAR_Response.py", title="SOAR Response"),
        st.Page("pages/05_Executive_Report.py", title="Executive Report"),
    ]
    config_pages = [
        st.Page("pages/06_Settings.py", title="Platform Settings"),
    ]
    pg = st.navigation({
        "Core Workflow": workspace_pages,
        "Configuration": config_pages,
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
