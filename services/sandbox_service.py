"""
 Malware Sandbox Service
==========================
Safe environment for analyzing suspicious files and URLs.

Features:
- File hash analysis
- URL detonation
- Behavioral analysis simulation
- Network activity tracking
- Process monitoring
"""

import os
import hashlib
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import streamlit as st

# Simulated malware behaviors for demo
MALWARE_BEHAVIORS = {
    "ransomware": {
        "processes": ["explorer.exe", "vssadmin.exe", "cipher.exe", "wmic.exe"],
        "files_created": [".encrypted", "DECRYPT_README.txt", "ransom_note.html"],
        "files_modified": 150,
        "registry_keys": ["HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"],
        "network": [("185.141.27.0", 443, "C2"), ("91.121.87.0", 8443, "Exfil")],
        "severity": "CRITICAL",
        "verdict": "MALICIOUS"
    },
    "trojan": {
        "processes": ["svchost.exe", "rundll32.exe", "regsvr32.exe"],
        "files_created": ["system32\\malware.dll", "appdata\\backdoor.exe"],
        "files_modified": 12,
        "registry_keys": ["HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"],
        "network": [("45.33.32.156", 4444, "Backdoor"), ("185.220.101.0", 443, "C2")],
        "severity": "HIGH",
        "verdict": "MALICIOUS"
    },
    "spyware": {
        "processes": ["keylogger.exe", "screenshot.exe"],
        "files_created": ["appdata\\logs\\keystrokes.log", "appdata\\screenshots\\"],
        "files_modified": 5,
        "registry_keys": ["HKCU\\Software\\Keylogger"],
        "network": [("91.92.93.94", 8080, "Data Exfil")],
        "severity": "HIGH",
        "verdict": "MALICIOUS"
    },
    "adware": {
        "processes": ["popup.exe", "browser_helper.exe"],
        "files_created": ["appdata\\ads.dll"],
        "files_modified": 3,
        "registry_keys": ["HKCU\\Software\\BrowserExtensions"],
        "network": [("ad-server.example.com", 80, "Ad Network")],
        "severity": "LOW",
        "verdict": "SUSPICIOUS"
    },
    "clean": {
        "processes": [],
        "files_created": [],
        "files_modified": 0,
        "registry_keys": [],
        "network": [],
        "severity": "NONE",
        "verdict": "CLEAN"
    }
}

PHISHING_INDICATORS = [
    "login", "signin", "sign-in", "account", "secure", "update", "verify",
    "confirm", "suspend", "restrict", "unlock", "validate", "authenticate",
    "bank", "wallet", "password", "credential",
    ".tk", ".ml", ".ga", ".cf", ".gq", "bit.ly", "tinyurl"
]

# Well-known brands for typosquatting detection
KNOWN_BRANDS = [
    "paypal", "amazon", "google", "microsoft", "apple", "facebook",
    "netflix", "instagram", "twitter", "linkedin", "dropbox", "github",
    "spotify", "adobe", "chase", "wellsfargo", "bankofamerica", "citibank",
    "ebay", "walmart", "target", "costco", "bestbuy", "steam", "epic",
    "discord", "slack", "zoom", "outlook", "yahoo", "icloud"
]

# Common homograph/leet substitutions
HOMOGRAPH_MAP = {
    '0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's',
    '7': 't', '8': 'b', '9': 'g', '@': 'a', '$': 's',
    '!': 'i', '|': 'l'
}

SUSPICIOUS_TLDS = [
    '.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.buzz',
    '.click', '.link', '.info', '.work', '.site', '.online',
    '.icu', '.club', '.space', '.win', '.bid', '.stream'
]

def _levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]

def _normalize_homographs(text: str) -> str:
    """Replace common homograph characters with their intended letters."""
    return ''.join(HOMOGRAPH_MAP.get(ch, ch) for ch in text)

def _extract_domain(url: str) -> str:
    """Extract the domain name from a URL (without TLD)."""
    url_lower = url.lower().strip()
    for prefix in ['https://', 'http://', 'ftp://']:
        if url_lower.startswith(prefix):
            url_lower = url_lower[len(prefix):]
            break
    if url_lower.startswith('www.'):
        url_lower = url_lower[4:]
    domain = url_lower.split('/')[0].split(':')[0]
    parts = domain.rsplit('.', 1)
    return parts[0] if parts else domain

def _detect_typosquatting(domain: str) -> tuple:
    """Detect if a domain is typosquatting a known brand."""
    normalized = _normalize_homographs(domain)
    for brand in KNOWN_BRANDS:
        if normalized == brand and domain != brand:
            return (True, brand, f"Homograph attack: '{domain}' mimics '{brand}'")
        dist = _levenshtein_distance(domain, brand)
        if 0 < dist <= 2 and len(domain) >= 4:
            return (True, brand, f"Typosquatting: '{domain}' is {dist} edit(s) from '{brand}'")
        if brand in domain and domain != brand:
            return (True, brand, f"Brand impersonation: '{domain}' contains '{brand}'")
        if brand in normalized and normalized != brand:
            if _levenshtein_distance(normalized, brand) <= 2:
                return (True, brand, f"Homograph typosquatting: '{domain}' mimics '{brand}'")
    return (False, None, None)

