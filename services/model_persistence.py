"""
Model Persistence Service
=========================
Saves and loads trained ML models to/from disk using joblib.
Keeps a training log so the system can track model evolution over time.

Models are stored in: data/models/
Training history is stored in: data/models/training_log.json
"""

import os
import json
import joblib
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models")

def _ensure_dir():
    """Ensure the models directory exists."""
    os.makedirs(MODELS_DIR, exist_ok=True)

def save_model(model_name: str, model_obj: Any, scaler_obj: Any = None, metadata: Dict = None):
    """
    Save a trained model (and optional scaler) to disk.
    
    Args:
        model_name: Identifier (e.g. 'isolation_forest', 'fuzzy_clustering')
        model_obj: The trained model object (or dict of objects)
        scaler_obj: Optional scaler/preprocessor to save alongside
        metadata: Optional dict with training metrics (accuracy, sample count, etc.)
    """
    _ensure_dir()
    
    model_path = os.path.join(MODELS_DIR, f"{model_name}_model.pkl")
    joblib.dump(model_obj, model_path)
    
    if scaler_obj is not None:
        scaler_path = os.path.join(MODELS_DIR, f"{model_name}_scaler.pkl")
        joblib.dump(scaler_obj, scaler_path)
    
    # Log training event
    log_entry = {
        "model_name": model_name,
        "saved_at": datetime.now().isoformat(),
        "model_path": model_path,
    }
    if metadata:
        log_entry["metadata"] = metadata
    
    _append_training_log(log_entry)
    
    print(f"[MODEL-PERSIST] Saved {model_name} to {model_path}")
    return model_path

def load_model(model_name: str) -> Optional[Tuple[Any, Any, Dict]]:
    """
    Load a previously saved model from disk.
    
    Args:
        model_name: Identifier used when saving
        
    Returns:
        Tuple of (model_obj, scaler_obj_or_None, metadata_dict) or None if not found
    """
    _ensure_dir()
    
    model_path = os.path.join(MODELS_DIR, f"{model_name}_model.pkl")
    scaler_path = os.path.join(MODELS_DIR, f"{model_name}_scaler.pkl")
    
    if not os.path.exists(model_path):
        return None
    
    try:
        model_obj = joblib.load(model_path)
        scaler_obj = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
        
        # Get latest metadata from training log
        metadata = get_latest_training_info(model_name)
        
        print(f"[MODEL-PERSIST] Loaded {model_name} from disk")
        return (model_obj, scaler_obj, metadata or {})
    except Exception as e:
        print(f"[MODEL-PERSIST] Error loading {model_name}: {e}")
        return None

def get_training_history(model_name: str = None) -> list:
    """
    Get training history entries, optionally filtered by model name.
    """
    log_path = os.path.join(MODELS_DIR, "training_log.json")
    if not os.path.exists(log_path):
        return []
    
    try:
        with open(log_path, "r") as f:
            entries = json.load(f)
        
        if model_name:
            entries = [e for e in entries if e.get("model_name") == model_name]
        return entries
    except Exception:
        return []

def get_latest_training_info(model_name: str) -> Optional[Dict]:
    """Get the most recent training log entry for a model."""
    history = get_training_history(model_name)
    return history[-1] if history else None

def get_last_training_sample_count(model_name: str) -> int:
    """Get the sample count from the last training run."""
    info = get_latest_training_info(model_name)
    if info and "metadata" in info:
        return info["metadata"].get("n_samples", 0)
    return 0

def _append_training_log(entry: Dict):
    """Append an entry to the training log."""
    _ensure_dir()
    log_path = os.path.join(MODELS_DIR, "training_log.json")
    
    entries = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                entries = json.load(f)
        except Exception:
            entries = []
    
    entries.append(entry)
    
    # Keep only last 100 entries to avoid unbounded growth
    if len(entries) > 100:
        entries = entries[-100:]
    
    with open(log_path, "w") as f:
        json.dump(entries, f, indent=2)
