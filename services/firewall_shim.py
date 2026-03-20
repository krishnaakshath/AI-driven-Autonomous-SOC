"""
Firewall Shim — IP Blocklist Manager
=====================================
Provides block_ip / unblock_ip / is_blocked API backed by a JSON file.
Used by the AI assistant and Firewall Control page.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from services.logger import get_logger
logger = get_logger("firewall_shim")


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
BLOCKLIST_FILE = os.path.join(DATA_DIR, "firewall_blocklist.json")


class FirewallShim:
    """Stateful IP blocklist backed by a JSON file."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    # ── persistence ──────────────────────────────────────────────────────────

    def _load(self) -> List[Dict]:
        if not os.path.exists(BLOCKLIST_FILE):
            return []
        try:
            with open(BLOCKLIST_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save(self, data: List[Dict]):
        with open(BLOCKLIST_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # ── public API ───────────────────────────────────────────────────────────

    def block_ip(self, ip: str, reason: str = "Manual block") -> bool:
        """Add an IP to the blocklist. Returns True on success."""
        blocklist = self._load()
        # Don't duplicate
        if any(entry["ip"] == ip and entry["status"] == "Active" for entry in blocklist):
            return False
        blocklist.append({
            "ip": ip,
            "reason": reason,
            "status": "Active",
            "blocked_at": datetime.now().isoformat(),
        })
        self._save(blocklist)

        # Log to DB
        try:
            from services.database import db
            import uuid
            db.insert_event({
                "id": f"EVT-FW-{str(uuid.uuid4())[:8]}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Firewall",
                "event_type": f"IP Blocked: {ip}",
                "severity": "HIGH",
                "source_ip": ip,
                "dest_ip": "0.0.0.0",
                "user": "system",
                "status": "Resolved",
            })
        except Exception:

            logger.debug("Suppressed exception", exc_info=True)
        return True

    def unblock_ip(self, ip: str) -> bool:
        """Remove an IP from the active blocklist. Returns True if found."""
        blocklist = self._load()
        new_list = [e for e in blocklist if e["ip"] != ip]
        if len(new_list) == len(blocklist):
            return False
        self._save(new_list)
        return True

    def is_blocked(self, ip: str) -> bool:
        """Check if an IP is actively blocked."""
        return any(
            entry["ip"] == ip and entry.get("status") == "Active"
            for entry in self._load()
        )

    def get_blocklist(self) -> List[Dict]:
        """Return full active blocklist."""
        return [e for e in self._load() if e.get("status") == "Active"]

    def get_all(self) -> List[Dict]:
        """Return all entries including disabled."""
        return self._load()


# Singleton
firewall = FirewallShim()
