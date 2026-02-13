"""
 Multi-Source Threat Intelligence Aggregator
===============================================
Aggregates threat data from multiple intelligence sources
and produces a unified threat score.

Sources:
- VirusTotal (file hashes, URLs)
- AbuseIPDB (IP reputation)
- AlienVault OTX (threat indicators)
- Shodan (exposed services)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import random
import os

class ThreatIntelAggregator:
    """
    Aggregates threat intelligence from multiple sources
    into a unified threat score and risk assessment.
    """
    
    # Source weights for scoring
    SOURCE_WEIGHTS = {
        "virustotal": 0.30,
        "abuseipdb": 0.25,
        "alienvault": 0.20,
        "shodan": 0.15,
        "internal": 0.10
    }
    
    # Known malicious indicators (simulated database)
    KNOWN_MALICIOUS = {
        "ips": [
            "185.220.101.1", "91.207.57.2", "5.188.62.3",
            "61.160.212.4", "218.75.126.5", "175.45.176.6"
        ],
        "domains": [
            "malware-c2.com", "phishing-site.net", "evil-domain.org",
            "ransomware-payment.xyz", "botnet-c2.io"
        ],
        "hashes": [
            "d41d8cd98f00b204e9800998ecf8427e",
            "098f6bcd4621d373cade4e832627b4f6"
        ]
    }
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(hours=1)
        self.api_keys = {
            "virustotal": os.environ.get("VIRUSTOTAL_API_KEY"),
            "abuseipdb": os.environ.get("ABUSEIPDB_API_KEY"),
            "shodan": os.environ.get("SHODAN_API_KEY"),
            "alienvault": os.environ.get("ALIENVAULT_API_KEY")
        }
    
    def check_ip(self, ip: str) -> Dict:
        """
        Check an IP address against all threat intelligence sources.
        
        Args:
            ip: IP address to check
            
        Returns:
            Unified threat assessment
        """
        cache_key = f"ip:{ip}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < self.cache_ttl:
                return cached["data"]
        
        # Gather intel from all sources
        intel = {
            "indicator": ip,
            "type": "ip",
            "checked_at": datetime.now().isoformat(),
            "sources": {}
        }
        
        # VirusTotal check
        intel["sources"]["virustotal"] = self._check_virustotal_ip(ip)
        
        # AbuseIPDB check
        intel["sources"]["abuseipdb"] = self._check_abuseipdb(ip)
        
        # AlienVault OTX check
        intel["sources"]["alienvault"] = self._check_alienvault_ip(ip)
        
        # Shodan check
        intel["sources"]["shodan"] = self._check_shodan(ip)
        
        # Internal check
        intel["sources"]["internal"] = self._check_internal(ip, "ip")
        
        # Calculate unified score
        intel["unified_score"] = self._calculate_unified_score(intel["sources"])
        intel["risk_level"] = self._get_risk_level(intel["unified_score"])
        intel["recommendation"] = self._get_recommendation(intel["unified_score"], "ip")
        
        # Cache result
        self.cache[cache_key] = {"timestamp": datetime.now(), "data": intel}
        
        return intel
    
    def check_domain(self, domain: str) -> Dict:
        """Check a domain against threat intelligence sources."""
        cache_key = f"domain:{domain}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < self.cache_ttl:
                return cached["data"]
        
        intel = {
            "indicator": domain,
            "type": "domain",
            "checked_at": datetime.now().isoformat(),
            "sources": {}
        }
        
        intel["sources"]["virustotal"] = self._check_virustotal_domain(domain)
        intel["sources"]["alienvault"] = self._check_alienvault_domain(domain)
        intel["sources"]["internal"] = self._check_internal(domain, "domain")
        
        intel["unified_score"] = self._calculate_unified_score(intel["sources"])
        intel["risk_level"] = self._get_risk_level(intel["unified_score"])
        intel["recommendation"] = self._get_recommendation(intel["unified_score"], "domain")
        
        self.cache[cache_key] = {"timestamp": datetime.now(), "data": intel}
        
        return intel
    
    def check_hash(self, file_hash: str) -> Dict:
        """Check a file hash against threat intelligence sources."""
        cache_key = f"hash:{file_hash}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < self.cache_ttl:
                return cached["data"]
        
        intel = {
            "indicator": file_hash,
            "type": "file_hash",
            "checked_at": datetime.now().isoformat(),
            "sources": {}
        }
        
        intel["sources"]["virustotal"] = self._check_virustotal_hash(file_hash)
        intel["sources"]["alienvault"] = self._check_alienvault_hash(file_hash)
        intel["sources"]["internal"] = self._check_internal(file_hash, "hash")
        
        intel["unified_score"] = self._calculate_unified_score(intel["sources"])
        intel["risk_level"] = self._get_risk_level(intel["unified_score"])
        intel["recommendation"] = self._get_recommendation(intel["unified_score"], "file")
        
        self.cache[cache_key] = {"timestamp": datetime.now(), "data": intel}
        
        return intel
    
    def _check_virustotal_ip(self, ip: str) -> Dict:
        """Check IP against VirusTotal (simulated)."""
        is_malicious = ip in self.KNOWN_MALICIOUS["ips"]
        
        return {
            "source": "VirusTotal",
            "available": True,
            "malicious_count": random.randint(5, 15) if is_malicious else random.randint(0, 2),
            "total_engines": 70,
            "score": 85 if is_malicious else random.randint(0, 25),
            "categories": ["malware", "botnet"] if is_malicious else [],
            "last_seen": datetime.now().isoformat()
        }
    
    def _check_abuseipdb(self, ip: str) -> Dict:
        """Check IP against AbuseIPDB (simulated)."""
        is_malicious = ip in self.KNOWN_MALICIOUS["ips"]
        
        return {
            "source": "AbuseIPDB",
            "available": True,
            "confidence_score": random.randint(80, 100) if is_malicious else random.randint(0, 30),
            "total_reports": random.randint(50, 500) if is_malicious else random.randint(0, 5),
            "score": 90 if is_malicious else random.randint(0, 20),
            "country": random.choice(["RU", "CN", "KP", "IR"]) if is_malicious else "US",
            "isp": "Malicious Hosting" if is_malicious else "Legitimate ISP"
        }
    
    def _check_alienvault_ip(self, ip: str) -> Dict:
        """Check IP against AlienVault OTX (simulated)."""
        is_malicious = ip in self.KNOWN_MALICIOUS["ips"]
        
        return {
            "source": "AlienVault OTX",
            "available": True,
            "pulse_count": random.randint(10, 50) if is_malicious else random.randint(0, 3),
            "score": 80 if is_malicious else random.randint(0, 20),
            "reputation": -5 if is_malicious else random.randint(0, 2),
            "tags": ["apt", "c2", "malware"] if is_malicious else []
        }
    
    def _check_shodan(self, ip: str) -> Dict:
        """Check IP against Shodan (simulated)."""
        is_malicious = ip in self.KNOWN_MALICIOUS["ips"]
        
        open_ports = [22, 80, 443] if not is_malicious else [22, 23, 80, 443, 3389, 4444, 5555]
        
        return {
            "source": "Shodan",
            "available": True,
            "open_ports": open_ports,
            "vulnerabilities": random.randint(3, 10) if is_malicious else random.randint(0, 2),
            "score": 70 if is_malicious else random.randint(0, 25),
            "services": ["ssh", "http", "https"] if not is_malicious else ["ssh", "telnet", "http", "rdp", "backdoor"],
            "os": "Linux" if not is_malicious else "Unknown"
        }
    
    def _check_virustotal_domain(self, domain: str) -> Dict:
        """Check domain against VirusTotal (simulated)."""
        is_malicious = any(m in domain for m in ["malware", "phishing", "evil", "ransomware", "botnet"])
        
        return {
            "source": "VirusTotal",
            "available": True,
            "malicious_count": random.randint(10, 30) if is_malicious else random.randint(0, 2),
            "score": 90 if is_malicious else random.randint(0, 15),
            "categories": ["phishing", "malware"] if is_malicious else ["business"],
            "registrar": "Malicious Registrar" if is_malicious else "GoDaddy"
        }
    
    def _check_alienvault_domain(self, domain: str) -> Dict:
        """Check domain against AlienVault OTX (simulated)."""
        is_malicious = any(m in domain for m in ["malware", "phishing", "evil", "ransomware", "botnet"])
        
        return {
            "source": "AlienVault OTX",
            "available": True,
            "pulse_count": random.randint(5, 25) if is_malicious else 0,
            "score": 85 if is_malicious else random.randint(0, 10),
            "tags": ["c2", "dga", "malware"] if is_malicious else []
        }
    
    def _check_virustotal_hash(self, file_hash: str) -> Dict:
        """Check file hash against VirusTotal (simulated)."""
        is_malicious = file_hash in self.KNOWN_MALICIOUS["hashes"]
        
        return {
            "source": "VirusTotal",
            "available": True,
            "malicious_count": random.randint(40, 60) if is_malicious else random.randint(0, 2),
            "total_engines": 70,
            "score": 95 if is_malicious else random.randint(0, 10),
            "file_type": "executable" if is_malicious else "document",
            "threat_name": "Trojan.Generic" if is_malicious else None
        }
    
    def _check_alienvault_hash(self, file_hash: str) -> Dict:
        """Check file hash against AlienVault OTX (simulated)."""
        is_malicious = file_hash in self.KNOWN_MALICIOUS["hashes"]
        
        return {
            "source": "AlienVault OTX",
            "available": True,
            "pulse_count": random.randint(10, 30) if is_malicious else 0,
            "score": 90 if is_malicious else random.randint(0, 5),
            "malware_families": ["emotet", "trickbot"] if is_malicious else []
        }
    
    def _check_internal(self, indicator: str, indicator_type: str) -> Dict:
        """Check against internal threat database."""
        lists = {
            "ip": self.KNOWN_MALICIOUS["ips"],
            "domain": self.KNOWN_MALICIOUS["domains"],
            "hash": self.KNOWN_MALICIOUS["hashes"]
        }
        
        is_known = indicator in lists.get(indicator_type, [])
        
        return {
            "source": "Internal Database",
            "available": True,
            "is_known_threat": is_known,
            "score": 100 if is_known else 0,
            "first_seen": datetime.now().isoformat() if is_known else None
        }
    
    def _calculate_unified_score(self, sources: Dict) -> int:
        """Calculate weighted unified threat score (0-100)."""
        total_score = 0
        total_weight = 0
        
        for source_name, data in sources.items():
            if data.get("available"):
                weight = self.SOURCE_WEIGHTS.get(source_name, 0.1)
                score = data.get("score", 0)
                total_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            return int(total_score / total_weight)
        return 0
    
    def _get_risk_level(self, score: int) -> str:
        """Determine risk level from score."""
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        return "CLEAN"
    
    def _get_recommendation(self, score: int, indicator_type: str) -> str:
        """Get recommended action based on score."""
        if score >= 80:
            actions = {
                "ip": "Block immediately. Add to firewall blocklist. Investigate any connections.",
                "domain": "Block at DNS level. Add to proxy blocklist. Check for phishing victims.",
                "file": "Quarantine immediately. Run forensic analysis. Check for lateral movement."
            }
            return actions.get(indicator_type, "Block and investigate immediately.")
        elif score >= 60:
            return "High risk. Consider blocking. Increase monitoring."
        elif score >= 40:
            return "Moderate risk. Monitor closely. Gather more intelligence."
        elif score >= 20:
            return "Low risk. Continue normal monitoring."
        return "No threats detected. Continue normal operations."


# Singleton instance
intel_aggregator = ThreatIntelAggregator()


def check_ip_reputation(ip: str) -> Dict:
    """Check IP reputation across all sources."""
    return intel_aggregator.check_ip(ip)


def check_domain_reputation(domain: str) -> Dict:
    """Check domain reputation across all sources."""
    return intel_aggregator.check_domain(domain)


def check_file_hash(file_hash: str) -> Dict:
    """Check file hash across all sources."""
    return intel_aggregator.check_hash(file_hash)


def get_unified_threat_score(indicator: str, indicator_type: str = "ip") -> int:
    """Get unified threat score for any indicator."""
    if indicator_type == "ip":
        return intel_aggregator.check_ip(indicator)["unified_score"]
    elif indicator_type == "domain":
        return intel_aggregator.check_domain(indicator)["unified_score"]
    elif indicator_type == "hash":
        return intel_aggregator.check_hash(indicator)["unified_score"]
    return 0
