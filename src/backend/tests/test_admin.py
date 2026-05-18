"""Tests for admin endpoints (fallback mode)."""
import pytest
from utils.auth import generate_token


class TestAdminAPI:
    def test_admin_update_no_auth(self, client):
        resp = client.put('/api/admin/orders/1/status', json={'status': 'shipped'})
        assert resp.status_code == 401

    def test_admin_update_non_admin(self, client):
        token = generate_token(1, 'regular_user', is_admin=False)
        resp = client.put('/api/admin/orders/1/status', json={'status': 'shipped'},
                          headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 403
        data = resp.get_json()
        assert data['error']['code'] == 'FORBIDDEN'

    def test_admin_update_invalid_status(self, client):
        token = generate_token(1, 'admin', is_admin=True)
        resp = client.put('/api/admin/orders/1/status', json={'status': 'invalid_status'},
                          headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_admin_update_db_unavailable(self, client):
        token = generate_token(1, 'admin', is_admin=True)
        resp = client.put('/api/admin/orders/1/status', json={'status': 'shipped'},
                          headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 503
        data = resp.get_json()
        assert data['error']['code'] == 'SERVICE_UNAVAILABLE'
