import time
import os
import sys
import random
import logging
from datetime import datetime

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alerting.email_sender import send_email_alert

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SOC_WATCHER")

def check_threats():
    """
    Simulates checking for high-risk threats in the background.
    In a real scenario, this would query a SIEM, Log Database, or API.
    """
    logger.info("Scanning network traffic and system logs...")
    
    # Simulate a random threat check
    # 5% chance of a critical threat in this polling interval
    if random.random() < 0.05:
        logger.warning("⚠️ ANOMALY DETECTED!")
        
        # Simulate threat details
        threat_data = {
            "attack_type": random.choice(["Brute Force", "SQL Injection", "Malware C2", "Unauthorized Access"]),
            "source_ip": f"{random.randint(11, 199)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
            "risk_score": random.randint(85, 99),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.critical(f"CRITICAL THREAT CONFIRMED: {threat_data['attack_type']} (Score: {threat_data['risk_score']})")
        
        # Trigger Alert
        try:
            subject = f"🚨 SOC ALERT: {threat_data['attack_type']} Detected"
            body = f"""
            CRITICAL SECURITY ALERT
            -----------------------
            Time: {threat_data['timestamp']}
            Threat: {threat_data['attack_type']}
            Risk Score: {threat_data['risk_score']}
            Source IP: {threat_data['source_ip']}
            
            Action Taken: AUTOMATED BLOCK
            
            Access Dashboard for full details.
            """
            
            if os.getenv('SENDER_EMAIL') and os.getenv('SENDER_PASSWORD'):
                send_email_alert(subject, body, os.getenv('SENDER_EMAIL')) # Send to self for now
                logger.info("✅ Alert email dispatched.")
            else:
                logger.warning("❌ Email credentials not set. Alert skipped.")
                
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            
    else:
        logger.info("System Nominal. No threats detected.")

if __name__ == "__main__":
    logger.info("🛡️ SOC BACKGROUND MONITOR INITIALIZED")
    logger.info("Running in 24/7 Surveillance Mode")
    
    while True:
        try:
            check_threats()
            # Wait for 60 seconds before next check
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Monitor stopping...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in monitor loop: {e}")
            time.sleep(10)
