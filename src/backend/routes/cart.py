"""Cart blueprint."""
from flask import Blueprint, request
from pydantic import ValidationError
from psycopg2.extras import RealDictCursor
from utils.response import json_response
from utils.db import get_db_connection, put_db_connection
from utils.fallback import _get_or_create_fallback_cart, _book_lookup
from utils.metrics import METRICS
from schemas import CartAddRequest, CartUpdateRequest

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/api/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'GET':
        session_id = request.args.get('session_id', '')
        if not session_id:
            return json_response({"error": "missing session_id"}, 400)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id FROM carts WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
            if not row:
                return json_response({"session_id": session_id, "items": [], "total": 0})
            cart_id = row["id"]
            cur.execute("""
                SELECT ci.id, ci.book_id, ci.quantity,
                       b.title, b.author, b.price
                FROM cart_items ci
                JOIN books b ON ci.book_id = b.id
                WHERE ci.cart_id = %s
            """, (cart_id,))
            items = [dict(r) for r in cur.fetchall()]
            total = sum(i["price"] * i["quantity"] for i in items)
            cur.close(); put_db_connection(conn)
            return json_response({"session_id": session_id, "items": items, "total": round(total, 2)})
        else:
            cart = _get_or_create_fallback_cart(session_id)
            items = []
            for it in cart["items"]:
                b = _book_lookup(it["book_id"])
                if b:
                    items.append({"id": it.get("id"), "book_id": it["book_id"], "quantity": it["quantity"],
                                  "title": b["title"], "author": b["author"], "price": b.get("price", 0)})
            total = sum(i["price"] * i["quantity"] for i in items)
            return json_response({"session_id": session_id, "items": items, "total": round(total, 2), "mode": "fallback"})

    else:  # POST
        body = request.get_json(silent=True) or {}
        try:
            req = CartAddRequest(**body)
        except ValidationError as e:
            return json_response({"error": e.errors()}, 400)

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM carts WHERE session_id = %s", (req.session_id,))
            row = cur.fetchone()
            if row:
                cart_id = row[0]
            else:
                cur.execute("INSERT INTO carts (session_id) VALUES (%s) RETURNING id", (req.session_id,))
                cart_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO cart_items (cart_id, book_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (cart_id, book_id) DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
            """, (cart_id, req.book_id, req.quantity))
            cur.close(); put_db_connection(conn)
            METRICS['cart_items_added_total'] += 1
            return json_response({"status": "added", "book_id": req.book_id, "quantity": req.quantity}, 201)
        else:
            cart = _get_or_create_fallback_cart(req.session_id)
            existing = next((it for it in cart["items"] if it["book_id"] == req.book_id), None)
            if existing:
                existing["quantity"] += req.quantity
            else:
                cart["items"].append({"id": len(cart["items"]) + 1, "book_id": req.book_id, "quantity": req.quantity})
            METRICS['cart_items_added_total'] += 1
            return json_response({"status": "added", "book_id": req.book_id, "quantity": req.quantity, "mode": "fallback"}, 201)


@cart_bp.route('/api/cart/item/<int:item_id>', methods=['PUT', 'DELETE'])
def cart_item(item_id):
    if request.method == 'PUT':
        body = request.get_json(silent=True) or {}
        try:
            req = CartUpdateRequest(**body)
        except ValidationError as e:
            return json_response({"error": e.errors()}, 400)

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            # Verify ownership via JOIN to prevent IDOR
            cur.execute("""
                SELECT ci.id FROM cart_items ci
                JOIN carts c ON ci.cart_id = c.id
                WHERE ci.id = %s AND c.session_id = %s
            """, (item_id, req.session_id))
            if not cur.fetchone():
                cur.close(); put_db_connection(conn)
                return json_response({"error": "item not found or access denied"}, 404)
            if req.quantity == 0:
                cur.execute("DELETE FROM cart_items WHERE id = %s", (item_id,))
            else:
                cur.execute("UPDATE cart_items SET quantity = %s WHERE id = %s", (req.quantity, item_id))
            cur.close(); put_db_connection(conn)
            return json_response({"status": "updated", "item_id": item_id, "quantity": req.quantity})
        else:
            cart = _get_or_create_fallback_cart(req.session_id)
            for it in cart["items"]:
                if it.get("id") == item_id:
                    if req.quantity == 0:
                        cart["items"].remove(it)
                    else:
                        it["quantity"] = req.quantity
                    return json_response({"status": "updated", "item_id": item_id, "quantity": req.quantity, "mode": "fallback"})
            return json_response({"error": "item not found"}, 404)

    else:  # DELETE
        session_id = request.args.get('session_id', '')
        if not session_id:
            return json_response({"error": "missing session_id"}, 400)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            # Verify ownership via JOIN to prevent IDOR
            cur.execute("""
                SELECT ci.id FROM cart_items ci
                JOIN carts c ON ci.cart_id = c.id
                WHERE ci.id = %s AND c.session_id = %s
            """, (item_id, session_id))
            if not cur.fetchone():
                cur.close(); put_db_connection(conn)
                return json_response({"error": "item not found or access denied"}, 404)
            cur.execute("DELETE FROM cart_items WHERE id = %s", (item_id,))
            cur.close(); put_db_connection(conn)
            return json_response({"status": "deleted", "item_id": item_id})
        else:
            cart = _get_or_create_fallback_cart(session_id)
            for it in cart["items"]:
                if it.get("id") == item_id:
                    cart["items"].remove(it)
                    return json_response({"status": "deleted", "item_id": item_id, "mode": "fallback"})
            return json_response({"error": "item not found"}, 404)
