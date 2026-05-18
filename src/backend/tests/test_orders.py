"""Tests for order endpoints (fallback mode)."""
import pytest


class TestOrdersAPI:
    def test_list_orders(self, client):
        resp = client.get('/api/orders?session_id=order-session-1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['session_id'] == 'order-session-1'
        assert data['count'] == 0

    def test_list_orders_pagination(self, client):
        resp = client.get('/api/orders?session_id=order-session-2&page=1&per_page=10')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['per_page'] == 10

    def test_list_orders_missing_session(self, client):
        resp = client.get('/api/orders')
        assert resp.status_code == 400

    def test_create_order_empty_cart(self, client):
        resp = client.post('/api/orders', json={
            'session_id': 'order-session-3'
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'cart is empty' in data['error']

    def test_create_order_and_get(self, client):
        # Add item to cart
        client.post('/api/cart', json={
            'session_id': 'order-session-4',
            'book_id': '2',
            'quantity': 1
        })
        # Create order
        resp = client.post('/api/orders', json={
            'session_id': 'order-session-4'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'created'
        order_id = data['order_id']

        # Get order
        resp = client.get(f'/api/orders/{order_id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == order_id
        assert data['status'] == 'confirmed'

    def test_get_order_not_found(self, client):
        resp = client.get('/api/orders/99999')
        assert resp.status_code == 404

    def test_create_order_missing_session(self, client):
        resp = client.post('/api/orders', json={})
        assert resp.status_code == 400
