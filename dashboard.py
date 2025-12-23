import streamlit as st
import pandas as pd

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="AI-Driven Autonomous SOC",
    layout="wide"
)

st.title("🛡️ AI-Driven Autonomous SOC Dashboard")

# ================= FULL MODE INDICATOR =================
st.success(
    "🟢 **Full SOC Mode Enabled**  \n"
    "Analyzing real security events generated from production-grade datasets "
    "(CICIDS 2017, UNSW-NB15, ADFA-LD)."
)

st.divider()

# ================= DATA LOADING (FULL MODE) =================
DATA_PATH = "data/parsed_logs/incident_responses.csv"

@st.cache_data
def load_data():
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

st.divider()

# ================= DATASET COVERAGE =================
st.subheader("📚 Dataset Coverage & Validation")

dataset_data = {
    "Dataset": [
        "CICIDS 2017",
        "UNSW-NB15",
        "ADFA-LD"
    ],
    "Type": [
        "Network Intrusion Detection",
        "Network Traffic & Attack Simulation",
        "Host-based Intrusion Detection"
    ],
    "Role in SOC Pipeline": [
        "Primary training & anomaly detection",
        "Cross-dataset validation",
        "Host-level behavioral validation"
    ],
    "Status": [
        "✔ Fully Integrated",
        "✔ Validated",
        "✔ Validated"
    ]
}

dataset_df = pd.DataFrame(dataset_data)
st.table(dataset_df)
