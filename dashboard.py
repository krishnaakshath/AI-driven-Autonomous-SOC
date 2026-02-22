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

st.set_page_config(page_title="SOC Platform", page_icon="S", layout="wide")

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE STARTUP (Background Threads)
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def start_active_services():
    """Start background services for Log Ingestion and Live Monitoring."""
    try:
        from services.log_ingestor import log_ingestor
        from services.background_monitor import background_monitor
        from services.siem_service import get_siem_events
        
        # Ensure DB is seeded with historical data immediately on startup
        get_siem_events(count=1)
        
        # Start Log Ingestor (Reads logs -> DB)
        log_ingestor.start_background_thread()
        
        # Start Background Monitor (Generates logs/Simulates Traffic)
        background_monitor.start()
        
        return True
    except Exception as e:
        print(f"Failed to start services: {e}")
        return False

# Initialize services once
start_active_services()

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION PERSISTENCE — Restore login from token file on every load
# ═══════════════════════════════════════════════════════════════════════════════
from services.auth_service import is_authenticated, is_admin, check_persistent_session

# Attempt to restore session from saved token
check_persistent_session()

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

elif user_is_admin:
    # ── Admin: full access to all pages ──
    pg = st.navigation({
        "Dashboards": [
            st.Page("pages/01_Dashboard.py", title="Dashboard", default=True),
            st.Page("pages/02_Executive.py", title="Executive"),
        ],
        "Monitoring": [
            st.Page("pages/03_Alerts.py", title="Alerts"),
            st.Page("pages/04_Logs.py", title="Logs"),
            st.Page("pages/05_Timeline.py", title="Timeline"),
            st.Page("pages/24_SIEM.py", title="SIEM"),
        ],
        "Threat Intelligence": [
            st.Page("pages/06_Threat_Intel.py", title="Threat Intel"),
            st.Page("pages/07_Geo_Predictions.py", title="Geo Predictions"),
            st.Page("pages/08_Kill_Chain.py", title="Kill Chain"),
            st.Page("pages/09_Dark_Web.py", title="Dark Web"),
            st.Page("pages/10_Threat_Hunt.py", title="Threat Hunt"),
        ],
        "Investigation": [
            st.Page("pages/11_Analysis.py", title="Analysis"),
            st.Page("pages/12_UBA.py", title="UBA"),
            st.Page("pages/13_Forensics.py", title="Forensics"),
            st.Page("pages/14_Sandbox.py", title="Sandbox"),
        ],
        "Operations": [
            st.Page("pages/15_Scanners.py", title="Scanners"),
            st.Page("pages/16_Security_Testing.py", title="Security Testing"),
            st.Page("pages/17_IP_Block.py", title="IP Block"),
            st.Page("pages/18_Rules.py", title="Rules"),
            st.Page("pages/19_Reports.py", title="Reports"),
            st.Page("pages/20_Playbooks.py", title="Playbooks"),
        ],
        "AI & Config": [
            st.Page("pages/21_CORTEX.py", title="CORTEX AI"),
            st.Page("pages/23_Settings.py", title="Settings"),
            st.Page("pages/25_Admin.py", title="Admin"),
        ],
    }, position="sidebar")

else:
    # ── Regular user: clean, limited sidebar ──
    pg = st.navigation({
        "Dashboards": [
            st.Page("pages/01_Dashboard.py", title="Dashboard", default=True),
            st.Page("pages/02_Executive.py", title="Executive"),
        ],
        "Monitoring": [
            st.Page("pages/03_Alerts.py", title="Alerts"),
            st.Page("pages/04_Logs.py", title="Logs"),
            st.Page("pages/05_Timeline.py", title="Timeline"),
        ],
        "Threat Intelligence": [
            st.Page("pages/06_Threat_Intel.py", title="Threat Intel"),
            st.Page("pages/07_Geo_Predictions.py", title="Geo Predictions"),
            st.Page("pages/10_Threat_Hunt.py", title="Threat Hunt"),
        ],
        "Investigation": [
            st.Page("pages/11_Analysis.py", title="Analysis"),
        ],
        "Tools": [
            st.Page("pages/15_Scanners.py", title="Scanners"),
            st.Page("pages/16_Security_Testing.py", title="Security Testing"),
            st.Page("pages/19_Reports.py", title="Reports"),
        ],
        "AI & Config": [
            st.Page("pages/21_CORTEX.py", title="CORTEX AI"),
            st.Page("pages/23_Settings.py", title="Settings"),
        ],
    }, position="sidebar")

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR LOGOUT BUTTON
# ═══════════════════════════════════════════════════════════════════════════════
if logged_in:
    with st.sidebar:
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
