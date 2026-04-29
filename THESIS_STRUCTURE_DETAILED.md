# CORTEX: AI-Driven Autonomous SOC
## Exhaustive Thesis Structure & Content Guide

This document serves as your master blueprint for writing the B.Tech thesis. It takes your proposed 7-chapter structure and expands every single section with the **exact technical details, bullet points, and side-headings** you need to write. You can literally use this as the skeleton for your thesis document.

---

### CHAPTER 1: INTRODUCTION

**1.1 Overview: The evolution of SOC from manual to autonomous**
*   **The Dawn of Cybersecurity:** Early perimeter defenses (firewalls, antivirus).
*   **The Rise of the SOC:** Centralized teams monitoring networks using logs.
*   **Introduction of SIEM:** First generation of log aggregation and correlation based on static signatures.
*   **The Autonomous Paradigm:** Moving from descriptive security (what happened) to prescriptive/autonomous security (CORTEX - mitigating it automatically using agentic AI).

**1.2 Problem Statement: Alert fatigue and the failure of static SIEM rules**
*   **The Scale Problem:** Modern enterprise networks generate millions of logs per day.
*   **Alert Fatigue:** SOC analysts face impossible volumes of alerts, leading to burnout and ignored critical warnings (the "Boy Who Cried Wolf" syndrome).
*   **Limitations of Static Rules (SIEM):** Traditional SIEMs rely strictly on `IF-THEN` rules (e.g., *IF password failed 5 times THEN alert*). Attackers easily bypass these by slightly changing their techniques (e.g., "low and slow" attacks).
*   **Zero-Day Blindness:** Signature-based systems cannot detect never-before-seen attacks.

**1.3 Motivation: Why Reinforcement Learning (RL) is the solution for tactical response**
*   **Beyond Classification:** Supervised ML can *detect* an attack, but it cannot *choose an action*.
*   **The Tactical Advantage of RL:** RL agents learn by interacting with the environment. They map states (network telemetry) to actions (Block, Restrict, Monitor).
*   **Continuous Adaptation:** The RL agent (DQN) continuously trains via rewards, adapting to evolving adversary behavior without requiring a human to write new rules.
*   **Bridging the Gap:** Fusing anomaly detection (Isolation Forest) with decision-making (RL) mirrors human cognitive response minus the physiological limitations.

**1.4 Objectives**
*   **Primary Goal:** Build an end-to-end intelligent pipeline that mimics a Tier-1 and Tier-2 SOC analyst.
*   **Performance Objective 1 (False Positive Reduction):** Reduce false positive alert saturation by ~80% utilizing the 7-Gate Governance Framework.
*   **Performance Objective 2 (Response Latency):** Achieve sub-500ms end-to-end detection-to-mitigation latency, neutralizing threats before significant lateral movement can occur.
*   **Secondary Goal:** Build a realistic live SIEM dashboard for operational visualization using Streamlit.

**1.5 Organization of Thesis**
*   Provide a brief 1-2 sentence roadmap detailing what Chapters 2 through 7 cover.

---

### CHAPTER 2: LITERATURE SURVEY & BACKGROUND

**2.1 Traditional Defense Systems: Intrusion Detection Systems (IDS) and SIEM**
*   **IDS/IPS Arc:** Network-based vs. Host-based detection.
*   **The SIEM Architecture:** Ingestion, Correlation, Alerting.
*   **Vulnerabilities in Traditional Methods:** High latency between detection and manual human response. Reliance on outdated Threat Intelligence feeds.

**2.2 Machine Learning in Security: Supervised vs. Unsupervised**
*   **Supervised Learning:** Needs heavily labeled datasets (Random Forest, SVM). Suffers from model drift when attacker vectors change.
*   **Unsupervised Learning (Isolation Forest):** Why CORTEX uses Isolation Forest (IF). IF isolates anomalies by randomly partitioning data rather than profiling normal behavior, making it highly effective for catching zero-day volumetric bursts.
*   **Fuzzy C-Means Clustering:** Grouping disparate network behaviors into soft clusters to identify statistical momentum in attack chains.

