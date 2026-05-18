"""Tests for payment endpoints (fallback mode)."""
import pytest


class TestPaymentsAPI:
    def test_payment_missing_order_id(self, client):
        resp = client.post('/api/payments', json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_payment_invalid_order_id(self, client):
        resp = client.post('/api/payments', json={'order_id': -1})
        assert resp.status_code == 400

    def test_payment_db_unavailable(self, client):
        resp = client.post('/api/payments', json={'order_id': 1})
        assert resp.status_code == 503
        data = resp.get_json()
        assert data['error']['code'] == 'SERVICE_UNAVAILABLE'
