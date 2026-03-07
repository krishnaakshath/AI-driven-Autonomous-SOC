# Report Generator Service
import io
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import random
import logging

try:
    from services.database import db
    HAS_DB = True
except ImportError:
    HAS_DB = False

def _get_report_data(date_range: str) -> Dict[str, Any]:
    """Fetch real data from DB for reports."""
    if not HAS_DB:
        return _get_mock_data()
        
    # Calculate start date
    days = 7
    if "30" in date_range: days = 30
    elif "Quarter" in date_range: days = 90
    
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    # Fetch data
    events = db.get_recent_events(limit=5000) # Get enough sample
    alerts = db.get_alerts(limit=1000)
    
    # Filter by date (simple string comparison works for ISO format)
    events = [e for e in events if e.get('timestamp', '') >= start_date]
    alerts = [a for a in alerts if a.get('timestamp', '') >= start_date]
    
    total_events = len(events)
    critical_threats = len([a for a in alerts if a.get('severity') == 'CRITICAL'])
    blocked_count = len([e for e in events if 'BLOCKED' in str(e.get('event_type', '')).upper()])
    
    # Attack Types
    attack_counts = {}
    for a in alerts:
        atype = a.get('title', 'Unknown').split(':')[-1].strip()
        attack_counts[atype] = attack_counts.get(atype, 0) + 1
    
    top_attacks = sorted(attack_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    if not top_attacks:
        top_attacks = [("No Significant Threats", 0)]
        
    # Geo Distribution (Mock extraction from source_ip if geoip not avail)
    # real log ingestor puts ip in source_ip. 
    # For reporting, we might need a lookup, but for now we can infer or use mock distribution if IP is private
    # Let's just aggregate source IPs
    ip_counts = {}
    for e in events:
        src = e.get('source_ip', 'Unknown')
        if src != 'Unknown':
             ip_counts[src] = ip_counts.get(src, 0) + 1
    
    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    
    # --- Statistical & Probabilistic Engine Integration ---
    try:
        from services.statistical_engine import statistical_engine
        
        # Calculate dynamic security risk score based on Bayesian-style weighting
        security_score = statistical_engine.calculate_probabilistic_risk_score(events, alerts)
        
        # Calculate Poisson probabilistic forecasts for the next 7 days
        forecasts = statistical_engine.forecast_threats(events, days_ahead=7, confidence_interval=0.90)
    except ImportError:
        # Fallback if statistical engine fails to load
        security_score = 100 - (min(critical_threats * 2, 100))
        forecasts = []
    
    return {
        "total_events": total_events,
        "critical_threats": critical_threats,
        "blocked_count": blocked_count,
        "top_attacks": top_attacks,
        "top_ips": top_ips,
        "security_score": security_score,
        "forecasts": forecasts,
        "alerts": alerts
    }

def _get_mock_data():
    return {
        "total_events": 0, "critical_threats": 0, "blocked_count": 0,
        "top_attacks": [], "top_ips": [], "security_score": 100, 
        "forecasts": [], "alerts": []
    }

def generate_security_report(report_type: str, date_range: str, include_charts: bool = True, 
                             include_raw: bool = False, executive_summary: bool = True) -> bytes:
    """Generate a comprehensive security report in text format"""
    
    data = _get_report_data(date_range)
    
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("                      AI-DRIVEN AUTONOMOUS SOC")
    report_lines.append("                    COMPREHENSIVE SECURITY REPORT")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Report Type:     {report_type}")
    report_lines.append(f"Date Range:      {date_range}")
    report_lines.append(f"Generated:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Report ID:       SOC-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    report_lines.append(f"Classification:  CONFIDENTIAL")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # 1. Executive Summary
    if executive_summary:
        report_lines.append("1. EXECUTIVE SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append("")
        report_lines.append("This report provides a comprehensive analysis of the security posture")
        report_lines.append("based on real-time data collected by the SOC.")
        report_lines.append("")
        report_lines.append("KEY FINDINGS:")
        report_lines.append("")
        report_lines.append(f"  * Total Events Analyzed: {data['total_events']}")
        report_lines.append(f"  * Critical Threats Identified: {data['critical_threats']}")
        report_lines.append(f"  * Attacks Automatically Blocked: {data['blocked_count']}")
        report_lines.append(f"  * Security Score: {data['security_score']}/100")
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("")
    
    # 2. Threat Analysis
    report_lines.append("2. THREAT ANALYSIS")
    report_lines.append("-" * 40)
    report_lines.append("")
    report_lines.append("Top Observed Threats:")
    for attack, count in data['top_attacks']:
        report_lines.append(f"  - {attack}: {count} occurrences")
    report_lines.append("")
    
    # 4. Probabilistic Forecasts
    report_lines.append("4. PROBABILISTIC THREAT FORECASTS (7-DAY OUTLOOK)")
    report_lines.append("-" * 40)
    report_lines.append("")
    if data.get('forecasts'):
        for f in data['forecasts']:
            report_lines.append(f"  - {f['threat_type']}: {f['probability_pct']}% probability ({f['risk_level']} Risk)")
            report_lines.append(f"    Expected volume: {f['expected_events']} incidents (Momentum: {f['momentum_multiplier']}x)")
            report_lines.append("")
    else:
        report_lines.append("  - Insufficient data for statistical forecasting.")
        report_lines.append("")
    
    # Footer
    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    
    return "\n".join(report_lines).encode('utf-8')


def generate_pdf_report(report_type: str, date_range: str, include_charts: bool = True,
                        include_raw: bool = False, executive_summary: bool = True) -> bytes:
    """Generate PDF report using reportlab"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        
        data = _get_report_data(date_range)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, alignment=1, textColor=colors.HexColor('#00D4FF'))
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#00D4FF'), spaceAfter=10)
        
        # Title Page
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("AI-Driven Autonomous SOC", title_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Comprehensive Security Report", styles['Heading2']))
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph(f"<b>Report Type:</b> {report_type}", styles['Normal']))
        story.append(Paragraph(f"<b>Date Range:</b> {date_range}", styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(PageBreak())
        
        # Executive Summary
        if executive_summary:
            story.append(Paragraph("1. Executive Summary", heading_style))
            story.append(Paragraph(
                "This report provides a comprehensive analysis of the security posture based on real-time data.",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>Key Findings:</b>", styles['Normal']))
            findings = [
                f"Total Events: {data['total_events']}",
                f"Critical Threats: {data['critical_threats']}",
                f"Blocked Attacks: {data['blocked_count']}",
                f"Security Score: {data['security_score']}/100"
            ]
            for f in findings:
                story.append(Paragraph(f"• {f}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # Threats Table
        story.append(Paragraph("2. Threat Analysis", heading_style))
        if data['top_attacks']:
            t_data = [['Attack Type', 'Count']] + [[k, str(v)] for k, v in data['top_attacks']]
            t = Table(t_data, colWidths=[4*inch, 2*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00D4FF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(t)
        else:
            story.append(Paragraph("No significant threats detected in this period.", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        return generate_security_report(report_type, date_range, include_charts, include_raw, executive_summary)


def generate_pdf_report(report_type: str, date_range: str, include_charts: bool = True,
                        include_raw: bool = False, executive_summary: bool = True) -> bytes:
    """Generate PDF report using reportlab if available, otherwise text"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, ListFlowable, ListItem
        from reportlab.lib import colors
        
        data = _get_report_data(date_range)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, alignment=1, textColor=colors.HexColor('#00D4FF'))
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#00D4FF'), spaceAfter=10)
        subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12, textColor=colors.HexColor('#00D4FF'), spaceBefore=10)
        normal_style = styles['Normal']
        
        # Title Page
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("AI-Driven Autonomous SOC", title_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Comprehensive Security Report", styles['Heading2']))
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph(f"<b>Report Type:</b> {report_type}", normal_style))
        story.append(Paragraph(f"<b>Date Range:</b> {date_range}", normal_style))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(Paragraph(f"<b>Report ID:</b> SOC-{datetime.now().strftime('%Y%m%d%H%M%S')}", normal_style))
        story.append(Paragraph("<b>Classification:</b> CONFIDENTIAL", normal_style))
        story.append(PageBreak())
        
        # 1. Executive Summary
        if executive_summary:
            story.append(Paragraph("1. Executive Summary", heading_style))
            story.append(Paragraph(
                "This report provides a comprehensive analysis of the security posture for the AI-Driven "
                "Autonomous SOC platform during the specified reporting period. The SOC has maintained "
                "continuous monitoring and automated response capabilities utilizing hybrid machine learning models.",
                normal_style
            ))
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>Key Findings:</b>", normal_style))
            findings = [
                f"Total security events analyzed: {data['total_events']:,}",
                f"Critical threats identified and mitigated: {data['critical_threats']}",
                f"Malicious attempts automatically blocked: {data['blocked_count']}",
                f"Top Attack Vector: {data['top_attacks'][0][0] if data['top_attacks'] else 'None'}",
                f"Overall security posture score: {data['security_score']}/100"
            ]
            
            bullet_list = []
            for f in findings:
                bullet_list.append(ListItem(Paragraph(f, normal_style)))
            story.append(ListFlowable(bullet_list, bulletType='bullet', start='circle'))
            story.append(Spacer(1, 0.3*inch))
        
        # 2. Key Metrics
        story.append(Paragraph("2. Key Metrics Overview", heading_style))
        metrics_data = [
            ['Metric', 'Current', 'Target', 'Status'],
            ['Total Events', f"{data['total_events']:,}", '-', 'Info'],
            ['Critical Threats', str(data['critical_threats']), '0', 'Active' if data['critical_threats'] > 0 else 'Stable'],
            ['Blocked Attacks', str(data['blocked_count']), '-', 'Protected'],
            ['Security Score', f"{data['security_score']}/100", '90+', 'Good' if data['security_score'] > 80 else 'Review'],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00D4FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#444')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f8f8')),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 3. Threat Analysis
        story.append(Paragraph("3. Threat Analysis", heading_style))
        threat_data = [['Attack Type', 'Count', 'Severity']]
        
        if data['top_attacks']:
            for attack, count in data['top_attacks']:
                 # Simple heuristic for severity mapping
                 sev = "HIGH"
                 if "SQL" in attack or "C2" in attack: sev = "CRITICAL"
                 elif "Probe" in attack or "Port" in attack: sev = "MEDIUM"
                 threat_data.append([str(attack), str(count), sev])
            
            threat_table = Table(threat_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
            threat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF4444')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#444')),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff5f5')),
            ]))
            story.append(threat_table)
        else:
            story.append(Paragraph("No significant threats detected in this period.", normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 4. Probabilistic Threat Forecasts
        story.append(Paragraph("4. Probabilistic Threat Forecasts (7-Day Outlook)", heading_style))
        story.append(Paragraph(
            "Using a poisson distribution model adjusted for short-term Markov momentum, "
            "the Autonomous SOC has calculated the mathematical probability of specific attack vectors "
            "occurring in the next 7 days.",
            normal_style
        ))
        story.append(Spacer(1, 0.1*inch))
        
        if data.get('forecasts'):
            forecast_data = [['Threat Type', 'Probability', 'Risk Level', 'Expected Vol']]
            for f in data['forecasts']:
                p_text = f"{f['probability_pct']}%"
                vol_text = f"{f['expected_events']} (x{f['momentum_multiplier']})"
                forecast_data.append([str(f['threat_type']), p_text, str(f['risk_level']), vol_text])
            
            f_table = Table(forecast_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.5*inch])
            f_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#444')),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f0ff')),
                # Color code risk column
                ('TEXTCOLOR', (2, 1), (2, -1), colors.black),
            ]))
            
            # Apply color coding to individual rows based on risk level
            for i, row in enumerate(forecast_data[1:], start=1):
                if row[2] == 'High':
                    f_table.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.red), ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')]))
                elif row[2] == 'Medium':
                    f_table.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.orange)]))
                else:
                    f_table.setStyle(TableStyle([('TEXTCOLOR', (2, i), (2, i), colors.green)]))
                    
            story.append(f_table)
        else:
             story.append(Paragraph("Insufficient data for statistical forecasting.", normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 5. Technical Methodology & Architecture
        story.append(Paragraph("5. Technical Methodology & Architecture", heading_style))
        story.append(Paragraph(
            "The security analysis in this report is generated by a multi-layered autonomous system:",
            normal_style
        ))
        story.append(Spacer(1, 0.1*inch))
        
        methodology_points = [
            ListItem(Paragraph("<b>Data Ingestion:</b> Real-time log processing and normalization of network traffic events.", normal_style)),
            ListItem(Paragraph("<b>Anomaly Detection (Unsupervised):</b> Uses an <i>Isolation Forest</i> algorithm alongside moving Z-Scores to identify deviations.", normal_style)),
            ListItem(Paragraph("<b>Threat Classification (Supervised):</b> A Hybrid Gradient Boosting model classifies detected anomalies into specific attack categories (DoS, Probe, U2R, R2L).", normal_style)),
            ListItem(Paragraph("<b>Probabilistic Engine:</b> Bayesian-weighted risk scoring and Poisson-distribution modeling for event forecasting.", normal_style)),
            ListItem(Paragraph("<b>Automated Response:</b> High-confidence threats trigger immediate containment actions (IP blocking, Session termination).", normal_style))
        ]
        story.append(ListFlowable(methodology_points, bulletType='bullet', start='square'))
        story.append(Spacer(1, 0.3*inch))

        # 6. Top Source Objects (Dynamic Geographics)
        story.append(Paragraph("6. Top Source Objects", heading_style))
        if data['top_ips']:
            geo_data = [['Source IP', 'Event Count', 'Status']]
            for ip, count in data['top_ips']:
                status = "Flagged" if count > 10 else "Monitoring"
                geo_data.append([str(ip), str(count), status])
            
            geo_table = Table(geo_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            geo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#444')),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f0ff')),
            ]))
            story.append(geo_table)
        else:
            story.append(Paragraph("No specific source IPs identified above threshold.", normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 7. Recommendations (Dynamic)
        story.append(Paragraph("7. Recommendations", heading_style))
        
        recs = []
        if data['critical_threats'] > 0:
            recs.append(("HIGH PRIORITY", f"Investigate {data['critical_threats']} critical incidents immediately."))
            recs.append(("High Priority", "Review firewall logs for the flagged Source IPs."))
        
        if data['blocked_count'] > 50:
             recs.append(("Medium Priority", "Consider tightening rate-limiting rules due to high volume of blocked attempts."))
        
        if data['security_score'] < 80:
             recs.append(("High Priority", "Overall security score is low. Conduct a full system audit."))
        
        recs.append(("Low Priority", "Schedule periodic review of user access logs."))
        recs.append(("Low Priority", "Update threat intelligence feeds."))

        for priority, text in recs:
            p_color = colors.red if "HIGH" in priority.upper() else colors.black
            story.append(Paragraph(f"<b>[{priority}]</b> {text}", ParagraphStyle('Rec', parent=normal_style, textColor=p_color)))
            story.append(Spacer(1, 0.05*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("─" * 50, normal_style))
        story.append(Paragraph("AI-Driven Autonomous SOC - Zero Trust Security Platform", normal_style))
        story.append(Paragraph(f"Report ID: SOC-{datetime.now().strftime('%Y%m%d%H%M%S')}", normal_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        return generate_security_report(report_type, date_range, include_charts, include_raw, executive_summary)
