# SLOs — Service Level Objectives

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Ingestion Latency** | < 5 s (p99) | Time from SIEM event creation to DB write |
| **Alert Freshness** | < 30 s | Time from threat detection to notification dispatch |
| **Dashboard Load** | < 3 s (p95) | Time for main dashboard to fully render |
| **RL Inference** | < 100 ms (p99) | Time for a single classify() call |
| **API Availability** | 99.5% uptime | Streamlit Cloud health checks |
| **Test Suite Pass Rate** | 100% (unit) | CI must always pass unit tests |
| **Coverage** | ≥ 80% | On `services/` and `ml_engine/` |

## Degradation Tiers

| Tier | Condition | Behaviour |
|------|-----------|-----------|
| **Healthy** | All APIs up, DB connected | Full functionality |
| **Degraded** | VirusTotal/OTX down | Cache-only threat intel, UI warning |
| **Offline** | Supabase unreachable | Local JSON fallback, limited persistence |
| **Critical** | App crash loop | Auto-restart via Streamlit Cloud, alert via Telegram |

## Monitoring

- Dashboard health gauge reflects composite of active SLO metrics
- RL accuracy tracked in real-time on the RL Intelligence bar
- Audit log captures all sensitive changes for post-incident review
