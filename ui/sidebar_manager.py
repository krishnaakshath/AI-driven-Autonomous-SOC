"""
 Sidebar Manager
==================
Manages sidebar visibility based on user role.
Call inject_sidebar_filter() at the top of each protected page.
"""

import streamlit as st


def inject_sidebar_filter():
    """
    Injects CSS to hide admin-only pages from the sidebar for non-admin users.
    Call this on every page for consistent navigation.
    """
    from services.auth_service import is_authenticated, is_admin
    
    # Base sidebar styling
    sidebar_css = """
    <style>
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0e17 0%, #151c2c 100%);
            border-right: 1px solid rgba(0, 212, 255, 0.1);
        }
        
        /* Hide Login and Register from sidebar when logged in */
        [data-testid="stSidebarNav"] li:has(a[href*="_Login"]),
        [data-testid="stSidebarNav"] li:has(a[href*="_Register"]) {
            display: none !important;
        }
    """
    
    # Admin-only pages to hide for non-admin users
    admin_pages = ['16_Security_Testing', '22_API', '25_Admin']
    
    # Hide admin pages if user is not admin
    if is_authenticated() and not is_admin():
        for page in admin_pages:
            sidebar_css += f"""
        [data-testid="stSidebarNav"] li:has(a[href*="{page}"]) {{
            display: none !important;
        }}
            """
    
    sidebar_css += """
        /* Add user info to sidebar */
        .sidebar-user-info {
            padding: 15px;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: auto;
        }
    </style>
    """
    
    st.markdown(sidebar_css, unsafe_allow_html=True)


def add_sidebar_user_info():
    """Add user info and logout to sidebar."""
    from services.auth_service import is_authenticated, is_admin
    
    if is_authenticated():
        with st.sidebar:
            st.markdown("---")
            
            # Admin badge
            if is_admin():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #FFD700, #FF8C00); color: #000; padding: 8px 12px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 0.85rem; margin-bottom: 10px;">
                     ADMIN
                </div>
                """, unsafe_allow_html=True)
            
            # User info
            user_email = st.session_state.get('user_email', 'Unknown')
            user_name = st.session_state.get('user_name', 'User')
            
            st.markdown(f"""
            <div style="color: #8B95A5; font-size: 0.85rem;">
                <p style="margin: 0;"><strong>{user_name}</strong></p>
                <p style="margin: 5px 0; color: #666;">{user_email}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button(" Logout", use_container_width=True, key="sidebar_logout"):
                for key in ['authenticated', 'user_email', 'user_name', 'login_step', 'pending_email', 'otp_store', 'cortex_messages', 'session_start']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.switch_page("pages/_Login.py")


def require_auth_with_sidebar():
    """
    Combined function that:
    1. Requires authentication
    2. Injects sidebar filter
    3. Adds user info to sidebar
    """
    from services.auth_service import is_authenticated
    
    if not is_authenticated():
        st.error(" **Authentication Required**")
        st.info("Please log in to access this page.")
        if st.button("Go to Login"):
            st.switch_page("pages/_Login.py")
        st.stop()
    
    inject_sidebar_filter()
    add_sidebar_user_info()
