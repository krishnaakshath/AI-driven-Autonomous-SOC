import streamlit as st
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Admin Panel | SOC", page_icon="👑", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .admin-card {
        background: rgba(26, 31, 46, 0.8);
        border: 1px solid rgba(255, 68, 68, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .user-row {
        background: rgba(26, 31, 46, 0.5);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .role-admin { color: #FF4444; }
    .role-analyst { color: #00D4FF; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

from auth.auth_manager import check_auth, show_user_info, load_users, save_users, hash_password

user = check_auth()
if not user:
    st.switch_page("pages/0_🔐_Login.py")
    st.stop()

if user.get('role') != 'admin':
    st.error("⛔ Access Denied - Admin privileges required")
    st.info("Only administrators can access this page.")
    st.stop()

show_user_info(user)

st.markdown("# 👑 Admin Panel")
st.markdown("Manage users, roles, and system settings")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["👥 User Management", "⚙️ System Config", "📊 Activity Logs"])

with tab1:
    st.markdown("### 👥 Registered Users")
    
    data = load_users()
    users = data.get("users", {})
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    for email, user_data in users.items():
        role_class = "role-admin" if user_data.get('role') == 'admin' else "role-analyst"
        role_icon = "👑" if user_data.get('role') == 'admin' else "👤"
        
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{role_icon} {user_data.get('name', 'Unknown')}**")
            st.caption(email)
        
        with col2:
            st.markdown(f"<span class='{role_class}'>{user_data.get('role', 'analyst').upper()}</span>", unsafe_allow_html=True)
        
        with col3:
            new_role = st.selectbox(
                "Role",
                ["analyst", "admin"],
                index=1 if user_data.get('role') == 'admin' else 0,
                key=f"role_{email}",
                label_visibility="collapsed"
            )
            if new_role != user_data.get('role'):
                if st.button("Save", key=f"save_{email}"):
                    data["users"][email]["role"] = new_role
                    save_users(data)
                    st.success(f"Updated {email} to {new_role}")
                    st.rerun()
        
        with col4:
            if email != user['email']:
                if st.button("🗑️", key=f"del_{email}"):
                    del data["users"][email]
                    save_users(data)
                    st.success(f"Deleted {email}")
                    st.rerun()
        
        st.markdown("---")
    
    st.markdown("### ➕ Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Name")
            new_email = st.text_input("Email")
        with col2:
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["analyst", "admin"])
        
        if st.form_submit_button("➕ Create User", type="primary"):
            if new_name and new_email and new_password:
                if new_email.lower() not in users:
                    data["users"][new_email.lower()] = {
                        "password": hash_password(new_password),
                        "name": new_name,
                        "role": new_role,
                        "created": datetime.now().isoformat(),
                        "last_login": None
                    }
                    save_users(data)
                    st.success(f"✅ Created user: {new_email}")
                    st.rerun()
                else:
                    st.error("Email already exists")
            else:
                st.warning("Please fill all fields")

with tab2:
    st.markdown("### ⚙️ System Configuration")
    
    config_file = ".soc_config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    st.markdown("#### 🔔 Alert Settings")
    col1, col2 = st.columns(2)
    with col1:
        alert_threshold = st.slider("Alert Threshold (Risk Score)", 0, 100, config.get('alert_threshold', 70))
        auto_block = st.checkbox("Auto-block high risk IPs", value=config.get('auto_block', True))
    with col2:
        block_threshold = st.slider("Block Threshold", 0, 100, config.get('block_threshold', 70))
        restrict_threshold = st.slider("Restrict Threshold", 0, 100, config.get('restrict_threshold', 30))
    
    st.markdown("#### 📧 Notification Settings")
    col1, col2 = st.columns(2)
    with col1:
        enable_email = st.checkbox("Enable Email Alerts", value=config.get('notification_email', True))
    with col2:
        enable_telegram = st.checkbox("Enable Telegram Alerts", value=config.get('notification_telegram', True))
    
    if st.button("💾 Save Configuration", type="primary"):
        config['alert_threshold'] = alert_threshold
        config['auto_block'] = auto_block
        config['block_threshold'] = block_threshold
        config['restrict_threshold'] = restrict_threshold
        config['notification_email'] = enable_email
        config['notification_telegram'] = enable_telegram
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        st.success("✅ Configuration saved!")

with tab3:
    st.markdown("### 📊 Recent Activity")
    
    data = load_users()
    users = data.get("users", {})
    
    activities = []
    for email, user_data in users.items():
        if user_data.get('last_login'):
            activities.append({
                'user': user_data.get('name', email),
                'action': 'Login',
                'time': user_data.get('last_login')
            })
        if user_data.get('created'):
            activities.append({
                'user': user_data.get('name', email),
                'action': 'Account Created',
                'time': user_data.get('created')
            })
    
    activities.sort(key=lambda x: x['time'], reverse=True)
    
    for activity in activities[:20]:
        try:
            time_str = datetime.fromisoformat(activity['time']).strftime('%Y-%m-%d %H:%M')
        except:
            time_str = activity['time'][:16]
        
        st.markdown(f"""
            <div class="user-row">
                <div>
                    <strong>{activity['user']}</strong>
                    <span style="color: #8B95A5; margin-left: 1rem;">{activity['action']}</span>
                </div>
                <span style="color: #8B95A5;">{time_str}</span>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">🛡️ AI-Driven Autonomous SOC | Admin Panel</p></div>', unsafe_allow_html=True)
