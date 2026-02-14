# AI-Driven Autonomous SOC

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![AI Model](https://img.shields.io/badge/AI-Llama%203.3%20(Groq)-purple.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An enterprise-grade, AI-powered Security Operations Center (SOC) with real-time log ingestion, persistent incident tracking, and autonomous response playbooks.

## Key Features

- **🛡️ Real-Time Dashboard**: Live monitoring of simulated or real network traffic.
- **🧠 Cortex AI**: Autonomous security analyst powered by **Llama-3.3-70b** (via Groq) for threat hunting and explaining alerts.
- **🔍 Advanced Analytics**: 
  - **Isolation Forest**: Unsupervised anomaly detection on NSL-KDD dataset.
  - **Fuzzy C-Means**: Soft clustering for attack categorization.
- **⚡ Autonomous Response**: Automated playbooks for IP blocking, User Quarantine, and Ransomware containment.
- **📂 Persistence**: SQLite-backed event logging and incident tracking (survives restarts).
- **🕸️ Zero Trust Architecture**: Continuous risk scoring for every user and entity.

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/your-username/ai-driven-autonomous-soc.git
cd ai-driven-autonomous-soc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.soc_config.json` file in the root directory (optional but recommended for API keys):

```json
{
    "gmail_email": "your-bot@gmail.com",
    "gmail_password": "your-app-password",
    "GROQ_API_KEY": "gsk_..."
}
```

*Note: You can also set these as Environment Variables or Streamlit Secrets.*

### 3. Run the SOC

```bash
streamlit run streamlit_app.py
```

Access the dashboard at **http://localhost:8501**

## Project Structure

```
├── streamlit_app.py          # Main Entry Point (Redirects to Dashboard)
├── Home.py                   # Background Service Initialization
├── pages/
│   ├── 01_Dashboard.py       # Main Operations View
│   ├── 11_Analysis.py        # ML Engine (Isolation Forest/Fuzzy C-Means)
│   ├── 21_CORTEX.py          # AI Chat Interface
│   ├── 24_SIEM.py            # Log Viewer & Correlation
│   └── ... (20+ modules)
├── services/
│   ├── ai_assistant.py       # Groq/Llama Interface
│   ├── auth_service.py       # User Management & 2FA
│   ├── database.py           # SQLite Persistence Layer
│   ├── log_ingestor.py       # Real-time Log Tailing
│   └── ...
├── ml_engine/
│   ├── isolation_forest.py   # Anomaly Detection Model
│   └── fuzzy_clustering.py   # Attack Categorization
└── data/                     # Persistent Storage (SQLite, JSON)
```

## AI Integration

This project uses **Groq** for ultra-fast inference with **Llama-3.3-70b**. 
1. Get a free API Key from [console.groq.com](https://console.groq.com).
2. Add it to your configuration (see above).
3. Chat with CORTEX in the "CORTEX AI" page to hunt threats or analyze files.

## License

MIT License - See LICENSE file for details.

## Features

- **Multi-Page Dashboard**: Dashboard, Alerts, Threat Map, Forensics, Reports, Settings
- **Real-time Monitoring**: Auto-refresh with configurable intervals
- **AI-Powered Analysis**: Gemini integration for threat analysis
- **IEEE Format Reports**: Professional security reports
- **Alerting**: Gmail and Telegram notifications
- **Zero Trust**: Risk-based access decisions (BLOCK/RESTRICT/ALLOW)

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-username/soc-dashboard.git
cd soc-dashboard

# Create virtual environment
python3 -m venv soc-env
source soc-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run dashboard.py
```

Access at **http://localhost:8501**

## Configuration

### Gmail Alerts
1. Enable 2FA on your Gmail account
2. Generate an App Password (Google Account → Security → App Passwords)
3. Configure in Settings → Gmail Alerts

### Telegram Alerts
1. Create a bot via @BotFather
2. Get your Chat ID from @userinfobot
3. Configure in Settings → Telegram Alerts

### AI Integration
1. Get free API key from [Google AI Studio](https://aistudio.google.com/)
2. Configure in Settings → AI Integration

## Deployment

### Streamlit Cloud
1. Push to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect repository
4. Set secrets in Advanced Settings

### Docker
```bash
docker build -t soc-dashboard .
docker run -p 8501:8501 soc-dashboard
```

## Project Structure

```
├── dashboard.py              # Main entry point
├── pages/
│   ├── 1_🏠_Dashboard.py     # Security metrics
│   ├── 2_🚨_Alerts.py        # Active alerts
│   ├── 3_🌍_Threat_Map.py    # Geographic view
│   ├── 4_🔬_Forensics.py     # Analysis tools
│   ├── 5_📊_Reports.py       # IEEE reports
│   └── 6_⚙️_Settings.py      # Configuration
├── ai_engine/
│   └── threat_analyzer.py    # Gemini AI
├── alerting/
│   ├── telegram_bot.py       # Telegram alerts
│   └── email_sender.py       # Gmail alerts
└── .streamlit/
    └── config.toml           # Theme config
```

## License

MIT License - See LICENSE file for details.
