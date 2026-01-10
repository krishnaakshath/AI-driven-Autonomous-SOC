import socket
import subprocess
import threading
import time
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class SecurityScanner:
    
    def __init__(self):
        self.scan_results = []
        self.is_scanning = False
    
    def port_scan(self, target_ip: str, ports: List[int] = None, timeout: float = 1.0) -> Dict:
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 8080, 8443]
        
        result = {
            "target": target_ip,
            "timestamp": datetime.now().isoformat(),
            "open_ports": [],
            "closed_ports": [],
            "filtered_ports": [],
            "scan_type": "TCP Connect"
        }
        
        def check_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                conn_result = sock.connect_ex((target_ip, port))
                sock.close()
                
                if conn_result == 0:
                    service = self.get_service_name(port)
                    return {"port": port, "state": "open", "service": service}
                else:
                    return {"port": port, "state": "closed", "service": ""}
            except socket.timeout:
                return {"port": port, "state": "filtered", "service": ""}
            except Exception as e:
                return {"port": port, "state": "error", "service": str(e)}
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(check_port, port): port for port in ports}
            for future in as_completed(futures):
                port_result = future.result()
                if port_result["state"] == "open":
                    result["open_ports"].append(port_result)
                elif port_result["state"] == "filtered":
                    result["filtered_ports"].append(port_result)
                else:
                    result["closed_ports"].append(port_result)
        
        result["open_ports"].sort(key=lambda x: x["port"])
        return result
    
    def get_service_name(self, port: int) -> str:
        services = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 135: "MSRPC", 139: "NetBIOS", 143: "IMAP",
            443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
            1433: "MSSQL", 1521: "Oracle", 3306: "MySQL", 3389: "RDP",
            5432: "PostgreSQL", 5900: "VNC", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt"
        }
        return services.get(port, "Unknown")
    
    def ping_host(self, target_ip: str) -> Dict:
        result = {
            "target": target_ip,
            "timestamp": datetime.now().isoformat(),
            "alive": False,
            "response_time": None
        }
        
        try:
            param = "-n" if os.name == "nt" else "-c"
            start = time.time()
            output = subprocess.run(
                ["ping", param, "1", "-W", "1", target_ip],
                capture_output=True,
                timeout=3
            )
            end = time.time()
            
            if output.returncode == 0:
                result["alive"] = True
                result["response_time"] = round((end - start) * 1000, 2)
        except:
            pass
        
        return result
    
    def network_discovery(self, network_prefix: str) -> List[Dict]:
        results = []
        
        def check_host(ip):
            return self.ping_host(ip)
        
        ips = [f"{network_prefix}.{i}" for i in range(1, 255)]
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(check_host, ip): ip for ip in ips}
            for future in as_completed(futures):
                result = future.result()
                if result["alive"]:
                    results.append(result)
        
        results.sort(key=lambda x: int(x["target"].split(".")[-1]))
        return results
    
    def grab_banner(self, target_ip: str, port: int, timeout: float = 2.0) -> str:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((target_ip, port))
            
            if port in [80, 8080]:
                sock.send(b"HEAD / HTTP/1.1\r\nHost: " + target_ip.encode() + b"\r\n\r\n")
            elif port == 22:
                pass
            else:
                sock.send(b"\r\n")
            
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            return banner.strip()[:200]
        except:
            return ""
    
    def full_scan(self, target_ip: str) -> Dict:
        result = {
            "target": target_ip,
            "timestamp": datetime.now().isoformat(),
            "ping": self.ping_host(target_ip),
            "ports": self.port_scan(target_ip),
            "banners": {}
        }
        
        for port_info in result["ports"]["open_ports"]:
            banner = self.grab_banner(target_ip, port_info["port"])
            if banner:
                result["banners"][port_info["port"]] = banner
        
        return result
    
    def vulnerability_check(self, scan_result: Dict) -> List[Dict]:
        vulnerabilities = []
        
        open_ports = scan_result.get("ports", {}).get("open_ports", [])
        
        vuln_rules = {
            21: {"severity": "HIGH", "issue": "FTP service exposed", "recommendation": "Disable FTP or use SFTP"},
            22: {"severity": "MEDIUM", "issue": "SSH exposed", "recommendation": "Use key-based auth, change default port"},
            23: {"severity": "CRITICAL", "issue": "Telnet exposed - unencrypted", "recommendation": "Disable Telnet immediately"},
            135: {"severity": "HIGH", "issue": "MSRPC exposed", "recommendation": "Block with firewall"},
            139: {"severity": "HIGH", "issue": "NetBIOS exposed", "recommendation": "Disable or block externally"},
            445: {"severity": "CRITICAL", "issue": "SMB exposed - ransomware risk", "recommendation": "Block SMB externally"},
            1433: {"severity": "HIGH", "issue": "MSSQL exposed", "recommendation": "Move behind VPN"},
            3306: {"severity": "HIGH", "issue": "MySQL exposed", "recommendation": "Move behind VPN"},
            3389: {"severity": "CRITICAL", "issue": "RDP exposed - brute force risk", "recommendation": "Use VPN or disable"},
            5432: {"severity": "HIGH", "issue": "PostgreSQL exposed", "recommendation": "Move behind VPN"},
            5900: {"severity": "CRITICAL", "issue": "VNC exposed - unencrypted", "recommendation": "Disable or use SSH tunnel"}
        }
        
        for port_info in open_ports:
            port = port_info["port"]
            if port in vuln_rules:
                vuln = vuln_rules[port].copy()
                vuln["port"] = port
                vuln["service"] = port_info.get("service", "Unknown")
                vulnerabilities.append(vuln)
        
        return vulnerabilities


scanner = SecurityScanner()


def run_port_scan(target: str, ports: List[int] = None) -> Dict:
    return scanner.port_scan(target, ports)


def run_ping(target: str) -> Dict:
    return scanner.ping_host(target)


def run_network_discovery(network: str) -> List[Dict]:
    return scanner.network_discovery(network)


def run_full_scan(target: str) -> Dict:
    return scanner.full_scan(target)


def check_vulnerabilities(scan_result: Dict) -> List[Dict]:
    return scanner.vulnerability_check(scan_result)
