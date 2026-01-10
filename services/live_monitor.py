import subprocess
import os
import json
import csv
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LiveNetworkMonitor:
    
    def __init__(self):
        self.is_capturing = False
        self.capture_process = None
        self.capture_file = "live_capture.pcap"
        self.csv_file = "live_capture.csv"
        self.alerts = []
    
    def check_tshark(self) -> bool:
        try:
            result = subprocess.run(["tshark", "-v"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def get_interfaces(self) -> List[str]:
        try:
            result = subprocess.run(
                ["tshark", "-D"],
                capture_output=True,
                text=True,
                timeout=10
            )
            interfaces = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(". ")
                    if len(parts) >= 2:
                        interfaces.append(parts[1].split(" ")[0])
            return interfaces
        except:
            return []
    
    def start_capture(self, interface: str = "en0", duration: int = 30) -> Dict:
        if self.is_capturing:
            return {"status": "error", "message": "Capture already running"}
        
        try:
            self.is_capturing = True
            
            cmd = [
                "tshark",
                "-i", interface,
                "-a", f"duration:{duration}",
                "-w", self.capture_file,
                "-q"
            ]
            
            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return {"status": "started", "interface": interface, "duration": duration}
        except Exception as e:
            self.is_capturing = False
            return {"status": "error", "message": str(e)}
    
    def stop_capture(self) -> Dict:
        if self.capture_process:
            self.capture_process.terminate()
            self.capture_process = None
        self.is_capturing = False
        return {"status": "stopped"}
    
    def convert_to_csv(self) -> bool:
        if not os.path.exists(self.capture_file):
            return False
        
        try:
            cmd = [
                "tshark",
                "-r", self.capture_file,
                "-T", "fields",
                "-e", "frame.number",
                "-e", "frame.time",
                "-e", "ip.src",
                "-e", "ip.dst",
                "-e", "ip.proto",
                "-e", "tcp.srcport",
                "-e", "tcp.dstport",
                "-e", "udp.srcport", 
                "-e", "udp.dstport",
                "-e", "frame.len",
                "-e", "tcp.flags",
                "-E", "header=y",
                "-E", "separator=,",
                "-E", "quote=d"
            ]
            
            with open(self.csv_file, 'w') as f:
                subprocess.run(cmd, stdout=f, timeout=60)
            
            return True
        except:
            return False
    
    def analyze_capture(self) -> Dict:
        if not os.path.exists(self.csv_file):
            if os.path.exists(self.capture_file):
                self.convert_to_csv()
            else:
                return {"error": "No capture file found"}
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "total_packets": 0,
            "unique_sources": set(),
            "unique_destinations": set(),
            "protocols": {},
            "top_talkers": {},
            "suspicious_activity": [],
            "port_stats": {}
        }
        
        try:
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    result["total_packets"] += 1
                    
                    src_ip = row.get("ip.src", "")
                    dst_ip = row.get("ip.dst", "")
                    
                    if src_ip:
                        result["unique_sources"].add(src_ip)
                        result["top_talkers"][src_ip] = result["top_talkers"].get(src_ip, 0) + 1
                    
                    if dst_ip:
                        result["unique_destinations"].add(dst_ip)
                    
                    proto = row.get("ip.proto", "unknown")
                    result["protocols"][proto] = result["protocols"].get(proto, 0) + 1
                    
                    dst_port = row.get("tcp.dstport") or row.get("udp.dstport", "")
                    if dst_port:
                        result["port_stats"][dst_port] = result["port_stats"].get(dst_port, 0) + 1
                    
                    tcp_flags = row.get("tcp.flags", "")
                    if tcp_flags:
                        if "0x002" in str(tcp_flags):
                            if src_ip:
                                syn_count = result["top_talkers"].get(src_ip, 0)
                                if syn_count > 50:
                                    result["suspicious_activity"].append({
                                        "type": "Possible Port Scan",
                                        "source": src_ip,
                                        "detail": f"High SYN packet count: {syn_count}"
                                    })
            
            result["unique_sources"] = list(result["unique_sources"])
            result["unique_destinations"] = list(result["unique_destinations"])
            
            sorted_talkers = sorted(result["top_talkers"].items(), key=lambda x: x[1], reverse=True)
            result["top_talkers"] = dict(sorted_talkers[:10])
            
            sorted_ports = sorted(result["port_stats"].items(), key=lambda x: x[1], reverse=True)
            result["port_stats"] = dict(sorted_ports[:10])
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def get_live_stats(self) -> Dict:
        try:
            cmd = [
                "tshark",
                "-i", "en0",
                "-a", "duration:5",
                "-q",
                "-z", "io,stat,1"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            return {
                "status": "captured",
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def detect_threats(self, analysis: Dict) -> List[Dict]:
        threats = []
        
        for ip, count in analysis.get("top_talkers", {}).items():
            if count > 100:
                threats.append({
                    "type": "HIGH_TRAFFIC",
                    "severity": "MEDIUM",
                    "source": ip,
                    "detail": f"Unusually high packet count: {count}",
                    "recommendation": "Investigate source for potential DDoS or scan"
                })
        
        suspicious_ports = {"23": "Telnet", "445": "SMB", "3389": "RDP", "22": "SSH"}
        for port, count in analysis.get("port_stats", {}).items():
            if str(port) in suspicious_ports and count > 20:
                threats.append({
                    "type": "SUSPICIOUS_PORT",
                    "severity": "HIGH",
                    "port": port,
                    "service": suspicious_ports.get(str(port), "Unknown"),
                    "count": count,
                    "detail": f"High traffic on sensitive port {port}",
                    "recommendation": f"Review {suspicious_ports.get(str(port), 'Unknown')} access"
                })
        
        return threats


monitor = LiveNetworkMonitor()


def check_wireshark() -> bool:
    return monitor.check_tshark()


def get_interfaces() -> List[str]:
    return monitor.get_interfaces()


def start_live_capture(interface: str = "en0", duration: int = 30) -> Dict:
    return monitor.start_capture(interface, duration)


def stop_live_capture() -> Dict:
    return monitor.stop_capture()


def analyze_traffic() -> Dict:
    return monitor.analyze_capture()


def detect_network_threats(analysis: Dict) -> List[Dict]:
    return monitor.detect_threats(analysis)
