import streamlit as st
import os
import sys
import hashlib
import uuid
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Profile | SOC", page_icon="P", layout="wide")

from ui.theme import PREMIUM_CSS, page_header, section_title
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

from auth.auth_manager import check_auth, show_user_info, get_current_user, update_user_profile, change_password, logout
from auth.two_factor import remove_trusted_device, clear_all_trusted_devices

user = check_auth()
if not user:
    st.switch_page("pages/0_Login.py")
    st.stop()

show_user_info(user)

is_admin = user.get('role') == 'admin'
page_title_text = "Admin Profile" if is_admin else "My Profile"
page_desc = "Manage your account and admin settings" if is_admin else "Manage your account settings and preferences"

st.markdown(page_header(page_title_text, page_desc), unsafe_allow_html=True)

# Get device ID for logout
def get_device_id():
    if 'device_id' not in st.session_state:
        st.session_state.device_id = hashlib.md5(str(uuid.getnode()).encode()).hexdigest()[:16]
    return st.session_state.device_id

# User avatar with photo support
initials = user.get('name', 'U')[0].upper()
role_color = "#FF4444" if is_admin else "#00D4FF"
user_photo = user.get('photo', '')

if user_photo:
    avatar_html = f'<img src="{user_photo}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3);">'
else:
    avatar_html = f'''<div style="
        width: 80px; height: 80px;
        background: linear-gradient(135deg, {role_color}, #8B5CF6);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 2rem; font-weight: 700; color: white;
        box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3);
    ">{initials}</div>'''

role_badge = "Creator / Admin" if is_admin else user.get('role', 'analyst').title()

st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 1.5rem; margin-bottom: 2rem;">
        {avatar_html}
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
            ">{role_badge}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Tabs - more for admin
if is_admin:
    tab1, tab2, tab3, tab4 = st.tabs(["Profile Info", "Security", "Admin Tools", "Preferences"])
else:
    tab1, tab2, tab3 = st.tabs(["Profile Info", "Security", "Preferences"])

with tab1:
    st.markdown(section_title("Personal Information"), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_name = st.text_input("Full Name", value=user.get('name', ''))
    
    with col2:
        email_display = st.text_input("Email", value=user.get('email', ''), disabled=True)
    
    department = st.selectbox("Department", ["Security Operations", "IT", "Engineering", "Management"], index=0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_title("Profile Photo"), unsafe_allow_html=True)
    
    photo_url = st.text_input("Photo URL", value=user.get('photo', ''), placeholder="https://example.com/photo.jpg")
    
    uploaded_file = st.file_uploader("Or upload a photo", type=['png', 'jpg', 'jpeg'], key="photo_upload")
    
    if uploaded_file:
        # Convert to base64 data URL
        file_bytes = uploaded_file.read()
        b64 = base64.b64encode(file_bytes).decode()
        photo_url = f"data:image/{uploaded_file.type.split('/')[1]};base64,{b64}"
        st.image(uploaded_file, width=100, caption="Preview")
    
    if st.button("Update Profile", type="primary"):
        if new_name:
            updates = {'name': new_name}
            if photo_url:
                updates['photo'] = photo_url
            success = update_user_profile(user.get('email'), updates)
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
    st.markdown(section_title("Trusted Devices"), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="color: #00C853;">●</span>
                    <span style="color: #FAFAFA; margin-left: 0.5rem;">Current Device</span>
                    <p style="color: #8B95A5; margin: 0.3rem 0 0 0; font-size: 0.85rem;">2FA not required on this device</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Remove All Trusted Devices", type="secondary"):
        clear_all_trusted_devices(user.get('email'))
        st.success("All devices removed. You'll need to verify 2FA on next login.")

# Admin Tools tab (only for admin)
if is_admin:
    with tab4 if is_admin else tab3:
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
    
    with tab3:
        st.markdown(section_title("Quick Admin Actions"), unsafe_allow_html=True)
        
        st.markdown("""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <p style="color: #8B95A5; margin: 0;">As the creator/admin, you have full access to all system functions.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Go to Admin Panel", use_container_width=True, type="primary"):
                st.switch_page("pages/99_Admin.py")
        
        with col2:
            if st.button("View System Logs", use_container_width=True):
                st.info("Check Admin Panel > Attack Logs")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Quick stats
        st.markdown(section_title("Your Activity"), unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Reports Generated", "12")
        with c2:
            st.metric("Threats Reviewed", "156")
        with c3:
            st.metric("Days Active", "30")

else:
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

col1, col2 = st.columns(2)

with col1:
    if st.button("Logout", type="secondary", use_container_width=True):
        # Remove device trust on logout
        remove_trusted_device(user.get('email'), get_device_id())
        logout()
        st.switch_page("pages/0_Login.py")

with col2:
    if st.button("Logout from All Devices", use_container_width=True):
        clear_all_trusted_devices(user.get('email'))
        logout()
        st.switch_page("pages/0_Login.py")

st.markdown('<div style="text-align: center; color: #8B95A5; margin-top: 1rem;"><p>AI-Driven Autonomous SOC | Profile</p></div>', unsafe_allow_html=True)
