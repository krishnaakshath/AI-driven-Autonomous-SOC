# ML Scorer (optional, may not exist)
try:
    from .ml_scorer import (
        score_network_event,
        score_dataframe,
        get_attack_type,
        check_ml_status,
        ML_AVAILABLE
    )
except ImportError:
    ML_AVAILABLE = False
    def score_network_event(*a, **kw): return 0
    def score_dataframe(*a, **kw): return None
    def get_attack_type(*a, **kw): return "Unknown"
    def check_ml_status(*a, **kw): return {"status": "unavailable"}

# ML Algorithms
from .isolation_forest import (
    detect_anomalies,
    get_anomaly_summary,
    SOCIsolationForest
)

from .fuzzy_clustering import (
    cluster_threats,
    get_threat_distribution,
    FuzzyCMeans
)

# RL Threat Classifier (optional, may not exist on first run)
try:
    from .rl_threat_classifier import (
        classify_event,
        classify_events,
        submit_feedback,
        get_rl_stats,
        RLThreatClassifier
    )
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False
    def classify_event(*a, **kw): return {}
    def classify_events(*a, **kw): return []
    def submit_feedback(*a, **kw): return False
    def get_rl_stats(*a, **kw): return {}

__all__ = [
    'score_network_event',
    'score_dataframe', 
    'get_attack_type',
    'check_ml_status',
    'ML_AVAILABLE',
    # Isolation Forest
    'detect_anomalies',
    'get_anomaly_summary',
    'SOCIsolationForest',
    # Fuzzy C-Means
    'cluster_threats',
    'get_threat_distribution',
    'FuzzyCMeans',
    # RL Threat Classifier
    'classify_event',
    'classify_events',
    'submit_feedback',
    'get_rl_stats',
    'RLThreatClassifier',
    'RL_AVAILABLE',
]


