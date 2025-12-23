import os
import pandas as pd
import joblib

# Load trained model & scaler
model = joblib.load("ml_engine/isolation_forest_model.pkl")
scaler = joblib.load("ml_engine/scaler.pkl")

ADFA_VALIDATE_DIR = "data/datasets/ADFA-LD/VALIDATE"

records = []

# Each file = one execution trace
for root, _, files in os.walk(ADFA_VALIDATE_DIR):
    for file in files:
        path = os.path.join(root, file)
        try:
            with open(path, "r", errors="ignore") as f:
                syscalls = f.read().split()
                records.append({
                    "Flow Duration": len(syscalls),
                    "Total Fwd Packets": syscalls.count(syscalls[0]) if syscalls else 0,
                    "Total Backward Packets": len(set(syscalls)),
                    "Flow Bytes/s": len(syscalls),
                    "Flow Packets/s": len(syscalls) / 10,
                    "Fwd Packet Length Mean": len(syscalls),
                    "Bwd Packet Length Mean": len(set(syscalls)),
                    "SYN Flag Count": 0,
                    "ACK Flag Count": 0,
                    "RST Flag Count": 0,
                    "Destination Port": 0
                })
        except:
            continue

df = pd.DataFrame(records)

print("[INFO] ADFA-LD validation samples:", df.shape)

# Scale features
X_scaled = scaler.transform(df)

# Predict anomalies
df["anomaly_label"] = model.predict(X_scaled)
df["anomaly_score"] = model.decision_function(X_scaled)

# Normalize risk score
min_s = df["anomaly_score"].min()
max_s = df["anomaly_score"].max()

df["risk_score"] = ((max_s - df["anomaly_score"]) / (max_s - min_s) * 100)

# Zero Trust decision
def decide(risk):
    if risk >= 70:
        return "BLOCK"
    elif risk >= 30:
        return "RESTRICT"
    else:
        return "ALLOW"

df["access_decision"] = df["risk_score"].apply(decide)

# Save output
OUTPUT_PATH = "data/parsed_logs/adfa_validation_results.csv"
df.to_csv(OUTPUT_PATH, index=False)

print("[✔] ADFA-LD validation complete")
print(df["access_decision"].value_counts())

