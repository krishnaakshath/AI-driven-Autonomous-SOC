# Reinforcement Learning Audit Report
## AI-Driven Autonomous SOC Platform

**Generated:** 2026-03-03 17:34 IST  
**Author:** Automated RL Integration Pipeline  
**Commit:** `32de540`

---

## 1. RL Architecture Overview

The SOC platform uses **Deep Q-Network (DQN)** reinforcement learning with the following architecture:

| Component | Detail |
|-----------|--------|
| **Algorithm** | DQN with Experience Replay |
| **Neural Network** | 3-layer MLP (input → 32 → 16 → n_actions) |
| **Activation** | ReLU (hidden), Linear (output) |
| **Optimizer** | SGD with gradient clipping |
| **Exploration** | ε-greedy (1.0 → 0.05, decay 0.995/episode) |
| **Replay Buffer** | 3,000 experiences per agent |
| **Framework** | Pure NumPy (no TensorFlow/PyTorch dependency) |
| **Training** | Background service every ~10 minutes |

---

## 2. RL Agents Inventory

### 2.1 Threat Classifier (Primary Agent)
| Property | Value |
|----------|-------|
| **File** | `ml_engine/rl_threat_classifier.py` |
| **State Dim** | 8 features |
| **Actions** | SAFE, SUSPICIOUS, DANGEROUS |
| **Ground Truth** | 5-signal composite (IF 30%, Severity 25%, Event Type 25%, Port 10%, Traffic 10%) |
| **Auto-Reward** | Multi-signal intelligence — no manual input needed |

### 2.2 Alert Prioritizer
| Property | Value |
|----------|-------|
| **File** | `ml_engine/rl_agents.py` → `RLAlertPrioritizer` |
| **Page** | `pages/03_Alerts.py` |
| **State Dim** | 6 features (severity, danger keywords, suspicious keywords, risk score, status, hour) |
| **Actions** | P1-CRITICAL, P2-QUEUE, P3-LOW |
| **Ground Truth** | Severity + keyword pattern matching + alert status |

### 2.3 SOAR Auto-Responder
| Property | Value |
|----------|-------|
| **File** | `ml_engine/rl_agents.py` → `RLSOARResponder` |
| **Page** | `pages/12_SOAR_Workbench.py` |
| **State Dim** | 6 features (severity, malware flag, brute flag, exfil flag, status, hour) |
| **Actions** | BLOCK-IP, ISOLATE-HOST, RATE-LIMIT, ALERT-ONLY, FULL-QUARANTINE |
| **Ground Truth** | Attack type keyword matching + severity level |

### 2.4 Firewall Policy Optimizer
| Property | Value |
|----------|-------|
| **File** | `ml_engine/rl_agents.py` → `RLFirewallOptimizer` |
| **Page** | `pages/25_Firewall_Control.py` |
| **State Dim** | 6 features (port, severity, blocked flag, malware port flag, traffic ratio, packet count) |
| **Actions** | ALLOW, RATE-LIMIT, BLOCK |
| **Ground Truth** | Malware port database + event type + severity |

### 2.5 Threat Intel Scorer
| Property | Value |
|----------|-------|
| **File** | `ml_engine/rl_agents.py` → `RLThreatIntelScorer` |
| **Page** | `pages/06_Threat_Intel.py` |
| **State Dim** | 5 features (count, severity, threats, count threshold, severity threshold) |
| **Actions** | MONITOR, ELEVATED, CRITICAL |
| **Ground Truth** | Threat count thresholds + severity level |

### 2.6 Hunt Recommender
| Property | Value |
|----------|-------|
| **File** | `ml_engine/rl_agents.py` → `RLHuntRecommender` |
| **Page** | `pages/10_Threat_Hunt.py` |
| **State Dim** | 5 features (high-value category, result count, hour, name risk, has results) |
| **Actions** | HUNT-NOW, SCHEDULE, SKIP |
| **Ground Truth** | MITRE category + historical result yield |

---

## 3. Training Pipeline

```
Background Service (cloud_background.py)
    │
    ├── Every ~10 min: Pull 30 recent events from Supabase DB
    │
    ├── Threat Classifier: Classify → Auto-reward → Train Q-network → Save
    │
    └── 5 Domain Agents: Classify → Auto-reward → Train → Save (15 events each)
```

