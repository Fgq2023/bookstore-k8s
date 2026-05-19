"""Orders blueprint."""
import json
import time
import logging
from flask import Blueprint, request
from pydantic import ValidationError
from psycopg2.extras import RealDictCursor
from utils.response import json_response
from utils.db import get_db_connection, put_db_connection, db_transaction
from utils.fallback import _get_or_create_fallback_cart, _book_lookup, _fallback_next_order_id, FALLBACK_ORDERS
from utils.metrics import METRICS
from schemas import OrderListQuery

orders_bp = Blueprint('orders', __name__)
logger = logging.getLogger('bookstore')


@orders_bp.route('/api/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'GET':
        session_id = request.args.get('session_id', '')
        if not session_id:
            return json_response({"error": "missing session_id"}, 400)
        try:
            q = OrderListQuery(session_id=session_id,
                               page=request.args.get('page', 1, type=int),
                               per_page=request.args.get('per_page', 20, type=int))
        except ValidationError as e:
            return json_response({"error": e.errors()}, 400)
        offset = (q.page - 1) * q.per_page
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE session_id = %s", (session_id,))
            total = cur.fetchone()['cnt']
            cur.execute("""
                SELECT id, total_amount, status, created_at, updated_at, status_history
                FROM orders WHERE session_id = %s ORDER BY id DESC LIMIT %s OFFSET %s
            """, (session_id, q.per_page, offset))
            orders_list = [dict(r) for r in cur.fetchall()]
            cur.close(); put_db_connection(conn)
            return json_response({
                "session_id": session_id, "count": len(orders_list), "total": total,
                "page": q.page, "per_page": q.per_page, "orders": orders_list
            })
        else:
            orders_list = FALLBACK_ORDERS.get(session_id, [])
            return json_response({"session_id": session_id, "count": len(orders_list), "total": len(orders_list),
                                  "page": 1, "per_page": q.per_page, "orders": orders_list, "mode": "fallback"})

    else:  # POST
        body = request.get_json(silent=True) or {}
        try:
            from schemas import OrderCreateRequest
            req = OrderCreateRequest(**body)
        except ValidationError as e:
            return json_response({"error": e.errors()}, 400)

        with db_transaction() as conn:
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM carts WHERE session_id = %s", (req.session_id,))
                row = cur.fetchone()
                if not row:
                    return json_response({"error": "cart is empty"}, 400)
                cart_id = row[0]
                cur.execute("""
                    SELECT ci.book_id, ci.quantity, b.price, b.title, b.author, b.stock_quantity
                    FROM cart_items ci
                    JOIN books b ON ci.book_id = b.id
                    WHERE ci.cart_id = %s
                """, (cart_id,))
                items = cur.fetchall()
                if not items:
                    return json_response({"error": "cart is empty"}, 400)

                stock_issues = []
                for book_id, qty, _, _, _, stock in items:
                    if stock < qty:
                        stock_issues.append(f"book {book_id}: requested {qty}, available {stock}")
                if stock_issues:
                    return json_response({"error": f"insufficient stock: {'; '.join(stock_issues)}"}, 400)

                total = sum(qty * price for _, qty, price, _, _, _ in items)
                now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                cur.execute(
                    "INSERT INTO orders (session_id, total_amount, status, status_history) VALUES (%s, %s, %s, %s) RETURNING id",
                    (req.session_id, total, 'pending', json.dumps([{"status": "pending", "at": now_iso}]))
                )
                order_id = cur.fetchone()[0]

                for book_id, qty, price, title, author, _ in items:
                    cur.execute(
                        "INSERT INTO order_items (order_id, book_id, quantity, price, title, author) VALUES (%s, %s, %s, %s, %s, %s)",
                        (order_id, book_id, qty, price, title, author)
                    )
                    cur.execute(
                        "UPDATE books SET stock_quantity = stock_quantity - %s WHERE id = %s",
                        (qty, book_id)
                    )

                cur.execute(
                    "UPDATE orders SET status = %s, status_history = status_history || %s::jsonb WHERE id = %s",
                    ('confirmed', json.dumps({"status": "confirmed", "at": now_iso}), order_id)
                )
                cur.execute("DELETE FROM cart_items WHERE cart_id = %s", (cart_id,))
                cur.close()
                logger.info(f"Order created: id={order_id}, total={total}, items={len(items)}")
                METRICS['orders_created_total'] += 1
                return json_response({"status": "created", "order_id": order_id, "total": float(total)}, 201)
            else:
                # Fallback mode — atomicity guaranteed by single-thread dict ops
                cart = _get_or_create_fallback_cart(req.session_id)
                if not cart["items"]:
                    return json_response({"error": "cart is empty"}, 400)
                total = 0
                order_items = []
                for it in cart["items"]:
                    b = _book_lookup(it["book_id"])
                    price = b.get("price", 0) if b else 0
                    total += price * it["quantity"]
                    order_items.append({
                        "book_id": it["book_id"], "quantity": it["quantity"],
                        "price": price, "title": b["title"] if b else "", "author": b["author"] if b else ""
                    })
                order_id = _fallback_next_order_id()
                now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                order = {
                    "id": order_id, "session_id": req.session_id, "total_amount": round(total, 2),
                    "status": "confirmed", "items": order_items,
                    "created_at": now_iso, "updated_at": now_iso,
                    "status_history": [{"status": "pending", "at": now_iso}, {"status": "confirmed", "at": now_iso}]
                }
                if req.session_id not in FALLBACK_ORDERS:
                    FALLBACK_ORDERS[req.session_id] = []
                FALLBACK_ORDERS[req.session_id].insert(0, order)
                cart["items"] = []
                METRICS['orders_created_total'] += 1
                return json_response({"status": "created", "order_id": order_id, "total": round(total, 2), "mode": "fallback"}, 201)


@orders_bp.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, session_id, total_amount, status, created_at, updated_at, status_history FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()
        if not order:
            cur.close(); put_db_connection(conn)
            return json_response({"error": "not found"}, 404)
        cur.execute("""
            SELECT book_id, quantity, price, title, author
            FROM order_items WHERE order_id = %s
        """, (order_id,))
        items = [dict(r) for r in cur.fetchall()]
        cur.close(); put_db_connection(conn)
        data = dict(order)
        data["items"] = items
        return json_response(data)
    else:
        found = None
        for sess, orders_list in FALLBACK_ORDERS.items():
            for o in orders_list:
                if o["id"] == order_id:
                    found = o
                    break
            if found:
                break
        if found:
            return json_response(found)
        else:
            return json_response({"error": "not found"}, 404)
