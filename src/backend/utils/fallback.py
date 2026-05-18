"""Fallback data and helpers when DB is unavailable."""

FALLBACK_BOOKS = [
    {"id": "1", "title": "Cloud Native Patterns", "author": "Cornelia Davis", "isbn": "978-1492041153", "price": 45.99, "stock_quantity": 100},
    {"id": "2", "title": "Kubernetes in Action", "author": "Marko Luksa", "isbn": "978-1617293726", "price": 49.99, "stock_quantity": 100},
    {"id": "3", "title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "isbn": "978-1449373320", "price": 55.00, "stock_quantity": 100},
    {"id": "4", "title": "The Phoenix Project", "author": "Gene Kim", "isbn": "978-1942788294", "price": 24.99, "stock_quantity": 100},
    {"id": "5", "title": "Site Reliability Engineering", "author": "Betsy Beyer", "isbn": "978-1491929124", "price": 39.99, "stock_quantity": 100},
]

FALLBACK_CARTS = {}
FALLBACK_ORDERS = {}
FALLBACK_ORDER_SEQ = 0


def _fallback_next_order_id():
    global FALLBACK_ORDER_SEQ
    FALLBACK_ORDER_SEQ += 1
    return FALLBACK_ORDER_SEQ


def _get_or_create_fallback_cart(session_id):
    if session_id not in FALLBACK_CARTS:
        FALLBACK_CARTS[session_id] = {"items": []}
    return FALLBACK_CARTS[session_id]


def _book_lookup(book_id):
    return next((b for b in FALLBACK_BOOKS if b["id"] == book_id), None)
