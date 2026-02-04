"""
🔮 CYBERPUNK 2077 THEME - AI-Driven Autonomous SOC
===================================================
Ultra-futuristic UI with neon glows, scanlines, glitch effects,
holographic elements, and interactive particle systems.
"""

import streamlit as st

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CYBERPUNK CSS
# ═══════════════════════════════════════════════════════════════════════════════

CYBERPUNK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap');
    
    /* ═══════════════════════════════════════════════════════════════════════════
       CSS VARIABLES - NEON COLOR PALETTE
    ═══════════════════════════════════════════════════════════════════════════ */
    :root {
        --neon-cyan: #00f3ff;
        --neon-purple: #bc13fe;
        --neon-pink: #ff00ff;
        --neon-red: #ff003c;
        --neon-orange: #ff6b00;
        --neon-green: #0aff0a;
        --neon-yellow: #f0ff00;
        --bg-dark: #030303;
        --bg-darker: #000000;
        --glass-bg: rgba(5, 5, 15, 0.85);
        --glass-border: rgba(0, 243, 255, 0.15);
        --text-primary: #e0e0e0;
        --text-secondary: #888;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       TYPOGRAPHY - CYBERPUNK FONTS
    ═══════════════════════════════════════════════════════════════════════════ */
    /* IMPORTANT: Exclude icon fonts (Material Icons) from font overrides */
    html, body, [class*="css"]:not([class*="icon"]):not([data-testid*="Collapse"]):not([aria-label*="sidebar"]), 
    .stMarkdown, p, div:not([data-testid*="Collapse"]), label {
        font-family: 'Rajdhani', 'Segoe UI', sans-serif !important;
        color: var(--text-primary);
        letter-spacing: 0.5px;
    }
    
    /* Preserve Material Icons font for Streamlit controls */
    span[class*="material"], 
    [data-testid="stSidebarCollapseButton"] span,
    button[aria-label*="sidebar"] span,
    button[aria-label*="Sidebar"] span {
        font-family: 'Material Icons', 'Material Symbols Rounded', sans-serif !important;
    }
    
    h1, h2, h3, h4, h5, h6, .metric-value, .cyber-title {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 3px;
        text-transform: uppercase;
    }
    
    /* Sidebar navigation - exclude toggle button */
    section[data-testid="stSidebar"] *:not(button):not(button *) {
        font-family: 'Rajdhani', sans-serif !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] a {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.85rem !important;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    
    /* All text inputs and labels */
    .stTextInput label, .stSelectbox label, .stNumberInput label,
    .stSlider label, .stCheckbox label, .stRadio label {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.75rem !important;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--neon-cyan) !important;
    }
    
    /* Data displays */
    .stDataFrame, .stTable, table, th, td {
        font-family: 'Share Tech Mono', monospace !important;
    }
    
    /* Metric displays */
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Rajdhani', sans-serif !important;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    /* Code and monospace */
    code, pre, .mono, .stCode {
        font-family: 'Share Tech Mono', 'Fira Code', monospace !important;
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1px;
    }
    
    /* Tab labels */
    .stTabs [data-baseweb="tab"] {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       MAIN BACKGROUND - ANIMATED GRID + SCANLINES
    ═══════════════════════════════════════════════════════════════════════════ */
    /* ═══════════════════════════════════════════════════════════════════════════
       MAIN BACKGROUND - CLEANER GRID
    ═══════════════════════════════════════════════════════════════════════════ */
    .stApp {
        background-color: var(--bg-dark);
        background-image: 
            /* Subtle static grid */
            linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
    }
    
    /* Removed moving scanline for cleaner professional look */

    /* ═══════════════════════════════════════════════════════════════════════════
       GLASS CARDS - HOLOGRAPHIC EFFECT
    ═══════════════════════════════════════════════════════════════════════════ */
    .glass-card, .metric-card {
        background: rgba(5, 5, 10, 0.6); /* More transparent, cleaner */
        border: 1px solid rgba(0, 243, 255, 0.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border-radius: 4px;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
        padding: 2rem; /* Increased padding */
        margin-bottom: 1rem;
    }
    
    /* Top laser line animation */
    .glass-card::before, .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, var(--neon-cyan), var(--neon-purple), transparent);
        transform: translateX(-100%);
        transition: transform 0.8s ease;
    }
    
    /* Corner accent */
    .glass-card::after, .metric-card::after {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 30px; height: 30px;
        border-top: 2px solid var(--neon-cyan);
        border-right: 2px solid var(--neon-cyan);
        opacity: 0.5;
    }
    
    .glass-card:hover::before, .metric-card:hover::before {
        transform: translateX(100%);
    }
    
    .glass-card:hover, .metric-card:hover {
        transform: translateY(-8px) scale(1.01);
        box-shadow: 
            0 0 40px rgba(0, 243, 255, 0.15),
            0 20px 40px rgba(0, 0, 0, 0.4),
            inset 0 0 40px rgba(0, 243, 255, 0.05);
        border-color: var(--neon-cyan);
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       METRIC CARDS - NEON GLOW
    ═══════════════════════════════════════════════════════════════════════════ */
    /* ═══════════════════════════════════════════════════════════════════════════
       METRIC CARDS - PROFESSIONAL GLOW
    ═══════════════════════════════════════════════════════════════════════════ */
    .metric-value {
        font-size: 3rem;
        font-weight: 700;
        /* Cleaner text shadow, less bloom */
        text-shadow: 0 0 15px rgba(0, 243, 255, 0.4);
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.75rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--text-secondary);
        margin: 0;
        opacity: 0.8;
    }
    
    /* Removed heavy neon flicker animation */

    /* ═══════════════════════════════════════════════════════════════════════════
       GLITCH EFFECT - HEADERS
    ═══════════════════════════════════════════════════════════════════════════ */
    /* ═══════════════════════════════════════════════════════════════════════════
       HEADERS - CLEAN TECH LOOK
    ═══════════════════════════════════════════════════════════════════════════ */
    .page-header h1 {
        /* Subtle glow only */
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       BUTTONS - CYBER STYLE
    ═══════════════════════════════════════════════════════════════════════════ */
    .stButton > button {
        background: transparent !important;
        border: 2px solid var(--neon-cyan) !important;
        color: var(--neon-cyan) !important;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 3px;
        padding: 0.8rem 2rem !important;
        transition: all 0.3s ease !important;
        position: relative;
        overflow: hidden;
        clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
        transition: left 0.5s ease;
    }
    
    .stButton > button:hover {
        background: rgba(0, 243, 255, 0.1) !important;
        box-shadow: 
            0 0 20px var(--neon-cyan),
            inset 0 0 20px rgba(0, 243, 255, 0.1);
        text-shadow: 0 0 10px var(--neon-cyan);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       TABS - CYBER NAVIGATION
    ═══════════════════════════════════════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(0, 243, 255, 0.1);
        border-radius: 0;
        padding: 5px;
        gap: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary);
        font-family: 'Orbitron', sans-serif;
        font-size: 0.8rem;
        letter-spacing: 1px;
        border: none;
        background: transparent;
        padding: 0.8rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--neon-cyan);
        background: rgba(0, 243, 255, 0.05);
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--neon-cyan) !important;
        background: rgba(0, 243, 255, 0.1) !important;
        border-bottom: 2px solid var(--neon-cyan) !important;
        text-shadow: 0 0 10px var(--neon-cyan);
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
    }
    
    .stTabs [data-baseweb="tab-border"], .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       LIVE BADGE - PULSING INDICATOR
    ═══════════════════════════════════════════════════════════════════════════ */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.75rem;
        letter-spacing: 2px;
        background: rgba(10, 255, 10, 0.1);
        border: 1px solid var(--neon-green);
        color: var(--neon-green);
        padding: 0.6rem 1.2rem;
        box-shadow: 
            0 0 15px rgba(10, 255, 10, 0.3),
            inset 0 0 15px rgba(10, 255, 10, 0.1);
        animation: badgePulse 2s ease-in-out infinite;
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: var(--neon-green);
        border-radius: 50%;
        box-shadow: 0 0 10px var(--neon-green);
        animation: dotPulse 1s ease-in-out infinite;
    }
    
    @keyframes badgePulse {
        0%, 100% { box-shadow: 0 0 15px rgba(10, 255, 10, 0.3), inset 0 0 15px rgba(10, 255, 10, 0.1); }
        50% { box-shadow: 0 0 25px rgba(10, 255, 10, 0.5), inset 0 0 20px rgba(10, 255, 10, 0.15); }
    }
    
    @keyframes dotPulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.5); opacity: 0.7; }
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       ALERT CARDS - SEVERITY BASED
    ═══════════════════════════════════════════════════════════════════════════ */
    .alert-card {
        background: var(--glass-bg);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-left: 4px solid;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .alert-card.critical { 
        border-left-color: var(--neon-red);
        box-shadow: inset 3px 0 20px rgba(255, 0, 60, 0.1);
    }
    .alert-card.high { 
        border-left-color: var(--neon-orange);
        box-shadow: inset 3px 0 20px rgba(255, 107, 0, 0.1);
    }
    .alert-card.medium { 
        border-left-color: var(--neon-yellow);
        box-shadow: inset 3px 0 20px rgba(240, 255, 0, 0.05);
    }
    .alert-card.low { 
        border-left-color: var(--neon-green);
        box-shadow: inset 3px 0 20px rgba(10, 255, 10, 0.05);
    }
    
    .alert-card:hover {
        transform: translateX(10px);
        background: rgba(10, 10, 20, 0.9);
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       INPUTS - CYBER STYLE
    ═══════════════════════════════════════════════════════════════════════════ */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background: rgba(0, 0, 0, 0.6) !important;
        border: 1px solid rgba(0, 243, 255, 0.2) !important;
        border-radius: 0 !important;
        color: var(--neon-cyan) !important;
        font-family: 'Share Tech Mono', monospace !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--neon-cyan) !important;
        box-shadow: 
            0 0 15px rgba(0, 243, 255, 0.2),
            inset 0 0 10px rgba(0, 243, 255, 0.05) !important;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       SCROLLBAR - NEON STYLE
    ═══════════════════════════════════════════════════════════════════════════ */
    ::-webkit-scrollbar { 
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track { 
        background: var(--bg-darker);
    }
    ::-webkit-scrollbar-thumb { 
        background: linear-gradient(180deg, var(--neon-cyan), var(--neon-purple));
        border-radius: 0;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--neon-cyan);
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       SIDEBAR - CYBER NAVIGATION
    ═══════════════════════════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(5, 5, 15, 0.98) 0%, rgba(0, 0, 0, 0.98) 100%);
        border-right: 1px solid rgba(0, 243, 255, 0.1);
    }
    
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-family: 'Rajdhani', sans-serif;
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       DATA FRAMES / TABLES
    ═══════════════════════════════════════════════════════════════════════════ */
    .stDataFrame {
        border: 1px solid rgba(0, 243, 255, 0.1);
    }
    
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: var(--glass-bg);
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       HIDE STREAMLIT DEFAULTS
    ═══════════════════════════════════════════════════════════════════════════ */
    #MainMenu, footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ═══════════════════════════════════════════════════════════════════════════
       PLOTLY CHART CONTAINERS
    ═══════════════════════════════════════════════════════════════════════════ */
    .js-plotly-plot {
        border: 1px solid rgba(0, 243, 255, 0.1);
        background: rgba(5, 5, 15, 0.5);
    }

    /* ═══════════════════════════════════════════════════════════════════════════
       EXPANDER - CYBER STYLE
    ═══════════════════════════════════════════════════════════════════════════ */
    .streamlit-expanderHeader {
        background: rgba(0, 243, 255, 0.05) !important;
        border: 1px solid rgba(0, 243, 255, 0.1) !important;
        border-radius: 0 !important;
        font-family: 'Orbitron', sans-serif;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--neon-cyan) !important;
    }

