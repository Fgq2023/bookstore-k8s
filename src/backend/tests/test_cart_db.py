"""Tests for cart endpoints with mocked DB."""
import pytest
from unittest.mock import MagicMock, patch


class TestCartWithDB:
    def test_get_cart_with_items(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        # First query: find cart id
        cur.fetchone.return_value = {'id': 5}
        # Second query: cart items
        cur.fetchall.return_value = [
            {'id': 1, 'book_id': 10, 'quantity': 2, 'title': 'Go Book', 'author': 'Gopher', 'price': 30.0}
        ]

        with patch('routes.cart.get_db_connection', return_value=conn):
            resp = client.get('/api/cart?session_id=sess_123')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['session_id'] == 'sess_123'
        assert len(data['items']) == 1
        assert data['items'][0]['title'] == 'Go Book'
        assert data['total'] == 60.0

    def test_get_empty_cart(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = None  # No cart found

        with patch('routes.cart.get_db_connection', return_value=conn):
            resp = client.get('/api/cart?session_id=sess_empty')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['items'] == []
        assert data['total'] == 0

    def test_add_to_cart_existing(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = [3]  # existing cart id

        with patch('routes.cart.get_db_connection', return_value=conn):
            resp = client.post('/api/cart', json={
                'session_id': 'sess_add',
                'book_id': '5',
                'quantity': 1
            })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'added'
        assert data['book_id'] == '5'

    def test_add_to_cart_new(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        # First SELECT returns None (no cart), then INSERT returns new cart id
        cur.fetchone.side_effect = [None, [7]]

        with patch('routes.cart.get_db_connection', return_value=conn):
            resp = client.post('/api/cart', json={
                'session_id': 'sess_new',
                'book_id': '8',
                'quantity': 3
            })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'added'
        assert data['quantity'] == 3

    def test_update_cart_item(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur

        with patch('routes.cart.get_db_connection', return_value=conn):
            resp = client.put('/api/cart/item/1', json={
                'session_id': 'sess_upd',
                'quantity': 5
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'updated'
        assert data['quantity'] == 5

    def test_delete_cart_item(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur

        with patch('routes.cart.get_db_connection', return_value=conn):
            resp = client.delete('/api/cart/item/1?session_id=sess_del')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'deleted'
