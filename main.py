from fastapi import FastAPI
import pandas as pd
import os

app = FastAPI(title="Autonomous SOC API")

DATA_PATH = "data/parsed_logs/incident_responses.csv"

# Graceful fallback if CSV does not exist
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=["access_decision", "automated_response"])

@app.get("/")
def root():
    return {"status": "Autonomous SOC backend running"}

@app.get("/summary")
def soc_summary():
    return {
        "total_events": int(len(df)),
        "high_risk_events": int((df["access_decision"] == "BLOCK").sum()) if "access_decision" in df.columns else 0,
        "restricted_events": int((df["access_decision"] == "RESTRICT").sum()) if "access_decision" in df.columns else 0
    }

@app.get("/alerts")
def get_alerts(limit: int = 50):
    if "access_decision" not in df.columns:
        return []
    alerts = df[df["access_decision"] != "ALLOW"].head(limit)
    return alerts.to_dict(orient="records")

@app.get("/responses")
def get_responses(limit: int = 50):
    cols = [c for c in ["access_decision", "automated_response"] if c in df.columns]
    if not cols:
        return []
    return df[cols].head(limit).to_dict(orient="records")