</style>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# PARTICLES.JS INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

def inject_particles():
    """Injects Particles.js for an interactive cyberpunk background"""
    particles_html = """
    <div id="particles-js" style="position: fixed; width: 100vw; height: 100vh; top: 0; left: 0; z-index: -1; pointer-events: none;"></div>
    <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
    <script>
        if (typeof particlesJS !== 'undefined') {
            particlesJS("particles-js", {
                "particles": {
                    "number": { "value": 80, "density": { "enable": true, "value_area": 800 } },
                    "color": { "value": ["#00f3ff", "#bc13fe", "#ff00ff"] },
                    "shape": { "type": "circle" },
                    "opacity": { "value": 0.4, "random": true, "anim": { "enable": true, "speed": 1, "opacity_min": 0.1 } },
                    "size": { "value": 2, "random": true },
                    "line_linked": { 
                        "enable": true, 
                        "distance": 150, 
                        "color": "#00f3ff", 
                        "opacity": 0.15, 
                        "width": 1 
                    },
                    "move": { 
                        "enable": true, 
                        "speed": 1.5, 
                        "direction": "none", 
                        "random": true, 
                        "straight": false, 
                        "out_mode": "out", 
                        "bounce": false 
                    }
                },
                "interactivity": {
                    "detect_on": "canvas",
                    "events": { 
                        "onhover": { "enable": true, "mode": "grab" }, 
                        "onclick": { "enable": true, "mode": "push" }, 
                        "resize": true 
                    },
                    "modes": { 
                        "grab": { "distance": 140, "line_linked": { "opacity": 0.8 } }, 
                        "push": { "particles_nb": 4 } 
                    }
                },
                "retina_detect": true
            });
        }
    </script>
    """
    st.components.v1.html(particles_html, height=0, width=0)

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def page_header(title, subtitle=""):
    """Creates a cyberpunk-styled page header with glitch effect"""
    return f"""
    <div class="page-header" style="
        margin-bottom: 2rem; 
        padding: 1.5rem 0;
        border-bottom: 1px solid rgba(0,243,255,0.2);
        position: relative;
    ">
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 0.5rem;">
            <span style="
                width: 4px; 
                height: 40px; 
                background: linear-gradient(180deg, #00f3ff, #bc13fe);
                box-shadow: 0 0 15px #00f3ff;
            "></span>
            <h1 class="glitch-text" style="
                color: #fff; 
                font-size: 2.2rem;
                margin: 0;
                text-shadow: 
                    0 0 10px rgba(0, 243, 255, 0.8),
                    0 0 20px rgba(0, 243, 255, 0.5),
                    0 0 40px rgba(0, 243, 255, 0.3);
            ">{title}</h1>
        </div>
        <p style="
            color: #00f3ff; 
            margin: 0 0 0 19px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.9rem;
            letter-spacing: 2px;
        ">&gt; {subtitle}_</p>
    </div>
    """

