# Hyper-Sanitization (Zero-Mock Lockdown)

This plan outlines the final removal of all remaining "Simulation 2.0" infrastructure, redundant legacy scripts, and purely visual "filler" UI components. The goal is a lean, 100% data-authentic security platform.

## User Review Required

> [!WARNING]
> This phase involves **DELETING** several core "legacy simulation" components:
> 1. `services/background_monitor.py` & `services/log_ingestor.py` (The fake traffic loop).
> 2. `ui/defense_module.py` (The Matrix-style fake log UI).
> 3. `ui/educational.py` (Glossary of terms/filler text).
> 4. `services/soc_monitor.py` (Formula-based metrics).
> 5. `seed_alerts.py` (Redundant setup script).

## Proposed Changes

### SIEM & Backend Purge
Eliminating the self-generating "fake data" cycle.

#### [DELETE] [background_monitor.py](file:///Users/k2a/Desktop/Project/services/background_monitor.py)
#### [DELETE] [log_ingestor.py](file:///Users/k2a/Desktop/Project/services/log_ingestor.py)
#### [DELETE] [background_job.py](file:///Users/k2a/Desktop/Project/services/background_job.py)
#### [DELETE] [seed_alerts.py](file:///Users/k2a/Desktop/Project/seed_alerts.py)

#### [MODIFY] [cloud_background.py](file:///Users/k2a/Desktop/Project/services/cloud_background.py)
- Remove `simulate_ingestion` calls.
- Keep ML retraining and real-time threat ingestion.

---

### Dashboard Refactoring
Transitioning dashboards from "Real-ish" formulas to absolute data ground truth.

#### [DELETE] [soc_monitor.py](file:///Users/k2a/Desktop/Project/services/soc_monitor.py)
- Replaced by direct database and `siem_service` queries in the pages.

#### [MODIFY] [01_Dashboard.py](file:///Users/k2a/Desktop/Project/pages/01_Dashboard.py)
- Remove `render_explanation` calls (dependent on `educational.py`).
- Refactor metric calculations to use `siem_service` data directly.

#### [MODIFY] [02_Executive.py](file:///Users/k2a/Desktop/Project/pages/02_Executive.py)
- Refactor ROI and KPI calculations to use direct database counts instead of `SOCMonitor` benchmarks.

---

### UI Sanitization

#### [DELETE] [defense_module.py](file:///Users/k2a/Desktop/Project/ui/defense_module.py)
- Removes the fake "Autonomous Defense Protocol" terminal.

#### [DELETE] [educational.py](file:///Users/k2a/Desktop/Project/ui/educational.py)
- Removes glossary filler content to declutter the interface.

## Verification Plan

### Automated Tests
1. Verify no import errors in any remaining page after the deletions.
2. Verify `cloud_background.py` runs without attempting to call deleted simulation methods.

### Manual Verification
1. Ensure the Dashboard and Executive pages still display accurate metrics derived from real data.
2. Confirm the "Matrix" fake log UI is gone from all dashboards.
3. Verify the "Learn" expanders are removed, resulting in a cleaner UI.
