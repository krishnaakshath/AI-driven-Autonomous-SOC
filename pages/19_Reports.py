import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    st.set_page_config(page_title="Reports | SOC", page_icon="R", layout="wide")
except st.errors.StreamlitAPIException:
    pass  # Already set by dashboard.py

from ui.theme import CYBERPUNK_CSS, inject_particles, page_header, section_title
st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
inject_particles()


# Authentication removed - public dashboard

st.markdown(page_header("Security Reports", "Generate comprehensive IEEE-format security reports"), unsafe_allow_html=True)

# Get real report stats
import glob
report_files = glob.glob("reports/*.pdf") + glob.glob("reports/*.txt")
total_reports = len(report_files)
# Count reports from last 7 days
recent_reports = 0
for rf in report_files:
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(rf))
        if mtime > datetime.now() - timedelta(days=7):
            recent_reports += 1
    except:
        pass

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00D4FF;">{total_reports}</p><p class="metric-label">Reports Generated</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><p class="metric-value" style="color: #00C853;">{recent_reports}</p><p class="metric-label">This Week</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="metric-card"><p class="metric-value" style="color: #8B5CF6;">PDF</p><p class="metric-label">Format</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="metric-card"><p class="metric-value" style="color: #FF8C00;">IEEE</p><p class="metric-label">Standard</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Generate Report", "Report History"])

with tab1:
    st.markdown(section_title("Report Configuration"), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox("Report Type", [
            "Weekly Security Summary",
            "Incident Response Report",
            "Threat Intelligence Report",
            "Compliance Audit Report",
            "Vulnerability Assessment"
        ])
        
        date_range = st.selectbox("Date Range", [
            "Last 7 Days",
            "Last 30 Days",
            "Last Quarter",
            "Custom Range"
        ])
    
    with col2:
        include_charts = st.checkbox("Include Visualizations", value=True)
        include_raw = st.checkbox("Include Raw Data", value=False)
        executive_summary = st.checkbox("Executive Summary", value=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Generate Report", type="primary", use_container_width=True):
        progress = st.progress(0)
        status = st.empty()
        
        steps = ["Collecting data...", "Analyzing threats...", "Generating content...", "Formatting report...", "Finalizing..."]
        for i, step in enumerate(steps):
            status.markdown(f'<p style="color: #00D4FF;">{step}</p>', unsafe_allow_html=True)
            progress.progress((i + 1) / len(steps))
            import time
            time.sleep(0.4)
        
        # Generate actual report
        try:
            from services.report_generator import generate_pdf_report, generate_security_report
            
            # Try PDF first, fallback to text
            try:
                report_data = generate_pdf_report(report_type, date_range, include_charts, include_raw, executive_summary)
                file_ext = "pdf"
                mime_type = "application/pdf"
            except:
                report_data = generate_security_report(report_type, date_range, include_charts, include_raw, executive_summary)
                file_ext = "txt"
                mime_type = "text/plain"
            
            st.success("Report generated successfully!")
            
            st.markdown("""
                <div class="glass-card" style="margin-top: 1rem;">
                    <h4 style="color: #00D4FF; margin: 0 0 1rem 0;">Report Preview</h4>
                    <div style="background: rgba(0,0,0,0.3); padding: 1.5rem; border-radius: 12px;">
                        <h3 style="color: #FAFAFA; text-align: center;">""" + report_type + """</h3>
                        <p style="color: #8B95A5; text-align: center;">AI-Driven Autonomous SOC</p>
                        <hr style="border-color: rgba(255,255,255,0.1);">
                        <p style="color: #FAFAFA;"><strong>Report Contents:</strong></p>
                        <ul style="color: #8B95A5;">
                            <li>Executive Summary</li>
                            <li>Threat Analysis</li>
                            <li>Geographic Distribution</li>
                            <li>Automated Response Summary</li>
                            <li>Recommendations</li>
                        </ul>
                        <p style="color: #8B95A5;">Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.download_button(
                f"Download Report ({file_ext.upper()})",
                data=report_data,
                file_name=f"SOC_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.{file_ext}",
                mime=mime_type,
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating report: {e}")

with tab2:
    st.markdown(section_title("Previous Reports"), unsafe_allow_html=True)
    
    # Show actual report files from disk
    reports = []
    for rf in sorted(report_files, key=lambda f: os.path.getmtime(f), reverse=True):
        fname = os.path.basename(rf)
        fsize = os.path.getsize(rf)
        fdate = datetime.fromtimestamp(os.path.getmtime(rf)).strftime("%b %d, %Y")
        size_str = f"{fsize / 1024:.1f} KB" if fsize < 1048576 else f"{fsize / 1048576:.1f} MB"
        rtype = "Incident" if "incident" in fname.lower() else "Threat Intel" if "threat" in fname.lower() else "Weekly"
        reports.append({"name": fname, "type": rtype, "date": fdate, "size": size_str})
    
    if not reports:
        st.info("No reports generated yet. Use the Generate Report tab to create your first report.")
    
    for r in reports:
        st.markdown(f"""
            <div class="glass-card" style="margin: 0.5rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #FAFAFA; font-weight: 600;">{r['name']}</span>
                        <div style="display: flex; gap: 1.5rem; margin-top: 0.3rem;">
                            <span style="color: #8B95A5; font-size: 0.85rem;">Type: {r['type']}</span>
                            <span style="color: #8B95A5; font-size: 0.85rem;">Date: {r['date']}</span>
                            <span style="color: #00D4FF; font-size: 0.85rem;">{r['size']}</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #8B95A5;"><p>AI-Driven Autonomous SOC | Reports</p></div>', unsafe_allow_html=True)
from ui.chat_interface import inject_floating_cortex_link
inject_floating_cortex_link()
