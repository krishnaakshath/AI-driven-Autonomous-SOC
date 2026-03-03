"""
RL Agents — Multi-Domain Reinforcement Learning for SOC
========================================================
5 specialized DQN agents that learn autonomously across every SOC module:
1. AlertPrioritizer    → Ranks alerts P1/P2/P3
2. SOARResponder       → Picks best incident response action
3. FirewallOptimizer   → Learns what to block/allow/rate-limit
4. ThreatIntelScorer   → Scores threat sources Monitor/Elevated/Critical
5. HuntRecommender     → Prioritizes threat hunts HuntNow/Schedule/Skip

All share the same QNetwork architecture from rl_threat_classifier.py
and train automatically via cloud_background.py.
"""

import numpy as np
import os
import json
import time
from datetime import datetime
from typing import Dict, List
from collections import deque

# Reuse QNetwork from threat classifier
from ml_engine.rl_threat_classifier import QNetwork

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rl_models")


# ═══════════════════════════════════════════════════════════════════════════════
# BASE AGENT (shared by all 5)
# ═══════════════════════════════════════════════════════════════════════════════
class BaseRLAgent:
    """Base DQN agent — subclass for each SOC domain."""

    def __init__(self, name: str, n_features: int, actions: List[str],
                 epsilon=1.0, epsilon_min=0.05, epsilon_decay=0.995,
                 gamma=0.95, batch_size=32, lr=0.001):
        self.name = name
        self.actions = actions
        self.n_actions = len(actions)
        self.n_features = n_features
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.gamma = gamma
        self.batch_size = batch_size

        self.q_net = QNetwork(lr=lr)
        # Reinitialize with correct dimensions
        self.q_net.W1 = np.random.randn(n_features, 32) * np.sqrt(2.0 / n_features)
        self.q_net.W3 = np.random.randn(16, self.n_actions) * np.sqrt(2.0 / 16)
        self.q_net.b3 = np.zeros(self.n_actions)

        self.replay_buffer: deque = deque(maxlen=3000)
        self.stats = {
            "classifications": 0, "episodes": 0,
            "correct": 0, "incorrect": 0,
            "total_reward": 0.0,
            "reward_history": [], "accuracy_history": [], "epsilon_history": [],
            "action_counts": {a: 0 for a in actions},
        }
        self._weights_path = os.path.join(MODEL_DIR, f"{name}_weights.npz")
        self._stats_path = os.path.join(MODEL_DIR, f"{name}_stats.json")
        self._load()

    def _sf(self, val, default=0.0):
        if val is None:
            return default
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def extract_state(self, data: Dict) -> np.ndarray:
        """Override in subclass."""
        raise NotImplementedError

    def classify(self, data: Dict) -> Dict:
        state = self.extract_state(data)
        if np.random.random() < self.epsilon:
            idx = np.random.randint(self.n_actions)
        else:
            q = self.q_net.forward(state.reshape(1, -1))[0]
            idx = int(np.argmax(q))

        q = self.q_net.forward(state.reshape(1, -1))[0]
        exp_q = np.exp(q - np.max(q))
        conf = float((exp_q / exp_q.sum())[idx])

        self.stats["classifications"] += 1
        self.stats["action_counts"][self.actions[idx]] += 1

        return {
            "action": self.actions[idx],
            "action_idx": idx,
            "q_values": q.tolist(),
            "confidence": round(conf * 100, 1),
            "state": state.tolist(),
        }

    def learn(self, state: np.ndarray, action_idx: int, reward: float):
        self.replay_buffer.append({
            "state": state.tolist(), "action": action_idx,
            "reward": reward, "next_state": state.tolist(), "done": True,
        })
        self.stats["total_reward"] += reward
        if reward > 0:
            self.stats["correct"] += 1
        else:
            self.stats["incorrect"] += 1
        total = self.stats["correct"] + self.stats["incorrect"]
        acc = round(self.stats["correct"] / total * 100, 1) if total > 0 else 0

        self.stats["reward_history"].append(reward)
        self.stats["reward_history"] = self.stats["reward_history"][-200:]
        self.stats["accuracy_history"].append(acc)
        self.stats["accuracy_history"] = self.stats["accuracy_history"][-200:]

        self._train_step()
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.stats["epsilon_history"].append(round(self.epsilon, 4))
        self.stats["epsilon_history"] = self.stats["epsilon_history"][-200:]
        self.stats["episodes"] += 1

        if self.stats["episodes"] % 20 == 0:
            self.save()

    def _train_step(self):
        if len(self.replay_buffer) < self.batch_size:
            return
        indices = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
        batch = [self.replay_buffer[i] for i in indices]
        states = np.array([b["state"] for b in batch])
        actions = np.array([b["action"] for b in batch])
        rewards = np.array([b["reward"] for b in batch])

        current_q = self.q_net.forward(states)
        target_q = current_q.copy()
        for i in range(self.batch_size):
            target_q[i, actions[i]] = rewards[i]
        self.q_net.forward(states)
        self.q_net.backward(target_q)

    def save(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        self.q_net.save(self._weights_path)
        with open(self._stats_path, "w") as f:
            json.dump(self.stats, f, indent=2, default=str)

    def _load(self):
        self.q_net.load(self._weights_path)
        if os.path.exists(self._stats_path):
            try:
                with open(self._stats_path) as f:
                    saved = json.load(f)
                self.stats.update(saved)
                eps_hist = self.stats.get("epsilon_history", [])
                if eps_hist:
                    self.epsilon = max(self.epsilon_min, eps_hist[-1])
            except Exception:
                pass

    def get_stats(self) -> Dict:
        total = self.stats["correct"] + self.stats["incorrect"]
        return {
            **self.stats,
            "name": self.name,
            "epsilon": round(self.epsilon, 4),
            "buffer_size": len(self.replay_buffer),
            "accuracy": round(self.stats["correct"] / total * 100, 1) if total > 0 else 0,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ALERT PRIORITIZER
# ═══════════════════════════════════════════════════════════════════════════════
class RLAlertPrioritizer(BaseRLAgent):
    """Learns which alerts matter most → P1 (Investigate Now) / P2 (Queue) / P3 (Ignore)."""

    DANGEROUS_TYPES = ["malware", "ransomware", "trojan", "c2", "exfiltration", "exploit", "injection"]
    SUSPICIOUS_TYPES = ["scan", "brute", "failed", "blocked", "denied", "anomal"]

    def __init__(self):
        super().__init__("alert_prioritizer", n_features=6, actions=["P1-CRITICAL", "P2-QUEUE", "P3-LOW"])

    def extract_state(self, alert: Dict) -> np.ndarray:
        sev_map = {"LOW": 0.1, "MEDIUM": 0.4, "HIGH": 0.7, "CRITICAL": 1.0}
        severity = sev_map.get(str(alert.get("severity", "LOW")).upper(), 0.25)
        title = str(alert.get("title", alert.get("type", ""))).lower()
        is_dangerous = 1.0 if any(k in title for k in self.DANGEROUS_TYPES) else 0.0
        is_suspicious = 1.0 if any(k in title for k in self.SUSPICIOUS_TYPES) else 0.0
        risk = self._sf(alert.get("risk_score", 0)) / 100
        status_val = 1.0 if str(alert.get("status", "")).lower() == "open" else 0.0

        try:
            ts = str(alert.get("timestamp", alert.get("time", "")))
            hour = float(datetime.fromisoformat(ts).hour) / 23.0
        except Exception:
            hour = 0.5
        return np.array([severity, is_dangerous, is_suspicious, risk, status_val, hour])

    def auto_reward(self, alert: Dict, classification: Dict) -> Dict:
        action = classification["action"]
        sev = str(alert.get("severity", "LOW")).upper()
        title = str(alert.get("title", alert.get("type", ""))).lower()
        status = str(alert.get("status", "")).lower()

        # Determine expected priority
        if sev == "CRITICAL" or any(k in title for k in self.DANGEROUS_TYPES):
            expected = "P1-CRITICAL"
        elif sev == "HIGH" or any(k in title for k in self.SUSPICIOUS_TYPES):
            expected = "P2-QUEUE"
        elif status in ("false positive", "resolved"):
            expected = "P3-LOW"
        else:
            expected = "P2-QUEUE"

        reward = 1.0 if action == expected else (-0.3 if abs(self.actions.index(action) - self.actions.index(expected)) == 1 else -1.0)
        self.learn(np.array(classification["state"]), classification["action_idx"], reward)
        return {"reward": reward, "expected": expected, "action": action, "correct": reward > 0}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SOAR AUTO-RESPONDER
# ═══════════════════════════════════════════════════════════════════════════════
class RLSOARResponder(BaseRLAgent):
    """Learns optimal incident response: Block / Isolate / RateLimit / AlertOnly / Quarantine."""

    def __init__(self):
        super().__init__("soar_responder", n_features=6,
                         actions=["BLOCK-IP", "ISOLATE-HOST", "RATE-LIMIT", "ALERT-ONLY", "FULL-QUARANTINE"])

    def extract_state(self, incident: Dict) -> np.ndarray:
        sev_map = {"LOW": 0.1, "MEDIUM": 0.4, "HIGH": 0.7, "CRITICAL": 1.0}
        severity = sev_map.get(str(incident.get("severity", "LOW")).upper(), 0.25)
        title = str(incident.get("title", "")).lower()
        is_malware = 1.0 if any(k in title for k in ["malware", "ransomware", "trojan", "c2"]) else 0.0
        is_brute = 1.0 if any(k in title for k in ["brute", "scan", "flood", "ddos"]) else 0.0
        is_exfil = 1.0 if any(k in title for k in ["exfil", "data theft", "leak"]) else 0.0
        status_val = 0.0 if str(incident.get("status", "")).lower() == "resolved" else 1.0
        try:
            hour = float(datetime.fromisoformat(str(incident.get("timestamp", ""))).hour) / 23.0
        except Exception:
            hour = 0.5
        return np.array([severity, is_malware, is_brute, is_exfil, status_val, hour])

    def auto_reward(self, incident: Dict, classification: Dict) -> Dict:
        action = classification["action"]
        sev = str(incident.get("severity", "LOW")).upper()
        title = str(incident.get("title", "")).lower()

        if any(k in title for k in ["ransomware", "c2", "exfil"]):
            expected = "FULL-QUARANTINE"
        elif any(k in title for k in ["malware", "trojan", "backdoor"]):
            expected = "ISOLATE-HOST"
        elif sev == "CRITICAL":
            expected = "BLOCK-IP"
        elif any(k in title for k in ["brute", "scan", "flood"]):
            expected = "RATE-LIMIT"
        else:
            expected = "ALERT-ONLY"

        reward = 1.0 if action == expected else -0.5
        self.learn(np.array(classification["state"]), classification["action_idx"], reward)
        return {"reward": reward, "expected": expected, "action": action, "correct": reward > 0}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FIREWALL POLICY OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════════
class RLFirewallOptimizer(BaseRLAgent):
    """Learns optimal firewall action: ALLOW / RATE-LIMIT / BLOCK."""

    MALWARE_PORTS = {4444, 5555, 8888, 1337, 31337, 6667, 12345}

    def __init__(self):
        super().__init__("firewall_optimizer", n_features=6, actions=["ALLOW", "RATE-LIMIT", "BLOCK"])

    def extract_state(self, event: Dict) -> np.ndarray:
        port = self._sf(event.get("port", 0))
        bytes_out = self._sf(event.get("bytes_out", 0))
        sev_map = {"LOW": 0.1, "MEDIUM": 0.4, "HIGH": 0.7, "CRITICAL": 1.0}
        severity = sev_map.get(str(event.get("severity", "LOW")).upper(), 0.25)
        is_blocked = 1.0 if "block" in str(event.get("event_type", "")).lower() else 0.0
        is_malware_port = 1.0 if int(port) in self.MALWARE_PORTS else 0.0
        traffic_ratio = min(bytes_out / 1_000_000, 1.0) if bytes_out > 0 else 0.0
        return np.array([port / 65535, severity, is_blocked, is_malware_port, traffic_ratio,
                         min(self._sf(event.get("packets", 0)) / 10000, 1.0)])

    def auto_reward(self, event: Dict, classification: Dict) -> Dict:
        action = classification["action"]
        sev = str(event.get("severity", "LOW")).upper()
        port = int(self._sf(event.get("port", 0)))
        event_type = str(event.get("event_type", "")).lower()

        if port in self.MALWARE_PORTS or any(k in event_type for k in ["malware", "exploit", "c2"]):
            expected = "BLOCK"
        elif sev in ("CRITICAL", "HIGH") or "block" in event_type:
            expected = "BLOCK"
        elif any(k in event_type for k in ["scan", "brute", "flood"]):
            expected = "RATE-LIMIT"
        else:
            expected = "ALLOW"

        reward = 1.0 if action == expected else (-0.3 if abs(self.actions.index(action) - self.actions.index(expected)) == 1 else -1.0)
        self.learn(np.array(classification["state"]), classification["action_idx"], reward)
        return {"reward": reward, "expected": expected, "action": action, "correct": reward > 0}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. THREAT INTEL SCORER
# ═══════════════════════════════════════════════════════════════════════════════
class RLThreatIntelScorer(BaseRLAgent):
    """Scores threat sources: MONITOR / ELEVATED / CRITICAL."""

    def __init__(self):
        super().__init__("threat_intel_scorer", n_features=5, actions=["MONITOR", "ELEVATED", "CRITICAL"])

    def extract_state(self, source: Dict) -> np.ndarray:
        count = self._sf(source.get("real_count", source.get("count", 0)))
        sev_map = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 1.0}
        severity = sev_map.get(str(source.get("severity", "low")).lower(), 0.25)
        threats = self._sf(source.get("threats", 0))
        return np.array([
            min(count / 50, 1.0),
            severity,
            min(threats / 500, 1.0),
            1.0 if count > 10 else (0.5 if count > 3 else 0.0),
            1.0 if severity >= 0.7 else 0.0,
        ])

    def auto_reward(self, source: Dict, classification: Dict) -> Dict:
        action = classification["action"]
        count = self._sf(source.get("real_count", source.get("count", 0)))
        severity = str(source.get("severity", "low")).lower()

        if count > 10 or severity == "critical":
            expected = "CRITICAL"
        elif count > 3 or severity == "high":
            expected = "ELEVATED"
        else:
            expected = "MONITOR"

        reward = 1.0 if action == expected else -0.5
        self.learn(np.array(classification["state"]), classification["action_idx"], reward)
        return {"reward": reward, "expected": expected, "action": action, "correct": reward > 0}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. THREAT HUNT RECOMMENDER
# ═══════════════════════════════════════════════════════════════════════════════
class RLHuntRecommender(BaseRLAgent):
    """Prioritizes threat hunts: HUNT-NOW / SCHEDULE / SKIP."""

    HIGH_VALUE_CATEGORIES = ["Execution", "Credential Access", "Exfiltration", "C2"]

    def __init__(self):
        super().__init__("hunt_recommender", n_features=5, actions=["HUNT-NOW", "SCHEDULE", "SKIP"])

    def extract_state(self, query: Dict) -> np.ndarray:
        cat = str(query.get("category", "")).strip()
        is_high_value = 1.0 if cat in self.HIGH_VALUE_CATEGORIES else 0.0
        has_results = self._sf(query.get("last_result_count", 0))
        try:
            hour = float(datetime.now().hour) / 23.0
        except Exception:
            hour = 0.5
        name_risk = 0.0
        name = str(query.get("name", "")).lower()
        if any(k in name for k in ["credential", "c2", "exfil", "ransomware"]):
            name_risk = 1.0
        elif any(k in name for k in ["lateral", "privilege", "powershell"]):
            name_risk = 0.6
        return np.array([is_high_value, min(has_results / 20, 1.0), hour, name_risk,
                         1.0 if has_results > 0 else 0.0])

    def auto_reward(self, query: Dict, classification: Dict) -> Dict:
        action = classification["action"]
        cat = str(query.get("category", ""))
        has_results = self._sf(query.get("last_result_count", 0))

        if cat in self.HIGH_VALUE_CATEGORIES and has_results > 0:
            expected = "HUNT-NOW"
        elif has_results > 0 or cat in self.HIGH_VALUE_CATEGORIES:
            expected = "SCHEDULE"
        else:
            expected = "SKIP"

        reward = 1.0 if action == expected else -0.5
        self.learn(np.array(classification["state"]), classification["action_idx"], reward)
        return {"reward": reward, "expected": expected, "action": action, "correct": reward > 0}


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETONS
# ═══════════════════════════════════════════════════════════════════════════════
alert_prioritizer = RLAlertPrioritizer()
soar_responder = RLSOARResponder()
firewall_optimizer = RLFirewallOptimizer()
threat_intel_scorer = RLThreatIntelScorer()
hunt_recommender = RLHuntRecommender()

ALL_AGENTS = [alert_prioritizer, soar_responder, firewall_optimizer, threat_intel_scorer, hunt_recommender]


def get_all_agent_stats() -> List[Dict]:
    """Get stats for all RL agents."""
    return [a.get_stats() for a in ALL_AGENTS]
