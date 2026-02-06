"""
👤 User Data Service
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
