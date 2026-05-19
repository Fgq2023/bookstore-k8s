"""End-to-end shopping flow test using Playwright API requests against a live server."""

import pytest


@pytest.mark.e2e
def test_full_shopping_flow(live_server):
    """Complete user journey: register -> login -> browse -> cart -> order -> pay -> verify."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        request = p.request.new_context(base_url=live_server)

        # Use unique username to avoid conflicts across test runs
        import uuid
        unique = str(uuid.uuid4())[:8]
        username = f"e2e_user_{unique}"
        password = "Password123!"
        session_id = f"e2e_session_{unique}"

        # Step 1: Register a new user
        register_resp = request.post("/api/auth/register", data={
            "username": username,
            "email": f"{username}@test.com",
            "password": password
        })
        assert register_resp.ok, f"Register failed: {register_resp.text()}"
        reg_data = register_resp.json()
        assert reg_data["success"] is True
        token = reg_data["data"]["token"]

        # Step 2: Login (and get fresh token)
        login_resp = request.post("/api/auth/login", data={
            "username": username,
            "password": password
        })
        assert login_resp.ok
        login_data = login_resp.json()
        assert login_data["success"] is True
        token = login_data["data"]["token"]

        # Step 3: Browse books
        books_resp = request.get("/api/books")
        assert books_resp.ok
        books_data = books_resp.json()
        assert books_data["count"] > 0
        first_book = books_data["books"][0]
        book_id = first_book["id"]

        # Step 4: Search books
        search_resp = request.get("/api/books/search", params={"q": "Cloud"})
        assert search_resp.ok
        search_data = search_resp.json()
        assert search_data["count"] >= 1

        # Step 5: Add to cart
        cart_resp = request.post("/api/cart", data={
            "session_id": session_id,
            "book_id": str(book_id),
            "quantity": 2
        })
        assert cart_resp.ok
        cart_data = cart_resp.json()
        assert cart_data["status"] == "added"

        # Step 6: View cart
        view_cart_resp = request.get("/api/cart", params={"session_id": session_id})
        assert view_cart_resp.ok
        view_cart_data = view_cart_resp.json()
        assert len(view_cart_data["items"]) == 1
        assert view_cart_data["items"][0]["quantity"] == 2

        # Step 7: Place order
        order_resp = request.post("/api/orders", data={
            "session_id": session_id,
            "payment_method": "mock"
        })
        assert order_resp.ok
        order_data = order_resp.json()
        assert order_data["status"] == "created"
        order_id = order_data["order_id"]

        # Step 8: Get order details
        order_detail_resp = request.get(f"/api/orders/{order_id}")
        assert order_detail_resp.ok
        order_detail = order_detail_resp.json()
        assert order_detail["status"] == "confirmed"
        assert len(order_detail["items"]) == 1

        # Step 9: Pay for order
        pay_resp = request.post("/api/payments", data={"order_id": order_id})
        assert pay_resp.ok
        pay_data = pay_resp.json()
        assert pay_data["success"] is True
        assert pay_data["data"]["order_status"] == "shipped"
        assert pay_data["data"]["payment_status"] == "paid"

        # Step 10: Verify order status updated
        final_order_resp = request.get(f"/api/orders/{order_id}")
        assert final_order_resp.ok
        final_order = final_order_resp.json()
        assert final_order["status"] == "shipped"

        # Step 11: List orders
        orders_list_resp = request.get("/api/orders", params={
            "session_id": session_id
        })
        assert orders_list_resp.ok
        orders_list = orders_list_resp.json()
        assert orders_list["total"] == 1

        # Step 12: Verify cart is empty
        empty_cart_resp = request.get("/api/cart", params={"session_id": session_id})
        assert empty_cart_resp.ok
        empty_cart = empty_cart_resp.json()
        assert empty_cart["items"] == []
        assert empty_cart["total"] == 0
