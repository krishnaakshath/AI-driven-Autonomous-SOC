"""
 Natural Language Query Engine
=================================
Translates natural language queries into structured data lookups.
Enables threat hunting with plain English commands.

Examples:
- "Show me all failed logins from Russia"
- "Find connections to known C2 servers"
- "What happened in the last 24 hours?"
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

class NaturalLanguageQueryEngine:
    """
    Parses natural language security queries and returns structured results.
    """
    
    # Time pattern keywords
    TIME_PATTERNS = {
        r"last (\d+) hours?": lambda m: timedelta(hours=int(m.group(1))),
        r"last (\d+) minutes?": lambda m: timedelta(minutes=int(m.group(1))),
        r"last (\d+) days?": lambda m: timedelta(days=int(m.group(1))),
        r"today": lambda m: timedelta(hours=datetime.now().hour),
        r"yesterday": lambda m: timedelta(days=1),
        r"this week": lambda m: timedelta(days=datetime.now().weekday()),
        r"past hour": lambda m: timedelta(hours=1),
        r"recent": lambda m: timedelta(hours=1),
    }
    
    # Event type keywords
    EVENT_KEYWORDS = {
        "login": ["login", "sign in", "authentication", "auth"],
        "failed_login": ["failed login", "login failure", "failed auth", "bad password", "wrong password"],
        "port_scan": ["port scan", "scanning", "nmap", "reconnaissance"],
        "malware": ["malware", "virus", "trojan", "ransomware", "worm"],
        "ddos": ["ddos", "denial of service", "flood", "dos attack"],
        "data_transfer": ["data transfer", "upload", "download", "exfil", "exfiltration"],
        "firewall": ["firewall", "blocked", "denied", "dropped"],
        "alert": ["alert", "warning", "critical", "incident"],
        "connection": ["connection", "connect", "network", "traffic"],
    }
    
    # Geographic keywords
    GEO_KEYWORDS = {
        "russia": ["russia", "russian", "ru", "moscow"],
        "china": ["china", "chinese", "cn", "beijing"],
        "north_korea": ["north korea", "dprk", "pyongyang"],
        "iran": ["iran", "iranian", "tehran"],
        "usa": ["usa", "united states", "america", "us"],
        "europe": ["europe", "eu", "european"],
        "asia": ["asia", "asian"],
    }
    
    # Action keywords
    ACTION_KEYWORDS = {
        "show": ["show", "display", "list", "get", "find", "search"],
        "count": ["count", "how many", "number of", "total"],
        "block": ["block", "blacklist", "deny", "drop"],
        "investigate": ["investigate", "analyze", "examine", "look into"],
        "report": ["report", "summary", "generate report"],
    }
    
    def __init__(self):
        self.query_history: List[Dict] = []
    
    def parse_query(self, query: str) -> Dict:
        """
        Parse a natural language query into structured components.
        
        Args:
            query: Natural language query string
            
        Returns:
            Structured query dictionary
        """
        query_lower = query.lower().strip()
        
        parsed = {
            "original_query": query,
            "action": self._extract_action(query_lower),
            "event_type": self._extract_event_type(query_lower),
            "time_range": self._extract_time_range(query_lower),
            "geo_filter": self._extract_geo_filter(query_lower),
            "ip_addresses": self._extract_ips(query_lower),
            "severity": self._extract_severity(query_lower),
            "limit": self._extract_limit(query_lower),
        }
        
        self.query_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "parsed": parsed
        })
        
        return parsed
    
    def _extract_action(self, query: str) -> str:
        """Extract the intended action from the query."""
        for action, keywords in self.ACTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return action
        return "show"  # Default action
    
    def _extract_event_type(self, query: str) -> Optional[str]:
        """Extract the event type from the query."""
        for event_type, keywords in self.EVENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return event_type
        return None
    
    def _extract_time_range(self, query: str) -> Dict:
        """Extract time range from the query."""
        now = datetime.now()
        
        for pattern, delta_func in self.TIME_PATTERNS.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                delta = delta_func(match)
                return {
                    "start": (now - delta).isoformat(),
                    "end": now.isoformat(),
                    "description": match.group(0)
                }
        
        # Default: last 24 hours
        return {
            "start": (now - timedelta(hours=24)).isoformat(),
            "end": now.isoformat(),
            "description": "last 24 hours (default)"
        }
    
    def _extract_geo_filter(self, query: str) -> Optional[str]:
        """Extract geographic filter from the query."""
        for geo, keywords in self.GEO_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return geo
        return None
    
    def _extract_ips(self, query: str) -> List[str]:
        """Extract IP addresses from the query."""
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        return re.findall(ip_pattern, query)
    
    def _extract_severity(self, query: str) -> Optional[str]:
        """Extract severity level from the query."""
        if any(word in query for word in ["critical", "severe", "emergency"]):
            return "critical"
        elif any(word in query for word in ["high", "important", "urgent"]):
            return "high"
        elif any(word in query for word in ["medium", "moderate", "warning"]):
            return "medium"
        elif any(word in query for word in ["low", "minor", "info"]):
            return "low"
        return None
    
    def _extract_limit(self, query: str) -> int:
        """Extract result limit from the query."""
        match = re.search(r'(?:top|first|last|limit)\s*(\d+)', query, re.IGNORECASE)
        if match:
            return min(int(match.group(1)), 100)  # Cap at 100
        
        match = re.search(r'(\d+)\s*(?:results?|records?|entries?|events?)', query, re.IGNORECASE)
        if match:
            return min(int(match.group(1)), 100)
        
        return 20  # Default limit
    
    def execute_query(self, query: str) -> Dict:
        """
        Execute a natural language query and return results.
        
        Args:
            query: Natural language query string
            
        Returns:
            Query results with matching events
        """
        parsed = self.parse_query(query)
        
        # Generate simulated results based on parsed query
        results = self._generate_results(parsed)
        
        return {
            "parsed_query": parsed,
            "result_count": len(results),
            "results": results,
            "summary": self._generate_summary(parsed, results)
        }
    
    def _generate_results(self, parsed: Dict) -> List[Dict]:
        """Generate simulated results based on parsed query."""
        import random
        
        event_type = parsed.get("event_type") or "security_event"
        geo = parsed.get("geo_filter")
        limit = parsed.get("limit", 20)
        
        results = []
        
        # Geo-specific IPs
        geo_ips = {
            "russia": ["185.220.101.", "91.207.57.", "5.188.62."],
            "china": ["61.160.212.", "218.75.126.", "222.186.15."],
            "north_korea": ["175.45.176.", "210.52.109."],
            "iran": ["5.160.218.", "91.98.102."],
            "usa": ["8.8.8.", "1.1.1.", "172.217.14."],
        }
        
        ip_prefix = geo_ips.get(geo, ["192.168.1.", "10.0.0."])[0]
        
        for i in range(min(limit, random.randint(5, 15))):
            event = {
                "id": f"EVT-{random.randint(10000, 99999)}",
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat(),
                "type": event_type,
                "source_ip": f"{ip_prefix}{random.randint(1, 255)}",
                "destination_ip": f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}",
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "status": random.choice(["blocked", "allowed", "pending"]),
                "details": f"Detected {event_type.replace('_', ' ')} activity"
            }
            
            if geo:
                event["geo_location"] = geo.replace("_", " ").title()
            
            results.append(event)
        
        # Sort by timestamp
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return results
    
    def _generate_summary(self, parsed: Dict, results: List[Dict]) -> str:
        """Generate a human-readable summary of results."""
        count = len(results)
        event_type = parsed.get("event_type", "events")
        geo = parsed.get("geo_filter")
        time_desc = parsed.get("time_range", {}).get("description", "")
        
        if count == 0:
            return f"No {event_type.replace('_', ' ')} events found for the specified criteria."
        
        summary = f"Found {count} {event_type.replace('_', ' ')} event(s)"
        if geo:
            summary += f" from {geo.replace('_', ' ').title()}"
        if time_desc:
            summary += f" in the {time_desc}"
        
        # Add severity breakdown
        severities = {}
        for r in results:
            sev = r.get("severity", "unknown")
            severities[sev] = severities.get(sev, 0) + 1
        
        if severities:
            sev_str = ", ".join([f"{v} {k}" for k, v in severities.items()])
            summary += f". Severity breakdown: {sev_str}."
        
        return summary
    
    def get_query_suggestions(self) -> List[str]:
        """Get example queries for users."""
        return [
            "Show me all failed logins in the last 24 hours",
            "Find connections from Russia this week",
            "List critical alerts from today",
            "How many port scans happened yesterday?",
            "Show malware detections from China",
            "Find all blocked firewall events",
            "Investigate traffic to 192.168.1.100",
            "Show data transfers over 100MB",
            "List top 10 attacking IPs",
            "Find suspicious connections in the past hour"
        ]


# Singleton instance
query_engine = NaturalLanguageQueryEngine()


def execute_natural_query(query: str) -> Dict:
    """Execute a natural language security query."""
    return query_engine.execute_query(query)


def get_query_suggestions() -> List[str]:
    """Get example queries."""
    return query_engine.get_query_suggestions()
