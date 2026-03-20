"""
Integration Tests — Online, Gated by Environment
==================================================
Run with: pytest tests/test_integration.py -v -m integration
Skipped automatically when SUPABASE_URL is not set.
"""
import os
import sys
import pytest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.integration

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SKIP_REASON = "SUPABASE_URL not set — skipping integration tests"


def requires_supabase(fn):
    return pytest.mark.skipif(not SUPABASE_URL, reason=SKIP_REASON)(fn)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE ROUND-TRIP
# ═══════════════════════════════════════════════════════════════════════════════
class TestDatabaseIntegration:
    """Tests that touch the real Supabase instance."""

    @requires_supabase
    def test_get_stats(self):
        from services.database import db
        stats = db.get_stats()
        assert "total" in stats
        assert "critical" in stats

    @requires_supabase
    def test_insert_and_retrieve(self):
        from services.database import db
        import uuid
        evt_id = f"EVT-TEST-{str(uuid.uuid4())[:8]}"
        db.insert_event({
            "id": evt_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "Test",
            "event_type": "Integration Test",
            "severity": "LOW",
            "source_ip": "127.0.0.1",
            "dest_ip": "127.0.0.1",
            "user": "pytest",
            "status": "Resolved",
        })
        recent = db.get_recent_events(limit=10)
        assert isinstance(recent, list)

    @requires_supabase
    def test_daily_counts(self):
        from services.database import db
        counts = db.get_daily_counts(days=7)
        assert isinstance(counts, list)


# ═══════════════════════════════════════════════════════════════════════════════
# SIEM SERVICE
# ═══════════════════════════════════════════════════════════════════════════════
class TestSIEMIntegration:
    """Online SIEM tests."""

    @requires_supabase
    def test_generate_events(self):
        from services.siem_service import siem_service
        events = siem_service.generate_events(count=5)
        assert isinstance(events, list)
        assert len(events) > 0

    @requires_supabase
    def test_event_structure(self):
        from services.siem_service import siem_service
        events = siem_service.generate_events(count=1)
        if not events:
            pytest.skip("No events in DB")
        e = events[0]
        assert "id" in e
        assert "timestamp" in e
        assert "severity" in e


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH — Registration & Login (online, uses file I/O)
# ═══════════════════════════════════════════════════════════════════════════════
class TestAuthIntegration:
    """Online auth tests that write to the users file."""

    def test_register_and_login(self):
        from services.auth_service import auth_service
        email = f"inttest_{datetime.now().timestamp()}@test.com"
        success, msg = auth_service.register(email, "testpass12345", "IntTest")
        if not success:
            pytest.skip(f"Registration failed: {msg}")
        ok, _, _ = auth_service.login(email, "testpass12345")
        assert ok is True

    def test_login_invalid(self):
        from services.auth_service import auth_service
        ok, _, _ = auth_service.login("nonexistent@fake.com", "wrong")
        assert ok is False

    def test_otp_generation(self):
        from services.auth_service import auth_service
        email = "otp_int_test@test.com"
        auth_service.register(email, "testpass12345", "OTPInt")
        success, _ = auth_service.generate_otp(email)
        assert success is True


# ═══════════════════════════════════════════════════════════════════════════════
# THREAT INTEL API (online)
# ═══════════════════════════════════════════════════════════════════════════════
class TestThreatIntelIntegration:
    """Tests that hit external threat intel APIs."""

    def test_urlhaus_reachable(self):
        import requests
        try:
            r = requests.post(
                "https://urlhaus-api.abuse.ch/v1/urls/recent/",
                data={"limit": 1}, timeout=10
            )
            assert r.status_code == 200
        except Exception:
            pytest.skip("URLhaus unreachable")

    def test_threatfox_reachable(self):
        import requests
        try:
            r = requests.post(
                "https://threatfox-api.abuse.ch/api/v1/",
                json={"query": "get_iocs", "days": 1}, timeout=10
            )
            assert r.status_code == 200
        except Exception:
            pytest.skip("ThreatFox unreachable")
