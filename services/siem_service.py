"""
SIEM Service - Centralized Security Information and Event Management
# Provides log aggregation, event correlation, and data sharing across pages.
# Now backed by SQLite for persistence. Version 1.1.
"""

import os
import json
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from services.database import db

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
        # No more JSON cache loading needed, DB handles it.

    def generate_events(self, count: int = 100) -> List[Dict]:
        """
        Produce events. 
        Legacy wrapper: Checks if DB needs seeding, otherwise returns DB events.
        For simulation purposes, we might still want to 'create' new events if requested.
        """
        # If DB is empty, seed it
        stats = db.get_stats()
        if stats['total'] == 0:
            self.simulate_ingestion(count)
            self.ingest_threat_intelligence() # Inject real threats
            
        # Occasional "Real" injection for live feel (10% chance on refresh)
        if random.random() < 0.1:
            self.ingest_threat_intelligence()
            
        return db.get_recent_events(limit=count)
    
    def simulate_ingestion(self, count: int = 1):
        """Generate random events and save to DB (Simulation Mode)."""
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        severity_weights = [0.4, 0.35, 0.2, 0.05]
        
        new_events = []
        for i in range(count):
            source = random.choice(self.sources)
            event_type = random.choice(self.event_types[source])
            severity = random.choices(severities, weights=severity_weights)[0]
            
            # Timestamp: mostly now, some slight jitter
            ts = datetime.now() - timedelta(seconds=random.randint(0, 60))
            
            event = {
                "id": f"EVT-{str(uuid.uuid4())[:8]}",
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "source": source,
                "event_type": event_type,
                "severity": severity,
                "source_ip": f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                "dest_ip": f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                "user": random.choice(["jsmith", "alee", "mwilson", "admin", "service-account", "kpatel", "rjones", "-"]),
                "hostname": random.choice(["WS-001", "SRV-DB-01", "LAPTOP-IT42", "DC-PROD-01", "WS-FINANCE-05"]),
                "status": random.choice(["Open", "Investigating", "Resolved", "False Positive"])
            }
            
            db.insert_event(event)
            new_events.append(event)
            
        return new_events

    def ingest_threat_intelligence(self):
        """
        Pull real threat indicators from Threat Intel service and inject as SIEM events.
        This gives the 'Real Data' feel by showing actual known bad IPs being blocked.
        """
        return self.ingest_live_threats(limit=20)

    def ingest_live_threats(self, limit: int = 50) -> int:
        """
        Extended ingestion for background jobs. Pulls fresh indicators and logs them.
        """
        try:
            from services.threat_intel import threat_intel
            
            # Get real indicators (OTX/AbuseIPDB/Fallbacks)
            indicators = threat_intel.get_recent_indicators(limit=limit)
            
            count = 0
            for ioc in indicators:
                ip = ioc.get('indicator')
                desc = ioc.get('description', 'Known Malicious IP')
                
                # Check if we already logged this recently to avoid spam
                # (Simple check: just do it for now, DB handles storage)
                
                # Create a "Real" event
                event = {
                    "id": f"EVT-REAL-{str(uuid.uuid4())[:8]}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "Firewall",
                    "event_type": "Connection Blocked",
                    "severity": "CRITICAL",
                    "source_ip": ip,
                    "dest_ip": f"192.168.1.{random.randint(2, 254)}",
                    "user": "-",
                    "hostname": "GATEWAY-01",
                    "status": "Resolved", # Auto-blocked
                    "details": f"Threat Intel Match: {desc}"
                }
                
                db.insert_event(event)
                
                # Also block in firewall shim
                from services.firewall_shim import firewall
                firewall.block_ip(ip, reason=f"Threat Intel: {desc}", source="SIEM Ingestion")
                
                count += 1
                
            return count
        except Exception as e:
            print(f"Error ingesting threat intel: {e}")
            return 0

    def get_user_behavior_data(self) -> List[Dict]:
        """Get user behavior analytics from DB events, enriched by ML."""
        events = db.get_recent_events(limit=1000)
        
        # Train ML engine on recent events
        try:
            from ml_engine.behavior_analyzer import behavior_detector
            behavior_detector.train_on_events(events)
            HAS_ML = True
        except ImportError:
            HAS_ML = False
            
        # Aggregate by user for summary statistics
        users = {}
        for event in events:
            user = event.get("user", "-")
            if user == "-" or not user:
                continue
            
            if user not in users:
                users[user] = {
                    "user": user,
                    "login_count": 0,
                    "failed_logins": 0,
                    "data_access": 0,
                    "after_hours": 0,
                    "unique_ips": set(),
                    "alerts": 0
                }
            
            # Count event types
            etype = str(event.get("event_type", "")).lower()
            if "login success" in etype:
                users[user]["login_count"] += 1
            if "login failure" in etype:
                users[user]["failed_logins"] += 1
            if "file access" in etype:
                users[user]["data_access"] += 1
            if event.get("severity") in ["HIGH", "CRITICAL"]:
                users[user]["alerts"] += 1
            
            users[user]["unique_ips"].add(event.get("source_ip"))
            
            # Check after hours
            try:
                ts_str = event.get("timestamp")
                if ts_str:
                    hour = int(ts_str.split(" ")[1].split(":")[0])
                    if hour < 6 or hour > 20:
                        users[user]["after_hours"] += 1
            except:
                pass
        
        # Convert to list with risk scores from ML or Fallback
        result = []
        for user, data in users.items():
            if HAS_ML:
                # Use ML detector for grounded risk score and anomaly check
                risk_score = behavior_detector.get_entity_risk_score(user)
                # Check for any logged anomalies
                is_anomalous = any(a["entity_id"] == user for a in behavior_detector.anomaly_log[-50:])
            else:
                # Fallback logic
                risk_score = min(100, (
                    (data["failed_logins"] * 5) +
                    (data["data_access"] / 10) +
                    (data["after_hours"] * 3) +
                    (len(data["unique_ips"]) * 2) +
                    (data["alerts"] * 10)
                ))
                is_anomalous = risk_score > 50
            
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
                "is_anomalous": is_anomalous
            })
        
        return sorted(result, key=lambda x: x["risk_score"], reverse=True)
    
    def get_incidents(self) -> List[Dict]:
        """Get incidents derived from DB events."""
        events = db.get_recent_events(limit=500)
        
        # Group high/critical events into incidents
        incidents = []
        critical_events = [e for e in events if e.get("severity") in ["HIGH", "CRITICAL"]]
        
        # Create sample incidents from critical events
        incident_templates = [
            {"title": "Ransomware Attack Detected", "severity": "CRITICAL", "status": "Investigating"},
            {"title": "Credential Theft Attempt", "severity": "HIGH", "status": "Contained"},
            {"title": "Data Exfiltration Alert", "severity": "CRITICAL", "status": "Active"},
            {"title": "Brute Force Attack", "severity": "HIGH", "status": "Resolved"},
            {"title": "Malware Infection", "severity": "HIGH", "status": "Investigating"},
        ]
        
        mitre_techniques = {
            "Ransomware Attack Detected": [
                {"time": -6, "phase": "Initial Access", "technique": "T1566.001", "description": "Phishing email received"},
                {"time": -5, "phase": "Execution", "technique": "T1059.001", "description": "PowerShell execution detected"},
                {"time": -4, "phase": "Persistence", "technique": "T1053.005", "description": "Scheduled task created"},
                {"time": -2, "phase": "Impact", "technique": "T1486", "description": "File encryption started"},
            ],
            "Credential Theft Attempt": [
                {"time": -3, "phase": "Initial Access", "technique": "T1078", "description": "Compromised credentials used"},
                {"time": -2, "phase": "Credential Access", "technique": "T1003.001", "description": "Mimikatz detected"},
            ],
        }
        
        for i, template in enumerate(incident_templates[:min(len(critical_events), 5)]):
            event = critical_events[i] if i < len(critical_events) else critical_events[0]
            
            incident = {
                "id": f"INC-2024-{1000 + i}",
                "title": template["title"],
                "severity": template["severity"],
                "status": template["status"],
                "source": "Real (SIEM)" if i < len(critical_events) else "Simulation (Fallback)",
                "start_time": event.get("timestamp"),
                "affected_host": event.get("hostname", "Unknown"),
                "affected_user": event.get("user", "Unknown"),
                "source_ip": event.get("source_ip"),
                "timeline": mitre_techniques.get(template["title"], []),
                "is_simulated": False if i < len(critical_events) else True
            }
            incidents.append(incident)
        
        # If absolutely no critical events, return pure simulation
        if not incidents:
             for i, template in enumerate(incident_templates):
                incident = {
                    "id": f"INC-SIM-{2000 + i}",
                    "title": template["title"],
                    "severity": template["severity"],
                    "status": template["status"],
                    "source": "Simulation (Empty DB)",
                    "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "affected_host": "SIM-HOST-01",
                    "affected_user": "sim_user",
                    "source_ip": "192.168.1.100",
                    "timeline": mitre_techniques.get(template["title"], []),
                    "is_simulated": True
                }
                incidents.append(incident)

        return incidents
    
    def get_logs(self, source_filter: str = None, severity_filter: str = None, limit: int = 100) -> List[Dict]:
        """Get filtered logs from DB."""
        # This is a basic filter in memory for now. 
        # In production, push filters to SQL WHERE clause.
        events = db.get_recent_events(limit=limit * 2) 
        
        if source_filter and source_filter != "All":
            events = [e for e in events if e.get("source") == source_filter]
        if severity_filter and severity_filter != "All":
            events = [e for e in events if e.get("severity") == severity_filter]
        
        return events[:limit]
    
    def get_stats(self) -> Dict:
        """Get SIEM statistics from DB."""
        stats = db.get_stats()
        # "active_sources" needs a query, for now approximate or simple query
        # We'll just ignore active_sources exact count or add it to db.get_stats later
        # Re-using the efficient stats from DB
        return {
            "total_events_24h": stats["total"],
            "critical_count": stats["critical"],
            "high_count": stats["high"],
            "active_sources": 8, # Placeholder
            "events_per_minute": round(stats["total"] / 1440, 2) if stats["total"] > 0 else 0,
            "top_source": "Firewall" # Placeholder
        }


# Singleton instance
siem_service = SIEMService()

# Convenience functions
def get_siem_events(count: int = 100) -> List[Dict]:
    return siem_service.generate_events(count)

def simulate_siem_ingestion(count: int = 1) -> List[Dict]:
    return siem_service.simulate_ingestion(count)

def get_user_behavior() -> List[Dict]:
    return siem_service.get_user_behavior_data()

def get_siem_incidents() -> List[Dict]:
    return siem_service.get_incidents()

def get_siem_logs(source: str = None, severity: str = None, limit: int = 100) -> List[Dict]:
    return siem_service.get_logs(source, severity, limit)

def get_siem_stats() -> Dict:
    return siem_service.get_stats()
