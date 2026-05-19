"""Tests for order endpoints with mocked DB."""
import pytest
from unittest.mock import MagicMock, patch


def _mock_transaction_cm(conn):
    """Helper to mock db_transaction context manager."""
    class _CM:
        def __enter__(self):
            return conn
        def __exit__(self, *args):
            return False
    return _CM()


class TestOrdersWithDB:
    def test_list_orders_from_db(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = {'cnt': 2}
        cur.fetchall.return_value = [
            {'id': 1, 'total_amount': 50.0, 'status': 'confirmed', 'created_at': '2024-01-01', 'updated_at': '2024-01-01', 'status_history': '[{"status":"pending"},{"status":"confirmed"}]'},
            {'id': 2, 'total_amount': 30.0, 'status': 'pending', 'created_at': '2024-01-02', 'updated_at': '2024-01-02', 'status_history': '[{"status":"pending"}]'},
        ]

        with patch('routes.orders.get_db_connection', return_value=conn):
            resp = client.get('/api/orders?session_id=sess_orders')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 2
        assert len(data['orders']) == 2

    def test_create_order_success(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        # fetchone calls: cart_id, then order_id after INSERT
        cur.fetchone.side_effect = [
            [1],        # cart id
            [42],       # RETURNING order_id
        ]
        # fetchall call: items in cart
        cur.fetchall.return_value = [
            [1, 2, 25.0, 'Book A', 'Author A', 10],  # book_id, qty, price, title, author, stock
        ]

        with patch('routes.orders.db_transaction', return_value=_mock_transaction_cm(conn)):
            resp = client.post('/api/orders', json={
                'session_id': 'sess_create',
                'payment_method': 'mock'
            })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'created'
        assert data['order_id'] == 42

    def test_create_order_empty_cart(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = None  # no cart

        with patch('routes.orders.db_transaction', return_value=_mock_transaction_cm(conn)):
            resp = client.post('/api/orders', json={
                'session_id': 'sess_empty',
                'payment_method': 'mock'
            })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'empty' in data['error']

    def test_create_order_insufficient_stock(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = [1]  # cart id
        cur.fetchall.return_value = [
            [1, 10, 25.0, 'Book A', 'Author A', 3],  # requested 10, stock 3
        ]

        with patch('routes.orders.db_transaction', return_value=_mock_transaction_cm(conn)):
            resp = client.post('/api/orders', json={
                'session_id': 'sess_stock',
                'payment_method': 'mock'
            })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'insufficient stock' in data['error']

    def test_get_order_by_id(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.side_effect = [
            {'id': 5, 'session_id': 'sess_1', 'total_amount': 100.0, 'status': 'shipped', 'created_at': '2024-01-01', 'updated_at': '2024-01-01', 'status_history': '[]'},
        ]
        cur.fetchall.return_value = [
            {'book_id': 1, 'quantity': 2, 'price': 50.0, 'title': 'Book', 'author': 'Author'}
        ]

        with patch('routes.orders.get_db_connection', return_value=conn):
            resp = client.get('/api/orders/5')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == 5
        assert data['status'] == 'shipped'
        assert len(data['items']) == 1

    def test_get_order_not_found(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = None

        with patch('routes.orders.get_db_connection', return_value=conn):
            resp = client.get('/api/orders/999')
        assert resp.status_code == 404
