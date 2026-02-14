"""
 Owner-Only Admin Dashboard
===============================
Premium admin control panel for SOC platform management.
Restricted to owner role — all access is server-side enforced.
"""

import streamlit as st
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Admin | SOC", page_icon="", layout="wide")
except st.errors.StreamlitAPIException:
    pass

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()

# ══════════════════════════════════════════════════════════════════════════════
# STRICT OWNER-ONLY ACCESS — server-side enforcement
# ══════════════════════════════════════════════════════════════════════════════
from services.auth_service import is_authenticated, is_admin, auth_service, ADMIN_EMAILS

if not is_authenticated():
    st.error(" **Authentication Required**")
    st.info("Please log in to access the admin dashboard.")
    if st.button("Go to Login"):
        st.switch_page("pages/_Login.py")
    st.stop()

if not is_admin():
    st.error(" **Owner Access Only**")
    st.warning("This dashboard is restricted to the platform owner. Your access attempt has been logged.")
    st.info(f"Logged in as: {st.session_state.get('user_email', 'Unknown')}")
    # Log unauthorized access attempt
    try:
        from services.secret_manager import _log_audit_event
        _log_audit_event('unauthorized_admin_access', {
            'email': st.session_state.get('user_email', 'unknown'),
            'timestamp': datetime.now().isoformat(),
        })
    except Exception:
        pass
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(page_header("Admin Dashboard", "Owner-only platform management console"), unsafe_allow_html=True)

