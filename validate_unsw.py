import pandas as pd
import joblib

# Load trained model and scaler
model = joblib.load("ml_engine/isolation_forest_model.pkl")
scaler = joblib.load("ml_engine/scaler.pkl")

# Load UNSW-NB15 dataset (Parquet)
DATA_PATH = "data/datasets/UNSW-NB15/UNSW_NB15_training-set.parquet"
df = pd.read_parquet(DATA_PATH)

print("[INFO] UNSW-NB15 original shape:", df.shape)

# Sample for validation
df_sample = df.sample(n=5000, random_state=42)
print("[INFO] UNSW-NB15 sampled shape:", df_sample.shape)

# ---- Feature Mapping (Behavioral Alignment) ----
# Map UNSW features → CICIDS-like behavior
mapped_df = pd.DataFrame({
    "Flow Duration": df_sample["dur"],
    "Total Fwd Packets": df_sample["spkts"],
    "Total Backward Packets": df_sample["dpkts"],
    "Flow Bytes/s": df_sample["sbytes"],
    "Flow Packets/s": df_sample["rate"],
    "Fwd Packet Length Mean": df_sample["smean"],
    "Bwd Packet Length Mean": df_sample["dmean"],
    "SYN Flag Count": df_sample["synack"],
    "ACK Flag Count": df_sample["ackdat"],
    "RST Flag Count": df_sample["is_sm_ips_ports"],

    # 🔑 Destination Port (behavioral proxy)
    "Destination Port": df_sample["ct_dst_sport_ltm"]
})


# Clean data
mapped_df = mapped_df.replace([float("inf"), -float("inf")], 0)
mapped_df = mapped_df.fillna(0)

# Scale features
X_scaled = scaler.transform(mapped_df)

# Predict anomalies
mapped_df["anomaly_label"] = model.predict(X_scaled)
mapped_df["anomaly_score"] = model.decision_function(X_scaled)

# Zero Trust decision
def decide(risk):
    if risk >= 70:
        return "BLOCK"
    elif risk >= 30:
        return "RESTRICT"
    else:
        return "ALLOW"

# Normalize risk
min_s = mapped_df["anomaly_score"].min()
max_s = mapped_df["anomaly_score"].max()

mapped_df["risk_score"] = (
    (max_s - mapped_df["anomaly_score"]) / (max_s - min_s) * 100
)

mapped_df["access_decision"] = mapped_df["risk_score"].apply(decide)

# Save results
OUTPUT_PATH = "data/parsed_logs/unsw_validation_results.csv"
mapped_df.to_csv(OUTPUT_PATH, index=False)

print("[✔] UNSW-NB15 validation complete")
print(mapped_df["access_decision"].value_counts())


