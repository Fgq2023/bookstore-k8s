"""Tests for cart endpoints (fallback mode)."""
import pytest


class TestCartAPI:
    def test_view_empty_cart(self, client):
        resp = client.get('/api/cart?session_id=test-session-1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['session_id'] == 'test-session-1'
        assert data['items'] == []

    def test_view_cart_missing_session(self, client):
        resp = client.get('/api/cart')
        assert resp.status_code == 400

    def test_add_to_cart(self, client):
        resp = client.post('/api/cart', json={
            'session_id': 'test-session-2',
            'book_id': '2',
            'quantity': 2
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'added'
        assert data['book_id'] == '2'
        assert data['quantity'] == 2

    def test_add_to_cart_invalid_quantity(self, client):
        resp = client.post('/api/cart', json={
            'session_id': 'test-session-3',
            'book_id': '1',
            'quantity': -1
        })
        assert resp.status_code == 400

    def test_add_to_cart_missing_session(self, client):
        resp = client.post('/api/cart', json={
            'book_id': '1',
            'quantity': 1
        })
        assert resp.status_code == 400

    def test_view_cart_with_items(self, client):
        client.post('/api/cart', json={
            'session_id': 'test-session-4',
            'book_id': '3',
            'quantity': 1
        })
        resp = client.get('/api/cart?session_id=test-session-4')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['items']) == 1
        assert data['items'][0]['book_id'] == '3'
        assert data['total'] > 0

    def test_update_cart_item(self, client):
        client.post('/api/cart', json={
            'session_id': 'test-session-5',
            'book_id': '1',
            'quantity': 2
        })
        resp = client.put('/api/cart/item/1', json={
            'session_id': 'test-session-5',
            'quantity': 5
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'updated'
        assert data['quantity'] == 5

    def test_update_cart_item_zero_quantity(self, client):
        client.post('/api/cart', json={
            'session_id': 'test-session-6',
            'book_id': '1',
            'quantity': 2
        })
        resp = client.put('/api/cart/item/1', json={
            'session_id': 'test-session-6',
            'quantity': 0
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'updated'

    def test_delete_cart_item(self, client):
        client.post('/api/cart', json={
            'session_id': 'test-session-7',
            'book_id': '1',
            'quantity': 1
        })
        resp = client.delete('/api/cart/item/1?session_id=test-session-7')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'deleted'

    def test_delete_cart_item_not_found(self, client):
        resp = client.delete('/api/cart/item/999?session_id=test-session-8')
        assert resp.status_code == 404