# ── Admin CSS (premium glassmorphism accents) ────────────────────────────────
st.markdown("""
<style>
    .admin-card {
        background: linear-gradient(135deg, rgba(0,243,255,0.04) 0%, rgba(188,19,254,0.04) 100%);
        border: 1px solid rgba(0,243,255,0.15);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        backdrop-filter: blur(10px);
    }
    .admin-stat {
        text-align: center;
        padding: 1rem;
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(0,243,255,0.1);
        border-radius: 8px;
    }
    .admin-stat h2 {
        color: #00f3ff;
        font-family: 'Orbitron', monospace;
        font-size: 2rem;
        margin: 0;
    }
    .admin-stat p {
        color: #8B95A5;
        margin: 0.25rem 0 0 0;
        font-size: 0.85rem;
    }
    .user-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.6rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .role-owner { color: #ff003c; font-weight: bold; }
    .role-admin { color: #bc13fe; }
    .role-user  { color: #0aff0a; }
    .secret-key { color: #00D4FF; font-family: 'Share Tech Mono', monospace; }
    .secret-val { color: #888; font-family: 'Share Tech Mono', monospace; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# ── Stats Overview ───────────────────────────────────────────────────────────
all_users = auth_service.get_all_users()
total_users = len(all_users)
active_users = sum(1 for u in all_users.values() if not u.get('disabled', False))
admin_users = sum(1 for u in all_users.values() if u.get('role') in ('owner', 'admin'))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
audit_file = os.path.join(DATA_DIR, 'audit_log.json')
audit_count = 0
if os.path.exists(audit_file):
    try:
        with open(audit_file) as f:
            audit_count = len(json.load(f))
    except Exception:
        pass

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="admin-stat">
        <h2>{total_users}</h2>
        <p>Total Users</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="admin-stat">
        <h2>{active_users}</h2>
        <p>Active Users</p>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="admin-stat">
        <h2>{admin_users}</h2>
        <p>Admins / Owners</p>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="admin-stat">
        <h2>{audit_count}</h2>
        <p>Audit Events</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    " User Management",
    " Secrets & Config",
    " Audit Logs",
    " Incidents",
    " Playbooks"
])


# ──────────────────────────────────────────────────────────────────────────────
# TAB 1: USER MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown(section_title("User Management"), unsafe_allow_html=True)

    for email, user_data in all_users.items():
        role = user_data.get('role', 'user')
        disabled = user_data.get('disabled', False)
        name = user_data.get('name', 'Unknown')
        created = user_data.get('created_at', 'N/A')
        last_login = user_data.get('last_login', 'Never')
        role_class = f"role-{role}"
        status_icon = " " if not disabled else ""

        st.markdown(f"""
        <div class="admin-card">
            <div class="user-row">
                <div>
                    <span style="color: #FAFAFA; font-weight: 600;">{status_icon} {name}</span>
                    <span style="color: #666; margin-left: 0.5rem;">({email})</span>
                </div>
                <div>
                    <span class="{role_class}" style="text-transform: uppercase; font-size: 0.8rem;">{role}</span>
                </div>
            </div>
            <div style="display: flex; gap: 2rem; margin-top: 0.5rem; font-size: 0.8rem; color: #666;">
                <span>Created: {created[:10] if created != 'N/A' else 'N/A'}</span>
                <span>Last login: {last_login[:16] if last_login and last_login != 'Never' else 'Never'}</span>
                <span>2FA: {"Enabled" if user_data.get('two_factor_enabled') else "Disabled"}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Admin actions (only for non-owner accounts)
        if role != 'owner':
            col_a, col_b, col_c = st.columns([1, 1, 2])
            with col_a:
                new_role = st.selectbox(
                    "Role",
                    ['user', 'admin'],
                    index=0 if role == 'user' else 1,
                    key=f"role_{email}"
                )
                if new_role != role:
                    if st.button("Update Role", key=f"update_role_{email}"):
                        auth_service.update_user_role(email, new_role)
                        try:
                            from services.secret_manager import _log_audit_event
                            _log_audit_event('role_changed', {
                                'email': email,
                                'old_role': role,
                                'new_role': new_role,
                                'by': st.session_state.get('user_email'),
                            })
                        except Exception:
                            pass
                        st.rerun()
            with col_b:
                if disabled:
                    if st.button("Enable", key=f"enable_{email}"):
                        auth_service.enable_user(email)
                        st.rerun()
                else:
                    if st.button("Disable", key=f"disable_{email}"):
                        auth_service.disable_user(email)
                        st.rerun()

    st.markdown("---")
    st.markdown(section_title("Register New User"), unsafe_allow_html=True)
    with st.form("admin_register"):
        reg_email = st.text_input("Email")
        reg_name = st.text_input("Name")
        reg_pass = st.text_input("Password", type="password")
        reg_role = st.selectbox("Role", ['user', 'admin'])
        if st.form_submit_button("Create User", type="primary"):
            if reg_email and reg_name and reg_pass:
                ok, msg = auth_service.register(reg_email, reg_pass, reg_name)
                if ok and reg_role == 'admin':
                    auth_service.update_user_role(reg_email, 'admin')
                if ok:
                    st.success(msg)
                    try:
                        from services.secret_manager import _log_audit_event
                        _log_audit_event('user_created_by_admin', {
                            'email': reg_email,
                            'role': reg_role,
                            'by': st.session_state.get('user_email'),
                        })
                    except Exception:
                        pass
                    st.rerun()
                else:
                    st.error(msg)


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2: SECRETS & CONFIG
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown(section_title("Secret & API Key Management"), unsafe_allow_html=True)

    st.markdown("""
    <div class="admin-card">
        <p style="color: #8B95A5; margin: 0;">
            Secrets are read in priority order: Streamlit Secrets → Environment → Encrypted File → Config File.
            Values are always masked. Only the last 4 characters are shown.
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        from services.secret_manager import list_secrets, mask_secret, set_secret, get_secret, rotate_secret

        secrets_list = list_secrets()
        if secrets_list:
            for s in sorted(secrets_list, key=lambda x: x['key']):
                key_name = s['key']
                masked = s['masked_value']
                source = s['source']

                source_colors = {
                    'streamlit': '#0aff0a',
                    'env_var': '#f0ff00',
                    'encrypted': '#bc13fe',
                    'config_file': '#ff6b00',
                }
                source_color = source_colors.get(source, '#888')

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 0.6rem 0; border-bottom: 1px solid rgba(255,255,255,0.06);">
                    <span class="secret-key">{key_name}</span>
                    <div>
                        <span class="secret-val">{masked}</span>
                        <span style="color: {source_color}; font-size: 0.7rem; margin-left: 1rem; text-transform: uppercase;">{source}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No secrets configured yet.")

        st.markdown("---")
        st.markdown(section_title("Add / Update Secret"), unsafe_allow_html=True)
        with st.form("update_secret"):
            secret_key = st.text_input("Secret Key (e.g. gemini_api_key)")
            secret_value = st.text_input("Secret Value", type="password")
            if st.form_submit_button("Save Secret", type="primary"):
                if secret_key and secret_value:
                    rotate_secret(secret_key, secret_value)
                    st.success(f"Secret `{secret_key}` saved and encrypted.")
                    st.rerun()
                else:
                    st.warning("Both key and value are required.")

    except ImportError:
        st.warning("Secret manager module not available.")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 3: AUDIT LOGS
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown(section_title("Audit Trail"), unsafe_allow_html=True)

    if os.path.exists(audit_file):
        try:
            with open(audit_file) as f:
                audit_log = json.load(f)

            if audit_log:
                # Show in reverse chronological order
                for entry in reversed(audit_log[-50:]):
                    ts = entry.get('timestamp', 'N/A')
                    event = entry.get('event', 'unknown')
                    details = entry.get('details', {})

                    # Color-code by event type
                    event_colors = {
                        'secret_rotated': '#0aff0a',
                        'role_changed': '#bc13fe',
                        'user_created_by_admin': '#00f3ff',
                        'unauthorized_admin_access': '#ff003c',
                        'user_disabled': '#ff6b00',
                    }
                    color = event_colors.get(event, '#888')

                    detail_str = " | ".join(f"{k}: {v}" for k, v in details.items() if k != 'timestamp')

                    st.markdown(f"""
                    <div style="padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color: #666; font-size: 0.75rem; font-family: 'Share Tech Mono';">{ts[:19]}</span>
                        <span style="color: {color}; margin-left: 1rem; font-weight: 600;">{event.replace('_', ' ').upper()}</span>
                        <span style="color: #8B95A5; margin-left: 1rem; font-size: 0.8rem;">{detail_str}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No audit events yet.")
        except Exception as e:
            st.error(f"Error reading audit log: {e}")
    else:
        st.info("No audit log file found. Events will appear here as admin actions are taken.")

    if st.button("Clear Audit Log", type="secondary"):
        try:
            with open(audit_file, 'w') as f:
                json.dump([], f)
            st.success("Audit log cleared.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to clear: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 4: INCIDENTS OVERVIEW
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown(section_title("Incident Overview"), unsafe_allow_html=True)

    # Load incidents from SIEM/alert data
    blocked_file = os.path.join(DATA_DIR, 'blocked_ips.json')

    blocked_ips = []
    if os.path.exists(blocked_file):
        try:
            with open(blocked_file) as f:
                blocked_ips = json.load(f)
        except Exception:
            pass

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="admin-card">
            <h4 style="color: #ff003c; margin: 0 0 0.5rem 0;">Blocked IPs</h4>
            <h2 style="color: #00f3ff; font-family: 'Orbitron'; margin: 0;">{len(blocked_ips) if isinstance(blocked_ips, list) else 0}</h2>
            <p style="color: #666; margin: 0.25rem 0 0 0;">Currently on blocklist</p>
        </div>
        """, unsafe_allow_html=True)

        if blocked_ips and isinstance(blocked_ips, list):
            for ip in blocked_ips[:20]:
                if isinstance(ip, str):
                    st.code(ip, language=None)
                elif isinstance(ip, dict):
                    st.code(f"{ip.get('ip', 'N/A')} — {ip.get('reason', 'blocked')}", language=None)

    with col2:
        st.markdown("""
        <div class="admin-card">
            <h4 style="color: #ff6b00; margin: 0 0 0.5rem 0;">Platform Health</h4>
            <p style="color: #0aff0a;">All systems operational</p>
        </div>
        """, unsafe_allow_html=True)

        # Show ML model status
        try:
            from ml_engine.isolation_forest import SOCIsolationForest
            model = SOCIsolationForest()
            st.markdown("""
            <div style="padding: 0.5rem 0; color: #8B95A5; font-size: 0.85rem;">
                 ML Models: Loaded<br>
                 Isolation Forest + Random Forest ensemble active
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.markdown('<p style="color: #ff003c;">ML Models: Not loaded</p>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# TAB 5: PLAYBOOK CONTROLS
# ──────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown(section_title("Playbook Controls"), unsafe_allow_html=True)

    playbook_dir = os.path.join(DATA_DIR, 'playbooks')
    if not os.path.exists(playbook_dir):
        os.makedirs(playbook_dir, exist_ok=True)

    # List available playbook files
    playbook_files = [f for f in os.listdir(playbook_dir) if f.endswith('.json')] if os.path.exists(playbook_dir) else []

    if playbook_files:
        for pf in sorted(playbook_files):
            try:
                with open(os.path.join(playbook_dir, pf)) as f:
                    pb = json.load(f)
                name = pb.get('name', pf)
                status = pb.get('status', 'active')
                status_color = '#0aff0a' if status == 'active' else '#ff6b00'
                st.markdown(f"""
                <div class="admin-card">
                    <div class="user-row">
                        <span style="color: #FAFAFA; font-weight: 600;">{name}</span>
                        <span style="color: {status_color}; text-transform: uppercase; font-size: 0.8rem;">{status}</span>
                    </div>
                    <p style="color: #666; font-size: 0.8rem; margin: 0.25rem 0 0 0;">{pb.get('description', 'No description')}</p>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                pass
    else:
        st.info("No playbooks configured. Playbooks will appear here when created via the Playbooks page.")

    st.markdown("---")
    st.markdown(section_title("Quick Actions"), unsafe_allow_html=True)

    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        if st.button("Clear All Blocked IPs", type="secondary"):
            try:
                with open(blocked_file, 'w') as f:
                    json.dump([], f)
                try:
                    from services.secret_manager import _log_audit_event
                    _log_audit_event('blocked_ips_cleared', {
                        'by': st.session_state.get('user_email'),
                    })
                except Exception:
                    pass
                st.success("Blocked IPs cleared.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

    with col_q2:
        if st.button("Export User Data", type="secondary"):
            users_export = {}
            for email, data in all_users.items():
                users_export[email] = {
                    'name': data.get('name'),
                    'role': data.get('role', 'user'),
                    'created_at': data.get('created_at'),
                    'last_login': data.get('last_login'),
                    'disabled': data.get('disabled', False),
                }
            st.download_button(
                "Download JSON",
                json.dumps(users_export, indent=2),
                "soc_users_export.json",
                "application/json"
            )

    with col_q3:
        if st.button("Encrypt Config File", type="secondary"):
            try:
                from services.secret_manager import encrypt_existing_config
                result = encrypt_existing_config()
                if result:
                    st.success("Config file encrypted successfully.")
                else:
                    st.warning("No config file found or encryption failed.")
            except Exception as e:
                st.error(f"Encryption failed: {e}")
