import sys
import os

# Mock streamlit
class MockStreamlit:
    class secrets:
        pass
    class session_state:
        pass
sys.modules['streamlit'] = MockStreamlit()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("1. Importing threat_intel...")
try:
    from services.threat_intel import threat_intel
    print("   Success.")
except Exception as e:
    print(f"   Failed: {e}")

print("2. Importing SOCMonitor...")
try:
    from services.soc_monitor import SOCMonitor
    print("   Success.")
except Exception as e:
    print(f"   Failed: {e}")

print("3. Importing database...")
try:
    from services.database import db
    print("   Success.")
except Exception as e:
    print(f"   Failed: {e}")
