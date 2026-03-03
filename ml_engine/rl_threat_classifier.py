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
N_FEATURES = 8  # state dimension

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rl_models")
WEIGHTS_FILE = os.path.join(MODEL_DIR, "dqn_weights.npz")
STATS_FILE = os.path.join(MODEL_DIR, "rl_stats.json")
REPLAY_FILE = os.path.join(MODEL_DIR, "replay_buffer.json")


# ═══════════════════════════════════════════════════════════════════════════════
# NEURAL NETWORK (numpy-only MLP)
# ═══════════════════════════════════════════════════════════════════════════════
class QNetwork:
    """Simple 3-layer MLP: input(8) → hidden1(32) → hidden2(16) → output(3)."""

    def __init__(self, lr: float = 0.001):
        self.lr = lr
        # Xavier initialization
        self.W1 = np.random.randn(N_FEATURES, 32) * np.sqrt(2.0 / N_FEATURES)
        self.b1 = np.zeros(32)
        self.W2 = np.random.randn(32, 16) * np.sqrt(2.0 / 32)
        self.b2 = np.zeros(16)
        self.W3 = np.random.randn(16, N_ACTIONS) * np.sqrt(2.0 / 16)
        self.b3 = np.zeros(N_ACTIONS)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass. Returns Q-values for each action."""
        self._x = x
        self._z1 = x @ self.W1 + self.b1
        self._a1 = np.maximum(0, self._z1)  # ReLU
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
        """Load weights from disk. Returns True if successful."""
        if os.path.exists(path):
            try:
                data = np.load(path)
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

    States:  8-dim feature vector extracted from SIEM events
    Actions: SAFE (0), SUSPICIOUS (1), DANGEROUS (2)
    Rewards: +1 correct classification, -1 incorrect (from analyst or auto)
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.995,
        gamma: float = 0.95,
        batch_size: int = 32,
        replay_capacity: int = 5000,
        lr: float = 0.001,
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
        Convert a raw SIEM event dict into an 8-dimensional state vector.

        Features:
            0: bytes_in (normalized)
            1: bytes_out (normalized)
            2: packets (normalized)
            3: duration (normalized)
            4: port (normalized)
            5: severity_num (0-4)
            6: hour_of_day (0-23, normalized)
            7: is_critical (0 or 1)
        """
        severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

        bytes_in = float(event.get("bytes_in", 0))
        bytes_out = float(event.get("bytes_out", 0))
        packets = float(event.get("packets", 1))
        duration = float(event.get("duration", 0))
        port = float(event.get("port", 0))

        severity_str = event.get("severity", event.get("siem_severity", "LOW"))
        severity_num = severity_map.get(str(severity_str).upper(), 1)

        # Extract hour from timestamp
        hour = 12.0
        try:
            ts = event.get("timestamp", "")
            if ts:
                hour = float(datetime.fromisoformat(ts).hour)
        except Exception:
            pass

        is_critical = 1.0 if severity_num >= 4 else 0.0

        # Normalize features to [0, 1] range with safe denominators
        state = np.array([
            min(bytes_in / 1_000_000, 1.0),
            min(bytes_out / 1_000_000, 1.0),
            min(packets / 10_000, 1.0),
            min(duration / 3600, 1.0),
            port / 65535,
            severity_num / 4.0,
            hour / 23.0,
            is_critical,
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

    def auto_reward(self, event: Dict, classification: Dict) -> float:
        """
        Generate automatic reward based on existing ML models.
        Uses Isolation Forest anomaly score as ground truth proxy.
        """
        action = classification["action"]

        # Try to get IF anomaly score
        anomaly_score = float(event.get("anomaly_score", event.get("ml_anomaly_score", -1)))

        if anomaly_score < 0:
            # No IF score available — try to compute
            try:
                from ml_engine.isolation_forest import isolation_forest
                results = isolation_forest.predict([event])
                if results:
                    anomaly_score = results[0].get("anomaly_score", 50)
            except Exception:
                anomaly_score = 50  # neutral

        # Determine expected classification from IF score
        if anomaly_score >= 70:
            expected = "DANGEROUS"
        elif anomaly_score >= 40:
            expected = "SUSPICIOUS"
        else:
            expected = "SAFE"

        # Compute reward
        if action == expected:
            reward = 1.0
        elif abs(ACTIONS.index(action) - ACTIONS.index(expected)) == 1:
            reward = -0.3  # off by one category
        else:
            reward = -1.0  # completely wrong

        event_id = classification.get("event_id", "unknown")

        # Clean up pending feedback for auto-rewarded events
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
        if reward > 0:
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

        return reward

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
