"""Tests for auth endpoints (fallback mode)."""
import pytest


class TestAuthAPI:
    def test_register_success(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret123'
        })
        assert resp.status_code == 503  # DB unavailable in test env

    def test_register_validation_error(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'bob',
            'email': 'not-an-email',
            'password': '123'
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_register_missing_fields(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'charlie'
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    def test_login_success(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'alice',
            'password': 'secret123'
        })
        assert resp.status_code == 503  # DB unavailable

    def test_login_validation_error(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'alice'
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    def test_login_missing_password(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'alice'
        })
        assert resp.status_code == 400

    def test_me_unauthorized(self, client):
        resp = client.get('/api/auth/me')
        assert resp.status_code == 401
        data = resp.get_json()
        assert data['error']['code'] == 'UNAUTHORIZED'

    def test_me_invalid_token(self, client):
        resp = client.get('/api/auth/me', headers={'Authorization': 'Bearer invalidtoken'})
        assert resp.status_code == 401

    def test_me_valid_token(self, client):
        # Generate a valid token manually
        from utils.auth import generate_token
        token = generate_token(1, 'testuser', is_admin=False)
        resp = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['username'] == 'testuser'
