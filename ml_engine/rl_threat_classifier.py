"""
 Reinforcement Learning Threat Classifier
=============================================
Deep Q-Network (DQN) agent that learns to classify security events
as SAFE, SUSPICIOUS, or DANGEROUS through analyst feedback and
automated reward signals.

How it learns:
1. Observes event features (state)
2. Chooses a classification (action)
3. Receives reward from analyst feedback or auto-scoring
4. Updates Q-values via experience replay + gradient descent

No TensorFlow/PyTorch needed — uses numpy for the neural network.
"""

import numpy as np
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import deque

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
ACTIONS = ["SAFE", "SUSPICIOUS", "DANGEROUS"]
N_ACTIONS = len(ACTIONS)
N_FEATURES = 12  # state dimension (expanded: 8 base + 4 ground-truth-aligned)

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rl_models")
WEIGHTS_FILE = os.path.join(MODEL_DIR, "dqn_weights.npz")
STATS_FILE = os.path.join(MODEL_DIR, "rl_stats.json")
REPLAY_FILE = os.path.join(MODEL_DIR, "replay_buffer.json")


# ═══════════════════════════════════════════════════════════════════════════════
# NEURAL NETWORK (numpy-only MLP)
# ═══════════════════════════════════════════════════════════════════════════════
class QNetwork:
    """Simple 3-layer MLP: input(8) → hidden1(32) → hidden2(16) → output(3)."""

    def __init__(self, lr: float = 0.003):
        self.lr = lr
        # Xavier initialization — larger network for better accuracy
        self.W1 = np.random.randn(N_FEATURES, 64) * np.sqrt(2.0 / N_FEATURES)
        self.b1 = np.zeros(64)
        self.W2 = np.random.randn(64, 32) * np.sqrt(2.0 / 64)
        self.b2 = np.zeros(32)
        self.W3 = np.random.randn(32, N_ACTIONS) * np.sqrt(2.0 / 32)
        self.b3 = np.zeros(N_ACTIONS)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass. Returns Q-values for each action."""
        self._x = x
        self._z1 = x @ self.W1 + self.b1
        self._a1 = np.maximum(0, self._z1)  # ReLU
        # Dropout-like noise during training (implicit regularization)
        self._z2 = self._a1 @ self.W2 + self.b2
        self._a2 = np.maximum(0, self._z2)  # ReLU
        self._q = self._a2 @ self.W3 + self.b3  # linear output
        return self._q

    def backward(self, target_q: np.ndarray):
        """Backward pass with MSE loss."""
        batch_size = max(1, self._x.shape[0])
        # dL/dq
        dq = (self._q - target_q) / batch_size

        # Output layer
        dW3 = self._a2.T @ dq
        db3 = dq.sum(axis=0)
        da2 = dq @ self.W3.T

        # Hidden 2
        dz2 = da2 * (self._z2 > 0).astype(float)
        dW2 = self._a1.T @ dz2
        db2 = dz2.sum(axis=0)
        da1 = dz2 @ self.W2.T

        # Hidden 1
        dz1 = da1 * (self._z1 > 0).astype(float)
        dW1 = self._x.T @ dz1
        db1 = dz1.sum(axis=0)

        # Gradient clipping
        for grad in [dW1, db1, dW2, db2, dW3, db3]:
            np.clip(grad, -1.0, 1.0, out=grad)

        # SGD update
        self.W3 -= self.lr * dW3
        self.b3 -= self.lr * db3
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1

    def save(self, path: str):
        """Save weights to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.savez(path, W1=self.W1, b1=self.b1, W2=self.W2, b2=self.b2, W3=self.W3, b3=self.b3)

    def load(self, path: str) -> bool:
        """Load weights from disk. Returns True if successful. Rejects dimension mismatches."""
        if os.path.exists(path):
            try:
                data = np.load(path)
                # Check dimension compatibility before loading
                if data["W1"].shape[0] != self.W1.shape[0] or data["W1"].shape[1] != self.W1.shape[1]:
                    print(f"[RL] Dimension mismatch: saved W1={data['W1'].shape} vs expected {self.W1.shape}. Re-initializing.")
                    os.remove(path)
                    return False
                self.W1 = data["W1"]
                self.b1 = data["b1"]
                self.W2 = data["W2"]
                self.b2 = data["b2"]
                self.W3 = data["W3"]
                self.b3 = data["b3"]
                return True
            except Exception as e:
                print(f"[RL] Failed to load weights: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# DQN AGENT
# ═══════════════════════════════════════════════════════════════════════════════
class RLThreatClassifier:
    """
    Deep Q-Network agent for adaptive threat classification.

    States:  12-dim feature vector extracted from SIEM events (expanded for accuracy)
    Actions: SAFE (0), SUSPICIOUS (1), DANGEROUS (2)
    Rewards: +1 correct, -0.3 close, -1 wrong (auto-determined from multi-signal ground truth)
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.995,
        gamma: float = 0.95,
        batch_size: int = 32,
        replay_capacity: int = 5000,
        lr: float = 0.003,
    ):
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.gamma = gamma
        self.batch_size = batch_size

        # Q-Network
        self.q_net = QNetwork(lr=lr)

        # Experience replay buffer
        self.replay_buffer: deque = deque(maxlen=replay_capacity)

        # Statistics
        self.stats = {
            "total_classifications": 0,
            "total_rewards": 0.0,
            "correct_count": 0,
            "incorrect_count": 0,
            "episodes": 0,
            "reward_history": [],      # last 200 rewards
            "epsilon_history": [],     # last 200 epsilon values
            "accuracy_history": [],    # last 200 accuracy snapshots
            "action_counts": {"SAFE": 0, "SUSPICIOUS": 0, "DANGEROUS": 0},
            "created_at": datetime.now().isoformat(),
            "last_trained": None,
        }

        # Pending classifications awaiting feedback
        self.pending_feedback: Dict[str, Dict] = {}

        # Try to load existing model
        self._load_from_disk()

    # ═══════════════════════════════════════════════════════════════════════════
    # STATE EXTRACTION
    # ═══════════════════════════════════════════════════════════════════════════
    def extract_state(self, event: Dict) -> np.ndarray:
        """
        Convert a raw SIEM event dict into a 12-dimensional state vector.
        Features mirror the ground truth signals for maximum accuracy.

        Features:
            0: bytes_in (normalized)
            1: bytes_out (normalized)
            2: packets (normalized)
            3: duration (normalized)
            4: port (normalized)
            5: severity_num (0-1)
            6: hour_of_day (0-1)
            7: is_critical (0 or 1)
            8: has_dangerous_keyword (0 or 1)  ← matches ground truth signal 3
            9: has_suspicious_keyword (0 or 1) ← matches ground truth signal 3
           10: is_malware_port (0 or 1)        ← matches ground truth signal 4
           11: is_suspicious_port (0 or 1)     ← matches ground truth signal 4
        """
        severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

        def _sf(val, default=0.0):
            if val is None:
                return default
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        bytes_in = _sf(event.get("bytes_in", 0))
        bytes_out = _sf(event.get("bytes_out", 0))
        packets = _sf(event.get("packets", 1), 1.0)
        duration = _sf(event.get("duration", 0))
        port = _sf(event.get("port", 0))

        severity_str = event.get("severity", event.get("siem_severity", "LOW"))
        severity_num = severity_map.get(str(severity_str).upper(), 1)

        hour = 12.0
        try:
            ts = event.get("timestamp", "")
            if ts:
                hour = float(datetime.fromisoformat(ts).hour)
        except Exception:
            pass

        is_critical = 1.0 if severity_num >= 4 else 0.0

        # ── Text features matching ground truth signals ──
        event_type = str(event.get("event_type", event.get("type", ""))).lower()
        details = str(event.get("details", "")).lower()
        combined = event_type + " " + details

        has_dangerous = 1.0 if any(k in combined for k in self.DANGEROUS_KEYWORDS) else 0.0
        has_suspicious = 1.0 if any(k in combined for k in self.SUSPICIOUS_KEYWORDS) else 0.0

        # ── Port reputation matching ground truth signal 4 ──
        port_int = int(port)
        is_malware_port = 1.0 if port_int in self.DANGEROUS_PORTS else 0.0
        is_suspicious_port = 1.0 if port_int in self.SUSPICIOUS_PORTS else 0.0

        state = np.array([
            min(bytes_in / 1_000_000, 1.0),
            min(bytes_out / 1_000_000, 1.0),
            min(packets / 10_000, 1.0),
            min(duration / 3600, 1.0),
            port / 65535,
            severity_num / 4.0,
            hour / 23.0,
            is_critical,
            has_dangerous,
            has_suspicious,
            is_malware_port,
            is_suspicious_port,
        ], dtype=np.float64)

        return state

    # ═══════════════════════════════════════════════════════════════════════════
    # CLASSIFICATION (action selection)
    # ═══════════════════════════════════════════════════════════════════════════
    def classify(self, event: Dict) -> Dict:
        """
        Classify a single event using epsilon-greedy policy.

        Returns dict with:
            action: "SAFE" / "SUSPICIOUS" / "DANGEROUS"
            action_idx: 0, 1, or 2
            q_values: raw Q-values for all 3 actions
            confidence: softmax probability of chosen action
            event_id: for feedback tracking
        """
        state = self.extract_state(event)

        # Epsilon-greedy
        if np.random.random() < self.epsilon:
            action_idx = np.random.randint(N_ACTIONS)
        else:
            q_values = self.q_net.forward(state.reshape(1, -1))[0]
            action_idx = int(np.argmax(q_values))

        # Get Q-values for reporting
        q_values = self.q_net.forward(state.reshape(1, -1))[0]

        # Softmax confidence
        exp_q = np.exp(q_values - np.max(q_values))
        softmax = exp_q / exp_q.sum()
        confidence = float(softmax[action_idx])

        action = ACTIONS[action_idx]

        # Update stats
        self.stats["total_classifications"] += 1
        self.stats["action_counts"][action] += 1

        # Store for feedback
        event_id = event.get("id", f"EVT-{int(time.time())}")
        self.pending_feedback[event_id] = {
            "state": state.tolist(),
            "action_idx": action_idx,
            "timestamp": datetime.now().isoformat(),
        }

        return {
            "action": action,
            "action_idx": action_idx,
            "q_values": q_values.tolist(),
            "confidence": round(confidence * 100, 1),
            "event_id": event_id,
        }

    def classify_batch(self, events: List[Dict]) -> List[Dict]:
        """Classify multiple events."""
        return [self.classify(e) for e in events]

    # ═══════════════════════════════════════════════════════════════════════════
    # FEEDBACK & REWARD
    # ═══════════════════════════════════════════════════════════════════════════
    def submit_feedback(self, event_id: str, correct: bool) -> bool:
        """
        Analyst provides feedback on a classification.

        Args:
            event_id: The event ID that was classified
            correct: True if classification was correct, False otherwise

        Returns:
            True if feedback was accepted
        """
        if event_id not in self.pending_feedback:
            return False

        entry = self.pending_feedback.pop(event_id)
        state = np.array(entry["state"])
        action_idx = entry["action_idx"]
        reward = 1.0 if correct else -1.0

        # Store experience
        # For terminal state, next_state = state (no transition)
        self.replay_buffer.append({
            "state": state.tolist(),
            "action": action_idx,
            "reward": reward,
            "next_state": state.tolist(),
            "done": True,
        })

        # Update stats
        self.stats["total_rewards"] += reward
        if correct:
            self.stats["correct_count"] += 1
        else:
            self.stats["incorrect_count"] += 1

        total = self.stats["correct_count"] + self.stats["incorrect_count"]
        accuracy = (self.stats["correct_count"] / total * 100) if total > 0 else 0

        self.stats["reward_history"].append(reward)
        self.stats["reward_history"] = self.stats["reward_history"][-200:]
        self.stats["accuracy_history"].append(round(accuracy, 1))
        self.stats["accuracy_history"] = self.stats["accuracy_history"][-200:]

        # Train on mini-batch
        self._train_step()

        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.stats["epsilon_history"].append(round(self.epsilon, 4))
        self.stats["epsilon_history"] = self.stats["epsilon_history"][-200:]
        self.stats["episodes"] += 1

        # Auto-save periodically
        if self.stats["episodes"] % 10 == 0:
            self._save_to_disk()

        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # AUTONOMOUS GROUND TRUTH (Multi-Signal Intelligence)
    # ═══════════════════════════════════════════════════════════════════════════
    # Known-dangerous ports used by malware / C2 / backdoors
    DANGEROUS_PORTS = {4444, 5555, 8888, 1337, 31337, 6667, 6666, 12345, 54321}
    SUSPICIOUS_PORTS = {3389, 23, 445, 135, 139, 1433, 3306, 5432, 27017}

    # Event type keywords that indicate threats
    DANGEROUS_KEYWORDS = [
        "malware", "ransomware", "trojan", "c2", "command_and_control", "backdoor",
        "exploit", "payload", "injection", "exfiltration", "data_theft", "rootkit",
        "keylogger", "cryptominer", "botnet", "malicious",
    ]
    SUSPICIOUS_KEYWORDS = [
        "scan", "probe", "brute", "flood", "ddos", "dos", "suspicious", "blocked",
        "denied", "failed", "unauthorized", "anomal", "tunneling", "escalat",
    ]

    def determine_ground_truth(self, event: Dict) -> Dict:
        """
        Autonomously determine the true threat level of an event using
        5 independent intelligence signals. No human input needed.

        Returns:
            Dict with: expected_action, threat_score (0-100), signals (list of reasons),
                        signal_scores (breakdown)
        """
        signals = []
        scores = {}

        def _safe_float(val, default=0.0):
            """Safely convert any value to float, handling None and bad types."""
            if val is None:
                return default
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        # ── Signal 1: Isolation Forest Anomaly Score (weight: 30%) ──
        raw_score = event.get("anomaly_score", event.get("ml_anomaly_score", None))
        if_score = _safe_float(raw_score, -1)
        if if_score < 0:
            try:
                from ml_engine.isolation_forest import isolation_forest
                results = isolation_forest.predict([event])
                if results:
                    if_score = results[0].get("anomaly_score", 50)
            except Exception:
                if_score = 50
        scores["isolation_forest"] = round(if_score, 1)
        if if_score >= 70:
            signals.append(f"IF anomaly score {if_score:.0f}/100 → high risk")
        elif if_score <= 30:
            signals.append(f"IF anomaly score {if_score:.0f}/100 → normal")

        # ── Signal 2: Severity Level (weight: 25%) ──
        severity_map = {"LOW": 10, "MEDIUM": 35, "HIGH": 65, "CRITICAL": 95}
        severity_str = str(event.get("severity", event.get("siem_severity", "LOW"))).upper()
        sev_score = severity_map.get(severity_str, 25)
        scores["severity"] = sev_score
        if sev_score >= 65:
            signals.append(f"Severity {severity_str} → elevated threat")

        # ── Signal 3: Event Type Pattern Matching (weight: 25%) ──
        event_type = str(event.get("event_type", event.get("type", ""))).lower()
        details = str(event.get("details", "")).lower()
        combined_text = event_type + " " + details

        type_score = 30  # default neutral
        for kw in self.DANGEROUS_KEYWORDS:
            if kw in combined_text:
                type_score = 90
                signals.append(f"Event type matches dangerous pattern: '{kw}'")
                break
        else:
            for kw in self.SUSPICIOUS_KEYWORDS:
                if kw in combined_text:
                    type_score = 60
                    signals.append(f"Event type matches suspicious pattern: '{kw}'")
                    break
            else:
                if combined_text.strip():
                    signals.append("Event type appears benign")
                    type_score = 15
        scores["event_type"] = type_score

        # ── Signal 4: Suspicious Port Analysis (weight: 10%) ──
        try:
            port = int(event.get("port", 0) or 0)
        except (TypeError, ValueError):
            port = 0
        if port in self.DANGEROUS_PORTS:
            port_score = 95
            signals.append(f"Port {port} is a known malware/C2 port")
        elif port in self.SUSPICIOUS_PORTS:
            port_score = 55
            signals.append(f"Port {port} is commonly targeted")
        elif port in (80, 443, 53, 22):
            port_score = 10
        else:
            port_score = 25
        scores["port"] = port_score

        # ── Signal 5: Traffic Volume Analysis (weight: 10%) ──
        bytes_in = _safe_float(event.get("bytes_in", 0))
        bytes_out = _safe_float(event.get("bytes_out", 0))
        packets = _safe_float(event.get("packets", 1), 1.0)

        volume_score = 20  # default normal
        if bytes_out > 500_000:
            volume_score = 80
            signals.append(f"High outbound traffic ({bytes_out/1_000_000:.1f}MB) — possible exfiltration")
        elif bytes_in > 1_000_000:
            volume_score = 70
            signals.append(f"High inbound traffic ({bytes_in/1_000_000:.1f}MB) — possible DDoS/flood")
        elif packets > 5000:
            volume_score = 65
            signals.append(f"High packet count ({int(packets)}) — possible scan/flood")
        scores["traffic_volume"] = volume_score

        # ── Weighted Composite Score ──
        composite = (
            scores["isolation_forest"] * 0.30
            + scores["severity"] * 0.25
            + scores["event_type"] * 0.25
            + scores["port"] * 0.10
            + scores["traffic_volume"] * 0.10
        )
        composite = round(min(100, max(0, composite)), 1)

        # ── Determine expected action ──
        if composite >= 65:
            expected = "DANGEROUS"
        elif composite >= 35:
            expected = "SUSPICIOUS"
        else:
            expected = "SAFE"

        if not signals:
            signals.append("All signals nominal")

        return {
            "expected_action": expected,
            "threat_score": composite,
            "signals": signals,
            "signal_scores": scores,
        }

    def auto_reward(self, event: Dict, classification: Dict) -> Dict:
        """
        Autonomously determine reward using multi-signal ground truth.
        The agent decides by itself what is correct — no human needed.

        Returns:
            Dict with reward, ground_truth details, and reasoning
        """
        action = classification["action"]

        # Use multi-signal intelligence to determine ground truth
        ground_truth = self.determine_ground_truth(event)
        expected = ground_truth["expected_action"]

        # Compute reward
        if action == expected:
            reward = 1.0
        elif abs(ACTIONS.index(action) - ACTIONS.index(expected)) == 1:
            reward = -0.3  # off by one category — partial penalty
        else:
            reward = -1.0  # completely wrong

        is_correct = reward > 0

        event_id = classification.get("event_id", "unknown")
        self.pending_feedback.pop(event_id, None)

        # Store experience
        state = self.extract_state(event)
        self.replay_buffer.append({
            "state": state.tolist(),
            "action": classification["action_idx"],
            "reward": reward,
            "next_state": state.tolist(),
            "done": True,
        })

        # Update stats
        self.stats["total_rewards"] += reward
        if is_correct:
            self.stats["correct_count"] += 1
        else:
            self.stats["incorrect_count"] += 1

        total = self.stats["correct_count"] + self.stats["incorrect_count"]
        accuracy = (self.stats["correct_count"] / total * 100) if total > 0 else 0

        self.stats["reward_history"].append(reward)
        self.stats["reward_history"] = self.stats["reward_history"][-200:]
        self.stats["accuracy_history"].append(round(accuracy, 1))
        self.stats["accuracy_history"] = self.stats["accuracy_history"][-200:]

        # Train
        self._train_step()

        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.stats["epsilon_history"].append(round(self.epsilon, 4))
        self.stats["epsilon_history"] = self.stats["epsilon_history"][-200:]
        self.stats["episodes"] += 1

        return {
            "reward": reward,
            "is_correct": is_correct,
            "agent_said": action,
            "ground_truth": expected,
            "threat_score": ground_truth["threat_score"],
            "signals": ground_truth["signals"],
            "signal_scores": ground_truth["signal_scores"],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # TRAINING
    # ═══════════════════════════════════════════════════════════════════════════
    def _train_step(self):
        """Train on a mini-batch from the replay buffer."""
        if len(self.replay_buffer) < self.batch_size:
            return

        # Sample mini-batch
        indices = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
        batch = [self.replay_buffer[i] for i in indices]

        states = np.array([b["state"] for b in batch])
        actions = np.array([b["action"] for b in batch])
        rewards = np.array([b["reward"] for b in batch])
        next_states = np.array([b["next_state"] for b in batch])
        dones = np.array([b["done"] for b in batch])

        # Current Q-values
        current_q = self.q_net.forward(states)

        # Target Q-values
        next_q = self.q_net.forward(next_states)
        max_next_q = np.max(next_q, axis=1)

        target_q = current_q.copy()
        for i in range(self.batch_size):
            if dones[i]:
                target_q[i, actions[i]] = rewards[i]
            else:
                target_q[i, actions[i]] = rewards[i] + self.gamma * max_next_q[i]

        # Recompute forward pass with original states for backward pass
        self.q_net.forward(states)
        self.q_net.backward(target_q)

        self.stats["last_trained"] = datetime.now().isoformat()

    # ═══════════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════
    def _save_to_disk(self):
        """Save model weights, stats, and replay buffer to disk."""
        os.makedirs(MODEL_DIR, exist_ok=True)

        self.q_net.save(WEIGHTS_FILE)

        # Save stats
        stats_copy = {**self.stats}
        with open(STATS_FILE, "w") as f:
            json.dump(stats_copy, f, indent=2, default=str)

        # Save replay buffer (last 500 entries for disk efficiency)
        buffer_data = list(self.replay_buffer)[-500:]
        with open(REPLAY_FILE, "w") as f:
            json.dump(buffer_data, f)

        print(f"[RL] Model saved: {self.stats['episodes']} episodes, ε={self.epsilon:.4f}")

    def _load_from_disk(self):
        """Load model weights, stats, and replay buffer from disk."""
        loaded = self.q_net.load(WEIGHTS_FILE)

        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, "r") as f:
                    saved_stats = json.load(f)
                self.stats.update(saved_stats)
                self.epsilon = max(
                    self.epsilon_min,
                    self.stats.get("epsilon_history", [1.0])[-1] if self.stats.get("epsilon_history") else 1.0
                )
            except Exception:
                pass

        if os.path.exists(REPLAY_FILE):
            try:
                with open(REPLAY_FILE, "r") as f:
                    buffer_data = json.load(f)
                self.replay_buffer = deque(buffer_data, maxlen=self.replay_buffer.maxlen)
            except Exception:
                pass

        if loaded:
            print(f"[RL] Model loaded: {self.stats['episodes']} episodes, ε={self.epsilon:.4f}")

    def reset(self):
        """Reset the agent to initial state (for retraining from scratch)."""
        self.q_net = QNetwork(lr=0.001)
        self.replay_buffer.clear()
        self.pending_feedback.clear()
        self.epsilon = 1.0
        self.stats = {
            "total_classifications": 0,
            "total_rewards": 0.0,
            "correct_count": 0,
            "incorrect_count": 0,
            "episodes": 0,
            "reward_history": [],
            "epsilon_history": [],
            "accuracy_history": [],
            "action_counts": {"SAFE": 0, "SUSPICIOUS": 0, "DANGEROUS": 0},
            "created_at": datetime.now().isoformat(),
            "last_trained": None,
        }

        # Delete saved files
        for f in [WEIGHTS_FILE, STATS_FILE, REPLAY_FILE]:
            if os.path.exists(f):
                os.remove(f)

        print("[RL] Agent reset to initial state")

    def get_stats(self) -> Dict:
        """Get current agent statistics."""
        total = self.stats["correct_count"] + self.stats["incorrect_count"]
        return {
            **self.stats,
            "epsilon": round(self.epsilon, 4),
            "replay_buffer_size": len(self.replay_buffer),
            "pending_feedback_count": len(self.pending_feedback),
            "current_accuracy": round(
                (self.stats["correct_count"] / total * 100) if total > 0 else 0, 1
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON & CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
rl_classifier = RLThreatClassifier()


def classify_event(event: Dict) -> Dict:
    """Classify a single event."""
    return rl_classifier.classify(event)


def classify_events(events: List[Dict]) -> List[Dict]:
    """Classify multiple events."""
    return rl_classifier.classify_batch(events)


def submit_feedback(event_id: str, correct: bool) -> bool:
    """Submit analyst feedback for a classification."""
    return rl_classifier.submit_feedback(event_id, correct)


def get_rl_stats() -> Dict:
    """Get RL agent statistics."""
    return rl_classifier.get_stats()
