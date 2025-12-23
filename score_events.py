import pandas as pd
import joblib

# Load model and scaler
model = joblib.load("ml_engine/isolation_forest_model.pkl")
scaler = joblib.load("ml_engine/scaler.pkl")

# Load full dataset
DATA_PATH = "data/parsed_logs/cicids_processed.csv"
df = pd.read_csv(DATA_PATH)

print("[INFO] Scoring dataset size:", df.shape)

# Scale features
X_scaled = scaler.transform(df)

# Predict anomalies
df["anomaly_label"] = model.predict(X_scaled)   # -1 = anomaly, 1 = normal
df["anomaly_score"] = model.decision_function(X_scaled)

# Convert to SOC-friendly labels
df["threat_level"] = df["anomaly_label"].apply(
    lambda x: "HIGH" if x == -1 else "LOW"
)

# Save scored events
OUTPUT_PATH = "data/parsed_logs/scored_events.csv"
df.to_csv(OUTPUT_PATH, index=False)

print("[✔] Anomaly scoring complete")
print("[✔] Output saved to:", OUTPUT_PATH)

