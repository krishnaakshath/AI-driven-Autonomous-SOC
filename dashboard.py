import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AI-Driven Autonomous SOC",
    layout="wide"
)

st.title("🛡️ AI-Driven Autonomous SOC Dashboard")

DATA_PATH = "data/parsed_logs/incident_responses.csv"
df = pd.read_csv(DATA_PATH)

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
st.dataframe(alerts, use_container_width=True)

st.divider()

# ================= AUTOMATED RESPONSES =================
st.subheader("🤖 Automated Incident Responses")
responses = df[["access_decision", "automated_response"]].head(100)
st.dataframe(responses, use_container_width=True)

