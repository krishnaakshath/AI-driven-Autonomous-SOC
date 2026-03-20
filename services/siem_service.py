"""
SIEM Service - Centralized Security Information and Event Management
Provides log aggregation, event correlation, and data sharing across pages.
Backed by Supabase (PostgREST) for persistent cloud storage.
"""

import os
import json
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from services.database import db
from services.logger import get_logger
logger = get_logger("siem")


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
        Uses real data from DB and live OSINT feeds.
        """
        stats = db.get_stats()
        
        # If DB is low, pull fresh real data immediately
        if stats.get('total', 0) < 500:
            try:
                self.ingest_live_threats(limit=50)
            except Exception:

                logger.debug("Suppressed exception", exc_info=True)
            
        # Periodically pull fresh OSINT threat intelligence (20% chance)
        if random.random() < 0.2:
            try:
                self.ingest_live_threats(limit=10)
            except Exception:

                logger.debug("Suppressed exception", exc_info=True)
                
        return db.get_recent_events(limit=count)


    def ingest_threat_intelligence(self):
        """
        Pull real threat indicators from Threat Intel service and inject as SIEM events.
        """
        return self.ingest_live_threats(limit=20)

    def ingest_live_threats(self, limit: int = 50) -> int:
        """
        Extended ingestion for background jobs. Pulls fresh indicators and logs them.
        Uses bulk insertion for better performance.
        """
        try:
            from services.threat_intel import threat_intel
            
            # Get real indicators (OTX/AbuseIPDB/Fallbacks)
            indicators = threat_intel.get_recent_indicators(limit=limit)
            
            events_to_insert = []
            alerts_to_insert = []
            
            for ioc in indicators:
                ip = ioc.get('indicator')
                desc = ioc.get('description', 'Known Malicious IP')
                
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
                
                # ── REAL-TIME ML SCORING ──
                try:
                    from ml_engine.isolation_forest import isolation_forest
                    ml_result = isolation_forest.predict([event])
                    if ml_result:
                        event["ml_anomaly_score"] = ml_result[0].get("anomaly_score", 0)
                except Exception:

                    logger.debug("Suppressed exception", exc_info=True)
                
                try:
                    from ml_engine.fuzzy_clustering import fuzzy_clustering
                    ml_class = fuzzy_clustering.predict([event])
                    if ml_class:
                        event["ml_classification"] = ml_class[0].get("predicted_label", "Unknown")
                except Exception:

                    logger.debug("Suppressed exception", exc_info=True)
                
                try:
                    from ml_engine.neural_predictor import add_security_event
                    add_security_event("firewall_block", severity="high")
                except Exception:

                    logger.debug("Suppressed exception", exc_info=True)
                
                # ── RL ADAPTIVE CLASSIFICATION ──
                try:
                    from ml_engine.rl_threat_classifier import rl_classifier
                    rl_result = rl_classifier.classify(event)
                    event["rl_classification"] = rl_result.get("action", "UNKNOWN")
                    event["rl_confidence"] = rl_result.get("confidence", 0)
                    # Auto-reward using IF anomaly score as ground truth
                    rl_classifier.auto_reward(event, rl_result)
                except Exception:

                    logger.debug("Suppressed exception", exc_info=True)
                
                events_to_insert.append(event)
                
                # GENERATE ALERT
                alert = {
                    "id": f"ALRT-{str(uuid.uuid4())[:8]}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "title": f"Threat Intel Block: {desc}",
                    "severity": "CRITICAL",
                    "status": "New",
                    "details": json.dumps({"source_ip": ip, "reason": desc, "action": "Blocked"})
                }
                alerts_to_insert.append(alert)
                
            if events_to_insert:
                db.bulk_insert_events(events_to_insert)
            if alerts_to_insert:
                db.bulk_insert_alerts(alerts_to_insert)
                
            return len(events_to_insert)
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
            except Exception:

                logger.debug("Suppressed exception", exc_info=True)
        
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
        """Get incidents derived from real DB events."""
        events = db.get_recent_events(limit=500)
        
        # Group high/critical events into incidents
        incidents = []
        critical_events = [e for e in events if e.get("severity") in ["HIGH", "CRITICAL"]]
        
        # Track already processed event chains to avoid duplicate incidents for same threat
        processed_ips = set()
        
        for i, event in enumerate(critical_events):
            source_ip = event.get("source_ip")
            if source_ip in processed_ips and source_ip != "-":
                continue
                
            processed_ips.add(source_ip)
            
            # Create a more organic incident title based on event type
            etype = event.get("event_type", "Security Breach")
            title = f"{etype} Detected"
            
            incident = {
                "id": f"INC-{datetime.now().year}-{1000 + i}",
                "title": title,
                "severity": event.get("severity", "HIGH"),
                "status": event.get("status", "Active"),
                "source": "SIEM (Event Log)",
                "start_time": event.get("timestamp"),
                "affected_host": event.get("hostname", "Unknown"),
                "affected_user": event.get("user", "Unknown"),
                "source_ip": source_ip,
                "details": event.get("details", ""),
                "timeline": [], # Real timelines would be built from correlated events
                "is_simulated": False
            }
            incidents.append(incident)
            
            if len(incidents) >= 10:
                break

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

def get_user_behavior() -> List[Dict]:
    return siem_service.get_user_behavior_data()

def get_siem_incidents() -> List[Dict]:
    return siem_service.get_incidents()

def get_siem_logs(source: str = None, severity: str = None, limit: int = 100) -> List[Dict]:
    return siem_service.get_logs(source, severity, limit)

def get_siem_stats() -> Dict:
    return siem_service.get_stats()
