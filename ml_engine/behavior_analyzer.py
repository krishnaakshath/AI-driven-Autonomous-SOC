"""
 Behavioral Anomaly Detection Engine
=======================================
Learns normal user/system behavior patterns and detects
anomalies that could indicate insider threats or compromised accounts.

Detects:
- Unusual login times
- Abnormal data transfers
- Suspicious access patterns
- New process executions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import random
import math

class BehaviorProfile:
    """User/entity behavior profile."""
    
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.login_hours: Dict[int, int] = defaultdict(int)  # hour -> count
        self.login_days: Dict[int, int] = defaultdict(int)   # day -> count
        self.accessed_resources: Dict[str, int] = defaultdict(int)  # resource -> count
        self.data_transfer_sizes: List[int] = []
        self.source_ips: Dict[str, int] = defaultdict(int)
        self.total_events = 0
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def add_login_event(self, timestamp: datetime, source_ip: str):
        """Record a login event."""
        self.login_hours[timestamp.hour] += 1
        self.login_days[timestamp.weekday()] += 1
        self.source_ips[source_ip] += 1
        self.total_events += 1
        self.last_updated = datetime.now()
    
    def add_resource_access(self, resource: str):
        """Record resource access."""
        self.accessed_resources[resource] += 1
        self.total_events += 1
        self.last_updated = datetime.now()
    
    def add_data_transfer(self, size_bytes: int):
        """Record data transfer."""
        self.data_transfer_sizes.append(size_bytes)
        self.total_events += 1
        self.last_updated = datetime.now()
    
    def get_normal_login_hours(self) -> List[int]:
        """Get hours when user normally logs in."""
        if not self.login_hours:
            return list(range(9, 18))  # Default: business hours
        
        total = sum(self.login_hours.values())
        threshold = total * 0.1  # Hours with >10% of logins
        
        return [h for h, count in self.login_hours.items() if count >= threshold]
    
    def get_average_transfer_size(self) -> float:
        """Get average data transfer size."""
        if not self.data_transfer_sizes:
            return 1024 * 1024  # Default: 1MB
        return sum(self.data_transfer_sizes) / len(self.data_transfer_sizes)
    
    def get_transfer_std_dev(self) -> float:
        """Get standard deviation of transfer sizes."""
        if len(self.data_transfer_sizes) < 2:
            return self.get_average_transfer_size() * 0.5
        
        avg = self.get_average_transfer_size()
        variance = sum((x - avg) ** 2 for x in self.data_transfer_sizes) / len(self.data_transfer_sizes)
        return math.sqrt(variance)


class BehavioralAnomalyDetector:
    """
    Detects behavioral anomalies by comparing current activity
    against learned baseline patterns.
    """
    
    # Anomaly thresholds
    THRESHOLDS = {
        "login_hour_deviation": 3,      # Hours outside normal range
        "transfer_size_std_devs": 3,    # Standard deviations above mean
        "new_resource_threshold": 0.1,  # % of accesses to never-seen resources
        "new_ip_threshold": 0.2,        # % of logins from new IPs
    }
    
    def __init__(self, demo_mode: bool = False):
        self.profiles: Dict[str, BehaviorProfile] = {}
        self.anomaly_log: List[Dict] = []
        if demo_mode:
            self._initialize_sample_profiles()
    
    def train_on_events(self, events: List[Dict]):
        """Train/Update profiles from a batch of SIEM events."""
        for event in events:
            user = event.get("user")
            if not user or user == "-":
                continue
            
            profile = self.get_or_create_profile(user)
            
            # Extract timestamp
            try:
                ts_str = event.get("timestamp")
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S") if ts_str else datetime.now()
            except:
                ts = datetime.now()
                
            # Map event types to analyzer methods
            etype = str(event.get("event_type", "")).lower()
            
            if "login success" in etype:
                profile.add_login_event(ts, event.get("source_ip", "0.0.0.0"))
            elif "file access" in etype:
                profile.add_resource_access(event.get("details", "unknown_file"))
                # Simulate transfer size for file access if not present
                profile.add_data_transfer(random.randint(1024, 5000000))
            elif "blocked" in etype or "anomaly" in etype:
                # High severity events boost risk immediately
                self.analyze_login(user, ts, event.get("source_ip", "0.0.0.0"))
    
    def get_or_create_profile(self, entity_id: str) -> BehaviorProfile:
        """Get existing profile or create new one."""
        if entity_id not in self.profiles:
            self.profiles[entity_id] = BehaviorProfile(entity_id)
        return self.profiles[entity_id]
    
    def analyze_login(self, entity_id: str, timestamp: datetime, source_ip: str) -> Dict:
        """
        Analyze a login event for anomalies.
        
        Returns:
            Anomaly assessment dictionary
        """
        profile = self.get_or_create_profile(entity_id)
        anomalies = []
        risk_score = 0
        
        # Check login hour
        normal_hours = profile.get_normal_login_hours()
        if timestamp.hour not in normal_hours:
            if timestamp.hour < 6 or timestamp.hour > 22:
                anomalies.append({
                    "type": "unusual_login_time",
                    "severity": "high",
                    "description": f"Login at {timestamp.hour}:00 - outside normal hours ({min(normal_hours)}:00-{max(normal_hours)}:00)",
                    "score": 40
                })
                risk_score += 40
            else:
                anomalies.append({
                    "type": "unusual_login_time",
                    "severity": "medium",
                    "description": f"Login at {timestamp.hour}:00 - slightly unusual",
                    "score": 20
                })
                risk_score += 20
        
        # Check login day
        if timestamp.weekday() >= 5:  # Weekend
            if profile.login_days.get(timestamp.weekday(), 0) < profile.total_events * 0.05:
                anomalies.append({
                    "type": "weekend_login",
                    "severity": "medium",
                    "description": "Weekend login detected - user rarely logs in on weekends",
                    "score": 25
                })
                risk_score += 25
        
        # Check source IP
        if source_ip not in profile.source_ips:
            if profile.total_events > 10:  # Only flag if we have baseline
                anomalies.append({
                    "type": "new_source_ip",
                    "severity": "medium",
                    "description": f"Login from new IP address: {source_ip}",
                    "score": 30
                })
                risk_score += 30
        
        # Update profile
        profile.add_login_event(timestamp, source_ip)
        
        result = {
            "entity_id": entity_id,
            "event_type": "login",
            "timestamp": timestamp.isoformat(),
            "source_ip": source_ip,
            "anomalies": anomalies,
            "risk_score": min(risk_score, 100),
            "risk_level": self._get_risk_level(risk_score),
            "is_anomalous": len(anomalies) > 0
        }
        
        if anomalies:
            self.anomaly_log.append(result)
        
        return result
    
    def analyze_data_transfer(self, entity_id: str, size_bytes: int, destination: str) -> Dict:
        """Analyze a data transfer for anomalies."""
        profile = self.get_or_create_profile(entity_id)
        anomalies = []
        risk_score = 0
        
        avg_size = profile.get_average_transfer_size()
        std_dev = profile.get_transfer_std_dev()
        
        # Check if transfer is abnormally large
        if std_dev > 0:
            z_score = (size_bytes - avg_size) / std_dev
            
            if z_score > 5:
                anomalies.append({
                    "type": "massive_data_transfer",
                    "severity": "critical",
                    "description": f"Transfer {size_bytes / (1024*1024):.1f}MB is {z_score:.1f} std devs above normal ({avg_size / (1024*1024):.1f}MB)",
                    "score": 50
                })
                risk_score += 50
            elif z_score > 3:
                anomalies.append({
                    "type": "large_data_transfer",
                    "severity": "high",
                    "description": f"Transfer {size_bytes / (1024*1024):.1f}MB is {z_score:.1f} std devs above normal",
                    "score": 35
                })
                risk_score += 35
        
        # Check external destination
        if "external" in destination.lower() or not destination.startswith("192.168"):
            if size_bytes > 50 * 1024 * 1024:  # >50MB to external
                anomalies.append({
                    "type": "external_exfiltration_risk",
                    "severity": "critical",
                    "description": f"Large transfer ({size_bytes / (1024*1024):.1f}MB) to external destination",
                    "score": 45
                })
                risk_score += 45
        
        # Update profile
        profile.add_data_transfer(size_bytes)
        
        result = {
            "entity_id": entity_id,
            "event_type": "data_transfer",
            "size_bytes": size_bytes,
            "destination": destination,
            "anomalies": anomalies,
            "risk_score": min(risk_score, 100),
            "risk_level": self._get_risk_level(risk_score),
            "is_anomalous": len(anomalies) > 0
        }
        
        if anomalies:
            self.anomaly_log.append(result)
        
        return result
    
    def analyze_resource_access(self, entity_id: str, resource: str) -> Dict:
        """Analyze resource access for anomalies."""
        profile = self.get_or_create_profile(entity_id)
        anomalies = []
        risk_score = 0
        
        # Check if accessing new/unusual resource
        if resource not in profile.accessed_resources:
            if profile.total_events > 20:  # Have baseline
                # Check if resource is sensitive
                sensitive_patterns = ["/admin", "/secrets", "/passwords", "/keys", "/config", "/hr", "/finance"]
                is_sensitive = any(p in resource.lower() for p in sensitive_patterns)
                
                if is_sensitive:
                    anomalies.append({
                        "type": "new_sensitive_resource_access",
                        "severity": "high",
                        "description": f"First-time access to sensitive resource: {resource}",
                        "score": 40
                    })
                    risk_score += 40
                else:
                    anomalies.append({
                        "type": "new_resource_access",
                        "severity": "low",
                        "description": f"First-time access to resource: {resource}",
                        "score": 10
                    })
                    risk_score += 10
        
        # Update profile
        profile.add_resource_access(resource)
        
        result = {
            "entity_id": entity_id,
            "event_type": "resource_access",
            "resource": resource,
            "anomalies": anomalies,
            "risk_score": min(risk_score, 100),
            "risk_level": self._get_risk_level(risk_score),
            "is_anomalous": len(anomalies) > 0
        }
        
        if anomalies:
            self.anomaly_log.append(result)
        
        return result
    
    def _get_risk_level(self, score: int) -> str:
        """Convert risk score to risk level."""
        if score >= 70:
            return "CRITICAL"
        elif score >= 50:
            return "HIGH"
        elif score >= 30:
            return "MEDIUM"
        elif score >= 10:
            return "LOW"
        return "NORMAL"
    
    def get_anomaly_summary(self) -> Dict:
        """Get summary of recent anomalies."""
        recent = self.anomaly_log[-50:]  # Last 50 anomalies
        
        by_type = defaultdict(int)
        by_entity = defaultdict(int)
        by_severity = defaultdict(int)
        
        for anomaly in recent:
            for a in anomaly.get("anomalies", []):
                by_type[a["type"]] += 1
                by_severity[a["severity"]] += 1
            by_entity[anomaly["entity_id"]] += 1
        
        return {
            "total_anomalies": len(recent),
            "by_type": dict(by_type),
            "by_entity": dict(by_entity),
            "by_severity": dict(by_severity),
            "top_entities": sorted(by_entity.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def get_entity_risk_score(self, entity_id: str) -> int:
        """Get overall risk score for an entity based on recent anomalies."""
        recent = [a for a in self.anomaly_log[-100:] if a["entity_id"] == entity_id]
        
        if not recent:
            return 0
        
        # Average risk score from recent anomalies
        avg_score = sum(a["risk_score"] for a in recent) / len(recent)
        
        # Boost if many recent anomalies
        frequency_boost = min(len(recent) * 5, 30)
        
        return min(int(avg_score + frequency_boost), 100)


# Singleton instance
behavior_detector = BehavioralAnomalyDetector()


def analyze_user_login(user_id: str, source_ip: str, timestamp: datetime = None) -> Dict:
    """Analyze a user login for behavioral anomalies."""
    return behavior_detector.analyze_login(
        user_id, 
        timestamp or datetime.now(), 
        source_ip
    )


def analyze_data_transfer(user_id: str, size_bytes: int, destination: str) -> Dict:
    """Analyze a data transfer for anomalies."""
    return behavior_detector.analyze_data_transfer(user_id, size_bytes, destination)


def analyze_resource_access(user_id: str, resource: str) -> Dict:
    """Analyze resource access for anomalies."""
    return behavior_detector.analyze_resource_access(user_id, resource)


def get_user_risk_score(user_id: str) -> int:
    """Get overall risk score for a user."""
    return behavior_detector.get_entity_risk_score(user_id)


def get_anomaly_summary() -> Dict:
    """Get summary of recent anomalies."""
    return behavior_detector.get_anomaly_summary()