def metric_card(value, label, color="#00f3ff"):
    """Creates a glowing metric card"""
    return f"""
    <div class="metric-card" style="
        text-align: center;
        border-top: 3px solid {color};
        box-shadow: 0 -5px 20px {color}30;
    ">
        <p class="metric-value" style="color: {color};">{value}</p>
        <p class="metric-label">{label}</p>
    </div>
    """

def section_title(text):
    """Creates a cyberpunk section title with decorative elements"""
    return f"""
    <div style="
        display: flex; 
        align-items: center; 
        margin: 2rem 0 1.5rem 0;
        gap: 15px;
    ">
        <span style="
            width: 12px; 
            height: 12px; 
            background: #00f3ff;
            box-shadow: 0 0 15px #00f3ff, 0 0 30px #00f3ff;
            clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
        "></span>
        <h3 style="
            margin: 0; 
            color: #fff; 
            font-family: 'Orbitron', sans-serif;
            font-size: 1rem;
            text-transform: uppercase; 
            letter-spacing: 4px;
            text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
        ">{text}</h3>
        <span style="
            flex: 1; 
            height: 1px; 
            background: linear-gradient(90deg, #00f3ff, #bc13fe, transparent);
            opacity: 0.5;
        "></span>
        <span style="
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.7rem;
            color: #666;
        ">[SYS]</span>
    </div>
    """

