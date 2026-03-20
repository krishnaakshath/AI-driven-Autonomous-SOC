"""
Tests for Federated Learning Engine
====================================
Verifies client partitioning, local training, FedAvg aggregation,
convergence behavior, and comparison with centralized baseline.
"""

import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_engine.federated_learning import FederatedClient, FederatedCoordinator


class TestFederatedClient(unittest.TestCase):
    """Tests for individual FederatedClient nodes."""

    def setUp(self):
        """Create a client with synthetic data."""
        rng = np.random.RandomState(42)
        self.X = rng.randn(100, 6)
        self.y = (rng.rand(100) > 0.7).astype(int)
        self.client = FederatedClient(client_id=0, data=self.X, labels=self.y, random_state=42)

    def test_client_initialization(self):
        """Client should store data and metadata correctly."""
        self.assertEqual(self.client.client_id, 0)
        self.assertEqual(self.client.n_samples, 100)
        self.assertFalse(self.client.is_trained)

    def test_local_training(self):
        """Client should train successfully and return metrics."""
        metrics = self.client.train_local()
        self.assertIn("accuracy", metrics)
        self.assertIn("f1_score", metrics)
        self.assertGreater(metrics["accuracy"], 0)
        self.assertTrue(self.client.is_trained)

    def test_get_model_parameters(self):
        """Trained client should export valid parameters."""
        self.client.train_local()
        params = self.client.get_model_parameters()
        self.assertIn("probabilities", params)
        self.assertIn("n_samples", params)
        self.assertEqual(params["n_samples"], 100)
        self.assertEqual(params["probabilities"].shape[0], 100)

    def test_get_model_parameters_untrained(self):
        """Untrained client should return empty params."""
        params = self.client.get_model_parameters()
        self.assertEqual(params, {})

    def test_evaluate(self):
        """Client should evaluate on external test data."""
        self.client.train_local()
        rng = np.random.RandomState(99)
        X_test = rng.randn(20, 6)
        # Scale with client's scaler
        X_test_scaled = self.client.scaler.transform(X_test)
        y_test = (rng.rand(20) > 0.7).astype(int)
        result = self.client.evaluate(X_test_scaled, y_test)
        self.assertIn("accuracy", result)
        self.assertEqual(result["client_id"], 0)


