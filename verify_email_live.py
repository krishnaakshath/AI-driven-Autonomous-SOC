
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alerting.alert_service import alert_service, send_test_alert

print("Testing Email Alert System...")
print(f"Configured Email: {alert_service.email.username}")
print(f"Password set? {'Yes' if alert_service.email.password else 'No'}")

try:
    print("\nAttempting to send LIVE test email...")
    result = send_test_alert()
    
    if result.get("email"):
        print("\nSUCCESS: Email sent successfully! ✅")
    else:
        print("\nFAILURE: Email send returned False. ❌")

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
