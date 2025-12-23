import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

# Load dataset
DATA_PATH = "data/parsed_logs/cicids_processed.csv"
df = pd.read_csv(DATA_PATH)

print("[INFO] Original dataset size:", df.shape)

# Sample data for efficient training
df_sample = df.sample(n=200000, random_state=42)
print("[INFO] Sampled dataset size:", df_sample.shape)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_sample)

# Train Isolation Forest
model = IsolationForest(
    n_estimators=150,
    contamination=0.05,
    random_state=42,
    n_jobs=-1
)

model.fit(X_scaled)

# Save model and scaler
joblib.dump(model, "ml_engine/isolation_forest_model.pkl")
joblib.dump(scaler, "ml_engine/scaler.pkl")

print("[✔] Isolation Forest trained and saved successfully")

