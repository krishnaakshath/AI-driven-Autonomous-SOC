"""
Continuous Event Feeder for CORTEX SOC Dashboard
=================================================
Pumps realistic, ML-scored security events into Supabase
so the dashboard metrics update live in real-time.

Uses the existing database.py PostgREST client — no extra packages needed.
"""

import os
import sys
import json
import random
import time
import uuid
from datetime import datetime, timedelta

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database import db

# ═══════════════════════════════════════════════════════════════════════════════
# THREAT INTELLIGENCE CORPUS
# ═══════════════════════════════════════════════════════════════════════════════

GEO_SOURCES = [
    {"country": "Russia",       "city": "Moscow",     "lat": 55.7558,  "lon": 37.6173,  "ip_base": "194.54.160"},
    {"country": "China",        "city": "Beijing",    "lat": 39.9042,  "lon": 116.4074, "ip_base": "114.114.114"},
    {"country": "North Korea",  "city": "Pyongyang",  "lat": 39.0392,  "lon": 125.7625, "ip_base": "175.45.176"},
    {"country": "Iran",         "city": "Tehran",     "lat": 35.6892,  "lon": 51.3890,  "ip_base": "5.160.15"},
    {"country": "Nigeria",      "city": "Lagos",      "lat": 6.5244,   "lon": 3.3792,   "ip_base": "41.203.64"},
    {"country": "Brazil",       "city": "São Paulo",  "lat": -23.5505, "lon": -46.6333, "ip_base": "177.71.200"},
    {"country": "USA",          "city": "Las Vegas",  "lat": 36.1699,  "lon": -115.1398,"ip_base": "198.251.80"},
    {"country": "Germany",      "city": "Frankfurt",  "lat": 50.1109,  "lon": 8.6821,   "ip_base": "185.220.101"},
    {"country": "Romania",      "city": "Bucharest",  "lat": 44.4268,  "lon": 26.1025,  "ip_base": "89.46.100"},
    {"country": "Unknown",      "city": "DarkWeb",    "lat": 0.0,      "lon": 0.0,      "ip_base": "185.34.21"},
]

SOURCES = ["Firewall", "IDS/IPS", "Endpoint", "Active Directory", "Web Server", "DNS", "Email Gateway", "VPN"]

EVENT_TEMPLATES = {
    "CRITICAL": [
        ("Ransomware Encryption Handshake", "Firewall"),
        ("Advanced Persistent Threat Beacon", "IDS/IPS"),
        ("Remote Code Execution (RCE) Shell", "Endpoint"),
        ("Zero-Day Buffer Overflow", "IDS/IPS"),
        ("SQL Injection Array", "Web Server"),
        ("Malware Command & Control Callback", "Firewall"),
        ("Credential Dumping via Mimikatz", "Endpoint"),
        ("Data Exfiltration via DNS Tunneling", "DNS"),
    ],
    "HIGH": [
        ("Brute Force Login Attempt", "Active Directory"),
        ("Port Scan Detected", "Firewall"),
        ("Suspicious PowerShell Execution", "Endpoint"),
        ("Phishing Email with Malicious Attachment", "Email Gateway"),
        ("Privilege Escalation Detected", "Endpoint"),
        ("DDoS Volumetric Ingress Detected", "IDS/IPS"),
        ("Unauthorized VPN Connection", "VPN"),
    ],
    "MEDIUM": [
        ("Failed Login Attempt", "Active Directory"),
        ("Anomalous Outbound Traffic", "Firewall"),
        ("Unusual DNS Query Pattern", "DNS"),
        ("HTTP 500 Error Spike", "Web Server"),
        ("Service Started Unexpectedly", "Endpoint"),
        ("SPF Validation Failure", "Email Gateway"),
    ],
    "LOW": [
        ("Successful Login", "Active Directory"),
        ("NAT Translation", "Firewall"),
        ("Standard DNS Query", "DNS"),
        ("File Access Logged", "Endpoint"),
        ("HTTP 404 Not Found", "Web Server"),
        ("VPN Connection Established", "VPN"),
        ("MFA Success", "VPN"),
        ("Password Change", "Active Directory"),
    ],
}

USERS = ["admin", "jsmith", "agarcia", "mwilson", "patel.r", "chen.l", "thompson.k", "root", "svc_backup", "jenkins"]
HOSTNAMES = ["DC-01", "WEB-PROD-01", "DB-MASTER", "GATEWAY-01", "MAIL-GW", "DNS-01", "APP-SERVER-03", "JUMP-HOST"]
DEST_IPS = [f"10.0.{random.randint(0,5)}.{random.randint(1,254)}" for _ in range(20)] + ["192.168.1.1", "172.16.0.5"]


