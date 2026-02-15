# SOC Platform Upgrade — Task Tracker

## Phase 1: Auth Persistence Fix
- [x] Fix `_load_users()` to reload from disk (not cache at init)
- [x] Add atomic write in `_save_users()`
- [x] Add `role` field to user records (owner/admin/user)
- [x] Pre-seed `users.json` with owner account
- [x] Test: register → restart → login works

## Phase 2: Secure Secret Manager
- [x] Create `services/secret_manager.py`
- [x] Implement `st.secrets` primary + Fernet-encrypted fallback
- [x] Add `get_secret()`, `set_secret()`, `mask_secret()`, `list_secrets()`
- [x] Migrate `auth_service.py` to use `secret_manager`
- [x] Test: secret read/write/mask round-trip

## Phase 3: Owner-Only Admin Dashboard
- [x] Create `pages/25_Admin.py` with `require_admin()` guard
- [x] Implement User Management tab
- [x] Implement Secrets/Config management tab
- [x] Implement Audit Logs tab
- [x] Implement Incidents/Playbook controls tabs
- [x] Register admin page in `dashboard.py` navigation
- [x] Test: non-admin gets denied, admin sees all tabs

## Phase 4: FCM + Combined Analysis Improvement
- [x] Increase training subsample to 15K
- [x] Add feature engineering (protocol/service one-hot encoding)
- [x] Add Hungarian algorithm for cluster-label alignment
- [x] Add Davies-Bouldin index to `evaluate()`
- [x] Build combined scoring: IF anomaly × FCM membership fusion
- [x] Add confusion matrix, ROC/PR curves to Analysis page
- [x] Report honest before/after metrics

## Phase 5: MFA + Session Persistence
- [x] Add `pyotp` TOTP support in `auth_service.py`
- [x] **Bug Fix**: Resolved `NameError` (missing `Tuple`) in `ml_engine/geo_predictor.py`.
- [x] **Grounding UBA**: Learning from real SIEM data.
- [x] **Grounding Executive Metrics**: MTTR, MTTD, ROI, and SNR are now dynamic.
- [x] **Ground Main Dashboard Metrics** (Completed)
    - [x] Refactor `load_soc_data` to use `DatabaseService`.
    - [x] Add "Live System" / "Simulation Mode" indicator.
    - [x] Fix empty state bug with robust fallback.
    - [x] **HOTFIX**: Resolved "Blank Screen" regression caused by premature `st.rerun()`.
- [x] **Audit and Ground All Pages** (Completed)
    - [x] Audit and fix `05_Timeline.py` (Added Live/Sim badges).
    - [x] Audit and fix `08_Kill_Chain.py` (Added Live/Sim badges).
    - [x] Audit and fix `09_Dark_Web.py` (Added Live/Historical badges).
    - [x] Fix missing methods in `services/threat_intel.py`.
    - [x] Verify transparency across all modules.
- [ ] **Final Verification**
    - [ ] Run full system test (Manual verification recommended).
- [x] **Bug Fix**: Resolved `NameError` (missing `time`) in `pages/08_Kill_Chain.py`.
- [x] **Bug Fix**: Resolved `NameError` (missing imports) in `pages/08_Kill_Chain.py`.
- [x] **Bug Fix**: Resolved `AttributeError` in `fuzzy_clustering.py`.
- [x] Implement session token persistence (data/sessions.json)
- [x] Auto-login on valid session token
- [x] Add "Remember this device" option
- [x] Update `requirements.txt` with new dependencies

## Phase 6: Final Verification
- [x] Run all tests
- [x] Verify no theme/style regressions
- [x] Git commit and push
- [x] Write walkthrough

## Phase 7: Enhancements & Fixes (User Requested)
- [x] Fix Settings API Key mismatch (Gemini -> Groq)
- [x] Add AbuseIPDB configuration
- [x] Make Executive Dashboard dynamic (connect to DB)


## Phase 8: ML Accuracy Boost (>95%)
- [x] Implement Supervised Fuzzy Centroid Classification in fuzzy_clustering.py
- [x] Tune Isolation Forest ensemble weights (95% RF / 5% IF)
## Phase 9: API & Auth Fixes (Completed)
- [x] Implement `reload_config()` in `ThreatIntelligence` and `AIAssistant`
- [x] Update Settings page to reload services on save
- [x] Add Gmail SMTP & Twilio config fields to Settings
- [x] Implement persistent `sessions.json` token storage
- [x] Add "Remember this device" checkbox to Login page
- [x] Verify auto-login on restart logic

