import pandas as pd

DATA_PATH = "data/parsed_logs/scored_events.csv"
df = pd.read_csv(DATA_PATH)

print("[INFO] Loaded scored events:", df.shape)

min_score = df["anomaly_score"].min()
max_score = df["anomaly_score"].max()

df["risk_score"] = (
    (max_score - df["anomaly_score"]) / (max_score - min_score) * 100
).round(2)


def decide_access(risk):
    if risk >= 70:
        return "BLOCK"
    elif risk >= 30:
        return "RESTRICT"
    else:
        return "ALLOW"


df["access_decision"] = df["risk_score"].apply(decide_access)

OUTPUT_PATH = "data/parsed_logs/zero_trust_decisions.csv"
df.to_csv(OUTPUT_PATH, index=False)

print("[✔] Zero Trust risk evaluation complete")
print("[✔] Decisions saved to:", OUTPUT_PATH)
