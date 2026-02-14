"""
 Geo-Attack Prediction Engine
================================
Predicts which countries are most likely to be attacked next
using historical attack patterns, geopolitical factors, and
time-series analysis.

Output: "USA: 78% probability of attack in next 6 hours"
"""

import random
import math
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from services.threat_intel import threat_intel

class GeoAttackPredictor:
    """
    Predicts attack probability for each country using:
    - Historical attack frequency
    - Current global threat landscape
    - Geopolitical risk factors
    - Time-of-day patterns
    - Seasonal trends
    """
    
    # Country risk profiles (base probabilities and factors)
    COUNTRY_PROFILES = {
        "USA": {
            "code": "US", "lat": 38.0, "lon": -97.0,
            "base_risk": 0.35, "infra_score": 0.9, "target_value": 0.95,
            "sectors": ["Finance", "Tech", "Government", "Healthcare"]
        },
        "China": {
            "code": "CN", "lat": 35.0, "lon": 105.0,
            "base_risk": 0.25, "infra_score": 0.85, "target_value": 0.8,
            "sectors": ["Manufacturing", "Tech", "Government"]
        },
        "Russia": {
            "code": "RU", "lat": 60.0, "lon": 100.0,
            "base_risk": 0.20, "infra_score": 0.7, "target_value": 0.7,
            "sectors": ["Energy", "Government", "Finance"]
        },
        "Germany": {
            "code": "DE", "lat": 51.0, "lon": 9.0,
            "base_risk": 0.22, "infra_score": 0.88, "target_value": 0.75,
            "sectors": ["Manufacturing", "Finance", "Auto"]
        },
        "UK": {
            "code": "GB", "lat": 54.0, "lon": -2.0,
            "base_risk": 0.24, "infra_score": 0.87, "target_value": 0.78,
            "sectors": ["Finance", "Government", "Healthcare"]
        },
        "Japan": {
            "code": "JP", "lat": 36.0, "lon": 138.0,
            "base_risk": 0.18, "infra_score": 0.92, "target_value": 0.72,
            "sectors": ["Tech", "Manufacturing", "Finance"]
        },
        "India": {
            "code": "IN", "lat": 20.0, "lon": 77.0,
            "base_risk": 0.28, "infra_score": 0.65, "target_value": 0.68,
            "sectors": ["Tech", "Finance", "Government"]
        },
        "Brazil": {
            "code": "BR", "lat": -14.0, "lon": -51.0,
            "base_risk": 0.20, "infra_score": 0.6, "target_value": 0.55,
            "sectors": ["Finance", "Energy", "Government"]
        },
        "Australia": {
            "code": "AU", "lat": -25.0, "lon": 133.0,
            "base_risk": 0.19, "infra_score": 0.85, "target_value": 0.65,
            "sectors": ["Mining", "Finance", "Government"]
        },
        "South Korea": {
            "code": "KR", "lat": 36.0, "lon": 128.0,
            "base_risk": 0.26, "infra_score": 0.9, "target_value": 0.7,
            "sectors": ["Tech", "Manufacturing", "Finance"]
        },
        "France": {
            "code": "FR", "lat": 46.0, "lon": 2.0,
            "base_risk": 0.21, "infra_score": 0.86, "target_value": 0.73,
            "sectors": ["Energy", "Finance", "Aerospace"]
        },
        "Israel": {
            "code": "IL", "lat": 31.0, "lon": 35.0,
            "base_risk": 0.32, "infra_score": 0.88, "target_value": 0.82,
            "sectors": ["Defense", "Tech", "Government"]
        },
        "UAE": {
            "code": "AE", "lat": 24.0, "lon": 54.0,
            "base_risk": 0.23, "infra_score": 0.82, "target_value": 0.68,
            "sectors": ["Finance", "Energy", "Aviation"]
        },
        "Singapore": {
            "code": "SG", "lat": 1.3, "lon": 103.8,
            "base_risk": 0.17, "infra_score": 0.95, "target_value": 0.7,
            "sectors": ["Finance", "Tech", "Logistics"]
        },
        "Canada": {
            "code": "CA", "lat": 56.0, "lon": -106.0,
            "base_risk": 0.18, "infra_score": 0.87, "target_value": 0.65,
            "sectors": ["Energy", "Finance", "Government"]
        },
    }
    
    # Attack type weights by country characteristics
    ATTACK_WEIGHTS = {
        "ransomware": {"infra_score": 0.8, "target_value": 0.7},
        "ddos": {"infra_score": 0.6, "target_value": 0.5},
        "espionage": {"infra_score": 0.5, "target_value": 0.9},
        "data_breach": {"infra_score": 0.7, "target_value": 0.8},
        "supply_chain": {"infra_score": 0.9, "target_value": 0.6},
    }
    
    def __init__(self):
        self.attack_history: Dict[str, List[Dict]] = defaultdict(list)
        self.predictions_cache: Dict = {}
        self.last_update = datetime.now()
        # No longer generating historical data upfront, will use API data
    
    def _get_live_threat_counts(self, force_refresh: bool = False) -> Dict[str, int]:
        """Fetch real-time threat counts from OTX."""
        try:
            return threat_intel.get_country_threat_counts(force_refresh=force_refresh)
        except Exception:
            return {}
    
    def _calculate_temporal_factor(self) -> float:
        """Calculate time-based risk factor."""
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
        
        # Higher risk during business hours
        if 8 <= hour <= 18:
            hour_factor = 1.2
        elif hour < 6 or hour > 22:
            hour_factor = 0.8
        else:
            hour_factor = 1.0
        
        # Slightly lower risk on weekends
        day_factor = 0.9 if day >= 5 else 1.0
        
        return hour_factor * day_factor
    
    def _calculate_trend_factor(self, country: str, live_count: int = 0) -> float:
        """Calculate trend factor based on recent attack frequency from API."""
        if live_count == 0:
            return 1.0
        
        # Scale risk based on pulse count (0 to 10+ pulses)
        risk_boost = min(0.5, live_count / 20.0) 
        return 1.0 + risk_boost
    
    def _calculate_geopolitical_factor(self, country: str) -> float:
        """Simulate geopolitical risk factor (would use real API in production)."""
        # Countries currently facing heightened tensions
        high_tension = ["USA", "Israel", "South Korea", "Ukraine", "Taiwan"]
        medium_tension = ["UK", "Germany", "France", "Japan", "Australia"]
        
        if country in high_tension:
            return 1.3
        elif country in medium_tension:
            return 1.1
        return 1.0
    
    def predict_country_attacks(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Predict attack probability for each country using live API data.
        
        Returns:
            Dictionary with country predictions
        """
        # Use cache if fresh and not forced
        cache_age = (datetime.now() - self.last_update).seconds
        if not force_refresh and self.predictions_cache and cache_age < 60:
            return self.predictions_cache
        
        # Fetch live data
        live_counts = self._get_live_threat_counts(force_refresh=force_refresh)
        
        predictions = {}
        temporal_factor = self._calculate_temporal_factor()
        
        # Normalization mapping for country names between services
        name_map = {
            "USA": "United States",
            "UK": "United Kingdom",
        }
        
        for country, profile in self.COUNTRY_PROFILES.items():
            # Get match from live counts
            match_name = name_map.get(country, country)
            live_count = live_counts.get(match_name, 0)
            
            # Base probability from country profile
            base_prob = profile["base_risk"]
            
            # Apply factors
            trend_factor = self._calculate_trend_factor(country, live_count=live_count)
            geo_factor = self._calculate_geopolitical_factor(country)
            
            # Target value influences attack likelihood
            target_factor = 0.8 + (profile["target_value"] * 0.4)
            
            # Calculate final probability
            probability = base_prob * temporal_factor * trend_factor * geo_factor * target_factor
            
            # Add randomness for realism
            probability *= (0.9 + random.random() * 0.2)
            
            # Cap at 95%
            probability = min(0.95, max(0.05, probability))
            
            # Determine most likely attack type
            attack_probs = {}
            for attack_type, weights in self.ATTACK_WEIGHTS.items():
                attack_prob = (
                    weights["infra_score"] * profile["infra_score"] +
                    weights["target_value"] * profile["target_value"]
                ) / 2
                attack_probs[attack_type] = attack_prob
            
            likely_attack = max(attack_probs.items(), key=lambda x: x[1])[0]
            
            # Determine risk level
            if probability >= 0.6:
                risk_level = "CRITICAL"
                color = "#ff0040"
            elif probability >= 0.4:
                risk_level = "HIGH"
                color = "#ff6600"
            elif probability >= 0.25:
                risk_level = "MEDIUM"
                color = "#ffcc00"
            else:
                risk_level = "LOW"
                color = "#00ff88"
            
            # ETA estimation
            eta_hours = int((1 - probability) * 24)
            
            predictions[country] = {
                "code": profile["code"],
                "lat": profile["lat"],
                "lon": profile["lon"],
                "probability": round(probability * 100, 1),
                "risk_level": risk_level,
                "color": color,
                "likely_attack": likely_attack.replace("_", " ").title(),
                "target_sectors": profile["sectors"][:2],
                "trend": "↑" if trend_factor > 1.0 else "→",
                "eta_hours": eta_hours,
                "recent_attacks": live_count,
                "factors": {
                    "temporal": round(temporal_factor, 2),
                    "trend": round(trend_factor, 2),
                    "geopolitical": round(geo_factor, 2),
                    "api_signal": live_count
                }
            }
        
        # Sort by probability
        predictions = dict(sorted(predictions.items(), 
                                  key=lambda x: x[1]["probability"], 
                                  reverse=True))
        
        self.predictions_cache = predictions
        self.last_update = datetime.now()
        
        return predictions
    
    def get_top_targets(self, n: int = 5) -> List[Tuple[str, Dict]]:
        """Get top N countries by attack probability."""
        predictions = self.predict_country_attacks()
        return list(predictions.items())[:n]
    
    def get_globe_data(self, refresh: bool = False) -> List[Dict]:
        """Get data formatted for 3D globe visualization."""
        predictions = self.predict_country_attacks(force_refresh=refresh)
        
        globe_data = []
        for country, data in predictions.items():
            globe_data.append({
                "country": country,
                "code": data["code"],
                "lat": data["lat"],
                "lon": data["lon"],
                "probability": data["probability"],
                "risk_level": data["risk_level"],
                "color": data["color"],
                "size": data["probability"] / 10,  # Scale for visualization
                "likely_attack": data["likely_attack"]
            })
        
        return globe_data
    
    def get_prediction_summary(self) -> str:
        """Get human-readable prediction summary."""
        top = self.get_top_targets(3)
        
        summaries = []
        for country, data in top:
            summaries.append(f"{country}: {data['probability']}%")
        
        return f"Top Targets: {' | '.join(summaries)}"


# Singleton instance
geo_predictor = GeoAttackPredictor()


def predict_country_attacks(refresh: bool = False) -> Dict[str, Dict]:
    """Get attack predictions for all countries."""
    return geo_predictor.predict_country_attacks(force_refresh=refresh)


def get_top_targets(n: int = 5, refresh: bool = False) -> List[Tuple[str, Dict]]:
    """Get top N most likely targets."""
    predictions = geo_predictor.predict_country_attacks(force_refresh=refresh)
    return list(predictions.items())[:n]


def get_globe_visualization_data(refresh: bool = False) -> List[Dict]:
    """Get data for 3D globe visualization."""
    return geo_predictor.get_globe_data(refresh=refresh)


def get_country_prediction(country: str) -> Dict:
    """Get prediction for a specific country."""
    predictions = geo_predictor.predict_country_attacks()
    return predictions.get(country, {})
