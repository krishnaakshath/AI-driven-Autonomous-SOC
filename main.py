from fastapi import FastAPI
import pandas as pd

app = FastAPI(title="Autonomous SOC API")

DATA_PATH = "data/parsed_logs/incident_responses.csv"
df = pd.read_csv(DATA_PATH)

@app.get("/")
def root():
    return {"status": "Autonomous SOC backend running"}

@app.get("/summary")
def soc_summary():
    return {
        "total_events": int(len(df)),
        "high_risk_events": int((df["access_decision"] == "BLOCK").sum()),
        "restricted_events": int((df["access_decision"] == "RESTRICT").sum())
    }

@app.get("/alerts")
def get_alerts(limit: int = 50):
    alerts = df[df["access_decision"] != "ALLOW"].head(limit)
    return alerts.to_dict(orient="records")

@app.get("/responses")
def get_responses(limit: int = 50):
    return df[["access_decision", "automated_response"]].head(limit).to_dict(
        orient="records"
    )

