import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import math

class StatisticalEngine:
    """
    Core engine for calculating probabilistic and statistical security metrics.
    Handles Z-Score anomaly detection and Poisson-based threat forecasting.
    """
    
    def __init__(self):
        # Base probabilities for Poisson distribution lambda calculation
        self.baseline_rates = {
            "SSH Brute Force": 4.5,   # Avg events per day
            "Port Scan": 12.0,
            "SQL Injection": 2.1,
            "Malware C2": 0.8,
            "DDoS Attempt": 1.5,
            "Credential Access": 3.2
        }
        
    def calculate_z_score_anomalies(self, time_series: pd.Series, window: int = 7) -> pd.DataFrame:
        """
        Calculate rolling Z-Scores for a time series to detect statistically significant anomalies.
        Returns a DataFrame with the original series, rolling mean, rolling std, and Z-Score.
        """
        df = pd.DataFrame({'value': time_series})
        
        # Calculate rolling statistics
        df['rolling_mean'] = df['value'].rolling(window=window, min_periods=1).mean()
        df['rolling_std'] = df['value'].rolling(window=window, min_periods=1).std()
        
        # Handle zero standard deviation (perfectly flat lines)
        df['rolling_std'] = df['rolling_std'].replace(0, 0.001)
        
        # Calculate Z-Score: (Value - Mean) / Standard Deviation
        df['z_score'] = (df['value'] - df['rolling_mean']) / df['rolling_std']
        
        # Define severity based on Z-Score magnitude
        df['anomaly_severity'] = 'Normal'
        df.loc[df['z_score'] >= 2.0, 'anomaly_severity'] = 'Warning (2σ)'
        df.loc[df['z_score'] >= 3.0, 'anomaly_severity'] = 'Critical (3σ)'
        
        return df

    def poisson_probability(self, lam: float, k: int) -> float:
        """
        Calculate the exact Poisson probability of exactly 'k' events occurring, 
        given an average rate of 'lam'.
        """
        return (math.exp(-lam) * (lam ** k)) / math.factorial(k)
        
    def cumulative_poisson_probability(self, lam: float, k: int = 0) -> float:
        """
        Calculate the cumulative probability of AT LEAST 1 event occurring.
        Formula: 1 - P(0)
        """
        p_zero = self.poisson_probability(lam, k)
        return 1.0 - p_zero

    def forecast_threats(self, current_events: List[Dict], days_ahead: int = 7, confidence_interval: float = 0.95) -> List[Dict]:
        """
        Generate probabilistic forecasts for future threat types based on recent event spikes.
        Uses a Poisson model scaled by short-term multipliers (simulating Markov momentum).
        """
        # Count recent events by type to calculate momentum multipliers
        recent_counts = {}
        for event in current_events:
            event_type = str(event.get("event_type", "Unknown"))
            recent_counts[event_type] = recent_counts.get(event_type, 0) + 1
            
        forecasts = []
        
        for threat, base_daily_rate in self.baseline_rates.items():
            # Calculate momentum multiplier based on recent activity vs expected average
            # (If we saw 20 port scans today but avg is 12, multiplier is 1.66)
            recent_count = recent_counts.get(threat, 0)
            
            # Dampen extreme spikes for more realistic poisson scaling
            multiplier = 1.0
            if recent_count > 0:
                 multiplier = min(max(recent_count / max(base_daily_rate, 1), 0.5), 3.0)
            
            # Calculate the expected lambda (λ) for the forecast window
            forecast_lam = (base_daily_rate * multiplier) * days_ahead
            
            # Calculate the cumulative probability of experiencing at least 1 critical incident of this type
            prob_at_least_one = self.cumulative_poisson_probability(forecast_lam)
            
            # Apply confidence interval gating
            if prob_at_least_one >= confidence_interval:
                risk_level = "High"
            elif prob_at_least_one >= (confidence_interval - 0.15):
                risk_level = "Medium"
            else:
                risk_level = "Low"
                
            forecasts.append({
                "threat_type": threat,
                "probability_pct": round(prob_at_least_one * 100, 1),
                "expected_events": round(forecast_lam, 1),
                "risk_level": risk_level,
                "momentum_multiplier": round(multiplier, 2)
            })
            
        # Sort by highest probability
        return sorted(forecasts, key=lambda x: x["probability_pct"], reverse=True)
        
    def calculate_probabilistic_risk_score(self, events: List[Dict], alerts: List[Dict]) -> float:
        """
        Calculates a dynamic security posture score (0-100) using a weighted Bayesian-style penalty system.
        Replaces the old hardcoded `100 - (min(critical_threats * 2, 100))` logic.
        """
        base_score = 100.0
        
        total_events = len(events)
        if total_events == 0: return base_score
        
        critical_alerts = len([a for a in alerts if a.get('severity') == 'CRITICAL'])
        high_alerts = len([a for a in alerts if a.get('severity') == 'HIGH'])
        
        # Penalty 1: Absolute volume of critical/high alerts
        penalty_critical = critical_alerts * 3.5
        penalty_high = high_alerts * 1.5
        
        # Penalty 2: Density (what % of traffic is malicious?)
        malicious_density = min((critical_alerts + high_alerts) / max(total_events, 1), 1.0)
        penalty_density = malicious_density * 20.0
        
        # Compute final score with a lower bound floor of 15 (a network is rarely 0 unless offline)
        final_score = base_score - penalty_critical - penalty_high - penalty_density
        return max(round(final_score, 1), 15.0)

# Instantiate singleton
statistical_engine = StatisticalEngine()
