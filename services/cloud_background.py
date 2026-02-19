
import threading
import time
import streamlit as st
from services.siem_service import siem_service
from datetime import datetime

# Global flag to control the thread
_STOP_FLAG = False

# Retraining interval: every 360 cycles (~6 hours at 60s/cycle)
_RETRAIN_INTERVAL = 360

# Weekly report check: every 60 cycles (~1 hour) — checks if 7 days have passed
_WEEKLY_REPORT_CHECK_INTERVAL = 60

def _run_ml_retrain():
    """Retrain ML models on accumulated database data."""
    try:
        from ml_engine.isolation_forest import isolation_forest
        from ml_engine.fuzzy_clustering import fuzzy_clustering
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Starting ML retrain cycle...")
        
        if_result = isolation_forest.retrain_from_db()
        fcm_result = fuzzy_clustering.retrain_from_db()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] ML retrain complete. "
              f"IF: {if_result.get('n_samples', if_result.get('reason', '?'))}, "
              f"FCM: {fcm_result.get('n_samples', fcm_result.get('reason', '?'))}")
    except Exception as e:
        print(f"[CLOUD-BG] ML retrain error: {e}")

def _run_weekly_report():
    """Check if weekly report is due and generate if so."""
    try:
        from services.weekly_reporter import should_generate_weekly_report, generate_weekly_report
        
        if should_generate_weekly_report():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Weekly report is due — generating...")
            result = generate_weekly_report()
            if result:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Weekly report generated: {result['id']}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Weekly report generation returned None")
    except Exception as e:
        print(f"[CLOUD-BG] Weekly report error: {e}")

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

    cycle_count = 0
    while not _STOP_FLAG:
        try:
            # Run ingestion
            count = siem_service.ingest_live_threats(limit=10)
            if count > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Ingested {count} events.")
            
            cycle_count += 1
            
            # Periodic ML retraining (every ~6 hours)
            if cycle_count % _RETRAIN_INTERVAL == 0:
                _run_ml_retrain()
            
            # Periodic weekly report check (every ~1 hour)
            if cycle_count % _WEEKLY_REPORT_CHECK_INTERVAL == 0:
                _run_weekly_report()
            
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
