# Shared Premium CSS for all SOC pages
# Import this at the top of each page file

PREMIUM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0e17 0%, #151c2c 50%, #0d1320 100%);
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: 
            radial-gradient(ellipse at 20% 80%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(139, 92, 246, 0.08) 0%, transparent 50%);
        pointer-events: none;
        animation: bgPulse 15s ease-in-out infinite;
    }
    
    @keyframes bgPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* Page Header */
    .page-header {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 24px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .page-header::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(0, 212, 255, 0.15) 0%, transparent 70%);
        animation: float 8s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(5deg); }
    }
    
    .page-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #00D4FF 50%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        position: relative;
    }
    
    .page-header p {
        color: #8B95A5;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, rgba(26, 31, 46, 0.9) 0%, rgba(15, 20, 30, 0.95) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.6s ease;
    }
    
    .metric-card:hover::before { left: 100%; }
    
    .metric-card:hover {
        transform: translateY(-5px) scale(1.02);
        border-color: rgba(0, 212, 255, 0.5);
        box-shadow: 0 20px 40px rgba(0, 212, 255, 0.2);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0.3rem 0;
        text-shadow: 0 0 30px currentColor;
    }
    
    .metric-label {
        color: #8B95A5;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    /* Glass Cards */
    .glass-card {
        background: rgba(26, 31, 46, 0.7);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        transition: all 0.4s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(0, 212, 255, 0.3);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
    }
    
    /* Alert Cards */
    .alert-card {
        background: rgba(26, 31, 46, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
        transition: all 0.3s ease;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .alert-critical { border-left-color: #FF4444; }
    .alert-high { border-left-color: #FF8C00; }
    .alert-medium { border-left-color: #FFD700; }
    .alert-low { border-left-color: #00C853; }
    
    .alert-card:hover {
        transform: translateX(10px);
        background: rgba(30, 36, 52, 0.9);
    }
    
    /* Section Titles */
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #FAFAFA;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(0, 212, 255, 0.3), transparent);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00D4FF 0%, #0099CC 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 30px rgba(0, 212, 255, 0.5) !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background: rgba(26, 31, 46, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #FAFAFA !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00D4FF !important;
        box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.2) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(26, 31, 46, 0.5);
        border-radius: 14px;
        padding: 5px;
        gap: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: #8B95A5;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00D4FF 0%, #0099CC 100%) !important;
        color: white !important;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #00D4FF, #8B5CF6, #FF4444);
        background-size: 200% 100%;
        animation: gradientFlow 2s linear infinite;
        border-radius: 10px;
    }
    
    @keyframes gradientFlow {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 14, 23, 0.98) 0%, rgba(15, 20, 30, 0.98) 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(26, 31, 46, 0.5); }
    ::-webkit-scrollbar-thumb { 
        background: linear-gradient(135deg, #00D4FF, #8B5CF6); 
        border-radius: 4px; 
    }
    
    /* Data tables */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Live badge */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(0, 200, 83, 0.15);
        border: 1px solid rgba(0, 200, 83, 0.4);
        padding: 0.4rem 1rem;
        border-radius: 30px;
        font-size: 0.85rem;
        color: #00C853;
        animation: livePulse 2s ease-in-out infinite;
    }
    
    .live-dot {
        width: 8px; height: 8px;
        background: #00C853;
        border-radius: 50%;
        animation: dotPulse 1.5s ease-in-out infinite;
    }
    
    @keyframes dotPulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.5); opacity: 0.5; }
    }
    
    @keyframes livePulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(0, 200, 83, 0.4); }
        50% { box-shadow: 0 0 0 10px rgba(0, 200, 83, 0); }
    }
</style>
"""

def page_header(title, subtitle=""):
    return f"""
    <div class="page-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """

def metric_card(value, label, color="#00D4FF"):
    return f"""
    <div class="metric-card">
        <p class="metric-value" style="color: {color};">{value}</p>
        <p class="metric-label">{label}</p>
    </div>
    """

def alert_card(severity, title, description, time_str=""):
    sev_class = f"alert-{severity.lower()}"
    sev_colors = {"critical": "#FF4444", "high": "#FF8C00", "medium": "#FFD700", "low": "#00C853"}
    color = sev_colors.get(severity.lower(), "#8B95A5")
    return f"""
    <div class="alert-card {sev_class}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="color: {color}; font-weight: 700; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 1px;">{severity}</span>
                <h4 style="color: #FAFAFA; margin: 0.3rem 0 0.5rem 0; font-size: 1.1rem;">{title}</h4>
                <p style="color: #8B95A5; margin: 0; font-size: 0.9rem;">{description}</p>
            </div>
            <span style="color: #8B95A5; font-size: 0.75rem; white-space: nowrap;">{time_str}</span>
        </div>
    </div>
    """

def section_title(text):
    return f'<p class="section-title">{text}</p>'
