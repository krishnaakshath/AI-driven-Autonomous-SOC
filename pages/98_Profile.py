import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Profile | SOC", page_icon="P", layout="wide")

from ui.theme import PREMIUM_CSS, page_header, section_title
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

from auth.auth_manager import check_auth, show_user_info, get_current_user, update_user_profile, change_password, logout

user = check_auth()
if not user:
    st.switch_page("pages/0_Login.py")
    st.stop()

show_user_info(user)

st.markdown(page_header("My Profile", "Manage your account settings and preferences"), unsafe_allow_html=True)

# User avatar
initials = user.get('name', 'U')[0].upper()
role_color = "#FF4444" if user.get('role') == 'admin' else "#00D4FF"

st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 1.5rem; margin-bottom: 2rem;">
        <div style="
            width: 80px; height: 80px;
            background: linear-gradient(135deg, {role_color}, #8B5CF6);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 2rem; font-weight: 700; color: white;
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3);
        ">{initials}</div>
        <div>
            <h2 style="color: #FAFAFA; margin: 0;">{user.get('name', 'User')}</h2>
            <p style="color: #8B95A5; margin: 0.3rem 0;">{user.get('email', '')}</p>
            <span style="
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid {role_color};
                color: {role_color};
                padding: 0.2rem 0.8rem;
                border-radius: 20px;
                font-size: 0.75rem;
                text-transform: uppercase;
            ">{user.get('role', 'analyst')}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Profile Info", "Security", "Preferences"])

with tab1:
    st.markdown(section_title("Personal Information"), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_name = st.text_input("Full Name", value=user.get('name', ''))
    
    with col2:
        email_display = st.text_input("Email", value=user.get('email', ''), disabled=True)
    
    department = st.selectbox("Department", ["Security Operations", "IT", "Engineering", "Management"], index=0)
    
    if st.button("Update Profile", type="primary"):
        if new_name:
            success = update_user_profile(user.get('email'), {'name': new_name})
            if success:
                st.success("Profile updated successfully!")
                st.rerun()
            else:
                st.error("Failed to update profile")

with tab2:
    st.markdown(section_title("Change Password"), unsafe_allow_html=True)
    
    current_pass = st.text_input("Current Password", type="password", key="curr_pass")
    new_pass = st.text_input("New Password", type="password", key="new_pass")
    confirm_pass = st.text_input("Confirm New Password", type="password", key="conf_pass")
    
    if st.button("Change Password", type="primary"):
        if not current_pass or not new_pass:
            st.warning("Please fill all fields")
        elif new_pass != confirm_pass:
            st.error("Passwords don't match")
        elif len(new_pass) < 6:
            st.error("Password must be at least 6 characters")
        else:
            success = change_password(user.get('email'), current_pass, new_pass)
            if success:
                st.success("Password changed successfully!")
            else:
                st.error("Current password is incorrect")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_title("Sessions"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="color: #00C853;">●</span>
                    <span style="color: #FAFAFA; margin-left: 0.5rem;">Current Session</span>
                    <p style="color: #8B95A5; margin: 0.3rem 0 0 0; font-size: 0.85rem;">Active now</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown(section_title("Display Preferences"), unsafe_allow_html=True)
    
    theme = st.selectbox("Theme", ["Dark (Default)", "Light", "System"])
    timezone = st.selectbox("Timezone", ["UTC", "America/New_York", "Europe/London", "Asia/Kolkata"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_title("Notification Preferences"), unsafe_allow_html=True)
    
    email_alerts = st.checkbox("Email Alerts", value=True)
    browser_notif = st.checkbox("Browser Notifications", value=True)
    critical_only = st.checkbox("Critical Alerts Only", value=False)
    
    if st.button("Save Preferences", type="primary"):
        st.success("Preferences saved!")

st.markdown("---")

if st.button("Logout", type="secondary", use_container_width=True):
    logout()
    st.switch_page("pages/0_Login.py")

st.markdown('<div style="text-align: center; color: #8B95A5; margin-top: 1rem;"><p>AI-Driven Autonomous SOC | Profile</p></div>', unsafe_allow_html=True)
