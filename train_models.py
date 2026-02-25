import sys
import os
import json
import time
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_engine.nsl_kdd_dataset import load_nsl_kdd_train, load_nsl_kdd_test
from ml_engine.isolation_forest import isolation_forest
from ml_engine.fuzzy_clustering import fuzzy_clustering

def run_training():
    print("="*60)
    print("AI-DRIVEN SOC: NSL-KDD MODEL TRAINING PIPELINE")
    print("="*60)
    print("[*] Target Requirements:")
    print("    - Accuracy: >95%")
    print("    - Efficiency: 100% (Parallelized Ensemble)")
    print("    - Cluster Purity: ~95%")
    print("="*60)
    
    start_time = time.time()
    
    # 1. Load Data
    print("\n[1/5] Loading NSL-KDD Dataset from local directory...")
    try:
        train_df = load_nsl_kdd_train()
        test_df = load_nsl_kdd_test()
        print(f"      ✅ Success: Loaded {len(train_df)} training and {len(test_df)} test records.")
    except Exception as e:
        print(f"      ❌ Failed to load dataset: {e}")
        return

    # 2. Train Isolation Forest (Anomaly Detection)
    print("\n[2/5] Training Isolation Forest & Supervised Ensemble...")
    t0 = time.time()
    iso_stats = isolation_forest.train_on_dataset()
    t1 = time.time()
    print(f"      ✅ Training Complete in {t1-t0:.2f} seconds.")
    
    # 3. Evaluate Isolation Forest
    print("\n[3/5] Evaluating Isolation Forest Ensemble...")
    iso_metrics = isolation_forest.evaluate()
    acc = iso_metrics.get('accuracy', 0)
    f1 = iso_metrics.get('f1_score', 0)
    
    print(f"      📊 Results:")
    print(f"         - Accuracy:  {acc:.2f}%")
    print(f"         - Precision: {iso_metrics.get('precision', 0):.2f}%")
    print(f"         - Recall:    {iso_metrics.get('recall', 0):.2f}%")
    print(f"         - F1-Score:  {f1:.2f}%")
    if acc >= 95.0:
        print("         🏆 STATUS: PASSED USER REQUIREMENT")
    else:
        print("         ⚠️ STATUS: FALLS SHORT OF 95% REQUIREMENT")

    # 4. Train Fuzzy C-Means (Threat Categorization)
    print("\n[4/5] Training Fuzzy C-Means Threat Clustering Engine...")
    t0 = time.time()
    fcm_stats = fuzzy_clustering.fit_on_dataset()
    t1 = time.time()
    print(f"      ✅ Training Complete in {t1-t0:.2f} seconds.")
    
    # 5. Evaluate Fuzzy C-Means
    print("\n[5/5] Evaluating Fuzzy C-Means Clusters...")
    fcm_metrics = fuzzy_clustering.evaluate()
    purity = fcm_metrics.get('overall_purity', 0)
    
    print(f"      📊 Results:")
    print(f"         - Overall Cluster Purity: {purity:.2f}%")
    if purity >= 95.0:
        print("         🏆 STATUS: PASSED USER REQUIREMENT")
    else:
        print("         ⚠️ STATUS: FALLS SHORT OF 95% REQUIREMENT")
        
    print("\n      🔍 Category Accuracy Breakdown:")
    for cat, val in fcm_metrics.get('category_accuracy', {}).items():
        print(f"         - {cat}: {val}%")

    total_time = time.time() - start_time
    print("="*60)
    print(f"PIPELINE COMPLETE (Total Time: {total_time:.2f}s)")
    print("Models have been successfully serialized and saved to disk.")
    print("The Dashboard SOC will now use these models for real-time inference.")
    print("="*60)


if __name__ == "__main__":
    # Force retraining by resetting the dataset flag so it doesn't just load from disk
    isolation_forest._trained_on_dataset = False
    fuzzy_clustering._trained_on_dataset = False
    run_training()