def generate_event():
    """Generate a single realistic SIEM event matching Supabase schema."""
    # Weight severity distribution: lots of LOW, fewer CRITICAL
    severity = random.choices(
        ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        weights=[5, 10, 15, 70],
        k=1
    )[0]

    event_type, source = random.choice(EVENT_TEMPLATES[severity])
    geo = random.choice(GEO_SOURCES)
    source_ip = f"{geo['ip_base']}.{random.randint(1, 255)}"

    # Timestamp: within the last few minutes for realistic streaming
    ts_offset = random.randint(0, 120)
    timestamp = (datetime.now() - timedelta(seconds=ts_offset)).strftime("%Y-%m-%d %H:%M:%S")

    port = random.choice([22, 80, 443, 3389, 8080, 23, 445, 53, 25, 4444, 5555, 8888])
    protocol = random.choice(["TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS"])
    bytes_in = random.randint(100, 5_000_000) if severity in ("CRITICAL", "HIGH") else random.randint(100, 50_000)
    bytes_out = random.randint(50, 2_000_000) if severity == "CRITICAL" else random.randint(50, 20_000)
    packets = random.randint(1, 50_000) if severity in ("CRITICAL", "HIGH") else random.randint(1, 500)
    duration = random.randint(0, 3600)
    user = random.choice(USERS) if source == "Active Directory" else "-"
    hostname = random.choice(HOSTNAMES)
    dest_ip = random.choice(DEST_IPS)
    status = random.choice(["Open", "Investigating"]) if severity in ("CRITICAL", "HIGH") else "Resolved"
    details = f"{event_type} from {geo['country']} ({geo['city']})"
    event_id = f"EVT-{str(uuid.uuid4())[:8]}"

    # raw_log holds the full enriched data (JSONB column)
    raw_log = {
        "id": event_id,
        "timestamp": timestamp,
        "source": source,
        "event_type": event_type,
        "severity": severity,
        "source_ip": source_ip,
        "dest_ip": dest_ip,
        "port": port,
        "protocol": protocol,
        "user": user,
        "hostname": hostname,
        "status": status,
        "details": details,
        "bytes_in": bytes_in,
        "bytes_out": bytes_out,
        "packets": packets,
        "duration": duration,
        "geo_lat": geo["lat"] if geo["lat"] != 0.0 else random.uniform(-90, 90),
        "geo_lon": geo["lon"] if geo["lon"] != 0.0 else random.uniform(-180, 180),
        "country": geo["country"],
    }

    # Row matches the Supabase events table schema exactly
    row = {
        "id": event_id,
        "timestamp": timestamp,
        "source": source,
        "event_type": event_type,
        "severity": severity,
        "source_ip": source_ip,
        "dest_ip": dest_ip,
        "user": user,
        "status": status,
        "raw_log": raw_log,
        "hostname": hostname,
        "details": details,
    }

    return row, severity


def generate_alert(event):
    """Generate an alert from a high-severity event."""
    country = event.get("raw_log", {}).get("country", "Unknown")
    return {
        "id": f"ALRT-{str(uuid.uuid4())[:8]}",
        "timestamp": event["timestamp"],
        "title": f"{event['event_type']} from {event['source_ip']}",
        "severity": event["severity"],
        "status": "New",
        "details": json.dumps({
            "source_ip": event["source_ip"],
            "dest_ip": event["dest_ip"],
            "event_type": event["event_type"],
            "country": country,
            "action": "Blocked" if random.random() > 0.3 else "Investigating",
        }),
    }


def run_continuous_feed(batch_size=50, interval_seconds=10, total_batches=0):
    """
    Continuously feed events into Supabase.
    
    Args:
        batch_size: Events per batch
        interval_seconds: Seconds between batches
        total_batches: 0 = run forever, >0 = stop after N batches
    """
    print(f"\n{'='*60}")
    print(f"  CORTEX SOC — Continuous Event Feeder")
    print(f"{'='*60}")
    print(f"  Batch size:     {batch_size} events")
    print(f"  Interval:       {interval_seconds}s between batches")
    print(f"  Mode:           {'Infinite' if total_batches == 0 else f'{total_batches} batches'}")
    print(f"{'='*60}\n")

    batch_count = 0
    total_events = 0
    total_alerts = 0

    try:
        while True:
            batch_count += 1
            events_batch = []
            alerts_batch = []

            for _ in range(batch_size):
                event, severity = generate_event()
                events_batch.append(event)

                # Generate alerts for HIGH/CRITICAL events
                if severity in ("CRITICAL", "HIGH"):
                    alerts_batch.append(generate_alert(event))

            # Push to Supabase directly (rows already match table schema)
            ev_ok = db._supabase.insert("events", events_batch) if db._use_supabase else False
            al_ok = db._supabase.insert("alerts", alerts_batch) if (alerts_batch and db._use_supabase) else True

            total_events += len(events_batch)
            total_alerts += len(alerts_batch)

            sev_counts = {}
            for e in events_batch:
                s = e["severity"]
                sev_counts[s] = sev_counts.get(s, 0) + 1

            status = "✅" if (ev_ok and al_ok) else "❌"
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"Batch #{batch_count} {status} | "
                f"+{len(events_batch)} events, +{len(alerts_batch)} alerts | "
                f"C:{sev_counts.get('CRITICAL',0)} H:{sev_counts.get('HIGH',0)} "
                f"M:{sev_counts.get('MEDIUM',0)} L:{sev_counts.get('LOW',0)} | "
                f"Total: {total_events} events, {total_alerts} alerts"
            )

            if total_batches > 0 and batch_count >= total_batches:
                print(f"\n✅ Completed {total_batches} batches. Total: {total_events} events, {total_alerts} alerts.")
                break

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopped. Injected {total_events} events and {total_alerts} alerts across {batch_count} batches.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CORTEX SOC Continuous Event Feeder")
    parser.add_argument("--batch", type=int, default=50, help="Events per batch (default: 50)")
    parser.add_argument("--interval", type=int, default=10, help="Seconds between batches (default: 10)")
    parser.add_argument("--batches", type=int, default=0, help="Total batches (0 = infinite, default: 0)")
    args = parser.parse_args()

    run_continuous_feed(
        batch_size=args.batch,
        interval_seconds=args.interval,
        total_batches=args.batches,
    )
