import os
import numpy as np

CLOUD_MODE = not os.path.exists("data/parsed_logs")

@st.cache_data
def load_data():
    if CLOUD_MODE:
        # Cloud demo data (same structure, same UI)
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
        # Local full SOC data (unchanged)
        return pd.read_csv(
            "data/parsed_logs/incident_responses.csv"
        )

df = load_data()
