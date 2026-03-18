import os
import time
import json
import random
from datetime import datetime
from dotenv import load_dotenv

import requests
from supabase import create_client, Client

# Load existing environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("FATAL: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# High Threat IP ranges and regions for cinematic effect
TARGET_GEO = [
    {"country": "Russia", "city": "Moscow", "lat": 55.7558, "lon": 37.6173, "ip_base": "194.54.160"},
    {"country": "China", "city": "Beijing", "lat": 39.9042, "lon": 116.4074, "ip_base": "114.114.114"},
    {"country": "North Korea", "city": "Pyongyang", "lat": 39.0392, "lon": 125.7625, "ip_base": "175.45.176"},
    {"country": "Iran", "city": "Tehran", "lat": 35.6892, "lon": 51.3890, "ip_base": "5.160.15"},
    {"country": "Unknown", "city": "DarkWeb Node", "lat": 0.0, "lon": 0.0, "ip_base": "185.34.21"}
]

ATTACK_TYPES = [
    "Volumetric DDoS Ingress", 
    "Remote Code Execution (RCE) Shell", 
    "SQL Injection Array", 
    "Advanced Persistent Threat (APT) Beacon", 
    "Ransomware Encryption Handshake", 
    "Zero-Day Buffer Overflow"
]

def generate_malicious_event():
    geo = random.choice(TARGET_GEO)
    malicious_ip = f"{geo['ip_base']}.{random.randint(1,255)}"
    
    # Generate cinematic raw packet structure
    raw_packet = json.dumps({
        "tcp_flags": "SYN, ACK, PSH, URG",
        "payload_entropy": random.uniform(7.8, 8.0), # High entropy indicates encrypted ransomware
        "attack_vector": random.choice(ATTACK_TYPES),
        "target_port": random.choice([22, 443, 3389, 8080, 23]),
        "bytes_in": random.randint(50000, 9999999)
    })
    
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "source_ip": malicious_ip,
        "destination_ip": "10.0.0.1", # Internal Core Router
        "event_type": "CRITICAL_THREAT",
        "severity": random.randint(85, 100), # Red-level alerts
        "raw_data": raw_packet,
        "resolved": False,
        "geo_lat": geo["lat"] if geo["lat"] != 0.0 else random.uniform(-90, 90),
        "geo_lon": geo["lon"] if geo["lon"] != 0.0 else random.uniform(-180, 180),
        "country": geo["country"]
    }
    return event

def burst_attack_simulation(num_events=150):
    print(f"\\n[!] INITIATING HOLLYWOOD TRAFFIC SIMULATOR")
    print(f"[!] Target Database: {SUPABASE_URL}")
    print(f"[!] Injecting {num_events} hyper-malicious events...\\n")
    
    events_injected = 0
    start_time = time.time()
    
    try:
        # We inject in dynamic bursts to look realistic on the timescale
        for i in range(num_events):
            event = generate_malicious_event()
            # Push securely to Supabase
            supabase.table("siem_events").insert(event).execute()
            events_injected += 1
            
            # Print visual feedback to the console
            print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] ALERT: Overwhelming ingress from {event['country']} (IP: {event['source_ip']}) | Threat: {json.loads(event['raw_data'])['attack_vector']} | Sev: {event['severity']}")
            
            # Random micro-sleep to simulate organic attack waves
            time.sleep(random.uniform(0.01, 0.4))
            
    except Exception as e:
        print(f"\\n[X] Simulation Interrupted: {e}")
        
    duration = time.time() - start_time
    print(f"\\n[=] SIMULATION COMPLETE.")
    print(f"[=] Total Injections: {events_injected} events safely logged to SIEM.")
    print(f"[=] Duration: {duration:.2f} seconds.")
    print(f"[=] Open Streamlit at `http://localhost:8501` to view your dashboard explode in real-time!")

if __name__ == "__main__":
    # This simulation generates 250 heavy attacks by default, scaling perfectly for a 2-minute project defense window.
    burst_attack_simulation(num_events=250)
