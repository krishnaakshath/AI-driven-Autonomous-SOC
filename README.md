# AI-Driven Autonomous SOC

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An enterprise-grade, AI-powered Security Operations Center with real-time threat detection, Zero Trust enforcement, and automated incident response.

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
