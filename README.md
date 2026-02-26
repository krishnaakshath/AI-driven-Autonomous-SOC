# AI-Driven Autonomous SOC

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![AI Model](https://img.shields.io/badge/AI-Llama%203.3%20(Groq)-purple.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An enterprise-grade, AI-powered Security Operations Center featuring real-time threat detection, autonomous response, and predictive intelligence — all in a single platform.

## Core Features

| Layer | Feature | Technology |
|---|---|---|
| 🛡️ **Dashboard** | Real-time metrics, Global Threat Matrix, Live Action Ticker | Plotly, Supabase |
| 🧠 **CORTEX AI** | Autonomous security analyst with tool-use | Llama-3.3-70b (Groq) |
| 🔬 **ML Insights** | Isolation Forest anomaly detection, Fuzzy C-Means clustering | scikit-learn, NSL-KDD |
| 🔮 **Neural Predictor** | LSTM-style probability forecasts for future attacks | Custom time-series |
| ⚡ **SOAR Workbench** | One-click playbooks (Quarantine, Revocation, Termination) | Custom SOAR engine |
| 🔥 **Active Firewall** | Real-time WAF with stateful auto-shun | Regex + DB-backed |
| 🕵️ **Forensics** | AI-powered root cause analysis with visual attack graphs | CORTEX + Mermaid.js |
| 📊 **Reports** | IEEE-format security reports with executive summaries | PDF generation |
| 🌍 **Threat Intel** | Live feeds from AbuseIPDB, VirusTotal, OTX | REST APIs |
| 🔐 **Auth** | bcrypt hashing, TOTP 2FA, session persistence | bcrypt, pyotp |

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

Create `.soc_config.json` in the root (or use env vars / Streamlit Secrets):

```json
{
    "GROQ_API_KEY": "gsk_...",
    "gmail_email": "your-bot@gmail.com",
    "gmail_password": "your-app-password"
}
```

## Project Structure

```
├── dashboard.py              # Main entry point & navigation
├── pages/
│   ├── 00_User_Guide.py      # Interactive platform guide
│   ├── 01_Dashboard.py       # SOC command center
│   ├── 02_Executive.py       # C-suite overview
│   ├── 03_Alerts.py          # Alert management
│   ├── 06_Threat_Intel.py    # Threat intelligence feeds
│   ├── 11_Analysis.py        # ML Insights (IF + FCM)
│   ├── 12_SOAR_Workbench.py  # Autonomous response
│   ├── 13_Forensics.py       # Neural forensics
│   ├── 21_CORTEX.py          # AI assistant
│   ├── 24_SIEM.py            # Log aggregation
│   ├── 25_Firewall_Control.py# WAF management
│   └── ... (20+ modules)
├── services/
│   ├── ai_assistant.py       # Groq/Llama interface
│   ├── auth_service.py       # Authentication & 2FA
│   ├── database.py           # Supabase persistence layer
│   ├── firewall_service.py   # Active WAF engine
│   ├── siem_service.py       # SIEM event correlation
│   └── threat_intel.py       # AbuseIPDB/VT/OTX integration
├── ml_engine/
│   ├── isolation_forest.py   # Anomaly detection (NSL-KDD trained)
│   ├── fuzzy_clustering.py   # Threat categorization
│   └── neural_predictor.py   # Predictive threat engine
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
