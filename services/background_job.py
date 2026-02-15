"""
Background Job - Continuous Threat Intelligence Ingestion
Run this script to enable "Live Mode" where new threats are automatically pulled and ingested.
"""

import time
import sys
import os
import signal
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.siem_service import siem_service
from services.threat_intel import threat_intel

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def run_job():
    log("Starting Continuous Threat Ingestion Service...")
    log("Press Ctrl+C to stop.")
    
    # Initial seed
    log("Performing initial seed...")
    siem_service.ingest_live_threats(limit=50)
    
    while True:
        try:
            log("Fetching fresh indicators...")
            count = siem_service.ingest_live_threats(limit=10)
            
            if count > 0:
                log(f"Successfully ingested {count} new threat events.")
            else:
                log("No new unique threats found this cycle.")
                
            # Wait for next cycle
            time.sleep(60) 
            
        except KeyboardInterrupt:
            log("Stopping service...")
            break
        except Exception as e:
            log(f"Error in background job: {e}")
            time.sleep(30) # Wait a bit before retrying

if __name__ == "__main__":
    run_job()
