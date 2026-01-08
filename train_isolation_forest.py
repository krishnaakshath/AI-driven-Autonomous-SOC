import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

DATA_PATH = "data/parsed_logs/cicids_processed.csv"
df = pd.read_csv(DATA_PATH)

print("[INFO] Training data shape:", df.shape)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df)

model = IsolationForest(
    n_estimators=150,
    contamination=0.05,
    random_state=42,
    n_jobs=-1
)

model.fit(X_scaled)

joblib.dump(model, "isolation_forest_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("[✔] Isolation Forest model trained successfully")
print("[✔] Model saved to: isolation_forest_model.pkl")
print("[✔] Scaler saved to: scaler.pkl")
