"""
Fuzzy C-Means Clustering for Threat Categorization in SOC
==========================================================
This module implements Fuzzy C-Means (FCM) clustering to group similar
security events and identify threat patterns.

HOW FUZZY C-MEANS WORKS:
- Unlike K-Means which assigns each point to exactly one cluster,
  FCM assigns a degree of membership to each cluster
- Each event can partially belong to multiple threat categories
- Uses iterative optimization to minimize within-cluster variance
- The "fuzziness" parameter (m) controls how fuzzy the clustering is

WHY FCM FOR SOC:
- Security events often exhibit characteristics of multiple threat types
- Soft clustering captures uncertainty in threat classification
- Better handles overlapping attack patterns
- Provides confidence scores for each classification
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from datetime import datetime


class FuzzyCMeans:
    """
    Fuzzy C-Means clustering implementation for threat categorization.
    
    Clusters events into threat categories:
    - Malware/Ransomware
    - Data Exfiltration
    - DDoS/DoS
    - Reconnaissance/Scanning
    - Insider Threat
    """
    
    def __init__(self, n_clusters: int = 5, m: float = 2.0, max_iter: int = 25, 
                 error: float = 1e-3, random_state: int = 42):
        """
        Initialize Fuzzy C-Means model.
        
        Args:
            n_clusters: Number of clusters (threat categories)
            m: Fuzziness parameter (m > 1, higher = fuzzier)
            max_iter: Maximum iterations for convergence
            error: Convergence threshold
            random_state: Random seed for reproducibility
        """
        self.n_clusters = n_clusters
        self.m = m
        self.max_iter = max_iter
        self.error = error
        self.random_state = random_state
        
        self.centers = None
        self.membership = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Threat category names
        self.cluster_names = [
            'Malware/Ransomware',
            'Data Exfiltration', 
            'DDoS/DoS Attack',
            'Reconnaissance',
            'Insider Threat'
        ]
    
    def _extract_features(self, events: List[Dict]) -> np.ndarray:
        """Extract and normalize features from events."""
        features = []
        for event in events:
            features.append([
                event.get('bytes_in', 0),
                event.get('bytes_out', 0),
                event.get('packets', 1),
                event.get('duration', 0),
                event.get('port', 0),
                event.get('risk_score', 50),
                1 if event.get('is_internal', False) else 0,
                self._attack_type_to_num(event.get('attack_type', 'Unknown'))
            ])
        return np.array(features)
    
    def _attack_type_to_num(self, attack_type: str) -> int:
        """Convert attack type to numeric."""
        attack_map = {
            'Malware': 1, 'Ransomware': 1,
            'Exfiltration': 2, 'Data Breach': 2,
            'DDoS': 3, 'DoS': 3,
            'Port Scan': 4, 'Reconnaissance': 4,
            'Insider': 5, 'Privilege Escalation': 5
        }
        return attack_map.get(attack_type, 0)
    
    def _initialize_membership(self, n_samples: int) -> np.ndarray:
        """Initialize membership matrix randomly."""
        np.random.seed(self.random_state)
        membership = np.random.rand(n_samples, self.n_clusters)
        # Normalize so each row sums to 1
        membership = membership / membership.sum(axis=1, keepdims=True)
        return membership
    
    def _update_centers(self, X: np.ndarray, membership: np.ndarray) -> np.ndarray:
        """Update cluster centers based on membership weights."""
        um = membership ** self.m
        centers = (um.T @ X) / um.sum(axis=0, keepdims=True).T
        return centers
    
    def _update_membership(self, X: np.ndarray, centers: np.ndarray) -> np.ndarray:
        """Update membership matrix based on distances to centers using vectorization."""
        n_samples = X.shape[0]
        
        # Calculate distances (N x C) using broadcasting
        # Expanding dims: (N, 1, D) - (1, C, D) -> (N, C, D) -> norm -> (N, C)
        # This can be memory intensive for large N*C*D. 
        # Alternative: ||x-c||^2 = ||x||^2 + ||c||^2 - 2<x,c>
        
        # Using sklearn if available for efficiency, else numpy
        try:
             from sklearn.metrics.pairwise import euclidean_distances
             dist = euclidean_distances(X, centers)
        except ImportError:
             # Manual broadcasting fallback
             dist = np.linalg.norm(X[:, None, :] - centers[None, :, :], axis=2)
             
        # Avoid division by zero
        dist = np.fmax(dist, 1e-10)
        
        # Calculate membership: u_ij = 1 / sum_k ( (d_ij / d_k)^ (2/(m-1)) )
        power = 2.0 / (self.m - 1)
        dist_pow = dist ** power
        
        # Inverse distance power
        inv_dist_pow = 1.0 / dist_pow
        
        # Sum over clusters for each sample
        sum_inv_dist_pow = np.sum(inv_dist_pow, axis=1, keepdims=True)
        
        # Compute membership
        membership = inv_dist_pow / sum_inv_dist_pow
        
        return membership
    
    def fit(self, events: List[Dict]) -> Dict:
        """
        Train the Fuzzy C-Means model on events.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Training statistics
        """
        if len(events) < self.n_clusters:
            return {"error": f"Need at least {self.n_clusters} events to train"}
        
        X = self._extract_features(events)
        X = self.scaler.fit_transform(X)
        
        n_samples = X.shape[0]
        
        # Initialize membership matrix
        self.membership = self._initialize_membership(n_samples)
        
        # Iterative optimization
        for iteration in range(self.max_iter):
            # Update centers
            self.centers = self._update_centers(X, self.membership)
            
            # Update membership
            new_membership = self._update_membership(X, self.centers)
            
            # Check convergence
            if np.max(np.abs(new_membership - self.membership)) < self.error:
                break
            
            self.membership = new_membership
        
        self.is_trained = True
        
        return {
            'n_clusters': self.n_clusters,
            'n_samples': n_samples,
            'iterations': iteration + 1,
            'converged': iteration < self.max_iter - 1,
            'trained_at': datetime.now().isoformat()
        }
    
    def predict(self, events: List[Dict]) -> List[Dict]:
        """
        Predict cluster memberships for events.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Events with cluster memberships and primary category
        """
        if not self.is_trained:
            self.fit(events)
        
        X = self._extract_features(events)
        X = self.scaler.transform(X)
        
        membership = self._update_membership(X, self.centers)
        
        results = []
        for i, event in enumerate(events):
            result = event.copy()
            
            # Add membership percentages for each cluster
            memberships = {}
            for j, name in enumerate(self.cluster_names):
                memberships[name] = round(membership[i, j] * 100, 1)
            
            result['cluster_memberships'] = memberships
            
            # Primary cluster (highest membership)
            primary_idx = np.argmax(membership[i])
            result['primary_category'] = self.cluster_names[primary_idx]
            result['primary_confidence'] = round(membership[i, primary_idx] * 100, 1)
            
            # Secondary cluster if membership > 20%
            sorted_idx = np.argsort(membership[i])[::-1]
            if membership[i, sorted_idx[1]] > 0.2:
                result['secondary_category'] = self.cluster_names[sorted_idx[1]]
            
            results.append(result)
        
        return results
    
    def get_cluster_summary(self, events: List[Dict]) -> Dict:
        """
        Get summary statistics for each cluster.
        
        Args:
            events: List of analyzed events
            
        Returns:
            Cluster summary statistics
        """
        results = self.predict(events)
        
        cluster_counts = {name: 0 for name in self.cluster_names}
        for r in results:
            cluster_counts[r['primary_category']] += 1
        
        cluster_avg_confidence = {name: [] for name in self.cluster_names}
        for r in results:
            for name, conf in r['cluster_memberships'].items():
                cluster_avg_confidence[name].append(conf)
        
        for name in cluster_avg_confidence:
            vals = cluster_avg_confidence[name]
            cluster_avg_confidence[name] = np.mean(vals) if vals else 0
        
        return {
            'cluster_counts': cluster_counts,
            'cluster_percentages': {
                name: round(count / len(results) * 100, 1) 
                for name, count in cluster_counts.items()
            },
            'avg_membership': cluster_avg_confidence,
            'total_events': len(results)
        }
    
    def fit_on_dataset(self) -> Dict:
        """
        Train on NSL-KDD dataset using the 5 attack categories.
        Maps NSL-KDD categories to FCM clusters.
        
        Returns:
            Training statistics
        """
        from ml_engine.nsl_kdd_dataset import (
            load_nsl_kdd_train, get_numeric_features,
            get_category_labels, get_dataset_summary
        )
        
        train_df = load_nsl_kdd_train()
        
        # Subsample for performance (FCM is computationally expensive O(N*C^2))
        max_samples = 5000
        if len(train_df) > max_samples:
            train_df = train_df.sample(n=max_samples, random_state=42)
            
        summary = get_dataset_summary(train_df)
        
        X = get_numeric_features(train_df)
        
        # Scale
        X_scaled = self.scaler.fit_transform(X)
        
        n_samples = X_scaled.shape[0]
        
        # Initialize membership
        self.membership = self._initialize_membership(n_samples)
        
        # Iterative optimization
        converged_iter = self.max_iter
        for iteration in range(self.max_iter):
            self.centers = self._update_centers(X_scaled, self.membership)
            new_membership = self._update_membership(X_scaled, self.centers)
            
            if np.max(np.abs(new_membership - self.membership)) < self.error:
                converged_iter = iteration + 1
                break
            self.membership = new_membership
        
        self.is_trained = True
        self._trained_on_dataset = True
        self._train_labels = get_category_labels(train_df)
        
        return {
            'n_clusters': self.n_clusters,
            'n_samples': n_samples,
            'n_features': X_scaled.shape[1],
            'iterations': converged_iter,
            'converged': converged_iter < self.max_iter,
            'trained_at': datetime.now().isoformat(),
            'dataset_summary': summary
        }
    
    def evaluate(self) -> Dict:
        """
        Evaluate clustering on NSL-KDD test data.
        
        Computes:
        - Cluster purity (how homogeneous each cluster is)
        - Per-category distribution across clusters
        - Silhouette score
        
        Returns:
            Evaluation metrics dictionary
        """
        if not hasattr(self, '_trained_on_dataset') or not self._trained_on_dataset:
            self.fit_on_dataset()
        
        from ml_engine.nsl_kdd_dataset import (
            load_nsl_kdd_test, get_numeric_features, get_category_labels
        )
        
        test_df = load_nsl_kdd_test()
        X_test = get_numeric_features(test_df)
        y_true_labels = get_category_labels(test_df)
        
        X_test_scaled = self.scaler.transform(X_test)
        
        # Get membership for test data
        membership = self._update_membership(X_test_scaled, self.centers)
        
        # Assign each sample to primary cluster
        cluster_assignments = np.argmax(membership, axis=1)
        
        # Map category names to numbers for purity calculation
        cat_names = sorted(set(y_true_labels))
        cat_to_idx = {name: idx for idx, name in enumerate(cat_names)}
        y_true_idx = np.array([cat_to_idx[label] for label in y_true_labels])
        
        # Cluster purity: for each cluster, find most common true label
        total_correct = 0
        cluster_details = {}
        for c in range(self.n_clusters):
            mask = cluster_assignments == c
            if mask.sum() == 0:
                cluster_details[self.cluster_names[c]] = {
                    'size': 0, 'dominant_category': 'N/A', 'purity': 0
                }
                continue
            
            cluster_true = y_true_labels[mask]
            unique, counts = np.unique(cluster_true, return_counts=True)
            dominant_idx = np.argmax(counts)
            dominant_cat = unique[dominant_idx]
            purity = counts[dominant_idx] / mask.sum()
            total_correct += counts[dominant_idx]
            
            cat_dist = {str(u): int(c) for u, c in zip(unique, counts)}
            
            cluster_details[self.cluster_names[c]] = {
                'size': int(mask.sum()),
                'dominant_category': dominant_cat,
                'purity': round(purity * 100, 2),
                'category_distribution': cat_dist
            }
        
        overall_purity = total_correct / len(y_true_labels) if len(y_true_labels) > 0 else 0
        
        # Silhouette score (sampled for speed)
        try:
            from sklearn.metrics import silhouette_score
            sample_size = min(1000, len(X_test_scaled))
            indices = np.random.choice(len(X_test_scaled), sample_size, replace=False)
            sil_score = silhouette_score(X_test_scaled[indices], cluster_assignments[indices])
        except Exception:
            sil_score = 0.0
        
        # Per-category accuracy
        category_accuracy = {}
        for cat in cat_names:
            cat_mask = y_true_labels == cat
            if cat_mask.sum() == 0:
                continue
            # Find which cluster this category maps to most
            cat_clusters = cluster_assignments[cat_mask]
            most_common = np.bincount(cat_clusters, minlength=self.n_clusters).argmax()
            correct = (cat_clusters == most_common).sum()
            category_accuracy[cat] = round(correct / cat_mask.sum() * 100, 2)
        
        self.dataset_metrics = {
            'overall_purity': round(overall_purity * 100, 2),
            'silhouette_score': round(sil_score, 4),
            'cluster_details': cluster_details,
            'category_accuracy': category_accuracy,
            'test_samples': len(y_true_labels),
            'categories_found': cat_names
        }
        
        return self.dataset_metrics


def generate_sample_events(n_events: int = 100) -> List[Dict]:
    """Generate sample SOC events for clustering demonstration."""
    np.random.seed(42)
    events = []
    
    threat_types = [
        ('Malware', {'bytes_in': (50000, 10000), 'bytes_out': (5000, 1000), 
                     'packets': (500, 100), 'duration': (60, 20), 'port': 443}),
        ('Exfiltration', {'bytes_in': (1000, 200), 'bytes_out': (500000, 100000),
                          'packets': (2000, 500), 'duration': (300, 60), 'port': 8080}),
        ('DDoS', {'bytes_in': (1000000, 200000), 'bytes_out': (100, 50),
                  'packets': (50000, 10000), 'duration': (5, 2), 'port': 80}),
        ('Port Scan', {'bytes_in': (100, 20), 'bytes_out': (50, 10),
                       'packets': (1000, 200), 'duration': (1, 0.5), 'port': 0}),
        ('Insider', {'bytes_in': (10000, 2000), 'bytes_out': (100000, 20000),
                     'packets': (500, 100), 'duration': (600, 120), 'port': 22})
    ]
    
    for i in range(n_events):
        threat_name, params = threat_types[i % len(threat_types)]
        
        events.append({
            'id': f'EVT-{i:04d}',
            'bytes_in': max(0, np.random.normal(*params['bytes_in'])),
            'bytes_out': max(0, np.random.normal(*params['bytes_out'])),
            'packets': max(1, int(np.random.normal(*params['packets']))),
            'duration': max(0, np.random.normal(*params['duration'])),
            'port': params['port'] if params['port'] else np.random.randint(1, 65535),
            'attack_type': threat_name,
            'risk_score': np.random.randint(30, 100),
            'is_internal': threat_name == 'Insider',
            'source_ip': f'192.168.{np.random.randint(0, 255)}.{np.random.randint(1, 255)}'
        })
    
    return events


# Singleton instance
fuzzy_clustering = FuzzyCMeans()


def cluster_threats(events: List[Dict]) -> List[Dict]:
    """
    Main function to cluster security events.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Events with cluster memberships
    """
    return fuzzy_clustering.predict(events)


def get_threat_distribution(events: List[Dict]) -> Dict:
    """
    Get the distribution of threat categories.
    
    Args:
        events: List of events to analyze
        
    Returns:
        Threat distribution summary
    """
    return fuzzy_clustering.get_cluster_summary(events)
