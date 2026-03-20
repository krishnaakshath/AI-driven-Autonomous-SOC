#!/usr/bin/env python3
"""
Production Readiness Probe (/healthz)
=====================================
Intended for Docker/Kubernetes healthchecks. Exits 0 if healthy, 1 otherwise.
Verifies critical infrastructure:
1. Supabase Event Database Persistence
2. API Key Configurations
3. Machine Learning Model Load States
"""

import sys
import logging
from datetime import datetime

# Disable SOC centralized logging for silent health checks
logging.getLogger("soc").setLevel(logging.CRITICAL)

def check_health():
    print(f"[{datetime.now().isoformat()}] Executing SOC Platform Healthcheck...")
    
    # 1. Database Connectivity
    try:
        from services.database import db
        if not db.is_connected():
            print("FAIL: Supabase Cloud Database is unreachable.")
            sys.exit(1)
        # Verify read capability
        count = len(db.get_recent_events(limit=1))
        print("OK: Supabase Connection Established. Read Capability Verified.")
    except Exception as e:
        print(f"FAIL: Database subsystem threw exception: {e}")
        sys.exit(1)
        
    # 2. ML Engine Initialization Checks
    try:
        from ml_engine.isolation_forest import isolation_forest
        # Model should exist and be initialized
        if isolation_forest is None:
            print("FAIL: Isolation Forest anomaly detector failed to load into memory.")
            sys.exit(1)
            
        from ml_engine.fuzzy_clustering import fuzzy_clustering
        if fuzzy_clustering is None:
            print("FAIL: Fuzzy C-Means threat categorization failed to load.")
            sys.exit(1)
            
        print("OK: ML Engines (Isolation Forest, Fuzzy C-Means) loaded into memory.")
    except Exception as e:
        print(f"FAIL: Machine Learning subsystem panic: {e}")
        sys.exit(1)
        
    # 3. Security/Environment Constraints
    try:
        import os
        from services.env_validator import load_config
        config = load_config()
        envs = [config.get("supabase_url"), config.get("supabase_key"), config.get("groq_api_key")]
        if not all(envs):
            print("FAIL: Missing critical API credentials (Supabase/Groq) required for SOC operation.")
            sys.exit(1)
            
        print("OK: Environment API configurations verified.")
    except Exception as e:
        print(f"FAIL: Configuration constraints validation failed: {e}")
        sys.exit(1)
        
    print(f"[{datetime.now().isoformat()}] SYSTEM STATUS: HEALTHY")
    sys.exit(0)

if __name__ == "__main__":
    check_health()