## Phase 10: UI/UX & RBAC Polish (Verified)
- [x] Fix Admin panel syntax error (`pages/25_Admin.py`)
- [x] Update `sidebar_manager.py` (hide Admin page, bold headers)
- [x] Refactor `Settings.py` (Role-based view: System vs User)
- [x] Enhance `Login.py` with animations and better styling

## Phase 12: Global API Integration (Current Focus)
- [x] **Alerts Page**: Enable AlienVault OTX & AbuseIPDB enrichment for all displayed alerts
- [x] **Executive Dashboard**: Replace static "0.0h" metrics with real calculations from `incident_history.json`
- [x] **Threat Intel**: Verify VirusTotal/AbuseIPDB real-time lookups
- [x] **Logs**: Ensure "Live Stream" actually reads from `services.log_ingestor`
- [x] **Reports**: Generate real PDF reports using `fpdf` and dynamic data
- [x] **Settings**: Validate API keys on save (check connectivity)

## Phase 13: Advanced Analytics & ML Optimization (Current Focus)
- [x] **Fuzzy C-Means**: Improve clustering accuracy (currently ~52%) via feature scaling and hyperparameter tuning
- [x] **Data Preprocessing**: Implement RobustScaler/MinMaxScaler to handle outliers in NSL-KDD
- [x] **Visualization**: Enhance cluster visualization with PCA/t-SNE for better separability

## Phase 14: Comprehensive API Integration & Live Data Updates
- [x] **API Configuration Audit**: Verified keys for VirusTotal, AbuseIPDB, OTX, Groq.
- [x] **Service Layer Enhancements**:
    - [x] Updated `services/threat_intel.py` with real pulse matching and fallback logic.
    - [x] Improved `get_country_threat_counts` with weighted geographic distribution.
- [x] **Page Integration & Live Data**:
    - [x] `pages/01_Dashboard.py`: Wired up live stats and added manual Refresh.
    - [x] `pages/06_Threat_Intel.py`: Integrated `force_refresh` and auto-feed.
    - [x] `services/background_monitor.py`: Integrated with `log_ingestor` for live feed.
- [x] **Verification**: Verified end-to-end data flow and refresh functionality.
- [x] **GitHub Sync**: Pushing all changes to repository.

[x] **Phase 14-B: Global API Integration & Continuous Data Refresh**
    [x] **ML Synchronization (Grounding Models in Reality)**
        [x] Update `geo_predictor.py` to ingest real OTX pulse counts (Replace synthetic history).
        [x] Ensure `fuzzy_clustering.py` handles live SIEM data streams.
    [x] **Continuous Updates (Apply to all 12 platform pages)**
        [x] **Executive Dashboard**: Connect KPI cards (Uptime, MTTR) to real database statistics + Refresh button.
        [x] **Geo Predictions**: Implement Refresh and automated model re-prediction.
        [x] **Kill Chain**: Link "Active Threats" to live SIEM alerts + Refresh stage mapping.
        [x] **Log Viewer**: Implement non-blocking auto-refresh mechanism.
    [x] **Final Verification**: Confirm all pages update without manual script restarts.

## Phase 15: Continuous Live Data Ingestion (User Requested)
- [x] **Create Background Job**: `services/background_job.py` to poll APIs independently.
- [x] **Enhance `siem_service`**: Add `ingest_live_threats()` method for higher volume/frequency.
- [x] **Data Pipeline**: Ensure new threats are auto-converted to SIEM events (Access Attempts/Blocks).
- [x] **Verification**: Run background job and verify `01_Dashboard.py` updates without manual refresh.
- [x] **Data Restoration**: Backfilled 2,000 historical events to restore dashboard volume metrics.
- [x] **Cloud Self-Healing**: Implemented auto-seeding in `siem_service.py` to fix empty state on Streamlit Cloud.

## Phase 16: Cloud-Ready Background Service
- [x] **Create Thread Manager**: Implement `services/cloud_background.py` using `threading` and `st.cache_resource`.
- [x] **dashboard Integration**: Start the background thread on `01_Dashboard.py` load.
- [x] **Verification**: Ensure thread is singleton and doesn't duplicate on reload.

## Phase 17: Inter-Page Consistency & Real-Time Sync (User Requested)
- [x] **Unified Data Model**: Ensure `ingest_live_threats` generates both Events AND Alerts (so Alerts page updates).
- [x] **Page Auto-Refresh**: Add "Live Mode" toggles or auto-refresh concepts to:
    - `03_Alerts.py`
    - `05_Timeline.py`
    - `06_Threat_Intel.py`
    - `24_SIEM.py`
- [x] **Verification**: Confirm that a single ingested threat appears on Dashboard, Alerts, SIEM, and Timeline.
