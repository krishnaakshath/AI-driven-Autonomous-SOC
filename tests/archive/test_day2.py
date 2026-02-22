import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database import db
from services.log_ingestor import LogIngestor, LOG_FILE_PATH

def test_ingestion():
    print("--- Testing Log Ingestion ---")
    
    # 1. Start Ingestor
    print("1. Starting Ingestor Thread...")
    ingestor = LogIngestor()
    ingestor.start_background_thread()
    time.sleep(1) # Let it settle
    
    # 2. Get current DB count
    stats_before = db.get_stats()
    count_before = stats_before['total']
    print(f"   Events before: {count_before}")
    
    # 3. Write to Log File
    print("2. Writing to Log File...")
    test_msg = f"TEST-LOG-{int(time.time())}"
    log_line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | TestSource | HIGH | {test_msg}\n"
    
    with open(LOG_FILE_PATH, "a") as f:
        f.write(log_line)
    print(f"   Wrote: {log_line.strip()}")
    
    # 4. Wait for Ingestion
    print("3. Waiting for Ingestion (2s)...")
    time.sleep(2)
    
    # 5. Verify in DB
    print("4. Verifying in DB...")
    stats_after = db.get_stats()
    count_after = stats_after['total']
    print(f"   Events after: {count_after}")
    
    assert count_after > count_before
    
    # Check specific event
    events = db.get_recent_events(10)
    found = False
    for e in events:
        if e.get('event_type') == test_msg:
            found = True
            break
    
    if found:
        print("   Verification Passed: Event found in DB.")
    else:
        print("   ❌ Verification Failed: Event NOT found in DB.")
        # Debug
        print("   Recent events:")
        for e in events:
            print(f"   - {e.get('event_type')}")
        raise Exception("Event not found")
        
    ingestor.stop()

if __name__ == "__main__":
    try:
        test_ingestion()
        print("\n✅ DAY 2 TEST PASSED: Real-Time Log Ingestion is functional.")
    except Exception as e:
        print(f"\n❌ DAY 2 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
