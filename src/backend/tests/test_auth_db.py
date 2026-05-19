"""Tests for auth endpoints with mocked DB."""
import pytest
from unittest.mock import MagicMock, patch


class TestAuthWithDB:
    def test_register_success(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = [42]  # RETURNING id

        with patch('routes.auth.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/register', json={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'Secret123!'
            })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['user_id'] == 42
        assert data['data']['username'] == 'newuser'
        assert 'token' in data['data']

    def test_register_duplicate_username(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.execute.side_effect = Exception('duplicate key')

        with patch('routes.auth.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/register', json={
                'username': 'existing',
                'email': 'ex@example.com',
                'password': 'Secret123!'
            })
        assert resp.status_code == 409
        data = resp.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'CONFLICT'

    def test_login_success(self, client):
        from werkzeug.security import generate_password_hash
        pw_hash = generate_password_hash('mypassword')
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = {
            'id': 7,
            'username': 'alice',
            'password_hash': pw_hash,
            'is_admin': False
        }

        with patch('routes.auth.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/login', json={
                'username': 'alice',
                'password': 'mypassword'
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['user_id'] == 7
        assert data['data']['is_admin'] is False
        assert 'token' in data['data']

    def test_login_invalid_credentials(self, client):
        from werkzeug.security import generate_password_hash
        pw_hash = generate_password_hash('realpassword')
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = {
            'id': 7,
            'username': 'alice',
            'password_hash': pw_hash,
            'is_admin': False
        }

        with patch('routes.auth.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/login', json={
                'username': 'alice',
                'password': 'wrongpassword'
            })
        assert resp.status_code == 401
        data = resp.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'UNAUTHORIZED'

    def test_login_user_not_found(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = None

        with patch('routes.auth.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/login', json={
                'username': 'ghost',
                'password': 'anypassword'
            })
        assert resp.status_code == 401
