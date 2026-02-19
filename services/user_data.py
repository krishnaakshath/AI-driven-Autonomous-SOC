"""
 User Data Service
====================
Manages per-user data storage including scan history, uploaded files, and activity logs.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

# Data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
USERS_DATA_DIR = os.path.join(DATA_DIR, 'user_data')


def _get_user_dir(user_email: str) -> str:
    """Get user-specific data directory, creating if needed."""
    # Create hash of email for directory name (privacy + filesystem safe)
    user_id = hashlib.md5(user_email.lower().encode()).hexdigest()[:12]
    user_dir = os.path.join(USERS_DATA_DIR, user_id)
    
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        # Create subdirectories
        os.makedirs(os.path.join(user_dir, 'scans'), exist_ok=True)
        os.makedirs(os.path.join(user_dir, 'files'), exist_ok=True)
        os.makedirs(os.path.join(user_dir, 'reports'), exist_ok=True)
        
        # Initialize user profile
        profile = {
            'email': user_email,
            'created_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        with open(os.path.join(user_dir, 'profile.json'), 'w') as f:
            json.dump(profile, f, indent=2)
    
    return user_dir


def _load_json(filepath: str) -> Dict:
    """Load JSON file, return empty dict if doesn't exist."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def _save_json(filepath: str, data: Dict):
    """Save data to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


# ==================== SCAN HISTORY ====================

def save_scan(user_email: str, scan_type: str, target: str, result: Dict) -> str:
    """
    Save a scan result for the user.
    
    Args:
        user_email: User's email
        scan_type: Type of scan (url, file, ip, domain, etc.)
        target: What was scanned (URL, filename, IP, etc.)
        result: Scan results dictionary
    
    Returns:
        scan_id: Unique scan ID
    """
    user_dir = _get_user_dir(user_email)
    scans_file = os.path.join(user_dir, 'scans', 'history.json')
    
    scans = _load_json(scans_file)
    if 'scans' not in scans:
        scans['scans'] = []
    
    scan_id = f"SCAN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(scans['scans']) + 1:04d}"
    
    scan_entry = {
        'id': scan_id,
        'type': scan_type,
        'target': target,
        'timestamp': datetime.now().isoformat(),
        'result': result
    }
    
    scans['scans'].insert(0, scan_entry)  # Most recent first
    
    # Keep last 100 scans
    scans['scans'] = scans['scans'][:100]
    
    _save_json(scans_file, scans)
    return scan_id


def get_scan_history(user_email: str, limit: int = 50) -> List[Dict]:
    """Get user's scan history."""
    user_dir = _get_user_dir(user_email)
    scans_file = os.path.join(user_dir, 'scans', 'history.json')
    scans = _load_json(scans_file)
    return scans.get('scans', [])[:limit]


def get_scan_by_id(user_email: str, scan_id: str) -> Optional[Dict]:
    """Get a specific scan by ID."""
    history = get_scan_history(user_email, limit=100)
    for scan in history:
        if scan.get('id') == scan_id:
            return scan
    return None


# ==================== FILE STORAGE ====================

def save_uploaded_file(user_email: str, filename: str, content: bytes, file_type: str = 'general') -> str:
    """
    Save an uploaded file for the user.
    
    Returns:
        file_id: Unique file ID
    """
    user_dir = _get_user_dir(user_email)
    files_dir = os.path.join(user_dir, 'files')
    
    # Create unique filename
    file_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(content).hexdigest()[:8]}"
    safe_name = f"{file_id}_{filename.replace('/', '_').replace('..', '_')}"
    filepath = os.path.join(files_dir, safe_name)
    
    # Save file
    with open(filepath, 'wb') as f:
        f.write(content)
    
    # Update file index
    index_file = os.path.join(files_dir, 'index.json')
    index = _load_json(index_file)
    if 'files' not in index:
        index['files'] = []
    
    index['files'].insert(0, {
        'id': file_id,
        'original_name': filename,
        'saved_name': safe_name,
        'type': file_type,
        'size': len(content),
        'uploaded_at': datetime.now().isoformat()
    })
    
    _save_json(index_file, index)
    return file_id


