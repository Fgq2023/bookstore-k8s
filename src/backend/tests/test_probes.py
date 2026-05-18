"""Tests for probes and metrics endpoints."""
import pytest


class TestProbes:
    def test_startup(self, client):
        resp = client.get('/startup')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'

    def test_healthz(self, client):
        resp = client.get('/healthz')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'backend'

    def test_ready(self, client):
        resp = client.get('/ready')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'ready' in data['status']


class TestMetrics:
    def test_metrics_endpoint(self, client):
        resp = client.get('/metrics')
        assert resp.status_code == 200
        assert resp.content_type.startswith('text/plain')
        text = resp.data.decode()
        assert 'http_requests_total' in text
        assert 'db_connections_success_total' in text
        assert 'orders_created_total' in text
