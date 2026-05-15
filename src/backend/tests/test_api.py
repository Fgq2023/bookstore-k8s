"""Tests for core API endpoints (fallback mode)."""
import json
import pytest


class TestBooksAPI:
    """Test /api/books endpoints."""

    def test_list_books(self, test_server):
        import urllib.request
        resp = urllib.request.urlopen(f"{test_server}/api/books")
        data = json.loads(resp.read())
        assert resp.status == 200
        assert data["count"] == 5
        assert len(data["books"]) == 5
        assert data["books"][0]["title"] == "Cloud Native Patterns"

    def test_get_book_by_id(self, test_server):
        import urllib.request
        resp = urllib.request.urlopen(f"{test_server}/api/books/2")
        data = json.loads(resp.read())
        assert resp.status == 200
        assert data["id"] == "2"
        assert data["title"] == "Kubernetes in Action"

    def test_get_book_not_found(self, test_server):
        import urllib.request
        import urllib.error
        try:
            urllib.request.urlopen(f"{test_server}/api/books/999")
            assert False, "Should have raised 404"
        except urllib.error.HTTPError as e:
            assert e.code == 404

    def test_search_books(self, test_server):
        import urllib.request
        resp = urllib.request.urlopen(f"{test_server}/api/books/search?q=Kubernetes")
        data = json.loads(resp.read())
        assert resp.status == 200
        assert data["count"] >= 1
        assert any("Kubernetes" in b["title"] for b in data["books"])


class TestCartAPI:
    """Test /api/cart endpoints."""

    def test_add_to_cart(self, test_server):
        import urllib.request
        req = urllib.request.Request(
            f"{test_server}/api/cart",
            data=json.dumps({"session_id": "test-session-1", "book_id": "1", "quantity": 2}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert resp.status in (200, 201)
        assert data["status"] == "added"
        assert data["book_id"] == "1"

    def test_view_cart(self, test_server):
        import urllib.request
        # Add item first
        req = urllib.request.Request(
            f"{test_server}/api/cart",
            data=json.dumps({"session_id": "test-session-2", "book_id": "3", "quantity": 1}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req)
        # View cart
        resp = urllib.request.urlopen(f"{test_server}/api/cart?session_id=test-session-2")
        data = json.loads(resp.read())
        assert resp.status == 200
        assert len(data["items"]) == 1
        assert data["items"][0]["book_id"] == "3"

    def test_update_cart_item(self, test_server):
        import urllib.request
        # Add item
        req = urllib.request.Request(
            f"{test_server}/api/cart",
            data=json.dumps({"session_id": "test-session-3", "book_id": "1", "quantity": 1}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req)
        # View to get item id
        resp = urllib.request.urlopen(f"{test_server}/api/cart?session_id=test-session-3")
        cart = json.loads(resp.read())
        item_id = cart["items"][0]["id"]
        # Update quantity
        req = urllib.request.Request(
            f"{test_server}/api/cart/item/{item_id}",
            data=json.dumps({"session_id": "test-session-3", "quantity": 5}).encode(),
            headers={"Content-Type": "application/json"},
            method="PUT"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert resp.status in (200, 201)
        assert data["status"] == "updated"

    def test_delete_cart_item(self, test_server):
        import urllib.request
        # Add item
        req = urllib.request.Request(
            f"{test_server}/api/cart",
            data=json.dumps({"session_id": "test-session-4", "book_id": "2", "quantity": 1}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req)
        # View to get item id
        resp = urllib.request.urlopen(f"{test_server}/api/cart?session_id=test-session-4")
        cart = json.loads(resp.read())
        item_id = cart["items"][0]["id"]
        # Delete
        req = urllib.request.Request(
            f"{test_server}/api/cart/item/{item_id}?session_id=test-session-4",
            method="DELETE"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert resp.status in (200, 201)
        assert data["status"] == "deleted"


class TestOrdersAPI:
    """Test /api/orders endpoints."""

    def test_create_order(self, test_server):
        import urllib.request
        # Add to cart
        req = urllib.request.Request(
            f"{test_server}/api/cart",
            data=json.dumps({"session_id": "test-session-5", "book_id": "1", "quantity": 2}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req)
        # Place order
        req = urllib.request.Request(
            f"{test_server}/api/orders",
            data=json.dumps({"session_id": "test-session-5"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        assert resp.status in (200, 201)
        assert data["status"] == "created"
        assert "order_id" in data or "id" in data
        assert data["total"] > 0

    def test_list_orders(self, test_server):
        import urllib.request
        # Add to cart and order
        req = urllib.request.Request(
            f"{test_server}/api/cart",
            data=json.dumps({"session_id": "test-session-6", "book_id": "4", "quantity": 1}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req)
        req = urllib.request.Request(
            f"{test_server}/api/orders",
            data=json.dumps({"session_id": "test-session-6"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req)
        # List orders
        resp = urllib.request.urlopen(f"{test_server}/api/orders?session_id=test-session-6")
        data = json.loads(resp.read())
        assert resp.status == 200
        assert len(data["orders"]) >= 1

    def test_get_order_by_id(self, test_server):
        import urllib.request
        # Add to cart and order
        req = urllib.request.Request(
            f"{test_server}/api/cart",
            data=json.dumps({"session_id": "test-session-7", "book_id": "5", "quantity": 1}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req)
        req = urllib.request.Request(
            f"{test_server}/api/orders",
            data=json.dumps({"session_id": "test-session-7"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        order = json.loads(resp.read())
        order_id = order["order_id"]
        # Get order details
        resp = urllib.request.urlopen(f"{test_server}/api/orders/{order_id}")
        data = json.loads(resp.read())
        assert resp.status == 200
        assert data.get("order_id", data.get("id")) == order_id