### Training Flow Per Agent:
1. **State Extraction** — Event dict → normalized feature vector
2. **ε-Greedy Action** — Random (explore) or Q-network argmax (exploit)
3. **Auto-Reward** — Compare action to ground truth → +1.0 / -0.3 / -1.0
4. **Experience Replay** — Store (s, a, r, s') in buffer
5. **Mini-batch SGD** — Sample 32 experiences, update Q-network
6. **ε Decay** — Reduce exploration rate (0.995× per episode)
7. **Persistence** — Save weights + stats to disk every 20 episodes

---

## 4. Ground Truth Methodology

### Multi-Signal Ground Truth (Threat Classifier)
The primary agent uses **5 weighted intelligence signals** to autonomously determine ground truth:

| Signal | Weight | Source |
|--------|--------|--------|
| Isolation Forest anomaly score | 30% | ML engine |
| Severity level (CRITICAL/HIGH/MED/LOW) | 25% | SIEM metadata |
| Event type keyword matching | 25% | Pattern database (~30 keywords) |
| Port reputation analysis | 10% | Known malware/C2 port database |
| Traffic volume anomalies | 10% | Bytes/packets thresholds |

**Composite Score**: Weighted sum → 0-100 scale → SAFE (<35) / SUSPICIOUS (35-65) / DANGEROUS (>65)

### Domain Agent Ground Truth
Each domain agent uses **rule-based heuristics** matched to its domain:
- **Alerts**: Severity + attack type keywords → P1/P2/P3
- **SOAR**: Attack category → response playbook mapping
- **Firewall**: Port reputation + severity → allow/block decision
- **Threat Intel**: Count thresholds + severity → risk level
- **Hunts**: MITRE category value + historical result yield → priority

---

## 5. Persistence & Model Files

All models persist to: `data/rl_models/`

| File Pattern | Contents |
|-------------|----------|
| `{name}_weights.npz` | Q-network weights (W1, b1, W2, b2, W3, b3) |
| `{name}_stats.json` | Episodes, accuracy, reward history, ε history |
| `rl_replay_buffer.json` | Experience replay buffer (threat classifier only) |

---

## 6. Testing Summary

| Test | Status |
|------|--------|
| RL module import | ✅ Pass |
| Event classification | ✅ Pass |
| Feedback loop | ✅ Pass |
| State extraction | ✅ Pass |
| 5 domain agents import & classify | ✅ Pass |
| Auto-reward for all agents | ✅ Pass |

---

## 7. Pages with RL Integration

| Page | RL Agent | Badge Shown |
|------|----------|-------------|
| Alerts (`03_Alerts.py`) | Alert Prioritizer | `RL:P1` / `RL:P2` / `RL:P3` |
| SOAR Workbench (`12_SOAR_Workbench.py`) | SOAR Responder | `RL: BLOCK-IP (73%)` |
| Firewall Control (`25_Firewall_Control.py`) | Firewall Optimizer | `BLOCK (85%)` per event |
| Threat Intel (`06_Threat_Intel.py`) | Threat Intel Scorer | `RL:CRITICAL` / `RL:MONITOR` |
| Threat Hunt (`10_Threat_Hunt.py`) | Hunt Recommender | `RL:HUNT-NOW` / `RL:SKIP` |
| RL Adaptive (`26_RL_Adaptive.py`) | Threat Classifier | Full dashboard with signal breakdown |

---

## 8. Security Considerations

- **No external network calls** — All RL training happens locally using numpy
- **No PII in state vectors** — Only numeric features extracted from events
- **Bounded exploration** — ε decays to 0.05 (never fully random after training)
- **Gradient clipping** — Prevents training instabilities
- **Replay buffer capped** — 3,000 max to bound memory usage
- **Fail-safe imports** — All RL integrations wrapped in try/except to prevent page crashes

---

## 9. Dependencies

- `numpy` — Neural network and linear algebra
- No TensorFlow, PyTorch, or scikit-learn required for RL

---

*This audit report documents the complete RL integration as of commit `32de540`.*
