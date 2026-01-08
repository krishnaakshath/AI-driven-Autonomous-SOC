import streamlit as st
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="File Scanner | SOC", page_icon="📁", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .scan-result {
        background: rgba(26, 31, 46, 0.8);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    .result-clean { border-left-color: #00C853; }
    .result-suspicious { border-left-color: #FF8C00; }
    .result-malicious { border-left-color: #FF4444; }
    .verdict-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .badge-clean { background: rgba(0, 200, 83, 0.2); color: #00C853; }
    .badge-suspicious { background: rgba(255, 140, 0, 0.2); color: #FF8C00; }
    .badge-malicious { background: rgba(255, 68, 68, 0.2); color: #FF4444; }
    .threat-item {
        background: rgba(255, 68, 68, 0.1);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

try:
    from services.pdf_scanner import PDFScanner, scan_pdf_file
    SCANNER_AVAILABLE = True
except:
    SCANNER_AVAILABLE = False

st.markdown("# 📁 File Scanner")
st.markdown("Upload files for malware analysis")
st.markdown("---")

if not SCANNER_AVAILABLE:
    st.warning("PDF Scanner module not loaded. Please check installation.")

tab1, tab2 = st.tabs(["📄 PDF Scanner", "📊 Scan History"])

with tab1:
    st.markdown("### Upload PDF for Analysis")
    st.markdown("Scan PDF files for malicious content, JavaScript, suspicious patterns, and phishing indicators.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        if st.button("🔍 Scan File", type="primary"):
            with st.spinner("Scanning file for threats..."):
                try:
                    result = scan_pdf_file(tmp_path)
                    
                    verdict = result['verdict']
                    risk = result['risk_score']
                    
                    if verdict == 'CLEAN':
                        result_class = "result-clean"
                        badge_class = "badge-clean"
                        verdict_icon = "✅"
                    elif verdict in ['SUSPICIOUS', 'POTENTIALLY_UNSAFE']:
                        result_class = "result-suspicious"
                        badge_class = "badge-suspicious"
                        verdict_icon = "⚠️"
                    else:
                        result_class = "result-malicious"
                        badge_class = "badge-malicious"
                        verdict_icon = "🔴"
                    
                    st.markdown(f"""
                        <div class="scan-result {result_class}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-size: 1.5rem;">{verdict_icon}</span>
                                    <span style="font-size: 1.3rem; font-weight: 600; color: #FAFAFA; margin-left: 0.5rem;">{result['file_name']}</span>
                                </div>
                                <span class="verdict-badge {badge_class}">{verdict}</span>
                            </div>
                            <div style="margin-top: 1rem; display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                                <div>
                                    <p style="color: #8B95A5; font-size: 0.8rem; margin: 0;">Risk Score</p>
                                    <p style="color: #FAFAFA; font-size: 1.5rem; font-weight: 700; margin: 0;">{risk}/100</p>
                                </div>
                                <div>
                                    <p style="color: #8B95A5; font-size: 0.8rem; margin: 0;">File Size</p>
                                    <p style="color: #FAFAFA; font-weight: 600; margin: 0;">{result['file_size']:,} bytes</p>
                                </div>
                                <div>
                                    <p style="color: #8B95A5; font-size: 0.8rem; margin: 0;">Threats Found</p>
                                    <p style="color: #FF4444; font-size: 1.5rem; font-weight: 700; margin: 0;">{len(result['threats_found'])}</p>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if result['threats_found']:
                        st.markdown("#### 🚨 Threats Detected")
                        for threat in result['threats_found']:
                            st.markdown(f'<div class="threat-item">⚠️ {threat}</div>', unsafe_allow_html=True)
                    else:
                        st.success("No threats detected in this file.")
                    
                    if result.get('metadata'):
                        with st.expander("📋 File Metadata"):
                            for key, value in result['metadata'].items():
                                st.markdown(f"**{key}**: {value}")
                    
                    st.markdown(f"**File Hash (MD5):** `{result.get('file_hash', 'N/A')}`")
                    
                except Exception as e:
                    st.error(f"Scan error: {str(e)}")
                finally:
                    os.unlink(tmp_path)

with tab2:
    st.markdown("### Recent Scan History")
    st.info("Scan history will appear here after scanning files.")
    
    if 'scan_history' not in st.session_state:
        st.session_state.scan_history = []
    
    if st.session_state.scan_history:
        for scan in st.session_state.scan_history[-10:]:
            st.markdown(f"- **{scan['file_name']}**: {scan['verdict']} (Risk: {scan['risk_score']})")

st.markdown("---")

st.markdown("### 🔧 Background Network Monitoring")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Start Manual Network Scan**")
    if st.button("🔍 Scan Network Now"):
        with st.spinner("Scanning network traffic..."):
            try:
                from services.soc_monitor import scan_network
                threats = scan_network()
                if threats:
                    st.warning(f"⚠️ Detected {len(threats)} potential threats!")
                    for t in threats[:5]:
                        st.markdown(f"- **{t['source_ip']}**: {t['attack_type']} (Risk: {t['risk_score']:.0f})")
                else:
                    st.success("✅ No threats detected in current network data.")
            except Exception as e:
                st.error(f"Scan error: {str(e)}")

with col2:
    st.markdown("**Background Monitor Status**")
    st.info("Run `python services/soc_monitor.py` in terminal for continuous monitoring")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5; padding: 1rem;"><p style="margin: 0;">🛡️ AI-Driven Autonomous SOC | File Analysis</p></div>', unsafe_allow_html=True)
