import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import db
from services.siem_service import siem_service

def verify_persistence():
    print("--- SOC Persistence Verification ---")
    
    # 1. Trigger generate_events to force backfill if needed
    print("Checking database state...")
    siem_service.generate_events(count=100)
    
    stats = db.get_stats()
    print(f"Total events in database: {stats['total']}")
    print(f"Critical events: {stats['critical']}")
    
    if stats['total'] < 1500:
        print("FAIL: Database not backfilled. Record count too low.")
        return False
        
    # 2. Verify monthly counts
    monthly_counts = db.get_monthly_counts()
    print(f"Monthly distribution (last 12 months):")
    for row in monthly_counts:
        print(f"  - {row['month']}: {row['count']} events")
        
    if len(monthly_counts) < 2:
        print("FAIL: Not enough historical months found.")
        return False
        
    # 3. Check for recently added events
    recent = db.get_recent_events(limit=5)
    print("Most recent events:")
    for r in recent:
        print(f"  - {r['timestamp']} | {r['event_type']} | {r['severity']}")
        
    # 4. Success criteria
    print("--- Verification Successful ---")
    return True

if __name__ == "__main__":
    success = verify_persistence()
    sys.exit(0 if success else 1)
