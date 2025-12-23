import pandas as pd

df = pd.read_csv("data/parsed_logs/incident_responses_explained.csv")

total = len(df)
blocked = (df["access_decision"] == "BLOCK").sum()
restricted = (df["access_decision"] == "RESTRICT").sum()
alert_rate = (blocked + restricted) / total * 100
mean_risk = df["risk_score"].mean()

summary = {
    "total_events": total,
    "blocked": blocked,
    "restricted": restricted,
    "alert_rate_%": round(alert_rate, 2),
    "mean_risk_score": round(mean_risk, 2)
}

print("[SOC KPIs]")
for k, v in summary.items():
    print(f"{k}: {v}")

