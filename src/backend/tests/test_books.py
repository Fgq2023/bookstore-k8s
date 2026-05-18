"""Tests for book endpoints (fallback mode)."""
import pytest


class TestBooksAPI:
    def test_list_books(self, client):
        resp = client.get('/api/books')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] == 5
        assert len(data['books']) == 5
        assert data['books'][0]['title'] == 'Cloud Native Patterns'

    def test_list_books_pagination(self, client):
        resp = client.get('/api/books?page=1&per_page=2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] == 5
        assert data['page'] == 1
        assert data['per_page'] == 2

    def test_list_books_invalid_page(self, client):
        resp = client.get('/api/books?page=-1')
        assert resp.status_code == 400

    def test_get_book_by_id(self, client):
        resp = client.get('/api/books/2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == '2'
        assert data['title'] == 'Kubernetes in Action'

    def test_get_book_not_found(self, client):
        resp = client.get('/api/books/999')
        assert resp.status_code == 404

    def test_search_books(self, client):
        resp = client.get('/api/books/search?q=Kubernetes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] >= 1

    def test_search_books_missing_q(self, client):
        resp = client.get('/api/books/search')
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'missing' in data['error']

    def test_search_books_no_results(self, client):
        resp = client.get('/api/books/search?q=xyznonexistent')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] == 0
