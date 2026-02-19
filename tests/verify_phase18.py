import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import db
from services.siem_service import siem_service
from services.soc_monitor import SOCMonitor

def test_real_time_sync():
    print("--- Phase 18 Verification: Real-Time Sync ---")
    
    # 1. Snapshot current state
    initial_stats = SOCMonitor().get_current_state()
    initial_blocked = initial_stats.get('blocked_today', 0)
    print(f"Initial Blocked Count: {initial_blocked}")
    
    # 2. Trigger Ingestion (Mocking threat intel to guarantee a hit)
    print("Simulating Threat Ingestion...")
    from datetime import datetime
    # Manually insert a blocked event
    mock_event = {
        "id": f"TEST-VERIFY-{int(time.time())}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "Firewall",
        "event_type": "Connection Blocked",
        "severity": "CRITICAL",
        "source_ip": "1.2.3.4", 
        "dest_ip": "192.168.1.50",
        "user": "-",
        "status": "Resolved",
        "details": "Phase 18 Verification Test"
    }
    db.insert_event(mock_event)
    
    # 3. Verify Update
    time.sleep(1) # Allow DB write
    
    new_stats = SOCMonitor().get_current_state()
    new_blocked = new_stats.get('blocked_today', 0)
    print(f"New Blocked Count: {new_blocked}")
    
    if new_blocked > initial_blocked:
        print("✅ SUCCESS: Executive Metrics updated correctly.")
    else:
        print("❌ FAILURE: Blocked count did not increase.")
        
    # 4. Verify Threat Hunt Search
    print("\nVerifying Threat Hunt DB Search...")
    hits = db.search_events("1.2.3.4")
    if hits:
        print(f"✅ SUCCESS: Found {len(hits)} events for IOC 1.2.3.4")
    else:
        print("❌ FAILURE: Could not find injected IOC.")

if __name__ == "__main__":
    test_real_time_sync()