def alert_card(severity, title, description, timestamp=""):
    """Creates a severity-colored alert card"""
    colors = {
        "critical": "#ff003c",
        "high": "#ff6b00", 
        "medium": "#f0ff00",
        "low": "#0aff0a"
    }
    color = colors.get(severity.lower(), "#00f3ff")
    
    return f"""
    <div class="alert-card {severity.lower()}" style="border-left-color: {color};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="
                    color: {color}; 
                    font-family: 'Orbitron', sans-serif;
                    font-size: 0.7rem;
                    letter-spacing: 2px;
                    text-transform: uppercase;
                ">{severity}</span>
                <h4 style="color: #fff; margin: 0.3rem 0; font-size: 1rem;">{title}</h4>
                <p style="color: #888; margin: 0; font-size: 0.85rem;">{description}</p>
            </div>
            <span style="
                color: #555; 
                font-family: 'Share Tech Mono', monospace;
                font-size: 0.7rem;
            ">{timestamp}</span>
        </div>
    </div>
    """

def cyber_badge(text, color="#00f3ff"):
    """Creates a cyberpunk-styled badge"""
    return f"""
    <span style="
        display: inline-block;
        padding: 0.3rem 0.8rem;
        background: {color}15;
        border: 1px solid {color}40;
        color: {color};
        font-family: 'Orbitron', sans-serif;
        font-size: 0.7rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    ">{text}</span>
    """

def status_indicator(status="online"):
    """Creates a status indicator with appropriate color"""
    colors = {
        "online": "#0aff0a",
        "offline": "#ff003c",
        "warning": "#f0ff00",
        "processing": "#00f3ff"
    }
    color = colors.get(status.lower(), "#00f3ff")
    
    return f"""
    <span style="
        display: inline-flex;
        align-items: center;
        gap: 8px;
    ">
        <span style="
            width: 8px;
            height: 8px;
            background: {color};
            border-radius: 50%;
            box-shadow: 0 0 10px {color};
            animation: dotPulse 1s ease-in-out infinite;
        "></span>
        <span style="
            color: {color};
            font-family: 'Share Tech Mono', monospace;
            font-size: 0.8rem;
            text-transform: uppercase;
        ">{status}</span>
    </span>
    """

# ═══════════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════════════
# Alias for older pages that still use PREMIUM_CSS
PREMIUM_CSS = CYBERPUNK_CSS

