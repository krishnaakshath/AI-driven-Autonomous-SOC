import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock libraries before import
sys.modules["numpy"] = MagicMock()
sys.modules["pandas"] = MagicMock()
sys.modules["sklearn"] = MagicMock()
sys.modules["sklearn.ensemble"] = MagicMock()
sys.modules["sklearn.metrics"] = MagicMock()
sys.modules["sklearn.preprocessing"] = MagicMock()
sys.modules["joblib"] = MagicMock()
sys.modules["streamlit"] = MagicMock()

import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_engine.isolation_forest import SOCIsolationForest

class TestIsolationForest(unittest.TestCase):
    def setUp(self):
        self.model = SOCIsolationForest()

    def test_extract_features(self):
        """Test feature extraction."""
        data = [
            {"protocol": "TCP", "service": "HTTP", "flag": "SF", "src_bytes": 100, "dst_bytes": 200},
            {"protocol": "UDP", "service": "DNS", "flag": "SF", "src_bytes": 50, "dst_bytes": 0}
        ]
        # We need to mock numpy array creation in _extract_features
        with patch('numpy.array') as mock_array:
            self.model._extract_features(data)
            self.assertTrue(mock_array.called)

    @patch('joblib.dump')
    def test_train(self, mock_dump):
        """Test model training."""
        train_data = [
            {"protocol": "TCP", "service": "HTTP", "flag": "SF", "src_bytes": 100, "dst_bytes": 200}
        ] * 10
        
        # Mock numpy operations inside train
        with patch('numpy.array'):
            metrics = self.model.train(train_data)
        
        self.assertIn("n_samples", metrics)
        self.assertEqual(metrics["n_samples"], 10)
        # Accuracy is not in train(), only in evaluate()
        self.assertNotIn("accuracy", metrics)

    @patch('joblib.load')
    def test_predict(self, mock_load):
        """Test prediction logic."""
        # Mock the underlying sklearn model
        self.model.model = MagicMock()
        self.model.model.predict.return_value = [1, -1] # 1=Normal, -1=Anomaly
        
        # Mock decision_function and its min/max for normalization
        mock_scores = MagicMock()
        mock_scores.min.return_value = -0.5
        mock_scores.max.return_value = 0.5
        # Allow subtraction/division on the mock (complex, so we just mock the result of operations if needed)
        # But the code does (scores - min) / (max - min). 
        # Since we mocked numpy, 'scores' is a MagicMock. 
        # We can just mock the normalization logic logic or ensure it doesn't crash.
        
        # Actually, simpler: Mock numpy zeros_like and the final values
        self.model.model.decision_function.return_value = mock_scores
        
        # Mock _score_to_risk to avoid comparing MagicMock with int
        self.model._score_to_risk = MagicMock(return_value="HIGH")

        test_data = [
            {"protocol": "TCP", "service": "HTTP", "flag": "SF", "src_bytes": 100, "dst_bytes": 200},
            {"protocol": "TCP", "service": "HTTP", "flag": "SF", "src_bytes": 99999, "dst_bytes": 99999}
        ]
        
        with patch('numpy.array'):
             with patch('numpy.zeros_like'):
                predictions = self.model.predict(test_data)
        
        self.assertEqual(len(predictions), 2)
        self.assertEqual(predictions[1]["is_anomaly"], True)

if __name__ == '__main__':
    unittest.main()
