import sys
import os
from unittest.mock import MagicMock

# Mock Streamlit to avoid import and session state errors
st_mock = MagicMock()
st_mock.session_state = {}
sys.modules["streamlit"] = st_mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alerting.alert_service import trigger_alert

def test_critical_alert():
    print("🚀 Triggering simulated critical alert...")
    event_data = {
        "attack_type": "Simulated DDoS",
        "risk_score": 95,
        "source_ip": "10.0.0.1",
        "target_host": "production-db-01",
        "access_decision": "BLOCK",
        "automated_response": "IP quarantined and firewall rules updated."
    }
    
    results = trigger_alert(event_data)
    print(f"✅ Alert results: {results}")

if __name__ == "__main__":
    test_critical_alert()
