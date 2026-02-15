
import threading
import time
import streamlit as st
from services.siem_service import siem_service
from datetime import datetime

# Global flag to control the thread
_STOP_FLAG = False

def _run_continuous_ingestion():
    """
    The actual worker function that runs in the background thread.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Starting background thread...")
    
    # Initial Seed
    try:
        siem_service.ingest_live_threats(limit=20)
    except Exception as e:
        print(f"[CLOUD-BG] Initial seed failed: {e}")

    while not _STOP_FLAG:
        try:
            # Run ingestion
            count = siem_service.ingest_live_threats(limit=10)
            if count > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Ingested {count} events.")
            
            # Sleep for 60 seconds
            time.sleep(60)
            
        except Exception as e:
            print(f"[CLOUD-BG] Error in thread: {e}")
            time.sleep(30)

@st.cache_resource
def start_cloud_background_service():
    """
    Singleton starter for the background thread. 
    Using/abusing st.cache_resource ensures this only runs ONCE per runtime, 
    persisting across page reloads and user sessions.
    """
    # Create and start the thread
    thread = threading.Thread(target=_run_continuous_ingestion, daemon=True)
    thread.start()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Service registered and started.")
    return thread
