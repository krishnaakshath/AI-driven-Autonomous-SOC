import time
import threading
import os
import uuid
import logging
import sys
from datetime import datetime

# Add parent directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import db

# Configure logging for the ingestor itself
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LOG_INGESTOR")

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "live_traffic.log")

class LogIngestor:
    def __init__(self):
        self.running = False
        self.thread = None
        self._ensure_log_file()
        
    def _ensure_log_file(self):
        """Create the log file if it doesn't exist."""
        if not os.path.exists(os.path.dirname(LOG_FILE_PATH)):
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        if not os.path.exists(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, 'w') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}|SYSTEM|INFO|Log Ingestor Initialized\n")

    def start_background_thread(self):
        """Start the ingestion thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._tail_log_file, daemon=True)
            self.thread.start()
            logger.info(f"Log Ingestor Started. Watching: {LOG_FILE_PATH}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            logger.info("Log Ingestor Stopped")

    def _tail_log_file(self):
        """Tail the log file and parse new lines."""
        try:
            # Open file and go to the end
            with open(LOG_FILE_PATH, 'r') as f:
                f.seek(0, 2)
                
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    
                    self._process_line(line)
        except Exception as e:
            logger.error(f"Tail Error: {e}")

    def _process_line(self, line):
        """Parse raw log line into DB event."""
        try:
            line = line.strip()
            if not line:
                return

            # Expected format: TIMESTAMP | SOURCE | SEVERITY | MESSAGE
            # Example: 2024-02-14 10:00:00 | Firewall | CRITICAL | Blocked Connection from 1.2.3.4
            parts = line.split('|')
            
            if len(parts) >= 4:
                timestamp = parts[0].strip()
                source = parts[1].strip()
                severity = parts[2].strip()
                message = parts[3].strip()
                
                # Check if it matches our expected severity levels
                valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                if severity not in valid_severities:
                    severity = "LOW"

                event = {
                    "id": f"LOG-{str(uuid.uuid4())[:8]}",
                    "timestamp": timestamp,
                    "source": source,
                    "event_type": message, # Map message to event_type for simplicity
                    "severity": severity,
                    "source_ip": "0.0.0.0", # Default, could parse from message
                    "dest_ip": "10.0.0.5",
                    "user": "-",
                    "status": "Open",
                    "raw_log": line
                }
                
                # Try to extract IP if present in message
                # Simple heuristic: find X.X.X.X
                import re
                ip_match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', message)
                if ip_match:
                    ip = ip_match.group(0)
                    event["source_ip"] = ip
                    
                    # Check Firewall Status
                    from services.firewall_shim import firewall
                    if firewall.is_blocked(ip):
                        event["event_type"] = f"BLOCKED_TRAFFIC: {message}"
                        event["severity"] = "INFO" # Downgrade severity as it is blocked, or keep logic? 
                        # actually, let's keep severity but verify it shows as blocked action
                        logger.info(f"Blocked Traffic Detected from {ip}")

                # Save to DB
                db.insert_event(event)
                logger.info(f"Ingested Event: {event['event_type']}")
                
                # If Critical, create an alert too!
                if severity == "CRITICAL":
                     alert = {
                        "id": f"ALT-{str(uuid.uuid4())[:8]}",
                        "timestamp": timestamp,
                        "title": f"Critical Log: {message}",
                        "severity": "CRITICAL",
                        "status": "New",
                        "details": line
                    }
                     db.insert_alert(alert)
                     
                     # Send Email Alert (Async to not block ingestion)
                     try:
                         from alerting.email_sender import send_email_alert
                         sender_email = os.environ.get('SENDER_EMAIL')
                         if sender_email:
                            subject = f"🚨 SOC ALERT: {message}"
                            body = f"CRITICAL SECURITY ALERT\n\nTime: {timestamp}\nEvent: {message}\nSource: {source}\n\nImmediate action required."
                            # Send in new thread
                            threading.Thread(target=send_email_alert, args=(subject, body, sender_email)).start()
                     except ImportError:
                         pass
                     except Exception as e:
                         logger.error(f"Failed to send email alert: {e}")

            else:
                logger.debug(f"Skipping malformed line: {line}")
            
        except Exception as e:
            logger.error(f"Parse Error processing line '{line}': {e}")

# Singleton
log_ingestor = LogIngestor()

if __name__ == "__main__":
    # Test run
    ingestor = LogIngestor()
    ingestor.start_background_thread()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ingestor.stop()
