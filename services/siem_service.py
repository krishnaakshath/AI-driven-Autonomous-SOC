"""
SIEM Service - Centralized Security Information and Event Management
Provides log aggregation, event correlation, and data sharing across pages.
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Cache file for persistent SIEM data
SIEM_CACHE_FILE = ".siem_cache.json"

class SIEMService:
    """Centralized SIEM service for log aggregation and event correlation."""
    
    def __init__(self):
        self.sources = ["Firewall", "IDS/IPS", "Endpoint", "Active Directory", "Web Server", "DNS", "Email Gateway", "VPN"]
        self.event_types = {
            "Firewall": ["Connection Blocked", "Port Scan Detected", "Rule Violation", "NAT Translation"],
            "IDS/IPS": ["Signature Match", "Anomaly Detected", "Protocol Violation", "Malicious Payload"],
            "Endpoint": ["Process Execution", "File Access", "Registry Change", "Service Started"],
            "Active Directory": ["Login Success", "Login Failure", "Password Change", "Group Modification"],
            "Web Server": ["HTTP 404", "HTTP 500", "SQL Injection Attempt", "XSS Attempt"],
            "DNS": ["Query", "Zone Transfer", "DNS Tunneling", "DGA Detection"],
            "Email Gateway": ["Spam Blocked", "Phishing Detected", "Malware Attachment", "SPF Failure"],
            "VPN": ["Connection Established", "Connection Failed", "MFA Success", "Unusual Location"]
        }
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cached SIEM data."""
        try:
            if os.path.exists(SIEM_CACHE_FILE):
                with open(SIEM_CACHE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"events": [], "incidents": [], "users": {}, "last_update": None}
    
    def _save_cache(self):
        """Save SIEM data to cache."""
        try:
            with open(SIEM_CACHE_FILE, 'w') as f:
                json.dump(self.cache, f)
        except:
            pass
    
    def generate_events(self, count: int = 100) -> List[Dict]:
        """Generate or retrieve SIEM events."""
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        severity_weights = [0.4, 0.35, 0.2, 0.05]
        
        events = []
        for i in range(count):
            source = random.choice(self.sources)
            event_type = random.choice(self.event_types[source])
            severity = random.choices(severities, weights=severity_weights)[0]
            
            events.append({
                "id": f"EVT-{100000 + i}",
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 1440))).strftime("%Y-%m-%d %H:%M:%S"),
                "source": source,
                "event_type": event_type,
                "severity": severity,
                "source_ip": f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                "dest_ip": f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                "user": random.choice(["jsmith", "alee", "mwilson", "admin", "service-account", "kpatel", "rjones", "-"]),
                "hostname": random.choice(["WS-001", "SRV-DB-01", "LAPTOP-IT42", "DC-PROD-01", "WS-FINANCE-05"]),
                "status": random.choice(["Open", "Investigating", "Resolved", "False Positive"])
            })
        
        return sorted(events, key=lambda x: x["timestamp"], reverse=True)
    
    def get_user_behavior_data(self) -> List[Dict]:
        """Get user behavior analytics from SIEM events."""
        events = self.generate_events(500)
        
        # Aggregate by user
        users = {}
        for event in events:
            user = event.get("user", "-")
            if user == "-":
                continue
            
            if user not in users:
                users[user] = {
                    "user": user,
                    "login_count": 0,
                    "failed_logins": 0,
                    "data_access": 0,
                    "after_hours": 0,
                    "unique_ips": set(),
                    "alerts": 0,
                    "events": []
                }
            
            users[user]["events"].append(event)
            
            # Count event types
            if "Login Success" in event["event_type"]:
                users[user]["login_count"] += 1
            if "Login Failure" in event["event_type"]:
                users[user]["failed_logins"] += 1
            if "File Access" in event["event_type"]:
                users[user]["data_access"] += 1
            if event["severity"] in ["HIGH", "CRITICAL"]:
                users[user]["alerts"] += 1
            
            users[user]["unique_ips"].add(event["source_ip"])
            
            # Check after hours (simulated - check hour)
            try:
                hour = int(event["timestamp"].split(" ")[1].split(":")[0])
                if hour < 6 or hour > 20:
                    users[user]["after_hours"] += 1
            except:
                pass
        
        # Convert to list with risk scores
        result = []
        for user, data in users.items():
            risk_score = min(100, (
                (data["failed_logins"] * 5) +
                (data["data_access"] / 10) +
                (data["after_hours"] * 3) +
                (len(data["unique_ips"]) * 2) +
                (data["alerts"] * 10)
            ))
            
            result.append({
                "user": user,
                "department": random.choice(["IT", "Finance", "HR", "Sales", "Engineering"]),
                "login_count": data["login_count"],
                "failed_logins": data["failed_logins"],
                "data_access": data["data_access"],
                "after_hours_activity": data["after_hours"],
                "unique_ips": len(data["unique_ips"]),
                "high_severity_alerts": data["alerts"],
                "risk_score": round(risk_score, 1),
                "is_anomalous": risk_score > 50
            })
        
        return sorted(result, key=lambda x: x["risk_score"], reverse=True)
    
    def get_incidents(self) -> List[Dict]:
        """Get incidents derived from SIEM events."""
        events = self.generate_events(200)
        
        # Group high/critical events into incidents
        incidents = []
        critical_events = [e for e in events if e["severity"] in ["HIGH", "CRITICAL"]]
        
        # Create sample incidents from critical events
        incident_templates = [
            {"title": "Ransomware Attack Detected", "severity": "CRITICAL", "status": "Investigating"},
            {"title": "Credential Theft Attempt", "severity": "HIGH", "status": "Contained"},
            {"title": "Data Exfiltration Alert", "severity": "CRITICAL", "status": "Active"},
            {"title": "Brute Force Attack", "severity": "HIGH", "status": "Resolved"},
            {"title": "Malware Infection", "severity": "HIGH", "status": "Investigating"},
            {"title": "Insider Threat Activity", "severity": "CRITICAL", "status": "Escalated"},
        ]
        
        mitre_techniques = {
            "Ransomware Attack Detected": [
                {"time": -6, "phase": "Initial Access", "technique": "T1566.001", "description": "Phishing email received"},
                {"time": -5, "phase": "Execution", "technique": "T1059.001", "description": "PowerShell execution detected"},
                {"time": -4, "phase": "Persistence", "technique": "T1053.005", "description": "Scheduled task created"},
                {"time": -2, "phase": "Impact", "technique": "T1486", "description": "File encryption started"},
                {"time": -1, "phase": "Detection", "technique": "-", "description": "EDR alert triggered"},
            ],
            "Credential Theft Attempt": [
                {"time": -3, "phase": "Initial Access", "technique": "T1078", "description": "Compromised credentials used"},
                {"time": -2, "phase": "Credential Access", "technique": "T1003.001", "description": "Mimikatz detected"},
                {"time": -1, "phase": "Detection", "technique": "-", "description": "Anomaly detected by UBA"},
            ],
        }
        
        for i, template in enumerate(incident_templates[:min(len(critical_events), 5)]):
            event = critical_events[i] if i < len(critical_events) else critical_events[0]
            
            incident = {
                "id": f"INC-2024-{1000 + i}",
                "title": template["title"],
                "severity": template["severity"],
                "status": template["status"],
                "source": event["source"],
                "start_time": event["timestamp"],
                "affected_host": event.get("hostname", "Unknown"),
                "affected_user": event.get("user", "Unknown"),
                "source_ip": event["source_ip"],
                "timeline": mitre_techniques.get(template["title"], [
                    {"time": -2, "phase": "Detection", "technique": "-", "description": f"Event detected: {event['event_type']}"},
                    {"time": -1, "phase": "Analysis", "technique": "-", "description": "Investigating alert"},
                ])
            }
            incidents.append(incident)
        
        return incidents
    
    def get_logs(self, source_filter: str = None, severity_filter: str = None, limit: int = 100) -> List[Dict]:
        """Get filtered logs from SIEM."""
        events = self.generate_events(limit * 2)
        
        if source_filter and source_filter != "All":
            events = [e for e in events if e["source"] == source_filter]
        if severity_filter and severity_filter != "All":
            events = [e for e in events if e["severity"] == severity_filter]
        
        return events[:limit]
    
    def get_stats(self) -> Dict:
        """Get SIEM statistics."""
        events = self.generate_events(100)
        
        return {
            "total_events_24h": len(events),
            "critical_count": len([e for e in events if e["severity"] == "CRITICAL"]),
            "high_count": len([e for e in events if e["severity"] == "HIGH"]),
            "active_sources": len(set(e["source"] for e in events)),
            "events_per_minute": round(len(events) / 1440, 2),
            "top_source": max(set(e["source"] for e in events), key=lambda x: len([e for e in events if e["source"] == x]))
        }


# Singleton instance
siem_service = SIEMService()

# Convenience functions
def get_siem_events(count: int = 100) -> List[Dict]:
    return siem_service.generate_events(count)

def get_user_behavior() -> List[Dict]:
    return siem_service.get_user_behavior_data()

def get_siem_incidents() -> List[Dict]:
    return siem_service.get_incidents()

def get_siem_logs(source: str = None, severity: str = None, limit: int = 100) -> List[Dict]:
    return siem_service.get_logs(source, severity, limit)

def get_siem_stats() -> Dict:
    return siem_service.get_stats()
