"""
 Weekly Report Generator
=============================
Automated weekly security report generation.
Runs via cloud_background.py every 7 days.
Generates a comprehensive weekly summary and saves to data/weekly_reports/.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
WEEKLY_DIR = os.path.join(DATA_DIR, 'weekly_reports')
REPORT_LOG = os.path.join(WEEKLY_DIR, 'report_log.json')


def _ensure_dirs():
    os.makedirs(WEEKLY_DIR, exist_ok=True)


def _load_report_log() -> list:
    if os.path.exists(REPORT_LOG):
        try:
            with open(REPORT_LOG, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def _save_report_log(log: list):
    _ensure_dirs()
    with open(REPORT_LOG, 'w') as f:
        json.dump(log, f, indent=2, default=str)


def should_generate_weekly_report() -> bool:
    """Check if a weekly report is due (7+ days since last report)."""
    log = _load_report_log()
    if not log:
        return True  # No reports yet — generate first one
    
    last = log[0]  # Most recent
    try:
        last_date = datetime.fromisoformat(last['generated_at'])
        return (datetime.now() - last_date).days >= 7
    except:
        return True


def generate_weekly_report() -> Optional[Dict]:
    """
    Generate a weekly security summary report.
    
    Returns:
        Dict with report metadata, or None if generation failed.
    """
    _ensure_dirs()
    
    now = datetime.now()
    week_start = now - timedelta(days=7)
    report_id = f"WEEKLY-{now.strftime('%Y%m%d-%H%M%S')}"
    
    logger.info(f"[WEEKLY-REPORT] Generating report {report_id}...")
    
    # ── Gather data from the database ──
    report_data = _gather_weekly_data(week_start, now)
    
    # ── Generate text report ──
    text_content = _build_weekly_text_report(report_data, week_start, now)
    
    # Save text report
    txt_filename = f"{report_id}.txt"
    txt_path = os.path.join(WEEKLY_DIR, txt_filename)
    with open(txt_path, 'w') as f:
        f.write(text_content)
    
    # ── Try to generate PDF report ──
    pdf_filename = None
    try:
        from services.report_generator import generate_pdf_report
        pdf_bytes = generate_pdf_report(
            report_type="weekly_summary",
            date_range="last_7_days",
            include_charts=True,
            executive_summary=True
        )
        if pdf_bytes:
            pdf_filename = f"{report_id}.pdf"
            pdf_path = os.path.join(WEEKLY_DIR, pdf_filename)
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
    except Exception as e:
        logger.warning(f"[WEEKLY-REPORT] PDF generation failed (text report saved): {e}")
    
    # ── Save metadata to report log ──
    metadata = {
        'id': report_id,
        'generated_at': now.isoformat(),
        'period_start': week_start.isoformat(),
        'period_end': now.isoformat(),
        'txt_file': txt_filename,
        'pdf_file': pdf_filename,
        'stats': {
            'total_events': report_data.get('total_events', 0),
            'critical_alerts': report_data.get('critical_alerts', 0),
            'threats_detected': report_data.get('threats_detected', 0),
            'anomalies': report_data.get('anomalies', 0),
        }
    }
    
    log = _load_report_log()
    log.insert(0, metadata)
    # Keep last 52 weeks (1 year)
    log = log[:52]
    _save_report_log(log)
    
    logger.info(f"[WEEKLY-REPORT] Report {report_id} saved ({len(text_content)} bytes text)")
    return metadata


def get_weekly_reports() -> list:
    """Get all weekly report metadata, most recent first."""
    return _load_report_log()


def get_report_file(filename: str) -> Optional[bytes]:
    """Read a report file from the weekly_reports directory."""
    filepath = os.path.join(WEEKLY_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None


# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL: Data gathering & formatting
# ═════════════════════════════════════════════════════════════════════════════

def _gather_weekly_data(start: datetime, end: datetime) -> Dict:
    """Pull metrics from the SIEM database for the given week."""
    data = {
        'total_events': 0,
        'critical_alerts': 0,
        'threats_detected': 0,
        'anomalies': 0,
        'top_sources': [],
        'top_attack_types': [],
        'severity_breakdown': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
    }
    
    try:
        from services.database import db
        events = db.get_all_events()
        
        # Filter to the reporting window
        week_events = []
        for evt in events:
            try:
                ts = datetime.fromisoformat(evt.get('timestamp', ''))
                if start <= ts <= end:
                    week_events.append(evt)
            except:
                # If timestamp parsing fails, include it anyway
                week_events.append(evt)
        
        data['total_events'] = len(week_events)
        
        # Severity breakdown
        for evt in week_events:
            sev = str(evt.get('severity', 'low')).lower()
            if sev in data['severity_breakdown']:
                data['severity_breakdown'][sev] += 1
            if sev == 'critical':
                data['critical_alerts'] += 1
        
        data['threats_detected'] = data['severity_breakdown']['critical'] + data['severity_breakdown']['high']
        
        # Top source IPs
        src_counts = {}
        for evt in week_events:
            src = evt.get('source_ip', evt.get('src_ip', 'unknown'))
            src_counts[src] = src_counts.get(src, 0) + 1
        data['top_sources'] = sorted(src_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Top attack types
        atk_counts = {}
        for evt in week_events:
            atk = evt.get('attack_type', evt.get('category', 'unknown'))
            atk_counts[atk] = atk_counts.get(atk, 0) + 1
        data['top_attack_types'] = sorted(atk_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Anomaly count (from ML scores if available)
        data['anomalies'] = sum(1 for e in week_events if float(e.get('anomaly_score', 0)) > 0.7)
        
    except Exception as e:
        logger.warning(f"[WEEKLY-REPORT] DB query failed: {e}")
    
    return data


def _build_weekly_text_report(data: Dict, start: datetime, end: datetime) -> str:
    """Build a formatted text report from gathered data."""
    sep = "=" * 72
    lines = [
        sep,
        f"  WEEKLY SECURITY REPORT",
        f"  Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        sep,
        "",
        "  EXECUTIVE SUMMARY",
        "-" * 72,
        f"  Total Events Processed : {data['total_events']:,}",
        f"  Critical Alerts        : {data['critical_alerts']:,}",
        f"  Threats Detected       : {data['threats_detected']:,}",
        f"  ML Anomalies           : {data['anomalies']:,}",
        "",
        "  SEVERITY DISTRIBUTION",
        "-" * 72,
    ]
    
    sev = data.get('severity_breakdown', {})
    total = max(sum(sev.values()), 1)
    for level in ['critical', 'high', 'medium', 'low']:
        count = sev.get(level, 0)
        pct = (count / total) * 100
        bar = "█" * int(pct / 2)
        lines.append(f"  {level.upper():10s}: {count:6,}  ({pct:5.1f}%)  {bar}")
    
    lines.extend(["", "  TOP SOURCE IPs", "-" * 72])
    for ip, count in data.get('top_sources', []):
        lines.append(f"  {ip:20s}: {count:,} events")
    
    lines.extend(["", "  TOP ATTACK CATEGORIES", "-" * 72])
    for atk, count in data.get('top_attack_types', []):
        lines.append(f"  {atk:30s}: {count:,}")
    
    lines.extend([
        "",
        sep,
        "  END OF REPORT",
        sep,
    ])
    
    return "\n".join(lines)
