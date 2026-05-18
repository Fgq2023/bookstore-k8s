"""Tests for book endpoints with mocked DB."""
import pytest
from unittest.mock import MagicMock, patch


class TestBooksWithDB:
    def test_list_books_from_db(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        # COUNT query
        cur.fetchone.side_effect = [
            {'cnt': 3},           # COUNT
            {'id': 1, 'title': 'DB Book 1', 'author': 'A1', 'isbn': '111', 'price': 10.0, 'stock_quantity': 5, 'created_at': '2024-01-01', 'updated_at': '2024-01-01'},
            {'id': 2, 'title': 'DB Book 2', 'author': 'A2', 'isbn': '222', 'price': 20.0, 'stock_quantity': 3, 'created_at': '2024-01-01', 'updated_at': '2024-01-01'},
            {'id': 3, 'title': 'DB Book 3', 'author': 'A3', 'isbn': '333', 'price': 30.0, 'stock_quantity': 1, 'created_at': '2024-01-01', 'updated_at': '2024-01-01'},
        ]
        cur.fetchall.return_value = [
            {'id': 1, 'title': 'DB Book 1', 'author': 'A1', 'isbn': '111', 'price': 10.0, 'stock_quantity': 5, 'created_at': '2024-01-01', 'updated_at': '2024-01-01'},
            {'id': 2, 'title': 'DB Book 2', 'author': 'A2', 'isbn': '222', 'price': 20.0, 'stock_quantity': 3, 'created_at': '2024-01-01', 'updated_at': '2024-01-01'},
            {'id': 3, 'title': 'DB Book 3', 'author': 'A3', 'isbn': '333', 'price': 30.0, 'stock_quantity': 1, 'created_at': '2024-01-01', 'updated_at': '2024-01-01'},
        ]

        with patch('routes.books.get_db_connection', return_value=conn):
            resp = client.get('/api/books')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 3
        assert data['count'] == 3
        assert data['books'][0]['title'] == 'DB Book 1'

    def test_get_book_by_id_from_db(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = {'id': '42', 'title': 'Mocked Book', 'author': 'Author', 'price': 15.0}

        with patch('routes.books.get_db_connection', return_value=conn):
            resp = client.get('/api/books/42')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['title'] == 'Mocked Book'

    def test_get_book_not_found_in_db(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = None

        with patch('routes.books.get_db_connection', return_value=conn):
            resp = client.get('/api/books/99')
        assert resp.status_code == 404

    def test_search_books_from_db(self, client):
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchall.return_value = [
            {'id': 1, 'title': 'Kubernetes Guide', 'author': 'K8s Author', 'price': 25.0}
        ]

        with patch('routes.books.get_db_connection', return_value=conn):
            resp = client.get('/api/books/search?q=kubernetes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] == 1
        assert data['books'][0]['title'] == 'Kubernetes Guide'

    def test_list_books_pagination_from_db(self, client):
        from utils.cache import _cache
        _cache.clear()  # avoid cache collision with previous tests
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        cur.fetchone.return_value = {'cnt': 100}
        cur.fetchall.return_value = [
            {'id': i, 'title': f'Book {i}', 'author': 'A', 'isbn': str(i), 'price': 10.0, 'stock_quantity': 1, 'created_at': '2024-01-01', 'updated_at': '2024-01-01'}
            for i in range(1, 21)
        ]

        with patch('routes.books.get_db_connection', return_value=conn):
            resp = client.get('/api/books?page=2&per_page=20')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['page'] == 2
        assert data['per_page'] == 20
        assert data['count'] == 20
        assert data['total'] == 100
