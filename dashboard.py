import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(
    page_title="AI-Driven Autonomous SOC",
    layout="wide"
)

st.title("AI-Driven Autonomous SOC Dashboard")

DATA_PATH = "data/parsed_logs/incident_responses.csv"
FULL_MODE = os.path.exists(DATA_PATH)

@st.cache_data
def load_data():
    if FULL_MODE:
        return pd.read_csv(DATA_PATH)
    else:
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

df = load_data()

# ================= MODE INDICATOR =================
if FULL_MODE:
    st.success(
        "Full SOC Mode Enabled \n"
        "Analyzing over 8 lakh real security events."
    )
else:
    st.info(
        "Demo Mode (Cloud Deployment)\n"
        "Running simulated telemetry for visualization."
    )

st.divider()

# ================= KPIs =================
total_events = len(df)
blocked = (df["access_decision"] == "BLOCK").sum()
restricted = (df["access_decision"] == "RESTRICT").sum()

c1, c2, c3 = st.columns(3)
c1.metric("Total Events", f"{total_events:,}")
c2.metric("Blocked (High Risk)", f"{blocked:,}")
c3.metric("Restricted", f"{restricted:,}")

st.divider()

# ================= RISK DISTRIBUTION =================
st.subheader("Risk Score Distribution")
st.bar_chart(df["risk_score"].value_counts().sort_index())

st.divider()

# ================= ALERTS =================
st.subheader("Active Security Alerts")
alerts = df[df["access_decision"] != "ALLOW"].head(100)
st.dataframe(alerts, width="stretch")

st.divider()

# ================= RESPONSES =================
st.subheader("Automated Incident Responses")
responses = df[["access_decision", "automated_response"]].head(100)
st.dataframe(responses, width="stretch")

st.divider()

# ================= DATASETS =================
st.subheader("Dataset Coverage")

dataset_df = pd.DataFrame({
    "Dataset": ["CICIDS 2017", "UNSW-NB15", "ADFA-LD"],
    "Role": [
        "Primary training & anomaly detection",
        "Cross-dataset validation",
        "Host-based behavioral validation"
    ]
})

st.table(dataset_df)