**2.3 Reinforcement Learning: Principles of Markov Decision Processes (MDP)**
*   **The RL Framework:** The Agent, the Environment, States ($S$), Actions ($A$), and Rewards ($R$).
*   **MDP in Network Security:** Defining the state as a highly compressed 12-dimensional vector of network telemetry (bytes_in, tcp_flags, etc.).
*   **Deep Q-Networks (DQN):** Why Q-learning needed deep neural networks to handle continuous network state spaces.

**2.4 Existing Gap: The "Human-in-the-Loop" bottleneck in current MSSPs**
*   **The Tier-1 Analyst Bottleneck:** Humans take 15-30 minutes just to contextualize an alert context (checking IP rep, looking up user).
*   **The Agentic AI Solution:** Removing the human from the *immediate* execution loop and elevating them to a supervisory/governance role over the AI.

---

### CHAPTER 3: SYSTEM REQUIREMENTS & TECH STACK

**3.1 Hardware Requirements**
*   **Training Constraints:** CPU/GPU profiling needed for training the DQN (PyTorch hardware acceleration).
*   **Deployment Environment:** Resource costs for running FastAPI, Streamlit, and PostgREST securely in cloud environments. Minimum RAM (8GB) and Storage specs.

**3.2 Software Requirements & Architecture**
*   **Backend:** Python 3.10+, FastAPI for asynchronous microservices.
*   **Machine Learning:** PyTorch (DQN and Neural layers), Scikit-Learn (Isolation Forest), Pandas/NumPy.
*   **Frontend Data-Viz:** Streamlit for live bidirectional SOC interfaces.
*   **Database:** Supabase (PostgreSQL with PostgREST) for high-frequency time-series log writes.

**3.3 Data Sources: NSL-KDD benchmark & Real-time ingestion**
*   **Benchmark Data:** NSL-KDD dataset structure—why it's the academic standard for evaluating IDS systems.
*   **Live Simulation (Hollywood Simulator):** Creating high-entropy, realistic telemetry (RCE shells, SQLi, DDoS) to simulate modern attacks.
*   **Continuous Ingestion:** The architecture of the asynchronous continuous feeder pushing 30+ events every 30 seconds into Supabase.

---

### CHAPTER 4: SYSTEM ARCHITECTURE & METHODOLOGY

**4.1 The CORTEX Blueprint: High-level architectural diagram**
*   **The 4 Pillars:** Ingestion Engine $\to$ AI Triage Engine $\to$ Governance Pipeline $\to$ Visualization.
*   *(Note: You will need to insert your architecture topology diagram here in the final thesis).*

**4.2 Data Preprocessing & Formatting**
*   **State Extraction:** Flattening raw JSON network logs into the 12-dimensional vector.
*   **Z-Score Normalization:** Standardizing inputs so high-volume traffic (ports, byte counts) doesn't over-saturate neural weights.
*   **Tanh Activation:** Squash values between -1 and 1 to stabilize DQN gradients.

**4.3 The AI Detection Engine (The Core Brain)**
*   **Phase 1: Unsupervised Layer (Isolation Forest)**
    *   Generates an initial `anomaly_score`.
    *   Splits traffic into 'baseline' vs 'outliers'.
*   **Phase 2: Decision Layer (Deep Q-Network)**
    *   **Architecture:** 12 (Input) $\to$ 128 (Hidden) $\to$ 128 (Hidden) $\to$ 3 (Outputs/Actions).
    *   **Action Space:** Safe, Suspicious, Dangerous.

**4.4 Governance Pipeline: The 7-Gate Security System**
*   *Detail every gate as it acts as your defense-in-depth framework:*
    *   **Gate 1:** Zero-Trust Boundary (API Header Validation).
    *   **Gate 2:** Rate Limiting (Token Bucket algorithm).
    *   **Gate 3:** Payload Sanitization (XSS/SQLi Regex stripping).
    *   **Gate 4:** SIEM Schema Enforcer (JSON struct validation).
    *   **Gate 5:** Live Threat Correlation (OTX/VirusTotal OSINT).
    *   **Gate 6:** Mathematical Outlier Engine (Fuzzy Clustering).
    *   **Gate 7:** DQN Final Execution Policy.

