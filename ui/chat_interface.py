import streamlit as st

def inject_floating_cortex_link():
    """
    Injects a floating CORTEX orb button that links to the CORTEX AI page.
    Call this function at the end of any page to show the floating orb.
    """
    st.markdown("""
    <style>
    /* Floating CORTEX Orb - Links to AI Page */
    .cortex-float-orb {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00f3ff 0%, #bc13fe 50%, #ff0080 100%);
        border: 3px solid rgba(255,255,255,0.4);
        box-shadow: 
            0 0 30px rgba(0, 243, 255, 0.6),
            0 0 60px rgba(188, 19, 254, 0.4),
            inset 0 0 20px rgba(255,255,255,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        cursor: pointer;
        z-index: 99999;
        text-decoration: none;
        animation: orb-glow 2s ease-in-out infinite, orb-float 3s ease-in-out infinite;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .cortex-float-orb:hover {
        transform: scale(1.15);
        box-shadow: 
            0 0 50px rgba(0, 243, 255, 0.9),
            0 0 100px rgba(188, 19, 254, 0.7),
            inset 0 0 30px rgba(255,255,255,0.3);
    }
    
    .cortex-float-orb:hover .orb-tooltip {
        opacity: 1;
        transform: translateX(-10px);
    }
    
    .orb-tooltip {
        position: absolute;
        right: 85px;
        background: rgba(0, 0, 0, 0.9);
        border: 1px solid rgba(0, 243, 255, 0.5);
        padding: 8px 16px;
        border-radius: 8px;
        white-space: nowrap;
        color: #00f3ff;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1px;
        opacity: 0;
        transition: all 0.3s ease;
        pointer-events: none;
    }
    
    .orb-tooltip::after {
        content: '';
        position: absolute;
        right: -8px;
        top: 50%;
        transform: translateY(-50%);
        border: 6px solid transparent;
        border-left-color: rgba(0, 243, 255, 0.5);
    }
    
    @keyframes orb-glow {
        0%, 100% { 
            box-shadow: 0 0 30px rgba(0, 243, 255, 0.6), 0 0 60px rgba(188, 19, 254, 0.4);
        }
        50% { 
            box-shadow: 0 0 50px rgba(0, 243, 255, 0.9), 0 0 80px rgba(188, 19, 254, 0.6);
        }
    }
    
    @keyframes orb-float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    
    /* Ring pulse effect */
    .cortex-float-orb::before {
        content: '';
        position: absolute;
        width: 90px;
        height: 90px;
        border-radius: 50%;
        border: 2px solid rgba(0, 243, 255, 0.5);
        animation: ring-expand 2s ease-out infinite;
    }
    
    @keyframes ring-expand {
        0% { transform: scale(0.8); opacity: 1; }
        100% { transform: scale(1.5); opacity: 0; }
    }
    </style>
    
    <a href="/CORTEX_AI" class="cortex-float-orb" target="_self">
        🤖
        <span class="orb-tooltip">OPEN CORTEX AI</span>
    </a>
    """, unsafe_allow_html=True)


def render_chat_interface():
    """Legacy function - now just injects the floating orb link."""
    inject_floating_cortex_link()


def inject_chat_floating():
    """Legacy function - now just injects the floating orb link."""
    inject_floating_cortex_link()