def get_uploaded_files(user_email: str) -> List[Dict]:
    """Get list of user's uploaded files."""
    user_dir = _get_user_dir(user_email)
    index_file = os.path.join(user_dir, 'files', 'index.json')
    index = _load_json(index_file)
    return index.get('files', [])


def get_file_content(user_email: str, file_id: str) -> Optional[bytes]:
    """Get file content by ID."""
    files = get_uploaded_files(user_email)
    for f in files:
        if f.get('id') == file_id:
            user_dir = _get_user_dir(user_email)
            filepath = os.path.join(user_dir, 'files', f['saved_name'])
            if os.path.exists(filepath):
                with open(filepath, 'rb') as file:
                    return file.read()
    return None


# ==================== ACTIVITY LOG ====================

def log_activity(user_email: str, action: str, details: Dict = None):
    """Log user activity."""
    user_dir = _get_user_dir(user_email)
    activity_file = os.path.join(user_dir, 'activity.json')
    
    activity = _load_json(activity_file)
    if 'log' not in activity:
        activity['log'] = []
    
    activity['log'].insert(0, {
        'action': action,
        'details': details or {},
        'timestamp': datetime.now().isoformat()
    })
    
    # Keep last 500 activities
    activity['log'] = activity['log'][:500]
    
    _save_json(activity_file, activity)


def get_activity_log(user_email: str, limit: int = 100) -> List[Dict]:
    """Get user's activity log."""
    user_dir = _get_user_dir(user_email)
    activity_file = os.path.join(user_dir, 'activity.json')
    activity = _load_json(activity_file)
    return activity.get('log', [])[:limit]


# ==================== REPORTS ====================

def save_report(user_email: str, report_type: str, content: str, format: str = 'pdf') -> str:
    """Save a generated report."""
    user_dir = _get_user_dir(user_email)
    reports_dir = os.path.join(user_dir, 'reports')
    
    report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    filename = f"{report_id}_{report_type}.{format}"
    filepath = os.path.join(reports_dir, filename)
    
    # Save report
    mode = 'wb' if isinstance(content, bytes) else 'w'
    with open(filepath, mode) as f:
        f.write(content)
    
    # Update index
    index_file = os.path.join(reports_dir, 'index.json')
    index = _load_json(index_file)
    if 'reports' not in index:
        index['reports'] = []
    
    index['reports'].insert(0, {
        'id': report_id,
        'type': report_type,
        'filename': filename,
        'format': format,
        'created_at': datetime.now().isoformat()
    })
    
    _save_json(index_file, index)
    return report_id


def get_reports(user_email: str) -> List[Dict]:
    """Get list of user's reports."""
    user_dir = _get_user_dir(user_email)
    index_file = os.path.join(user_dir, 'reports', 'index.json')
    index = _load_json(index_file)
    return index.get('reports', [])


def get_report_content(user_email: str, report_id: str) -> Optional[bytes]:
    """Get report content by ID."""
    reports = get_reports(user_email)
    for r in reports:
        if r.get('id') == report_id:
            user_dir = _get_user_dir(user_email)
            filepath = os.path.join(user_dir, 'reports', r['filename'])
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    return f.read()
    return None


# ==================== USER SETTINGS ====================

def save_user_setting(user_email: str, key: str, value: Any):
    """Save a user-specific setting."""
    user_dir = _get_user_dir(user_email)
    settings_file = os.path.join(user_dir, 'settings.json')
    settings = _load_json(settings_file)
    settings[key] = value
    _save_json(settings_file, settings)


def get_user_setting(user_email: str, key: str, default: Any = None) -> Any:
    """Get a user-specific setting."""
    user_dir = _get_user_dir(user_email)
    settings_file = os.path.join(user_dir, 'settings.json')
    settings = _load_json(settings_file)
    return settings.get(key, default)


def get_all_user_settings(user_email: str) -> Dict:
    """Get all user settings."""
    user_dir = _get_user_dir(user_email)
    settings_file = os.path.join(user_dir, 'settings.json')
    return _load_json(settings_file)


# ==================== LOGIN FOOTPRINT TRACKING ====================

