"""Tests for health/readiness probes."""
import json


class TestProbes:
    """Test /healthz and /ready endpoints."""

    def test_healthz(self, test_server):
        import urllib.request
        resp = urllib.request.urlopen(f"{test_server}/healthz")
        data = json.loads(resp.read())
        assert resp.status == 200
        assert data["status"] == "healthy"
        assert data["service"] == "backend"
        assert data["db"] in ("connected", "disconnected")

    def test_ready(self, test_server):
        import urllib.request
        resp = urllib.request.urlopen(f"{test_server}/ready")
        data = json.loads(resp.read())
        assert resp.status == 200
        assert data["status"] in ("ready", "ready (fallback)")
        assert "dependencies" in data
        assert "database" in data["dependencies"]
