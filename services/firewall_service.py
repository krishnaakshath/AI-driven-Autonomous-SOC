import re
import json
from datetime import datetime
import uuid
from typing import Dict, List, Optional, Tuple

class FirewallService:
    """
    Active Application-Level Firewall (WAF).
    Processes requests and payloads to detect and block malicious hits.
    """
    
    def __init__(self):
        # Common WAF Attack Patterns
        self.patterns = {
            "SQL_INJECTION": [
                r"union.*select", r"select.*from", r"insert.*into", r"drop.*table",
                r"sleep\(.*\)", r"benchmark\(.*\)", r"'.*--", r"admin'--", r"'.*or.*1=1"
            ],
            "XSS": [
                r"<script.*>.*</script>", r"javascript:.*", r"onload=.*", r"onerror=.*",
                r"alert\(.*\)", r"<img.*src=.*>"
            ],
            "PATH_TRAVERSAL": [
                r"\.\./\.\./", r"/etc/passwd", r"/etc/shadow", r"c:\\windows"
            ]
        }
        # Stateful Tracking
        self.hit_tracker = {} # {ip: {count: N, last_hit: timestamp}}
        self.shun_threshold = 3 # 3 violations = perm block
        
    def scan_payload(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Scans a text payload for malicious patterns.
        Returns: (is_blocked, threat_type)
        """
        if not text:
            return False, None
            
        text_lower = str(text).lower()
        
        for threat_type, regex_list in self.patterns.items():
            for regex in regex_list:
                if re.search(regex, text_lower):
                    return True, threat_type
        
        return False, None

    def log_block(self, source_ip: str, threat_type: str, payload: str):
        """
        Logs a block to the SIEM and database.
        """
        try:
            from services.database import db
            
            event_id = f"EVT-FW-{str(uuid.uuid4())[:8]}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            event = {
                "id": event_id,
                "timestamp": timestamp,
                "source": "Firewall",
                "event_type": f"Active Block: {threat_type}",
                "severity": "CRITICAL",
                "source_ip": source_ip,
                "dest_ip": "127.0.0.1", # Internal WAF
                "user": "N/A",
                "status": "Resolved", # Automatically blocked
                "details": {
                    "reason": f"WAF Match - {threat_type}",
                    "blocked_payload": payload[:100] + ("..." if len(payload) > 100 else ""),
                    "action": "Dropped Request"
                }
            }
            
            # Insert into database
            db.insert_event(event)
            
            # Create a corresponding Alert
            alert = {
                "id": f"ALRT-FW-{str(uuid.uuid4())[:8]}",
                "timestamp": timestamp,
                "title": f"Firewall Protection: {threat_type}",
                "severity": "CRITICAL",
                "status": "New",
                "details": json.dumps(event)
            }
            db.insert_alert(alert)
            
        except Exception as e:
            print(f"Firewall logging error: {e}")

    def check_request(self, params: Dict, source_ip: str = "127.0.0.1") -> bool:
        """
        Checks all parameters in a request.
        Also implements STATEFUL AUTO-SHUN.
        """
        # 1. Check if IP is already shunned (Global Block)
        try:
            from services.database import db
            # Quick check against recently blocked IPs to simulate a shun list
            # In a full impl, we'd have a 'blacklist' table
            shunned_ips = [e.get("source_ip") for e in db.get_recent_events(limit=100) if "AUTO-SHUN" in e.get("event_type", "")]
            if source_ip in shunned_ips:
                return False
        except Exception:
            pass

        # 2. Scan payloads
        for key, value in params.items():
            is_blocked, threat = self.scan_payload(str(value))
            if is_blocked:
                # Update hit tracker
                stats = self.hit_tracker.get(source_ip, {"count": 0})
                stats["count"] += 1
                stats["last_hit"] = datetime.now()
                self.hit_tracker[source_ip] = stats
                
                # Check for SHUN threshold
                final_threat = threat
                if stats["count"] >= self.shun_threshold:
                    final_threat = f"PERMANENT AUTO-SHUN ({threat})"
                
                self.log_block(source_ip, final_threat, str(value))
                return False
                
        return True

# Singleton 
firewall = FirewallService()
