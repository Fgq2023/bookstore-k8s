"""Tests for probe endpoints with mocked DB."""
import pytest
from unittest.mock import MagicMock, patch


class TestProbesWithDB:
    def test_startup_db_connected(self, client):
        conn = MagicMock()
        with patch('routes.probes.get_db_connection', return_value=conn):
            resp = client.get('/startup')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert data['db'] == 'connected'

    def test_healthz_db_connected(self, client):
        conn = MagicMock()
        with patch('routes.probes.get_db_connection', return_value=conn):
            resp = client.get('/healthz')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'healthy'
        assert data['db'] == 'connected'

    def test_ready_db_connected(self, client):
        conn = MagicMock()
        with patch('routes.probes.get_db_connection', return_value=conn):
            resp = client.get('/ready')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ready'
        assert data['dependencies']['database'] is True
