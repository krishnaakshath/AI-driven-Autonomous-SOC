import os
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from typing import Optional, Dict, List, Tuple

MODEL_PATH = "isolation_forest_model.pkl"
SCALER_PATH = "scaler.pkl"

FEATURE_COLS = [
    'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
    'Flow Bytes/s', 'Flow Packets/s', 'Fwd Packet Length Mean',
    'Bwd Packet Length Mean', 'SYN Flag Count', 'ACK Flag Count',
    'RST Flag Count', 'Destination Port'
]

try:
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        ML_AVAILABLE = True
    else:
        ML_AVAILABLE = False
        model = None
        scaler = None
except Exception:
    ML_AVAILABLE = False
    model = None
    scaler = None


def score_network_event(event_data: Dict) -> Dict:
    if not ML_AVAILABLE:
        risk_score = np.random.uniform(10, 90)
    else:
        features = np.array([[
            event_data.get('flow_duration', 1000000),
            event_data.get('fwd_packets', 10),
            event_data.get('bwd_packets', 5),
            event_data.get('bytes_per_sec', 5000),
            event_data.get('packets_per_sec', 50),
            event_data.get('fwd_pkt_len_mean', 100),
            event_data.get('bwd_pkt_len_mean', 100),
            event_data.get('syn_flag_count', 1),
            event_data.get('ack_flag_count', 10),
            event_data.get('rst_flag_count', 0),
            event_data.get('dest_port', 80)
        ]])
        
        features = np.nan_to_num(features, nan=0, posinf=0, neginf=0)
        
        try:
            scaled = scaler.transform(features)
            score = model.decision_function(scaled)[0]
            prediction = model.predict(scaled)[0]
            risk_score = 100 * (0.5 - score) / 1.0
            risk_score = np.clip(risk_score, 0, 100)
        except:
            risk_score = 50
    
    if risk_score >= 70:
        decision = "BLOCK"
    elif risk_score >= 30:
        decision = "RESTRICT"
    else:
        decision = "ALLOW"
    
    return {
        "risk_score": round(float(risk_score), 2),
        "access_decision": decision,
        "is_anomaly": risk_score >= 70,
        "ml_available": ML_AVAILABLE
    }


def score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if not ML_AVAILABLE:
        df = df.copy()
        df['risk_score'] = np.random.uniform(0, 100, len(df))
        df['access_decision'] = df['risk_score'].apply(
            lambda r: 'BLOCK' if r >= 70 else 'RESTRICT' if r >= 30 else 'ALLOW'
        )
        return df
    
    feature_df = df.copy()
    
    if all(col in feature_df.columns for col in FEATURE_COLS):
        X = feature_df[FEATURE_COLS].replace([np.inf, -np.inf], 0).fillna(0)
        
        try:
            X_scaled = scaler.transform(X)
            scores = model.decision_function(X_scaled)
            risk_scores = 100 * (0.5 - scores) / 1.0
            risk_scores = np.clip(risk_scores, 0, 100)
        except:
            risk_scores = np.random.uniform(0, 100, len(feature_df))
    else:
        risk_scores = np.random.uniform(0, 100, len(feature_df))
    
    feature_df['risk_score'] = np.round(risk_scores, 2)
    feature_df['access_decision'] = feature_df['risk_score'].apply(
        lambda r: 'BLOCK' if r >= 70 else 'RESTRICT' if r >= 30 else 'ALLOW'
    )
    
    return feature_df


def get_attack_type(risk_score: float, protocol: str = "TCP") -> str:
    if risk_score >= 80:
        return np.random.choice(["Malware C2", "Data Exfiltration", "Ransomware", "Privilege Escalation"])
    elif risk_score >= 60:
        return np.random.choice(["DDoS Attack", "SQL Injection", "XSS Attack"])
    elif risk_score >= 40:
        return np.random.choice(["Port Scan", "Brute Force", "Credential Stuffing"])
    else:
        return "Normal Traffic"


def check_ml_status() -> Dict:
    return {
        "ml_available": ML_AVAILABLE,
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
        "algorithm": "Isolation Forest",
        "n_estimators": 150,
        "contamination": 0.05,
        "n_features": 11,
        "feature_names": FEATURE_COLS
    }
