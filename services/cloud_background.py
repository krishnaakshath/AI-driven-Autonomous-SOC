
import threading
import time
import streamlit as st
from services.siem_service import siem_service
from datetime import datetime
from services.logger import get_logger
logger = get_logger("cloud_bg")


# Global flag to control the thread
_STOP_FLAG = False

# Retraining interval: every 120 cycles (~2 hours at 60s/cycle)
_RETRAIN_INTERVAL = 120

# Weekly report check: every 60 cycles (~1 hour) — checks if 7 days have passed
_WEEKLY_REPORT_CHECK_INTERVAL = 60

# RL auto-training: every 10 cycles (~10 minutes)
_RL_TRAIN_INTERVAL = 10

def _run_ml_retrain():
    """Retrain ML models on accumulated live database data."""
    try:
        from ml_engine.isolation_forest import isolation_forest
        from ml_engine.fuzzy_clustering import fuzzy_clustering
        from services.database import db
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Starting ML retrain on live DB data...")
        
        # Pull latest 5000 events from the live database for training
        live_events = db.get_recent_events(limit=5000)
        
        if live_events and len(live_events) > 100:
            # Retrain Isolation Forest on live accumulated data
            if_result = isolation_forest.retrain_from_db()
            
            # Retrain Fuzzy Clustering on live accumulated data
            fcm_result = fuzzy_clustering.retrain_from_db()
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] ML retrain complete on {len(live_events)} live events. "
                  f"IF: {if_result.get('n_samples', if_result.get('reason', '?'))}, "
                  f"FCM: {fcm_result.get('n_samples', fcm_result.get('reason', '?'))}")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Not enough live data for retrain ({len(live_events) if live_events else 0} events)")
    except Exception as e:
        logger.warning("[CLOUD-BG] ML retrain: %s", e)

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
        logger.warning("[CLOUD-BG] Weekly report: %s", e)

def _run_rl_training():
    """Run autonomous RL self-learning cycle on recent events — all 6 agents."""
    try:
        from ml_engine.rl_threat_classifier import rl_classifier
        from services.database import db

        # Pull latest events from DB
        recent_events = db.get_recent_events(limit=30)
        if not recent_events or len(recent_events) < 5:
            return

        # ── Train main threat classifier ──
        correct = 0
        total = 0
        for evt in recent_events:
            classification = rl_classifier.classify(evt)
            result = rl_classifier.auto_reward(evt, classification)
            total += 1
            if isinstance(result, dict) and result.get("is_correct"):
                correct += 1

        rl_classifier._save_to_disk()

        acc = round(correct / total * 100, 1) if total > 0 else 0
        stats = rl_classifier.get_stats()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] RL threat-classifier: "
              f"{total} events, {acc}% accurate, ε={stats['epsilon']:.4f}")

        # ── Train domain-specific agents ──
        try:
            from ml_engine.rl_agents import ALL_AGENTS
            for agent in ALL_AGENTS:
                for evt in recent_events[:15]:
                    cls = agent.classify(evt)
                    agent.auto_reward(evt, cls)
                agent.save()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] RL domain agents: "
                  f"5 agents trained on {min(15, len(recent_events))} events each")
        except Exception as e:
            logger.warning("[CLOUD-BG] RL domain agents: %s", e)

    except Exception as e:
        logger.warning("[CLOUD-BG] RL training: %s", e)

def _run_continuous_ingestion():
    """
    The actual worker function that runs in the background thread.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Starting background thread...")
    
    # Initial Seed
    try:
        siem_service.ingest_live_threats(limit=20)
    except Exception as e:
        logger.warning("[CLOUD-BG] Initial seed failed: %s", e)

    cycle_count = 0
    while not _STOP_FLAG:
        try:
            # Run real OSINT ingestion (pulls real threats and blocks them) every 5 cycles
            if cycle_count % 5 == 0:
                real_count = siem_service.ingest_live_threats(limit=5)
                if real_count > 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [CLOUD-BG] Ingested {real_count} real threat indicators.")
            
            cycle_count += 1
            
            # Periodic ML retraining (every ~2 hours = 120 cycles)
            if cycle_count % 120 == 0:
                _run_ml_retrain()
            
            # RL auto-training (every ~10 minutes = 10 cycles)
            if cycle_count % _RL_TRAIN_INTERVAL == 0:
                _run_rl_training()
            
            # Periodic weekly report check (every ~1 hour = 60 cycles)
            if cycle_count % 60 == 0:
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
