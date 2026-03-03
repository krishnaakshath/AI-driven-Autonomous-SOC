"""
Unit Tests — Offline / Deterministic
======================================
Run with: pytest tests/test_unit.py -v -m unit
These tests use mocks and never hit external services.
"""
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.unit


# ═══════════════════════════════════════════════════════════════════════════════
# FIREWALL SERVICE — Pattern Matching
# ═══════════════════════════════════════════════════════════════════════════════
class TestFirewallPatterns:
    """Offline tests for firewall_service.py regex engine."""

    def test_import(self):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        assert fw is not None

    def test_sql_injection_detected(self):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        blocked, threat = fw.scan_payload("' OR 1=1 --")
        assert blocked is True
        assert threat == "SQL_INJECTION"

    def test_xss_detected(self):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        blocked, threat = fw.scan_payload("<script>alert('xss')</script>")
        assert blocked is True
        assert threat == "XSS"

    def test_path_traversal_detected(self):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        blocked, threat = fw.scan_payload("../../etc/passwd")
        assert blocked is True
        assert threat == "PATH_TRAVERSAL"

    def test_safe_payload_passes(self):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        blocked, threat = fw.scan_payload("Hello, normal request")
        assert blocked is False
        assert threat is None

    def test_empty_payload_passes(self):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        blocked, threat = fw.scan_payload("")
        assert blocked is False


# ═══════════════════════════════════════════════════════════════════════════════
# FIREWALL SHIM — IP Blocklist (mocked I/O)
# ═══════════════════════════════════════════════════════════════════════════════
class TestFirewallShim:
    """Offline tests for firewall_shim.py using mocked file I/O."""

    @patch("os.makedirs")
    def test_import(self, _):
        from services.firewall_shim import FirewallShim
        fw = FirewallShim()
        assert fw is not None

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    def test_block_ip(self, _, mock_exists, mock_dump, mock_file):
        from services.firewall_shim import FirewallShim
        fw = FirewallShim()
        with patch.object(fw, "_load", return_value=[]):
            success = fw.block_ip("1.2.3.4", "Test")
        assert success is True

    @patch("os.makedirs")
    def test_is_blocked(self, _):
        from services.firewall_shim import FirewallShim
        fw = FirewallShim()
        test_data = [
            {"ip": "10.0.0.1", "status": "Active"},
            {"ip": "10.0.0.2", "status": "Disabled"},
        ]
        with patch.object(fw, "_load", return_value=test_data):
            assert fw.is_blocked("10.0.0.1") is True
            assert fw.is_blocked("10.0.0.2") is False
            assert fw.is_blocked("1.1.1.1") is False

    @patch("os.makedirs")
    def test_unblock_ip(self, _):
        from services.firewall_shim import FirewallShim
        fw = FirewallShim()
        test_data = [{"ip": "1.2.3.4", "status": "Active"}]
        with patch.object(fw, "_load", return_value=test_data):
            with patch.object(fw, "_save") as mock_save:
                result = fw.unblock_ip("1.2.3.4")
                assert result is True
                mock_save.assert_called_once_with([])


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH SERVICE — Password Hashing & Validation
# ═══════════════════════════════════════════════════════════════════════════════
class TestAuthOffline:
    """Offline auth tests — validates hashing logic and input validation."""

    def test_import(self):
        from services.auth_service import AuthService
        assert AuthService is not None

    def test_password_too_short_rejected(self):
        from services.auth_service import auth_service
        success, msg = auth_service.register("short@test.com", "123", "Test")
        assert success is False
        assert "8 characters" in msg

    def test_invalid_email_rejected(self):
        from services.auth_service import auth_service
        success, msg = auth_service.register("notanemail", "validpass123", "Test")
        assert success is False
        assert "email" in msg.lower()

    def test_password_hash_roundtrip(self):
        from services.auth_service import auth_service
        hashed, salt = auth_service._hash_password("securepass123")
        assert hashed is not None
        assert salt is not None
        assert auth_service._verify_password("securepass123", hashed, salt) is True
        assert auth_service._verify_password("wrongpass", hashed, salt) is False


# ═══════════════════════════════════════════════════════════════════════════════
# RL ENGINE — State Extraction & Inference
# ═══════════════════════════════════════════════════════════════════════════════
class TestRLOffline:
    """Offline RL tests — state extraction and classify without DB."""

    def test_state_extraction_shape(self):
        from ml_engine.rl_threat_classifier import RLThreatClassifier
        agent = RLThreatClassifier()
        event = {
            "bytes_in": 1_000_000, "bytes_out": 500_000,
            "packets": 10_000, "duration": 3600,
            "port": 65535, "severity": "CRITICAL",
        }
        state = agent.extract_state(event)
        assert state.shape == (12,)
        assert all(0.0 <= s <= 1.0 for s in state)

    def test_classify_returns_valid_action(self):
        from ml_engine.rl_threat_classifier import RLThreatClassifier
        agent = RLThreatClassifier()
        event = {"id": "T1", "bytes_in": 100, "bytes_out": 50,
                 "packets": 10, "duration": 1, "port": 80, "severity": "LOW"}
        result = agent.classify(event)
        assert result["action"] in ["SAFE", "SUSPICIOUS", "DANGEROUS"]
        assert "confidence" in result
        assert "q_values" in result

    def test_feedback_accepted(self):
        from ml_engine.rl_threat_classifier import RLThreatClassifier
        agent = RLThreatClassifier()
        event = {"id": "T-FB", "bytes_in": 100, "bytes_out": 50,
                 "packets": 10, "duration": 1, "port": 80, "severity": "LOW"}
        result = agent.classify(event)
        accepted = agent.submit_feedback(result["event_id"], correct=True)
        assert accepted is True


# ═══════════════════════════════════════════════════════════════════════════════
# ML PIPELINE — Isolation Forest & Clustering
# ═══════════════════════════════════════════════════════════════════════════════
class TestMLOffline:
    """Offline ML tests."""

    def test_isolation_forest_import(self):
        try:
            from ml_engine.isolation_forest import isolation_forest
            assert isolation_forest is not None
        except ImportError:
            pytest.skip("Isolation forest not available")

    def test_fuzzy_clustering_import(self):
        try:
            from ml_engine.fuzzy_clustering import fuzzy_clustering
            assert fuzzy_clustering is not None
        except ImportError:
            pytest.skip("Fuzzy clustering not available")


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATOR — Import & Structure
# ═══════════════════════════════════════════════════════════════════════════════
class TestReportGeneratorOffline:
    """Offline report generator tests."""

    def test_import(self):
        from services.report_generator import generate_security_report
        assert generate_security_report is not None


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════
class TestInputValidation:
    """Validate sanitization of external inputs."""

    def test_firewall_handles_none(self):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        blocked, _ = fw.scan_payload(None)
        assert blocked is False

    def test_firewall_handles_numeric(self):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        blocked, _ = fw.scan_payload("12345")
        assert blocked is False
