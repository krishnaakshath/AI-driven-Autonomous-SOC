import time
import os
import sys
import random
import logging
from datetime import datetime

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alerting.email_sender import send_email_alert
from services.threat_intel import threat_intel

# Configure Logging to file for Log Ingestor
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "live_traffic.log")

# Custom Formatter for Log Ingestor: TIMESTAMP | SOURCE | SEVERITY | MESSAGE
class IngestorFormatter(logging.Formatter):
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        return f"{timestamp} | {record.name} | {record.levelname} | {record.getMessage()}"

# Setup File Handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(IngestorFormatter())

# Setup Stream Handler (Console)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger("SOC_WATCHER")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def generate_ip_from_country(country_counts):
    """Generate a random IP that 'belongs' to a weighted country distribution."""
    if not country_counts:
        return f"{random.randint(11, 199)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    
    countries = list(country_counts.keys())
    weights = list(country_counts.values())
    
    # Normalize weights
    total = sum(weights)
    if total == 0:
        return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
    probs = [w/total for w in weights]
    chosen_country = random.choices(countries, weights=probs, k=1)[0]
    
    # Mock IP ranges for fun (not real Geolocation, but consistent for demo)
    ranges = {
        "China": (1, 50), "Russia": (51, 80), "United States": (81, 120),
        "Iran": (121, 130), "North Korea": (131, 135), "Brazil": (136, 150),
        "India": (151, 170), "Germany": (171, 180)
    }
    
    start, end = ranges.get(chosen_country, (181, 223))
    return f"{random.randint(start, end)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

import threading

# ... (Logging setup remains similar, but we need to ensure unique loggers if re-imported)
# We can keep the module-level logger for simplicity

class BackgroundMonitor:
    def __init__(self):
        self.running = False
        self.thread = None
        
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logger.info("Background Monitor Thread Started")
            
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            logger.info("Background Monitor Thread Stopped")
            
    def _run_loop(self):
        logger.info("Monitor Loop Active")
        while self.running:
            try:
                self.check_threats()
                # Dynamic sleep to make it look organic (3-8 seconds)
                interval = random.uniform(3.0, 8.0)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(10)
                
    def check_threats(self):
        """
        Simulates checking for high-risk threats and generating background noise.
        Feeds 'live_traffic.log' which powers the Dashboard and SIEM.
        """
        # Get current threat landscape (cached)
        try:
            country_counts = threat_intel.get_country_threat_counts()
        except:
            country_counts = {}
        
        # 1. Generate Background Noise (Low/Medium events) - "Active Data"
        # ----------------------------------------------------------------
        if random.random() < 0.7: # High frequency
            src_ip = generate_ip_from_country(country_counts)
            event_type = random.choice(["Port Scan", "Failed Login", "DNS Query", "Web Request"])
            severity = "LOW"
            if event_type == "Failed Login": severity = "MEDIUM"
            
            logger.info(f"{event_type} detected from {src_ip}") # Writes to log file with INFO level
        
        # 2. Simulate Critical Threat (Rare)
        # ----------------------------------
        if random.random() < 0.1: # 10% chance per polling interval
            # Simulate threat details
            attack_type = random.choice(["Brute Force", "SQL Injection", "Malware C2", "Unauthorized Access", "Ransomware Attempt"])
            src_ip = generate_ip_from_country(country_counts)
            risk_score = random.randint(85, 99)
            
            # Log as CRITICAL - Ingestor will pick this up and alert
            logger.critical(f"{attack_type} from {src_ip}")
            
            # Trigger Email Alert directly
            # ... (Email logic preserved)
            try:
                from alerting.email_sender import EmailNotifier
                notifier = EmailNotifier()
                if notifier.is_configured():
                    subject = f" SOC ALERT: {attack_type} Detected"
                    body = f"CRITICAL SECURITY ALERT\nTime: {datetime.now()}\nThreat: {attack_type}\nSource: {src_ip}\nScore: {risk_score}\n\nAutomated Defense Engaged."
                    recipient = notifier.username
                    send_email_alert(subject, body, recipient)
            except Exception:
                pass

# Singleton instance
background_monitor = BackgroundMonitor()

if __name__ == "__main__":
    logger.info("SOC BACKGROUND MONITOR INITIALIZED")
    logger.info("Running in 24/7 Surveillance Mode - Feeding Live Stream")
    
    monitor = BackgroundMonitor()
    monitor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
