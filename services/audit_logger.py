"""
Audit Logger — Centralized Security Audit Trail
=================================================
Logs privilege-sensitive actions: role changes, firewall blocks,
user management, authentication events.
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
AUDIT_FILE = os.path.join(DATA_DIR, "audit_log.json")

# Keep last N entries in the file to prevent unbounded growth
MAX_ENTRIES = 10_000


class AuditLogger:
    """Append-only audit logger backed by JSON file + optional DB."""

    CATEGORIES = {
        "AUTH": "Authentication",
        "ROLE": "Role Change",
        "FIREWALL": "Firewall Action",
        "USER_MGMT": "User Management",
        "CONFIG": "Configuration Change",
        "DATA": "Data Access",
    }

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def log(
        self,
        category: str,
        action: str,
        actor: str = "system",
        target: Optional[str] = None,
        details: Optional[Dict] = None,
        severity: str = "INFO",
    ):
        """
        Record an audit event.

        Args:
            category: One of CATEGORIES keys (AUTH, ROLE, FIREWALL, etc.)
            action:   Human-readable action description
            actor:    Who performed the action (email or 'system')
            target:   Who/what was affected (IP, email, etc.)
            details:  Extra context dict
            severity: INFO, WARNING, CRITICAL
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "action": action,
            "actor": actor,
            "target": target,
            "severity": severity,
            "details": details or {},
        }

        # Write to file
        self._append_to_file(entry)

        # Also write to DB if available
        self._write_to_db(entry)

    def _append_to_file(self, entry: Dict):
        try:
            entries = self._load_file()
            entries.append(entry)
            # Trim to MAX_ENTRIES
            if len(entries) > MAX_ENTRIES:
                entries = entries[-MAX_ENTRIES:]
            with open(AUDIT_FILE, "w") as f:
                json.dump(entries, f, indent=2)
        except Exception as e:
            print(f"Audit file write error: {e}")

    def _write_to_db(self, entry: Dict):
        try:
            from services.database import db
            import uuid
            db.insert_event({
                "id": f"AUDIT-{str(uuid.uuid4())[:8]}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "AuditLog",
                "event_type": f"[{entry['category']}] {entry['action']}",
                "severity": "LOW" if entry["severity"] == "INFO" else entry["severity"],
                "source_ip": "127.0.0.1",
                "dest_ip": "127.0.0.1",
                "user": entry["actor"],
                "status": "Logged",
            })
        except Exception:
            pass  # DB logging is best-effort

    def _load_file(self) -> List[Dict]:
        if not os.path.exists(AUDIT_FILE):
            return []
        try:
            with open(AUDIT_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def get_recent(self, limit: int = 100, category: Optional[str] = None) -> List[Dict]:
        """Get recent audit entries, optionally filtered by category."""
        entries = self._load_file()
        if category:
            entries = [e for e in entries if e.get("category") == category]
        return entries[-limit:]


# Singleton
audit_logger = AuditLogger()