**4.5 Agentic Workflow: Natural Language Copilot**
*   **Integration:** Groq API (Llama-3 LLM).
*   **Automated Contextualization:** Generating human-readable MITRE ATT&CK mitigation plans instantly based on JSON alert context.
*   **The Copilot Interface:** Allowing SOC analysts to query the status of the database via natural language.

---

### CHAPTER 5: IMPLEMENTATION & TRAINING

**5.1 Database Schema (Supabase/PostgreSQL)**
*   **`events` Table:** Schema details (`id`, `timestamp`, `event_type`, `severity`, `source_ip`, `raw_log`).
*   **`alerts` Table:** Schema mapped to generated high-severity violations.
*   **`mitigations` Table/Logs:** How actions taken by the RL agent are persisted.

**5.2 DQN Training Dynamics**
*   **Experiential Replay Buffer:** How the agent stores transitions `(State, Action, Reward, Next_State)`. Minibatch randomly sampling 32 vectors to break correlation.
*   **Epsilon-Greedy Strategy:** Exploration (random actions) vs. Exploitation (using network weights), decaying $\epsilon$ from 1.0 to 0.05.
*   **Autonomous Reward Function:**
    *   $+10$ for correctly identifying Danger (based on OSINT/IF alignment).
    *   $-10$ for false positives.
    *   $+1$ for classifying safe benign traffic.

**5.3 API Development & Services**
*   **FastAPI Routing:** How `/api/v1/ingest` catches raw logs.
*   **Concurrency:** Using Python `async/await` to handle threat intel lookups (VirusTotal) without blocking the main SIEM pipeline.
*   **State Management:** Integrating all modules (`live_monitor.py`, `siem_service.py`, `rl_threat_classifier.py`) gracefully.

---

### CHAPTER 6: RESULTS & PERFORMANCE ANALYSIS

**6.1 Accuracy & Model Metrics**
*   **Evaluation Metrics:** Formulas and charts for Precision, Recall, and overall Accuracy (~91.7% from RL dashboard).
*   **Confusion Matrix Context:** Discussing False Positives vs True Negatives in the context of network defense.

**6.2 Latency Testing**
*   **Real-time Definition:** Proving the framework processes end-to-end telemetry.
*   **Latency Breakdown:**
    *   API Ingestion overhead.
    *   ML Inference Time (Isolation Forest + DQN forward pass).
    *   DB Write operations.
    *   Total latency mapping to the target $<$500ms constraint (proving 48+ events/min throughput).

**6.3 Comparative Study: CORTEX vs. Traditional Systems**
*   **Table Comparison:**
    *   SIEM (Static rules, high false positive, manual response).
    *   SOAR (Automated playbooks, but brittle to zero-days).
    *   CORTEX (Autonomous learning, dynamic response, highly resilient).

**6.4 UI Walkthrough & Operation**
*   **Timeline Analysis:** How auto-generated MITRE ATT&CK progression stages are visualized.
*   **SIEM Live Feed:** Correlation engines, probabilistic attack chain mappings, dynamic EPS counting.
*   **Copilot Interaction:** Showcasing how the analyst interacts with the system.

---

### CHAPTER 7: CONCLUSION & FUTURE SCOPE

**7.1 Summary of Contributions**
*   Successful architecture of a self-sustaining SOC framework using multi-model AI.
*   Implementation of the 7-Gate Governance system proving RL models can be deployed safely.

**7.2 System Limitations**
*   **Encrypted Traffic:** Difficulty dealing with payloads using modern TLS 1.3 without SSL termination.
*   **Third-Party API Limits:** Dependence on external OSINT APIs (VirusTotal, OTX) subject to rate limiting during massive volumetric layer-7 attacks.

**7.3 Future Directions & Scalability**
*   **Federated Learning (FedAvg):** Expanding CORTEX to cross-cloud deployments where multiple organizations train the same DQN without sharing underlying PII/logs.
*   **Deep Packet Inspection (PCAP):** Shifting from log-analysis to real-time micro-packet analysis utilizing eBPF capabilities.

---
**Note to Student:** Each of these bullet points should map to 1 to 3 paragraphs of text in your final Word processing document. Use equations for the DQN reward function and normalizations to boost academic density. Use the Streamlit screenshots (like the one we just took) in Chapter 6!
