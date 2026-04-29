# AI-Driven Autonomous SOC (Security Operations Center)
## Final Year Project Documentation

**Project Title:** AI-Driven Autonomous SOC Platform
**Domain:** Cybersecurity / Artificial Intelligence
**Author:** Krishna Akshath

---

## 1. Project Overview & Problem Statement

### The Problem
Traditional Security Operations Centers (SOCs) are overwhelmed by the sheer volume of security alerts (Alert Fatigue). Human analysts cannot manually review thousands of events per second, leading to delayed responses, missed threats, and high operational costs.

### The Solution
This project implements an **AI-Driven Autonomous SOC** that automates the entire threat lifecycle: **Detection, Analysis, Decision, and Response**. By leveraging Machine Learning (Random Forest / Isolation Forest) and Threat Intelligence APIs (AlienVault OTX, VirusTotal), the system serves as a "Virtual Analyst" that operates 24/7 with zero fatigue.

### Key Innovations
1.  **Autonomous Decision Engine:** AI decides whether to BLOCK, RESTRICT, or ALLOW traffic without human intervention.
2.  **Dynamic Threat Mapping:** Real-time visualization of global threats using OTX API data.
3.  **Zero-Trust Architecture:** Strict Role-Based Access Control (RBAC) and Multi-Factor Authentication (MFA).

---

## 2. System Architecture

The system follows a modular microservices-like architecture, with a **Streamlit** frontend and a **Python** backend powered by specialized engines.

```mermaid
graph TD
    User[Admin / Analyst] -->|HTTPS| Frontend[Streamlit Dashboard]
    
    subgraph "Core System"
        Frontend --> Auth[Auth Manager (RBAC + 2FA)]
        Frontend --> Backend[Services Layer]
        
        Backend --> MLEngine[ML Engine (RF Classifier)]
        Backend --> ThreatIntel[Threat Intel Service]
        Backend --> Alerting[Alert Service]
    end
    
    subgraph "External Integration"
        ThreatIntel <-->|API| OTX[AlienVault OTX]
        ThreatIntel <-->|API| VT[VirusTotal]
        Alerting -->|SMTP| Gmail[Email Alerts]
    end
    
    MLEngine -->|Risk Score| Decision[Decision Logic]
    Decision -->|BLOCK/ALLOW| Firewall[Mock Firewall Action]
```

---

## 3. Technology Stack

*   **Language:** Python 3.10+
*   **Frontend Framework:** Streamlit (Custom CSS/JS for Premium UI)
*   **Machine Learning:** Scikit-Learn (Random Forest, Isolation Forest), Pandas, NumPy
*   **Data Visualization:** Plotly Interactive Charts, PyDeck (Maps)
*   **Authentication:** PBKDF2 Hashing, PyOTP (2FA), Persistent Sessions
*   **APIs:** AlienVault OTX, VirusTotal, AbuseIPDB, Gmail SMTP

---

## 4. Module-by-Module Explanation

### A. Authentication Module (`auth/`)
Handles strict security access to the platform.
*   **`auth_manager.py`**: Manages user sessions, password hashing (PBKDF2), and persistent sessions (Remember Me).
    *   *Key Function:* `check_auth()` handles auto-login via `.local_session` token file.
*   **`two_factor.py`**: Implements Time-based OTP (TOTP) and Email OTP for 2FA.
    *   *Key Function:* `verify_otp()` validates 6-digit codes.
    *   *Key Function:* `is_device_trusted()` checks device fingerprint to bypass 2FA for trusted devices.

### B. Machine Learning Engine (`ml_engine/`)
The brain of the SOC, responsible for analyzing network packets.
*   **`model_train.py`**: (Offline) Trains the Random Forest model on CIC-IDS2017 dataset features.
*   **`ml_scorer.py`**: (Online) Loads the trained model (`rf_model.pkl`) and predicts "Attack Type" and "Risk Score" (0-100) for live events.
    *   *Logic:* Inputs (Source IP, Port, Protocol) -> Transformation -> Prediction.

### C. Services Layer (`services/`)
*   **`threat_intel.py`**: Connects to external APIs.
    *   *Feature:* Fetches live pulses from AlienVault OTX.
    *   *Feature:* `get_country_threat_counts()` parses OTX data to populate the dynamic Threat Map.
*   **`security_scanner.py`**: Performs active scanning (Port Logic, OS Verification).
*   **`live_monitor.py`**: Simulates/Ingests network traffic logs for the Dashboard.

### D. User Interface (`pages/`)
*   **`0_Login.py`**: Premium Login Page with Glassmorphism UI. Features "Admin Only" restriction (Registration Disabled).
*   **`1_Dashboard.py`**: The Command Center.
    *   *Dynamic Data:* Displays "Real-time" metrics that fluctuate to simulate a live network.
    *   *Visuals:* Plotly charts for Attack Distribution and Traffic Timeline.
*   **`3_Threat_Intel.py`**: Global Threat Map.
    *   *Implementation:* Uses PyDeck/Plotly Mapbox. Data is fetched dynamically from OTX API (not static).
*   **`8_Settings.py`**: Admin Configuration.
    *   *Security:* API Keys (masked) and Alert Policies are managed here.
*   **`98_Profile.py`**: User Preferences.
    *   *Feature:* Setup Email Alerts and Change Password.

### E. Alerting System (`alerting/`)
*   **`alert_service.py`**: Central dispatcher. checks `risk_score > 80` (Critical).
*   **`email_sender.py`**: Sends formatted HTML emails via Gmail SMTP (TLS encrypted).
    *   *Removal:* All Telegram related code was removed for professional streamlining.

---

## 5. Workflow: How It Works

1.  **Ingestion:** Network logs (Simulated or Pcap) enter the system.
2.  **Enrichment:** `threat_intel.py` checks IPs against AbuseIPDB/OTX.
3.  **Analysis:** `ml_scorer.py` calculates a Risk Score (e.g., 85/100).
4.  **Decision:**
    *   **Score > 70 (Critical):** AI Decision = **BLOCK**.
    *   **Score 30-70 (Suspicious):** AI Decision = **RESTRICT**.
    *   **Score < 30 (Safe):** AI Decision = **ALLOW**.
5.  **Action:**
    *   Dashboard updates counters.
    *   **Alert:** If Critical, `alert_service` sends an email to the Admin immediately.

---

## 6. How to Run

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Launch Application:**
    ```bash
    streamlit run main.py
    ```
    *First-time setup will create the admin account.*
3.  **Login:**
    *   Email: `admin@soc.local` / Password: `admin123`
    *   Map API: Enter OTX Key in Settings.
