import streamlit as st

def kpi_card(title: str, value: str, subtext: str = "", color: str = "#00f3ff"):
    """Renders a highly reusable KPI metric card."""
    theme_mode = st.session_state.get("theme", "cyberpunk")
    
    # Render different CSS classes depending on the active top-level theme
    card_class = "glass-card" if theme_mode == "cyberpunk" else "prof-card"
    glow_style = f"box-shadow: 0 0 15px {color}22; border-left: 3px solid {color};" if theme_mode == "cyberpunk" else f"border-left: 4px solid {color};"
    value_color = color if theme_mode == "cyberpunk" else "#e2e8f0"
    
    return f"""
    <div class="{card_class}" style="padding: 1.2rem; {glow_style}; height: 100%;">
        <div style="font-size: 0.85rem; color: #888; text-transform: uppercase; font-weight: 600; margin-bottom: 0.5rem; font-family: 'Inter', sans-serif;">{title}</div>
        <div style="font-size: 2rem; font-weight: 700; color: {value_color}; font-family: 'Orbitron', 'Inter', sans-serif; line-height: 1;">{value}</div>
        <div style="font-size: 0.75rem; color: #666; margin-top: 0.5rem;">{subtext}</div>
    </div>
    """

def severity_badge(level: str):
    """Renders a strict severity pill badge."""
    colors = {
        "Critical": "#EF4444", "High": "#F97316",
        "Medium": "#EAB308", "Low": "#6B7280"
    }
    c = colors.get(level.capitalize(), "#888")
    return f"""
    <span style="
        background: {c}22;
        color: {c};
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid {c}55;
        text-transform: uppercase;
        display: inline-block;
    ">{level}</span>
    """

def empty_state(title: str, message: str, icon: str = "📭"):
    """Renders a standardized empty state panel."""
    theme_mode = st.session_state.get("theme", "cyberpunk")
    border_color = "rgba(0, 243, 255, 0.15)" if theme_mode == "cyberpunk" else "rgba(255, 255, 255, 0.05)"
    
    return f"""
    <div style="
        text-align: center;
        padding: 4rem 2rem;
        background: rgba(10, 10, 20, 0.3);
        border: 1px dashed {border_color};
        border-radius: 8px;
        margin: 1rem 0;
    ">
        <div style="font-size: 2.5rem; margin-bottom: 1rem; opacity: 0.7;">{icon}</div>
        <h3 style="color: #E2E8F0; margin: 0 0 0.5rem 0; font-family: 'Inter', sans-serif; font-size: 1.1rem;">{title}</h3>
        <p style="color: #64748B; margin: 0; font-size: 0.9rem;">{message}</p>
    </div>
    """

def error_panel(title: str, message: str, traceback_str: str = None):
    """Renders a distinct Error Panel instead of dropping raw Streamlit exception blocks."""
    html = f"""
    <div style="
        border-left: 4px solid #EF4444;
        background: rgba(239, 68, 68, 0.05);
        padding: 1.2rem;
        border-radius: 4px;
        margin: 1rem 0;
        font-family: 'Inter', sans-serif;
    ">
        <div style="color: #FCA5A5; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 8px;">
            <span class="material-icons" style="font-size: 18px;">error_outline</span> {title}
        </div>
        <div style="color: #94A3B8; font-size: 0.85rem;">{message}</div>
    </div>
    """
    return html

def page_header(title: str, subtitle: str = ""):
    """Standardizes the top-level Page Header typography based on the active theme."""
    theme_mode = st.session_state.get("theme", "cyberpunk")
    if theme_mode == "cyberpunk":
        return f"""
        <div style="margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(0, 243, 255, 0.1);">
            <h1 style="color: #00f3ff; margin:0; font-size: 1.8rem; text-shadow: 0 0 10px rgba(0,243,255,0.3);"><span class="material-icons" style="vertical-align: middle; margin-right: 12px; font-size: 28px;">stream</span>{title}</h1>
            <p style="color: #888; font-size: 0.9rem; margin: 0.5rem 0 0 0; font-family: 'Share Tech Mono', monospace;">{subtitle}</p>
        </div>
        """
    else:
        return f"""
        <div style="margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
            <h1 style="color: #F8FAFC; margin:0; font-size: 1.6rem; font-family: 'Inter', sans-serif; font-weight: 600;">{title}</h1>
            <p style="color: #64748B; font-size: 0.9rem; margin: 0.4rem 0 0 0; font-family: 'Inter', sans-serif;">{subtitle}</p>
        </div>
        """