class SandboxService:
    """Malware sandbox for safe analysis."""
    
    def __init__(self):
        self.analysis_history: List[Dict] = []
        self.cache: Dict[str, Dict] = {}
    
    def _calculate_hash(self, content: bytes) -> Dict[str, str]:
        """Calculate multiple hashes for a file."""
        return {
            "md5": hashlib.md5(content).hexdigest(),
            "sha1": hashlib.sha1(content).hexdigest(),
            "sha256": hashlib.sha256(content).hexdigest()
        }
    
    def _simulate_behavior(self, file_type: str, content_hash: str) -> Dict:
        """Simulate malware behavior based on file characteristics."""
        # Use hash to deterministically pick behavior
        hash_int = int(content_hash[:8], 16)
        
        # Simulate detection probability
        behaviors = list(MALWARE_BEHAVIORS.keys())
        
        # Higher chance of clean for normal files
        if file_type in ['.txt', '.pdf', '.docx', '.jpg', '.png']:
            if hash_int % 10 < 7:  # 70% clean
                return MALWARE_BEHAVIORS["clean"]
        
        # Pick behavior based on hash
        behavior_idx = hash_int % len(behaviors)
        return MALWARE_BEHAVIORS[behaviors[behavior_idx]]
    
    def analyze_file(self, file_content: bytes, filename: str) -> Dict:
        """
        Analyze a file in the sandbox.
        
        Returns detailed behavioral analysis report.
        """
        start_time = time.time()
        
        # Calculate hashes
        hashes = self._calculate_hash(file_content)
        
        # Check cache
        if hashes["sha256"] in self.cache:
            cached = self.cache[hashes["sha256"]].copy()
            cached["cached"] = True
            return cached
        
        # Get file extension
        ext = os.path.splitext(filename)[1].lower()
        
        # Simulate sandbox execution
        behavior = self._simulate_behavior(ext, hashes["sha256"])
        
        # Build report
        analysis_time = random.uniform(15, 45)  # Simulated analysis time
        
        report = {
            "id": hashlib.md5(f"{filename}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            "filename": filename,
            "file_size": len(file_content),
            "file_type": ext,
            "hashes": hashes,
            "submitted_at": datetime.now().isoformat(),
            "analysis_time": round(analysis_time, 2),
            "verdict": behavior["verdict"],
            "severity": behavior["severity"],
            "behavior": {
                "processes_spawned": behavior["processes"],
                "files_created": behavior["files_created"],
                "files_modified": behavior["files_modified"],
                "registry_modified": behavior["registry_keys"],
                "network_connections": [
                    {"ip": ip, "port": port, "type": typ}
                    for ip, port, typ in behavior["network"]
                ]
            },
            "indicators": self._extract_indicators(behavior),
            "mitre_techniques": self._map_to_mitre(behavior),
            "screenshots": self._generate_screenshot_urls(behavior["verdict"]),
            "cached": False
        }
        
        # Cache result
        self.cache[hashes["sha256"]] = report
        self.analysis_history.append(report)
        
        return report
    
    def analyze_url(self, url: str) -> Dict:
        """
        Analyze a URL in the sandbox with multi-layer phishing detection.
        """
        import re
        start_time = time.time()
        
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        if url_hash in self.cache:
            cached = self.cache[url_hash].copy()
            cached["cached"] = True
            return cached
        
        url_lower = url.lower()
        detected_indicators = []
        phishing_score = 0
        
        # Layer 1: Keyword matching
        for indicator in PHISHING_INDICATORS:
            if indicator in url_lower:
                phishing_score += 1
                detected_indicators.append(f"Keyword: '{indicator}'")
        
        # Layer 2: Typosquatting + Homograph detection
        domain = _extract_domain(url)
        is_typosquat, matched_brand, typo_detail = _detect_typosquatting(domain)
        if is_typosquat:
            phishing_score += 3
            detected_indicators.append(typo_detail)
        
        # Layer 3: Suspicious TLD
        for tld in SUSPICIOUS_TLDS:
            if url_lower.split('?')[0].endswith(tld) or tld + '/' in url_lower:
                phishing_score += 1
                detected_indicators.append(f"Suspicious TLD: '{tld}'")
                break
        
        # Layer 4: HTTP on brand domain
        if not url_lower.startswith('https') and (is_typosquat or any(b in domain for b in KNOWN_BRANDS)):
            phishing_score += 1
            detected_indicators.append("No HTTPS on brand-related domain")
        
        # Layer 5: IP-based URL
        if re.match(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url_lower):
            phishing_score += 2
            detected_indicators.append("IP-based URL (no domain name)")
        
        # Layer 6: Excessive subdomains
        full_domain = url_lower.split('//')[1].split('/')[0] if '//' in url_lower else url_lower.split('/')[0]
        if full_domain.count('.') >= 3:
            phishing_score += 1
            detected_indicators.append(f"Excessive subdomains ({full_domain.count('.')} dots)")
        
        # Layer 7: @ symbol trick
        if '@' in url_lower.split('?')[0]:
            phishing_score += 2
            detected_indicators.append("URL contains @ symbol (redirect trick)")
        
        # Determine verdict
        if phishing_score >= 3:
            verdict = "PHISHING"
            severity = "CRITICAL"
        elif phishing_score >= 2:
            verdict = "SUSPICIOUS"
            severity = "HIGH"
        elif phishing_score >= 1:
            verdict = "SUSPICIOUS"
            severity = "MEDIUM"
        elif any(bad in url_lower for bad in ['.exe', '.scr', '.bat', 'download']):
            verdict = "SUSPICIOUS"
            severity = "MEDIUM"
        else:
            verdict = "CLEAN"
            severity = "NONE"
        
        # Network activity for non-clean verdicts
        network = []
        if verdict != "CLEAN":
            network = [
                {"ip": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}", 
                 "port": random.choice([80, 443, 8080]), 
                 "type": "HTTP" if random.random() > 0.5 else "HTTPS"}
            ]
        
        report = {
            "id": hashlib.md5(f"{url}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            "url": url,
            "submitted_at": datetime.now().isoformat(),
            "analysis_time": round(time.time() - start_time + random.uniform(2, 5), 2),
            "verdict": verdict,
            "severity": severity,
            "phishing_indicators": detected_indicators,
            "typosquatting": {"detected": is_typosquat, "brand": matched_brand, "detail": typo_detail} if is_typosquat else None,
            "network_activity": network,
            "redirects": random.randint(1, 5) if verdict != "CLEAN" else 0,
            "ssl_valid": url_lower.startswith("https"),
            "domain_age_days": random.randint(1, 30) if is_typosquat else random.randint(30, 3000),
            "screenshot_url": f"/sandbox/screenshot/{url_hash[:8]}.png",
            "cached": False
        }
        
        self.cache[url_hash] = report
        self.analysis_history.append(report)
        
        return report
    
    def _extract_indicators(self, behavior: Dict) -> List[Dict]:
        """Extract indicators of compromise."""
        indicators = []
        
        for ip, port, typ in behavior.get("network", []):
            indicators.append({
                "type": "ip",
                "value": ip,
                "context": typ
            })
        
        for proc in behavior.get("processes", []):
            if proc in ["vssadmin.exe", "cipher.exe", "wmic.exe"]:
                indicators.append({
                    "type": "process",
                    "value": proc,
                    "context": "Suspicious process execution"
                })
        
        return indicators
    
    def _map_to_mitre(self, behavior: Dict) -> List[Dict]:
        """Map behavior to MITRE ATT&CK techniques."""
        techniques = []
        
        if behavior.get("processes"):
            techniques.append({"id": "T1059", "name": "Command and Scripting Interpreter"})
        
        if behavior.get("registry_keys"):
            techniques.append({"id": "T1547", "name": "Boot or Logon Autostart Execution"})
        
        if behavior.get("network"):
            techniques.append({"id": "T1071", "name": "Application Layer Protocol"})
            techniques.append({"id": "T1041", "name": "Exfiltration Over C2 Channel"})
        
        if "cipher.exe" in behavior.get("processes", []):
            techniques.append({"id": "T1486", "name": "Data Encrypted for Impact"})
        
        return techniques
    
    def _generate_screenshot_urls(self, verdict: str) -> List[str]:
        """Generate simulated screenshot URLs."""
        if verdict == "CLEAN":
            return []
        return [
            f"/sandbox/screenshot/exec_{i}.png" 
            for i in range(random.randint(1, 3))
        ]
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent analysis history."""
        return sorted(
            self.analysis_history,
            key=lambda x: x["submitted_at"],
            reverse=True
        )[:limit]
    
    def get_stats(self) -> Dict:
        """Get sandbox statistics."""
        total = len(self.analysis_history)
        if total == 0:
            return {"total": 0, "malicious": 0, "suspicious": 0, "clean": 0}
        
        malicious = sum(1 for a in self.analysis_history if a["verdict"] == "MALICIOUS")
        suspicious = sum(1 for a in self.analysis_history if a["verdict"] == "SUSPICIOUS")
        phishing = sum(1 for a in self.analysis_history if a["verdict"] == "PHISHING")
        clean = sum(1 for a in self.analysis_history if a["verdict"] == "CLEAN")
        
        return {
            "total": total,
            "malicious": malicious,
            "suspicious": suspicious,
            "phishing": phishing,
            "clean": clean,
            "detection_rate": round((malicious + suspicious + phishing) / total * 100, 1)
        }


# Singleton instance
sandbox = SandboxService()


def analyze_file(content: bytes, filename: str) -> Dict:
    """Analyze a file in the sandbox."""
    return sandbox.analyze_file(content, filename)


def analyze_url(url: str) -> Dict:
    """Analyze a URL in the sandbox."""
    return sandbox.analyze_url(url)


def get_analysis_history(limit: int = 10) -> List[Dict]:
    """Get recent analysis history."""
    return sandbox.get_history(limit)


def get_sandbox_stats() -> Dict:
    """Get sandbox statistics."""
    return sandbox.get_stats()
