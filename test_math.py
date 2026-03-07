import sys
import os
import pandas as pd

# Add Project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.statistical_engine import statistical_engine

print("Testing Z-Score Anomalies...")
ts = pd.Series([10, 12, 11, 13, 10, 50, 12, 11])
z_scores = statistical_engine.calculate_z_score_anomalies(ts, window=5)
print(z_scores.tail(3))

print("\nTesting Poisson Forecasts...")
events = [{"event_type": "Port Scan"} for _ in range(25)] + [{"event_type": "SSH Brute Force"} for _ in range(2)]
forecasts = statistical_engine.forecast_threats(events, days_ahead=7, confidence_interval=0.95)
for f in forecasts[:3]:
    print(f)

print("\nTesting Probabilistic Risk Score...")
alerts = [{"severity": "CRITICAL"}, {"severity": "HIGH"}]
score = statistical_engine.calculate_probabilistic_risk_score(events, alerts)
print(f"Risk Score: {score}")
