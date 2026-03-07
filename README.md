# AI-Driven Autonomous SOC

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![AI Model](https://img.shields.io/badge/AI-Llama%203.3%20(Groq)-purple.svg)
![Supabase](https://img.shields.io/badge/DB-Supabase-green.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An enterprise-grade, AI-powered Security Operations Center featuring real-time threat detection, autonomous response, reinforcement learning, federated learning, and predictive intelligence — all in a single platform.

## Live Demo

**[socdashboard.streamlit.app](https://socdashboard.streamlit.app)**

## Core Features

| Layer | Feature | Technology |
|---|---|---|
| **Dashboard** | Real-time metrics, Global Threat Map (GeoIP), bar chart timeline | Plotly, Supabase |
| **Executive** | C-suite KPIs with hover tooltips, real PDF export, auto-refresh | Dynamic from Supabase |
| **CORTEX AI** | Autonomous security analyst with tool-use and context awareness | Llama-3.3-70b (Groq) |
| **ML Insights** | Isolation Forest anomaly detection, Fuzzy C-Means clustering | scikit-learn, NSL-KDD |
| **RL Adaptive** | DQN reinforcement learning threat classifier with live SIEM events | Custom RL engine |
| **Federated Learning** | Privacy-preserving collaborative training with differential privacy | FedAvg + DP |
| **Neural Predictor** | LSTM-style probability forecasts for future attacks | Custom time-series |
| **SOAR Workbench** | One-click playbooks with dynamic KPIs from Supabase | Custom SOAR engine |
| **Active Firewall** | Real-time WAF with stateful auto-shun | Regex + DB-backed |
| **Forensics** | AI root cause analysis with dynamic Mermaid.js attack graphs | CORTEX + Mermaid |
| **SIEM** | Real-time event ingestion from AlienVault OTX with correlation | OTX API + Supabase |
| **Threat Intel** | Live feeds from AbuseIPDB, VirusTotal, AlienVault OTX | REST APIs |
| **Kill Chain** | MITRE ATT&CK mapping with real alert integration | MITRE framework |
| **Reports** | IEEE-format security reports with PDF generation | ReportLab |
| **Auth** | bcrypt hashing, TOTP 2FA, session persistence, 30-min timeout | bcrypt, pyotp |

## Quick Start

```bash
# Clone & install
git clone https://github.com/KrishnaAkshath/AI-driven-Autonomous-SOC.git
cd AI-driven-Autonomous-SOC
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run
streamlit run dashboard.py
```

Access at **http://localhost:8501**

## Configuration

Create `.soc_config.json` in the root (or use Streamlit Secrets):

```json
{
    "SUPABASE_URL": "https://your-project.supabase.co",
    "SUPABASE_KEY": "your-service-role-key",
    "GROQ_API_KEY": "gsk_...",
    "ABUSEIPDB_KEY": "your-key",
    "VIRUSTOTAL_KEY": "your-key",
    "OTX_API_KEY": "your-key"
}
```

## Project Structure

```
├── dashboard.py              # Main entry point & navigation
├── pages/
│   ├── 00_User_Guide.py      # Interactive platform guide
│   ├── 01_Dashboard.py       # SOC command center + threat map
│   ├── 02_Executive.py       # C-suite KPIs + PDF export
│   ├── 03_Alerts.py          # Alert triage & management
│   ├── 04_Logs.py            # Intelligent log analyzer
│   ├── 05_Timeline.py        # Event timeline visualization
│   ├── 06_Threat_Intel.py    # VT/AbuseIPDB/OTX integration
│   ├── 08_Kill_Chain.py      # MITRE ATT&CK mapping
│   ├── 09_OSINT_Feeds.py     # Open-source intelligence
│   ├── 10_Threat_Hunt.py     # Proactive threat hunting
│   ├── 11_Analysis.py        # ML Insights (IF + FCM)
│   ├── 12_SOAR_Workbench.py  # Autonomous response
│   ├── 13_Forensics.py       # Digital forensics
│   ├── 15_Scanners.py        # Network scanners
│   ├── 19_Reports.py         # Report generation
│   ├── 21_CORTEX.py          # AI assistant
│   ├── 24_SIEM.py            # SIEM event management
│   ├── 25_Firewall_Control.py# WAF management
│   ├── 26_RL_Adaptive.py     # Reinforcement learning
│   └── 27_Federated_Learning.py # Federated learning
├── services/
│   ├── ai_assistant.py       # Groq/Llama interface
│   ├── auth_service.py       # Authentication & 2FA
│   ├── database.py           # Supabase persistence layer
│   ├── firewall_service.py   # Active WAF engine
│   ├── report_generator.py   # PDF report builder
│   ├── siem_service.py       # SIEM event correlation
│   └── threat_intel.py       # AbuseIPDB/VT/OTX integration
├── ml_engine/
│   ├── isolation_forest.py   # Anomaly detection (NSL-KDD)
│   ├── fuzzy_clustering.py   # Threat categorization
│   ├── neural_predictor.py   # Predictive threat engine
│   ├── rl_threat_classifier.py # DQN reinforcement learning
│   ├── rl_agents.py          # RL SOAR responder agents
│   └── federated_learning.py # Privacy-preserving FL
└── ui/
    └── theme.py              # Cyberpunk design system
```

## Deployment

### Streamlit Cloud
1. Push to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Set `dashboard.py` as the main file
4. Add secrets in Advanced Settings

### Docker
```bash
docker build -t soc-dashboard .
docker run -p 8501:8501 soc-dashboard
```

## License

MIT License — See [LICENSE](LICENSE) for details.