def log_login_attempt(user_email: str, success: bool, ip_address: str = "127.0.0.1",
                      user_agent: str = "unknown") -> Dict:
    """
    Record a login attempt in the user's digital footprint.
    
    Args:
        user_email: User's email
        success: Whether login succeeded
        ip_address: Client IP address
        user_agent: Browser/client user agent string
    
    Returns:
        Login record dict
    """
    user_dir = _get_user_dir(user_email)
    login_file = os.path.join(user_dir, 'login_history.json')
    
    data = _load_json(login_file)
    if 'logins' not in data:
        data['logins'] = []
    
    record = {
        'timestamp': datetime.now().isoformat(),
        'success': success,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'hour': datetime.now().hour,
    }
    
    data['logins'].insert(0, record)
    
    # Keep last 1000 login records (never delete — they persist indefinitely)
    data['logins'] = data['logins'][:1000]
    
    _save_json(login_file, data)
    
    # Also log to general activity
    log_activity(user_email, "login_attempt", {
        "success": success,
        "ip": ip_address,
    })
    
    return record


def get_login_history(user_email: str, limit: int = 200) -> List[Dict]:
    """Get user's complete login history (digital footprint)."""
    user_dir = _get_user_dir(user_email)
    login_file = os.path.join(user_dir, 'login_history.json')
    data = _load_json(login_file)
    return data.get('logins', [])[:limit]


def check_suspicious_login(user_email: str, current_ip: str = "127.0.0.1") -> Dict:
    """
    Analyze current login against historical patterns to detect suspicious behavior.
    
    Checks for:
    - New/unseen IP address
    - Login at unusual hour (e.g., 1-5 AM if user normally logs in 9-18)
    - Rapid failed login attempts (brute-force indicator)
    - Multiple IPs in short time window
    
    Returns:
        Dict with 'is_suspicious', 'risk_score' (0-100), 'reasons' list, 'details'
    """
    history = get_login_history(user_email, limit=500)
    
    if not history:
        # First login — not suspicious, just new
        return {
            'is_suspicious': False,
            'risk_score': 0,
            'reasons': [],
            'details': {'note': 'First login recorded'}
        }
    
    risk_score = 0
    reasons = []
    details = {}
    
    # 1. Check for new/unseen IP
    known_ips = set(h.get('ip_address', '') for h in history if h.get('success'))
    if current_ip not in known_ips and current_ip != "127.0.0.1":
        risk_score += 35
        reasons.append(f"New IP address: {current_ip}")
        details['new_ip'] = True
        details['known_ips_count'] = len(known_ips)
    
    # 2. Check for unusual login hour
    current_hour = datetime.now().hour
    successful_hours = [h.get('hour', 12) for h in history if h.get('success')]
    if successful_hours:
        avg_hour = sum(successful_hours) / len(successful_hours)
        # If login is more than 6 hours off from average pattern
        hour_diff = abs(current_hour - avg_hour)
        if hour_diff > 12:
            hour_diff = 24 - hour_diff
        if hour_diff > 6:
            risk_score += 20
            reasons.append(f"Unusual login hour ({current_hour}:00, typically ~{int(avg_hour)}:00)")
            details['unusual_time'] = True
    
    # 3. Check for rapid failed attempts (last 30 minutes)
    recent_fails = 0
    now = datetime.now()
    for h in history[:20]:
        try:
            ts = datetime.fromisoformat(h['timestamp'])
            if (now - ts).total_seconds() < 1800 and not h.get('success'):
                recent_fails += 1
        except:
            pass
    
    if recent_fails >= 3:
        risk_score += 30
        reasons.append(f"{recent_fails} failed attempts in last 30 minutes")
        details['rapid_fails'] = recent_fails
    elif recent_fails >= 1:
        risk_score += 10
        details['recent_fails'] = recent_fails
    
    # 4. Check for multiple IPs in last hour
    recent_ips = set()
    for h in history[:50]:
        try:
            ts = datetime.fromisoformat(h['timestamp'])
            if (now - ts).total_seconds() < 3600:
                recent_ips.add(h.get('ip_address', ''))
        except:
            pass
    
    if len(recent_ips) > 3:
        risk_score += 15
        reasons.append(f"Login from {len(recent_ips)} different IPs in last hour")
        details['multiple_ips'] = list(recent_ips)
    
    risk_score = min(risk_score, 100)
    
    return {
        'is_suspicious': risk_score >= 30,
        'risk_score': risk_score,
        'reasons': reasons,
        'details': details,
    }
