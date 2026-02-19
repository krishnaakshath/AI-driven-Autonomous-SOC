
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import db

if __name__ == "__main__":
    print("Checking Database Stats...")
    stats = db.get_stats()
    print(f"Total Events in DB: {stats['total']}")
    print(f"Critical Events in DB: {stats['critical']}")
    print(f"High Severity Events in DB: {stats['high']}")
    
    events_count = db.get_event_count()
    print(f"Fast Count: {events_count}")
    
    if stats['total'] > 5000:
        print("\nSUCCESS: Database has more than 5000 events. The dashboard should now show this number.")
    else:
        print(f"\nNOTE: Database has {stats['total']} events. Refilling to > 5000 to test...")
        # Simulate filling if low
        from services.siem_service import siem_service
        needed = 5500 - stats['total']
        if needed > 0:
            print(f"Injecting {needed} events...")
            siem_service.simulate_ingestion(count=needed)
            new_stats = db.get_stats()
            print(f"New Total: {new_stats['total']}")
