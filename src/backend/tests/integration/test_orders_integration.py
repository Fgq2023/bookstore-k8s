"""Integration tests for orders using a real PostgreSQL database via testcontainers."""

import pytest


@pytest.mark.integration
class TestOrdersIntegration:
    def test_create_order_deducts_stock(self, real_db_client):
        """Verify that creating an order atomically deducts stock."""
        client = real_db_client
        session_id = "stock_test_session"

        # Read initial stock
        resp = client.get('/api/books/1')
        assert resp.status_code == 200
        initial_stock = resp.get_json()['stock_quantity']

        # Add book to cart
        resp = client.post('/api/cart', json={
            'session_id': session_id,
            'book_id': '1',
            'quantity': 5
        })
        assert resp.status_code == 201

        # Create order
        resp = client.post('/api/orders', json={
            'session_id': session_id,
            'payment_method': 'mock'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'created'
        order_id = data['order_id']

        # Verify order is confirmed
        resp = client.get(f'/api/orders/{order_id}')
        assert resp.status_code == 200
        order = resp.get_json()
        assert order['status'] == 'confirmed'

        # Verify stock was deducted by 5
        resp = client.get('/api/books/1')
        assert resp.status_code == 200
        book = resp.get_json()
        assert book['stock_quantity'] == initial_stock - 5

    def test_insufficient_stock_blocks_order(self, real_db_client):
        """Verify order is rejected when stock is insufficient."""
        client = real_db_client
        session_id = "no_stock_session"

        # Use book 5 which still has full stock (100)
        resp = client.post('/api/cart', json={
            'session_id': session_id,
            'book_id': '5',
            'quantity': 200
        })
        assert resp.status_code == 201

        # Try to create order
        resp = client.post('/api/orders', json={
            'session_id': session_id,
            'payment_method': 'mock'
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'insufficient stock' in data['error']

        # Verify stock unchanged
        resp = client.get('/api/books/5')
        assert resp.status_code == 200
        book = resp.get_json()
        assert book['stock_quantity'] == 100

    def test_payment_transitions_to_shipped(self, real_db_client):
        """Verify payment transitions order from confirmed to shipped."""
        client = real_db_client
        session_id = "pay_test_session"

        # Add and order
        client.post('/api/cart', json={
            'session_id': session_id,
            'book_id': '2',
            'quantity': 1
        })
        resp = client.post('/api/orders', json={
            'session_id': session_id,
            'payment_method': 'mock'
        })
        order_id = resp.get_json()['order_id']

        # Pay
        resp = client.post('/api/payments', json={'order_id': order_id})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['order_status'] == 'shipped'

        # Verify DB state
        resp = client.get(f'/api/orders/{order_id}')
        assert resp.get_json()['status'] == 'shipped'

    def test_order_status_history_persisted(self, real_db_client):
        """Verify status_history JSONB is populated correctly."""
        client = real_db_client
        session_id = "history_test_session"

        client.post('/api/cart', json={
            'session_id': session_id,
            'book_id': '3',
            'quantity': 1
        })
        resp = client.post('/api/orders', json={
            'session_id': session_id,
            'payment_method': 'mock'
        })
        order_id = resp.get_json()['order_id']

        resp = client.get(f'/api/orders/{order_id}')
        order = resp.get_json()
        history = order['status_history']
        assert len(history) >= 2
        assert history[0]['status'] == 'pending'
        assert history[1]['status'] == 'confirmed'

    def test_cart_emptied_after_order(self, real_db_client):
        """Verify cart items are removed after successful order creation."""
        client = real_db_client
        session_id = "empty_cart_session"

        client.post('/api/cart', json={
            'session_id': session_id,
            'book_id': '4',
            'quantity': 2
        })
        resp = client.post('/api/orders', json={
            'session_id': session_id,
            'payment_method': 'mock'
        })
        assert resp.status_code == 201

        resp = client.get('/api/cart', query_string={'session_id': session_id})
        assert resp.status_code == 200
        cart = resp.get_json()
        assert cart['items'] == []
        assert cart['total'] == 0

    def test_order_list_pagination_with_real_data(self, real_db_client):
        """Verify order list pagination works with real DB queries."""
        client = real_db_client
        session_id = "pagination_session"

        # Create 3 orders
        for i, book_id in enumerate(['1', '2', '3']):
            client.post('/api/cart', json={
                'session_id': session_id,
                'book_id': book_id,
                'quantity': 1
            })
            resp = client.post('/api/orders', json={
                'session_id': session_id,
                'payment_method': 'mock'
            })
            assert resp.status_code == 201

        # List orders with pagination
        resp = client.get('/api/orders', query_string={
            'session_id': session_id,
            'page': 1,
            'per_page': 2
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 3
        assert data['count'] == 2
        assert data['page'] == 1

        # Second page
        resp = client.get('/api/orders', query_string={
            'session_id': session_id,
            'page': 2,
            'per_page': 2
        })
        data = resp.get_json()
        assert data['count'] == 1
        assert data['page'] == 2
