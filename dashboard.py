import streamlit as st
import pandas as pd
import numpy as np
import os

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="AI-Driven Autonomous SOC",
    layout="wide"
)

st.title("🛡️ AI-Driven Autonomous SOC Dashboard")

# ================= DATA LOADING =================
DATA_PATH = "data/parsed_logs/incident_responses.csv"
CLOUD_MODE = not os.path.exists(DATA_PATH)

@st.cache_data
def load_data():
    if CLOUD_MODE:
        # -------- CLOUD DEMO DATA --------
        return pd.DataFrame({
            "risk_score": np.random.normal(18, 6, 800).clip(0, 100),
            "access_decision": np.random.choice(
                ["ALLOW", "RESTRICT", "BLOCK"],
                size=800,
                p=[0.8, 0.18, 0.02]
            ),
            "automated_response": np.random.choice(
                [
                    "No action required",
                    "Throttle connection",
                    "Block IP temporarily",
                    "Require MFA verification"
                ],
                size=800
            )
        })
    else:
        # -------- LOCAL FULL SOC DATA --------
        return pd.read_csv(DATA_PATH)

df = load_data()

# ================= KPI SECTION =================
total_events = len(df)
blocked = (df["access_decision"] == "BLOCK").sum()
restricted = (df["access_decision"] == "RESTRICT").sum()

c1, c2, c3 = st.columns(3)
c1.metric("Total Events", f"{total_events:,}")
c2.metric("Blocked (High Risk)", f"{blocked:,}")
c3.metric("Restricted", f"{restricted:,}")

st.divider()

# ================= RISK DISTRIBUTION =================
st.subheader("📊 Risk Score Distribution")
st.bar_chart(df["risk_score"].value_counts().sort_index())

st.divider()

# ================= ALERTS =================
st.subheader("🚨 Active Security Alerts")
alerts = df[df["access_decision"] != "ALLOW"].head(100)
st.dataframe(alerts, width="stretch")

st.divider()

# ================= AUTOMATED RESPONSES =================
st.subheader("🤖 Automated Incident Responses")
responses = df[["access_decision", "automated_response"]].head(100)
st.dataframe(responses, width="stretch")