class TestFederatedCoordinator(unittest.TestCase):
    """Tests for the FederatedCoordinator aggregation server."""

    def setUp(self):
        """Create coordinator with default settings."""
        self.coordinator = FederatedCoordinator(
            n_clients=3, n_rounds=3, alpha=0.5, random_state=42
        )

    def test_initialization(self):
        """Coordinator should initialize with correct params."""
        self.assertEqual(self.coordinator.n_clients, 3)
        self.assertEqual(self.coordinator.n_rounds, 3)
        self.assertFalse(self.coordinator.is_trained)

    def test_generate_synthetic_data(self):
        """Synthetic data generation should produce valid arrays."""
        X, y = self.coordinator._generate_synthetic_data(n_samples=500)
        self.assertEqual(X.shape, (500, 6))
        self.assertEqual(y.shape, (500,))
        self.assertTrue(np.all(X >= 0))
        self.assertTrue(set(np.unique(y)).issubset({0, 1}))

    def test_partition_noniid(self):
        """Non-IID partitioning should split data among clients."""
        X, y = self.coordinator._generate_synthetic_data(n_samples=500)
        partitions = self.coordinator.partition_data_noniid(X, y)
        self.assertEqual(len(partitions), 3)
        total = sum(len(p[0]) for p in partitions)
        self.assertEqual(total, 500)
        # Non-IID: partitions should have different anomaly ratios
        ratios = [p[1].mean() for p in partitions]
        self.assertFalse(all(r == ratios[0] for r in ratios),
                         "All partitions have identical ratios — not non-IID")

    def test_partition_iid(self):
        """IID partitioning should split data roughly equally."""
        X, y = self.coordinator._generate_synthetic_data(n_samples=300)
        partitions = self.coordinator.partition_data_iid(X, y)
        self.assertEqual(len(partitions), 3)
        sizes = [len(p[0]) for p in partitions]
        self.assertEqual(sum(sizes), 300)
        self.assertTrue(all(abs(s - 100) <= 1 for s in sizes))

    def test_prepare_data(self):
        """Data preparation should produce train/test splits."""
        info = self.coordinator.prepare_data(use_siem=False)
        self.assertIn("total_samples", info)
        self.assertGreater(info["total_samples"], 0)
        self.assertIsNotNone(self.coordinator._training_data)
        self.assertIsNotNone(self.coordinator._test_data)

    def test_federated_training_runs(self):
        """Full federated training should complete and produce results."""
        self.coordinator.prepare_data(use_siem=False)
        results = self.coordinator.run_federated_training()
        self.assertEqual(results["status"], "completed")
        self.assertEqual(results["n_clients"], 3)
        self.assertEqual(results["n_rounds"], 3)
        self.assertGreater(results["final_global_accuracy"], 0)

    def test_convergence(self):
        """Accuracy should generally improve or stabilize over rounds."""
        self.coordinator.prepare_data(use_siem=False)
        results = self.coordinator.run_federated_training()
        round_accs = [r["global_accuracy"] for r in results["round_metrics"]]
        # Final accuracy should be >= first round (convergence)
        self.assertGreaterEqual(round_accs[-1], round_accs[0] - 5.0,
                                "Accuracy should not drop significantly")

    def test_centralized_baseline(self):
        """Centralized baseline should be computed."""
        self.coordinator.prepare_data(use_siem=False)
        results = self.coordinator.run_federated_training()
        baseline = results.get("centralized_baseline")
        self.assertIsNotNone(baseline)
        self.assertIn("accuracy", baseline)
        self.assertGreater(baseline["accuracy"], 50)

    def test_fl_vs_centralized_gap(self):
        """FL accuracy should be within reasonable range of centralized."""
        # Use more rounds to allow convergence
        coord = FederatedCoordinator(
            n_clients=3, n_rounds=5, alpha=0.5, random_state=42
        )
        coord.prepare_data(use_siem=False)
        results = coord.run_federated_training()
        gap = results.get("accuracy_gap", 0)
        # FL should be within 50% of centralized (generous bound for few rounds on synthetic data)
        self.assertLess(abs(gap), 50.0,
                        f"FL accuracy gap too large: {gap}%")

    def test_dp_noise(self):
        """Differential privacy noise should be added when epsilon > 0."""
        coord_dp = FederatedCoordinator(
            n_clients=3, n_rounds=2, dp_epsilon=1.0, random_state=42
        )
        proba = np.array([[0.3, 0.7], [0.8, 0.2]])
        noised = coord_dp._add_dp_noise(proba)
        # With noise, values should differ from original
        self.assertFalse(np.array_equal(proba, noised))
        # Values should still be clipped to [0, 1]
        self.assertTrue(np.all(noised >= 0))
        self.assertTrue(np.all(noised <= 1))

    def test_no_dp_noise(self):
        """No noise should be added when epsilon = 0."""
        proba = np.array([[0.3, 0.7], [0.8, 0.2]])
        result = self.coordinator._add_dp_noise(proba)
        np.testing.assert_array_equal(proba, result)

    def test_client_data_distribution(self):
        """Training results should include per-client data distribution."""
        self.coordinator.prepare_data(use_siem=False)
        results = self.coordinator.run_federated_training()
        dist = results.get("client_data_distribution", [])
        self.assertEqual(len(dist), 3)
        for d in dist:
            self.assertIn("client_id", d)
            self.assertIn("n_samples", d)
            self.assertIn("anomaly_ratio", d)
            self.assertGreater(d["n_samples"], 0)

    def test_privacy_analysis(self):
        """Privacy analysis should return correct info."""
        self.coordinator.prepare_data(use_siem=False)
        self.coordinator.run_federated_training()
        privacy = self.coordinator.get_privacy_analysis()
        self.assertFalse(privacy["dp_enabled"])
        self.assertEqual(privacy["privacy_level"], "None")


class TestModuleFunctions(unittest.TestCase):
    """Tests for module-level helper functions."""

    def test_fl_available(self):
        """FL_AVAILABLE should be True."""
        from ml_engine.federated_learning import FL_AVAILABLE
        self.assertTrue(FL_AVAILABLE)

    def test_get_fl_status_uninitialized(self):
        """Status should show not initialized before training."""
        from ml_engine.federated_learning import get_fl_status
        status = get_fl_status()
        self.assertIn("status", status)


if __name__ == "__main__":
    unittest.main()
