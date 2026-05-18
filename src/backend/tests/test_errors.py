"""Tests for error handlers and edge cases."""
import pytest


class TestErrorHandlers:
    def test_404_handler(self, client):
        resp = client.get('/api/nonexistent')
        assert resp.status_code == 404
        data = resp.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'NOT_FOUND'

    def test_cors_headers(self, client):
        resp = client.get('/api/books', headers={'Origin': 'http://localhost:5173'})
        assert resp.status_code == 200
        assert 'Access-Control-Allow-Origin' in resp.headers

    def test_security_headers(self, client):
        resp = client.get('/api/books')
        assert resp.status_code == 200
        assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
        assert resp.headers.get('X-Frame-Options') == 'DENY'
