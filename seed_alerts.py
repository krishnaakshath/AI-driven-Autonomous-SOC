import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database import db
import uuid
from datetime import datetime

print("Fetching recent events to generate alerts...")
events = db.get_recent_events(limit=5000)
alerts = []

for ev in events:
    if ev.get("severity") in ["CRITICAL", "HIGH"]:
        alerts.append({
            "id": f"ALRT-{str(uuid.uuid4())[:8]}",
            "timestamp": ev.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": f"{ev.get('event_type')} from {ev.get('source_ip')}",
            "severity": ev.get("severity"),
            "status": "Investigating" if ev.get("severity") == "CRITICAL" else "Open"
        })

print(f"Generated {len(alerts)} alerts. Inserting into Supabase...")
if alerts:
    db.bulk_insert_alerts(alerts)
print("Alerts seeded successfully.")
