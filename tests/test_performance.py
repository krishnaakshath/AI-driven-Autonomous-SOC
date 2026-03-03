"""
Performance Tests — Synthetic Data Replay
==========================================
Measures ingestion throughput and data-load times.
Run with: pytest tests/test_performance.py -v -s
"""
import os
import sys
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIngestionPerformance:
    """Measure event generation + processing throughput."""

    def test_siem_generation_throughput(self):
        """Generate 1000 events and measure time."""
        from services.siem_service import siem_service
        start = time.time()
        events = siem_service.generate_events(count=1000)
        elapsed = time.time() - start
        print(f"\n  SIEM: {len(events)} events in {elapsed:.2f}s ({len(events)/max(elapsed,0.001):.0f} evt/s)")
        assert elapsed < 30, "SIEM generation took > 30s for 1000 events"

    def test_rl_classify_throughput(self):
        """Classify 100 events and measure latency."""
        from ml_engine.rl_threat_classifier import RLThreatClassifier
        agent = RLThreatClassifier()
        event = {"bytes_in": 5000, "bytes_out": 1000, "packets": 50,
                 "duration": 10, "port": 443, "severity": "HIGH"}

        start = time.time()
        for _ in range(100):
            agent.classify(event)
        elapsed = time.time() - start
        avg_ms = (elapsed / 100) * 1000
        print(f"\n  RL classify: 100 calls in {elapsed:.2f}s (avg {avg_ms:.1f}ms)")
        assert avg_ms < 100, "RL inference > 100ms per call"

    def test_firewall_scan_throughput(self):
        """Scan 1000 payloads through WAF patterns."""
        from services.firewall_service import FirewallService
        fw = FirewallService()
        payloads = [
            "SELECT * FROM users", "<script>alert(1)</script>",
            "../../etc/passwd", "normal request", "hello world",
        ] * 200

        start = time.time()
        for p in payloads:
            fw.scan_payload(p)
        elapsed = time.time() - start
        print(f"\n  WAF: {len(payloads)} scans in {elapsed:.2f}s ({len(payloads)/max(elapsed,0.001):.0f} scan/s)")
        assert elapsed < 5, "WAF scanning too slow"
