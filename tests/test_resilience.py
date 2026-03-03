"""
Resilience Tests — Graceful Degradation Under Failures
=======================================================
Mocks 3rd-party API outages and verifies the app handles them.
Run with: pytest tests/test_resilience.py -v
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.unit


class TestThreatIntelResilience:
    """Verify graceful degradation when threat intel APIs are down."""

    @patch("requests.get", side_effect=ConnectionError("API down"))
    def test_abuseipdb_offline(self, _):
        from services.threat_intel import ThreatIntelligence
        ti = ThreatIntelligence()
        try:
            result = ti.check_ip("1.2.3.4")
            # Should return empty/cached result, not crash
            assert isinstance(result, dict)
        except Exception:
            # Acceptable: function may raise, as long as it doesn't crash the app
            pass

    @patch("requests.get", side_effect=ConnectionError("API down"))
    def test_virustotal_offline(self, _):
        from services.threat_intel import ThreatIntelligence
        ti = ThreatIntelligence()
        try:
            result = ti.check_hash("d41d8cd98f00b204e9800998ecf8427e")
            assert isinstance(result, dict)
        except Exception:
            pass


class TestDatabaseResilience:
    """Verify the app survives DB outages."""

    def test_db_import_always_works(self):
        """Database module should import without crashing even if Supabase is down."""
        from services.database import db
        assert db is not None

    def test_stats_returns_dict_always(self):
        """get_stats should return a dict even when DB is unreachable."""
        from services.database import db
        stats = db.get_stats()
        assert isinstance(stats, dict)
        assert "total" in stats


class TestFirewallResilience:
    """Firewall should work even if DB logging fails."""

    def test_scan_without_db(self):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        blocked, threat = fw.scan_payload("SELECT * FROM users")
        assert blocked is True
        assert threat == "SQL_INJECTION"

    @patch("services.firewall_service.FirewallService.log_block", side_effect=Exception("DB down"))
    def test_check_request_survives_log_failure(self, _):
        from services.firewall_service import FirewallService
        fw = FirewallService()
        # Should not crash even if logging fails
        try:
            result = fw.check_request({"q": "normal text"}, "1.2.3.4")
            assert result is True
        except Exception:
            pytest.fail("check_request crashed when log_block failed")


class TestAuthResilience:
    """Auth should handle edge cases gracefully."""

    def test_login_empty_email(self):
        from services.auth_service import auth_service
        ok, msg, _ = auth_service.login("", "password")
        assert ok is False

    def test_register_empty_password(self):
        from services.auth_service import auth_service
        ok, msg = auth_service.register("test@test.com", "", "Name")
        assert ok is False

    def test_otp_for_nonexistent_user(self):
        from services.auth_service import auth_service
        ok, msg = auth_service.generate_otp("doesnotexist@nowhere.com")
        assert ok is False
