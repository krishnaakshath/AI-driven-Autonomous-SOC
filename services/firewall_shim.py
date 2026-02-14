"""
 Firewall Shim - Mock Persistence Layer for Active Response
==============================================================
Manages a JSON-based blocklist to simulate firewall rules.
Used by Playbooks and IP Blocking page to demonstrate "Active Response".

File: data/blocked_ips.json
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
BLOCKLIST_FILE = os.path.join(DATA_DIR, 'blocked_ips.json')

class FirewallShim:
    """
    Simulates a firewall management interface.
    Persists blocked IPs to a JSON file.
    """
    
    def __init__(self):
        self._ensure_data_dir()
        # Ensure file exists with empty list if not present
        if not os.path.exists(BLOCKLIST_FILE):
             self._save([])

    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def _load(self) -> List[Dict]:
        """Load blocklist from JSON."""
        if os.path.exists(BLOCKLIST_FILE):
            try:
                with open(BLOCKLIST_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load blocklist: {e}")
                return []
        return []

    def _save(self, blocklist: List[Dict]):
        """Save blocklist to JSON."""
        try:
            with open(BLOCKLIST_FILE, 'w') as f:
                json.dump(blocklist, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save blocklist: {e}")

    def block_ip(self, ip: str, reason: str = "Manual Block", source: str = "System") -> bool:
        """
        Block an IP address.
        
        Args:
            ip: IP address to block
            reason: Reason for blocking
            source: Source of the block (e.g., "Playbook", "User")
            
        Returns:
            bool: True if blocked (or already blocked), False on error
        """
        blocklist = self._load()
        
        # Check if already blocked
        for entry in blocklist:
            if entry['ip'] == ip:
                # Update existing entry
                entry['reason'] = reason
                entry['source'] = source
                entry['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save(blocklist)
                return True
        
        # Add new entry
        new_entry = {
            "ip": ip,
            "reason": reason,
            "source": source,
            "added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Active"
        }
        blocklist.append(new_entry)
        self._save(blocklist)
        logger.info(f"Blocked IP: {ip} ({reason})")
        return True

    def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address."""
        blocklist = self._load()
        initial_len = len(blocklist)
        blocklist = [entry for entry in blocklist if entry['ip'] != ip]
        
        if len(blocklist) < initial_len:
            self._save(blocklist)
            logger.info(f"Unblocked IP: {ip}")
            return True
        return False

    def is_blocked(self, ip: str) -> bool:
        """Check if an IP is currently blocked."""
        blocklist = self._load()
        for entry in blocklist:
            if entry['ip'] == ip and entry['status'] == "Active":
                return True
        return False

    def get_all_blocked_ips(self) -> List[Dict]:
        """Get list of all blocked IPs."""
        return self._load()

# Singleton Instance
firewall = FirewallShim()
