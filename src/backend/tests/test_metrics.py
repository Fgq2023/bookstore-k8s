"""Tests for Prometheus /metrics endpoint."""


class TestMetrics:
    """Test /metrics endpoint returns Prometheus-style text."""

    def test_metrics_status(self, test_server):
        import urllib.request
        resp = urllib.request.urlopen(f"{test_server}/metrics")
        assert resp.status == 200
        body = resp.read().decode()
        assert "http_requests_total" in body
        assert "db_connections_success_total" in body
        assert "db_connections_failed_total" in body

    def test_metrics_counters_increase(self, test_server):
        import urllib.request
        # Trigger a request first
        urllib.request.urlopen(f"{test_server}/api/books")
        # Check metrics
        resp = urllib.request.urlopen(f"{test_server}/metrics")
        body = resp.read().decode()
        assert "http_requests_total" in body
        assert "method=\"GET\"" in body
        assert "/api/books\"" in body
