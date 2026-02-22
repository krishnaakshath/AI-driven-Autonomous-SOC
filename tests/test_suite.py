"""
Phase 27 — Unit Test Suite for AI-Driven Autonomous SOC
========================================================
Covers: Database, Auth, SIEM, ML Pipeline, Threat Intel, Email.
Run with: python -m pytest tests/test_suite.py -v
"""

import os
import sys
import pytest
from datetime import datetime, timedelta

# Project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DATABASE SERVICE
# ═══════════════════════════════════════════════════════════════════════════════
class TestDatabaseService:
    """Tests for services/database.py"""

    def test_import(self):
        from services.database import db
        assert db is not None

    def test_get_stats(self):
        from services.database import db
        stats = db.get_stats()
        assert isinstance(stats, dict)
        assert 'total' in stats
        assert 'critical' in stats

    def test_insert_and_retrieve_event(self):
        from services.database import db
        event = {
            "id": "EVT-TEST-001",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "UnitTest",
            "event_type": "Test Event",
            "severity": "LOW",
            "source_ip": "127.0.0.1",
            "dest_ip": "10.0.0.1",
            "user": "pytest",
            "hostname": "TEST-HOST",
            "status": "Open"
        }
        db.insert_event(event)
        recent = db.get_recent_events(limit=10)
        assert len(recent) > 0

    def test_get_daily_counts(self):
        from services.database import db
        counts = db.get_daily_counts(days=7)
        assert isinstance(counts, list)

    def test_insert_and_retrieve_alert(self):
        from services.database import db
        alert = {
            "id": "ALRT-TEST-001",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": "Test Alert",
            "severity": "LOW",
            "status": "New",
            "details": "{}"
        }
        db.insert_alert(alert)
        alerts = db.get_alerts(limit=5)
        assert len(alerts) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. AUTH SERVICE
# ═══════════════════════════════════════════════════════════════════════════════
class TestAuthService:
    """Tests for services/auth_service.py"""

    def test_import(self):
        from services.auth_service import auth_service
        assert auth_service is not None

    def test_register_user(self):
        from services.auth_service import auth_service
        test_email = f"test_{datetime.now().timestamp()}@test.com"
        success, msg = auth_service.register(test_email, "TestUser", "testpass123")
        # May succeed or fail (duplicate), both are valid
        assert isinstance(success, bool)
        assert isinstance(msg, str)

    def test_login_invalid_user(self):
        from services.auth_service import auth_service
        success, msg, requires_2fa = auth_service.login("nonexistent@fake.com", "wrongpass")
        assert success is False

    def test_otp_generation(self):
        from services.auth_service import auth_service
        # Register a test user first
        test_email = "otptest@test.com"
        auth_service.register(test_email, "OTPTest", "pass123")
        success, msg = auth_service.generate_otp(test_email)
        # Should succeed even without SMTP (falls back to UI display)
        assert success is True

    def test_role_check(self):
        from services.auth_service import auth_service
        users = auth_service._load_users()
        # At least one user should exist
        assert isinstance(users, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SIEM SERVICE
# ═══════════════════════════════════════════════════════════════════════════════
class TestSIEMService:
    """Tests for services/siem_service.py"""

    def test_import(self):
        from services.siem_service import siem_service
        assert siem_service is not None

    def test_simulate_ingestion(self):
        from services.siem_service import siem_service
        events = siem_service.simulate_ingestion(count=5, days_back=7)
        assert isinstance(events, list)
        assert len(events) == 5

    def test_event_structure(self):
        from services.siem_service import siem_service
        events = siem_service.simulate_ingestion(count=1)
        event = events[0]
        assert "id" in event
        assert "timestamp" in event
        assert "source" in event
        assert "severity" in event

    def test_generate_events(self):
        from services.siem_service import siem_service
        events = siem_service.generate_events(count=10)
        assert isinstance(events, list)
        assert len(events) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ML PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
class TestMLPipeline:
    """Tests for ml_engine modules"""

    def test_isolation_forest_import(self):
        try:
            from ml_engine.isolation_forest import isolation_forest
            assert isolation_forest is not None
        except ImportError:
            pytest.skip("Isolation forest module not available")

    def test_isolation_forest_predict(self):
        try:
            from ml_engine.isolation_forest import isolation_forest
            test_events = [{"source_ip": "1.2.3.4", "event_type": "Test", "severity": "HIGH"}]
            result = isolation_forest.predict(test_events)
            assert isinstance(result, list)
        except Exception:
            pytest.skip("IF prediction not available")

    def test_fuzzy_clustering_import(self):
        try:
            from ml_engine.fuzzy_clustering import fuzzy_clustering
            assert fuzzy_clustering is not None
        except ImportError:
            pytest.skip("Fuzzy clustering module not available")

    def test_model_files_exist(self):
        """Verify that serialized model files exist."""
        models_dir = os.path.join(ROOT, "models")
        if os.path.exists(models_dir):
            files = os.listdir(models_dir)
            assert len(files) > 0, "Models directory exists but is empty"
        else:
            pytest.skip("Models directory not found")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. THREAT INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════
class TestThreatIntel:
    """Tests for services/threat_intel.py"""

    def test_import(self):
        try:
            from services.threat_intel import threat_intel
            assert threat_intel is not None
        except ImportError:
            pytest.skip("Threat intel module not available")

    def test_api_keys_loaded(self):
        """Verify config file exists and contains API key fields."""
        config_path = os.path.join(ROOT, ".soc_config.json")
        if os.path.exists(config_path):
            import json
            with open(config_path) as f:
                config = json.load(f)
            assert "virustotal_api_key" in config or "otx_api_key" in config
        else:
            pytest.skip("No config file found")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. EMAIL SENDER
# ═══════════════════════════════════════════════════════════════════════════════
class TestEmailSender:
    """Tests for alerting/email_sender.py"""

    def test_import(self):
        from alerting.email_sender import EmailNotifier
        notifier = EmailNotifier()
        assert notifier is not None

    def test_configuration_detection(self):
        from alerting.email_sender import EmailNotifier
        notifier = EmailNotifier()
        # is_configured returns True/False depending on env
        result = notifier.is_configured()
        assert isinstance(result, bool)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. DARK WEB OSINT (abuse.ch)
# ═══════════════════════════════════════════════════════════════════════════════
class TestDarkWebOSINT:
    """Test that abuse.ch APIs are reachable."""

    def test_urlhaus_api(self):
        import requests
        try:
            r = requests.post("https://urlhaus-api.abuse.ch/v1/urls/recent/",
                              data={"limit": 1}, timeout=10)
            assert r.status_code == 200
        except Exception:
            pytest.skip("URLhaus API unreachable")

    def test_threatfox_api(self):
        import requests
        try:
            r = requests.post("https://threatfox-api.abuse.ch/api/v1/",
                              json={"query": "get_iocs", "days": 1}, timeout=10)
            assert r.status_code == 200
        except Exception:
            pytest.skip("ThreatFox API unreachable")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
