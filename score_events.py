import pandas as pd
import joblib

model = joblib.load("isolation_forest_model.pkl")
scaler = joblib.load("scaler.pkl")

DATA_PATH = "data/parsed_logs/cicids_processed.csv"
df = pd.read_csv(DATA_PATH)

print("[INFO] Scoring dataset size:", df.shape)

X_scaled = scaler.transform(df)

df["anomaly_label"] = model.predict(X_scaled)
df["anomaly_score"] = model.decision_function(X_scaled)

df["threat_level"] = df["anomaly_label"].apply(
    lambda x: "HIGH" if x == -1 else "LOW"
)

OUTPUT_PATH = "data/parsed_logs/scored_events.csv"
df.to_csv(OUTPUT_PATH, index=False)

print("[✔] Anomaly scoring complete")
print("[✔] Output saved to:", OUTPUT_PATH)
