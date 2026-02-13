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
    "login", "signin", "account", "secure", "update", "verify",
    "bank", "paypal", "amazon", "microsoft", "google", "apple",
    ".tk", ".ml", ".ga", ".cf", ".gq", "bit.ly", "tinyurl"
]

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
        Analyze a URL in the sandbox.
        
        Returns screenshot, network activity, and verdict.
        """
        start_time = time.time()
        
        # Calculate URL hash
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        
        # Check cache
        if url_hash in self.cache:
            cached = self.cache[url_hash].copy()
            cached["cached"] = True
            return cached
        
        # Check for phishing indicators
        url_lower = url.lower()
        phishing_score = sum(1 for indicator in PHISHING_INDICATORS if indicator in url_lower)
        
        # Determine verdict
        if phishing_score >= 3:
            verdict = "PHISHING"
            severity = "CRITICAL"
        elif phishing_score >= 2:
            verdict = "SUSPICIOUS"
            severity = "MEDIUM"
        elif any(bad in url_lower for bad in ['.exe', '.scr', '.bat', 'download']):
            verdict = "SUSPICIOUS"
            severity = "MEDIUM"
        else:
            verdict = "CLEAN"
            severity = "NONE"
        
        # Simulate network activity
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
            "analysis_time": round(random.uniform(5, 15), 2),
            "verdict": verdict,
            "severity": severity,
            "phishing_indicators": [ind for ind in PHISHING_INDICATORS if ind in url_lower],
            "network_activity": network,
            "redirects": random.randint(0, 3) if verdict != "CLEAN" else 0,
            "ssl_valid": "https" in url_lower,
            "domain_age_days": random.randint(1, 1000),
            "screenshot_url": f"/sandbox/screenshot/{url_hash[:8]}.png",
            "cached": False
        }
        
        # Flag young domains as suspicious
        if report["domain_age_days"] < 30 and verdict == "CLEAN":
            report["verdict"] = "SUSPICIOUS"
            report["severity"] = "LOW"
        
        # Cache result
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
