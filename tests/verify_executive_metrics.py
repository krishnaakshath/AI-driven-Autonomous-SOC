import sys
import os
from unittest.mock import MagicMock
from datetime import datetime

# Mock Streamlit to avoid import errors in CLI
st_mock = MagicMock()
st_mock.session_state = {}
st_mock.cache_data = MagicMock(lambda x: x)
sys.modules["streamlit"] = st_mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database import db
from services.soc_monitor import SOCMonitor

def test_executive_grounding():
    print("🚀 Seeding DB with executive KPIs...")
    
    # Insert a False Positive event
    db.insert_event({
        "id": "EVT-FP-01",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "IDS",
        "event_type": "Signature Match",
        "severity": "LOW",
        "status": "False Positive",
        "user": "-"
    })
    
    # Insert a Resolved alert
    db.insert_alert({
        "id": "ALRT-RES-01",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": "DDoS Mitigated",
        "severity": "CRITICAL",
        "status": "Resolved"
    })

    print("🧠 Fetching Executive State...")
    soc = SOCMonitor()
    state = soc.get_current_state()
    
    print(f"✅ FP Rate: {state['false_positive_rate']}%")
    print(f"✅ MTTR: {state['avg_response_time']}h")
    print(f"✅ MTTD: {state['avg_detection_time']}h")
    
    if state['avg_response_time'] > 0 and state['false_positive_rate'] > 0:
        print("🌟 SUCCESS: Executive metrics are grounded and dynamic!")
    else:
        print("❌ FAILURE: Metrics are still static or zero.")

if __name__ == "__main__":
    test_executive_grounding()
