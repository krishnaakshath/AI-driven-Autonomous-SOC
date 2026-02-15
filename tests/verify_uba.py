import sys
import os
from unittest.mock import MagicMock
from datetime import datetime, timedelta

# Mock Streamlit to avoid import errors in CLI
st_mock = MagicMock()
st_mock.session_state = {}
st_mock.cache_data = MagicMock(lambda x: x)
sys.modules["streamlit"] = st_mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import db
from services.siem_service import get_user_behavior
import random

def test_uba_grounding():
    print("🚀 Seeding SIEM with normal behavior for 'tester'...")
    # Normal: Last 10 days, 10:00 AM
    for i in range(10):
        ts = (datetime.now() - timedelta(days=i)).replace(hour=10, minute=0, second=0)
        event = {
            "id": f"TEST-NORM-{i}",
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "Active Directory",
            "event_type": "Login Success",
            "severity": "LOW",
            "source_ip": "192.168.1.50",
            "user": "tester",
            "hostname": "WS-TEST-01"
        }
        db.insert_event(event)

    print("🚨 Injecting anomalous login (3:00 AM)...")
    ts_bad = datetime.now().replace(hour=3, minute=0, second=0)
    bad_event = {
        "id": "TEST-ANOM-01",
        "timestamp": ts_bad.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "Active Directory",
        "event_type": "Login Success",
        "severity": "MEDIUM",
        "source_ip": "10.99.1.5",
        "user": "tester",
        "hostname": "WS-TEST-01"
    }
    db.insert_event(bad_event)

    print("🧠 Fetching UBA Analysis...")
    behavior = get_user_behavior()
    
    tester_data = next((u for u in behavior if u['user'] == 'tester'), None)
    
    if tester_data:
        print(f"✅ Tester Score: {tester_data['risk_score']}")
        print(f"✅ Anomalous Flag: {tester_data['is_anomalous']}")
        if tester_data['risk_score'] > 20: # Should be boosted from baseline 0
             print("🌟 SUCCESS: ML Engine detected and scored the behavior!")
        else:
             print("❌ FAILURE: ML Engine didn't boost the score.")
    else:
        print("❌ FAILURE: User 'tester' not found in analysis.")

if __name__ == "__main__":
    test_uba_grounding()
