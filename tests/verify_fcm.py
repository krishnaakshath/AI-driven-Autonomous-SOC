
import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_engine.fuzzy_clustering import FuzzyCMeans

def verify_fcm():
    print("Initializing FCM with improvements...")
    fcm = FuzzyCMeans(n_clusters=5, m=1.6, max_iter=100)
    
    print("Training on NSL-KDD dataset...")
    try:
        stats = fcm.fit_on_dataset()
        print("Training complete.")
        print(f"Stats: {stats}")
    except Exception as e:
        print(f"Training failed: {e}")
        return

    print("Evaluating...")
    try:
        metrics = fcm.evaluate()
        print("\n=== FCM EVALUATION METRICS ===")
        print(f"Overall Purity: {metrics['overall_purity']}%")
        print(f"Silhouette Score: {metrics['silhouette_score']}")
        print(f"Davies-Bouldin Index: {metrics['davies_bouldin_index']}")
        print("\nCategory Accuracy:")
        for cat, acc in metrics['category_accuracy'].items():
            print(f"  {cat}: {acc}%")
            
        print("\nCluster Details:")
        for name, details in metrics['cluster_details'].items():
            print(f"  {name}: Size={details['size']}, Purity={details['purity']}%, Dominant={details['dominant_category']}")
            
    except Exception as e:
        print(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_fcm()
