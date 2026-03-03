# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     STREAMLIT CLOUD                             │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Dashboard  │  │  Alerts  │  │   SIEM   │  │ Threat Intel │  │
│  │  (main)   │  │   Page   │  │   Page   │  │    Page      │  │
│  └─────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│        └──────────────┴─────────────┴───────────────┘          │
│                           │                                     │
│  ┌────────────────────────┴────────────────────────────────┐   │
│  │                  SERVICE LAYER                           │   │
│  │  ┌──────────┐  ┌────────────┐  ┌──────────────────┐     │   │
│  │  │ database │  │ siem_svc   │  │ firewall_service │     │   │
│  │  │  .py     │  │    .py     │  │ firewall_shim.py │     │   │
│  │  └────┬─────┘  └────────────┘  └──────────────────┘     │   │
│  │       │         ┌────────────┐  ┌──────────────────┐     │   │
│  │       │         │ auth_svc   │  │ audit_logger.py  │     │   │
│  │       │         │    .py     │  │ (rate-limited)   │     │   │
│  │       │         └────────────┘  └──────────────────┘     │   │
│  └───────┼──────────────────────────────────────────────────┘   │
│          │                                                       │
│  ┌───────┴──────────────────────────────────────────────────┐   │
│  │                  ML ENGINE                                │   │
│  │  ┌─────────────────┐  ┌──────────────┐  ┌────────────┐  │   │
│  │  │ rl_threat_class  │  │ isolation_   │  │ fuzzy_     │  │   │
│  │  │ ifier.py        │  │ forest.py    │  │ clustering │  │   │
│  │  │ (Q-Network)     │  │ (anomaly)    │  │    .py     │  │   │
│  │  └─────────────────┘  └──────────────┘  └────────────┘  │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ rl_agents.py — 6 domain-specific RL agents          │ │   │
│  │  │ (alerts, hunt, soar, firewall, osint, threat_intel) │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │       SUPABASE          │
              │  ┌──────┐  ┌────────┐   │
              │  │events│  │alerts  │   │
              │  │table │  │table   │   │
              │  └──────┘  └────────┘   │
              └─────────────────────────┘
```

## Data Flow

1. **Ingestion**: SIEM service generates/retrieves events → DB insert
2. **Detection**: RL classifier extracts state → Q-network inference → action (SAFE/SUSPICIOUS/DANGEROUS)
3. **Response**: Firewall blocks, alerts triggered, audit logged
4. **Presentation**: Dashboard renders metrics, charts, map from DB data

## Key Design Decisions

- **RL over rule-based**: Self-improving threat classification via Q-learning
- **JSON file auth**: Portable, no external auth service dependency
- **Supabase PostgREST**: Cloud-native, no ORM overhead
- **Local fallback**: App runs fully offline when DB unreachable

## Incident Recovery Runbook

### App Not Loading
1. Check Streamlit Cloud logs for import errors
2. Verify `requirements.txt` has all deps
3. Check if Supabase credentials are set in secrets

### DB Connection Failed
1. App falls back to local JSON — data persists in `data/local_db.json`
2. Check Supabase dashboard for quota/rate limits
3. Re-deploy to pick up new credentials

### RL Accuracy Dropped
1. Check `data/rl_weights/` for corrupted `.npz` files
2. Delete weights to force re-training with fresh architecture
3. Monitor training episodes via RL Intelligence bar

### Security Incident
1. Check `data/audit_log.json` for suspicious actions
2. Review IP blocks in `data/firewall_blocklist.json`
3. Disable compromised accounts via admin panel
