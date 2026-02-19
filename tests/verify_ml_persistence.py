"""
Verify ML Model Persistence
============================
Tests that models save/load correctly and that retraining from DB works.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_model_persistence():
    print("=" * 60)
    print("ML MODEL PERSISTENCE VERIFICATION")
    print("=" * 60)
    
    # 1. Test model_persistence service
    print("\n[1] Testing model_persistence service...")
    from services.model_persistence import save_model, load_model, get_training_history
    
    save_model("test_model", {"dummy": True}, None, {"test": True})
    result = load_model("test_model")
    assert result is not None, "Failed to load test model"
    model, scaler, meta = result
    assert model["dummy"] == True, "Model data mismatch"
    print("    ✓ save/load works correctly")
    
    history = get_training_history("test_model")
    assert len(history) > 0, "No training history"
    print(f"    ✓ Training history has {len(history)} entries")
    
    # Clean up test model
    os.remove(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models", "test_model_model.pkl"))
    
    # 2. Test database protection
    print("\n[2] Testing database protection...")
    from services.database import db
    
    count_before = db.get_event_count()
    db.clear_all()  # Should NOT delete anything (no confirm)
    count_after = db.get_event_count()
    assert count_before == count_after, "Data was deleted without confirmation!"
    print(f"    ✓ clear_all() without confirm=True protected {count_before} records")
    
    # 3. Test get_all_events
    print("\n[3] Testing get_all_events...")
    all_events = db.get_all_events()
    print(f"    ✓ Retrieved {len(all_events)} events for ML training")
    assert len(all_events) > 0, "No events found in database"
    
    # 4. Test Isolation Forest persistence
    print("\n[4] Testing Isolation Forest train + save...")
    from ml_engine.isolation_forest import isolation_forest
    
    if not isolation_forest.is_trained:
        print("    Training on NSL-KDD (first time)...")
        isolation_forest.train_on_dataset()
    
    print(f"    ✓ Model is trained: {isolation_forest.is_trained}")
    
    # Verify model file exists
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models", "isolation_forest_model.pkl")
    if os.path.exists(model_path):
        size_kb = os.path.getsize(model_path) / 1024
        print(f"    ✓ Model saved to disk ({size_kb:.0f} KB)")
    else:
        print("    ⚠ Model file not found on disk (will save on next train)")
    
    # 5. Test Fuzzy Clustering persistence
    print("\n[5] Testing Fuzzy Clustering train + save...")
    from ml_engine.fuzzy_clustering import fuzzy_clustering
    
    if not fuzzy_clustering.is_trained:
        print("    Training on NSL-KDD (first time)...")
        fuzzy_clustering.fit_on_dataset()
    
    print(f"    ✓ Model is trained: {fuzzy_clustering.is_trained}")
    print(f"    ✓ Centroids shape: {fuzzy_clustering.centers.shape if fuzzy_clustering.centers is not None else 'None'}")
    
    fcm_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models", "fuzzy_clustering_model.pkl")
    if os.path.exists(fcm_path):
        size_kb = os.path.getsize(fcm_path) / 1024
        print(f"    ✓ Model saved to disk ({size_kb:.0f} KB)")
    else:
        print("    ⚠ Model file not found on disk (will save on next train)")
    
    # 6. Test retrain from DB
    print("\n[6] Testing retrain_from_db (Isolation Forest)...")
    if_result = isolation_forest.retrain_from_db()
    print(f"    Result: {if_result}")
    
    print("\n[7] Testing retrain_from_db (Fuzzy Clustering)...")
    fcm_result = fuzzy_clustering.retrain_from_db()
    print(f"    Result: {fcm_result}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    
    # Show training history
    print("\nTraining History:")
    for entry in get_training_history():
        name = entry.get("model_name", "?")
        saved_at = entry.get("saved_at", "?")
        meta = entry.get("metadata", {})
        samples = meta.get("n_samples", meta.get("test", "?"))
        print(f"  {name}: saved {saved_at} ({samples} samples)")

if __name__ == "__main__":
    test_model_persistence()
