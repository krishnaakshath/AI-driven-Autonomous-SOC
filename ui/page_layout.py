"""
 Standardized Page Layout
============================
Provides consistent layout functions for all SOC pages.
Wraps theme helpers into a unified page structure:
  header -> KPI row -> filters -> content sections -> footer
"""

import streamlit as st
from ui.theme import (
    CYBERPUNK_CSS, MOBILE_CSS, COLORS, SEV_COLORS,
    inject_particles, page_header, section_title,
    metric_card, alert_card, cyber_badge, status_indicator,
    loading_skeleton, empty_state,
)


def init_page(title: str, subtitle: str = "", particles: bool = True):
    """
    Initialize a standard page with theme CSS, optional particles, and header.
    Call this at the top of every page.
    """
    st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
    if particles:
        inject_particles()
    st.markdown(page_header(title, subtitle), unsafe_allow_html=True)


def require_auth():
    """
    Redirect unauthenticated users to the login page.
    Returns True if the user is authenticated, False otherwise.
    Call after init_page() on protected pages.
    """
    from services.auth_service import is_authenticated
    if not is_authenticated():
        st.warning("Please log in to access this page.")
        st.switch_page("pages/_Login.py")
        return False
    return True


def kpi_row(metrics: list[dict]):
    """
    Render a uniform KPI row.
    
    Args:
        metrics: list of dicts with keys: value, label, color
                 e.g. [{"value": "1,234", "label": "Total Events", "color": "#00f3ff"}]
    """
    if not metrics:
        return
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.markdown(
                metric_card(m["value"], m["label"], m.get("color", "#00f3ff")),
                unsafe_allow_html=True
            )


def section_gap():
    """Insert consistent vertical spacing between sections."""
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)


def content_section(title: str):
    """Render a section title with consistent styling. Returns None - use inline."""
    st.markdown(section_title(title), unsafe_allow_html=True)


def show_loading(rows: int = 3):
    """Show animated loading skeleton."""
    st.markdown(loading_skeleton(rows), unsafe_allow_html=True)


def show_empty(title: str, message: str, icon: str = ""):
    """Show a styled empty-state message."""
    # Use a neutral icon instead of emoji for professional look
    st.markdown(empty_state(title, message, icon if icon else ""), unsafe_allow_html=True)


def show_error(title: str, detail: str = ""):
    """Show a styled error state."""
    error_html = f"""
    <div style="
        text-align: center;
        padding: 2rem;
        background: rgba(255, 0, 60, 0.05);
        border: 1px solid rgba(255, 0, 60, 0.15);
        border-radius: 12px;
        margin: 1rem 0;
    ">
        <h3 style="color: #ff003c; margin: 0 0 0.5rem 0; font-family: 'Rajdhani', sans-serif;">{title}</h3>
        <p style="color: #8B95A5; margin: 0; font-size: 0.85rem; font-family: 'Share Tech Mono', monospace;">{detail}</p>
    </div>
    """
    st.markdown(error_html, unsafe_allow_html=True)


def page_footer(module_name: str = ""):
    """Render a consistent page footer with optional CORTEX link."""
    section_gap()
    st.markdown("---")
    label = f" // {module_name.upper()} MODULE //" if module_name else ""
    st.markdown(f"""
    <div style="text-align:center; color:#555; padding:0.5rem; font-family:'Share Tech Mono',monospace; font-size:0.8rem;">
        // AI-DRIVEN AUTONOMOUS SOC //{label} ZERO TRUST PLATFORM //
    </div>
    """, unsafe_allow_html=True)
    try:
        from ui.chat_interface import inject_floating_cortex_link
        inject_floating_cortex_link()
    except Exception:
        pass


def refresh_button(label: str = "Refresh", key: str = "refresh_btn"):
    """Render a standard refresh button that clears cache and reruns."""
    if st.button(f"↻ {label}", use_container_width=True, key=key):
        st.cache_data.clear()
        st.rerun()


# Re-export theme constants for convenience
__all__ = [
    "init_page", "require_auth", "kpi_row", "section_gap",
    "content_section", "show_loading", "show_empty", "show_error",
    "page_footer", "refresh_button",
    "COLORS", "SEV_COLORS", "section_title", "metric_card",
    "alert_card", "cyber_badge", "status_indicator",
]
