#!/usr/bin/env python3
"""
Cloud-Native Bookstore Backend API (Flask)
- PostgreSQL integration with retry logic
- Health/Ready probes with DB connectivity check
- Fallback to memory list if DB is temporarily unavailable
- Full REST API: books, cart, orders
- Prometheus-style /metrics endpoint
"""
import os, json, sys, time, re, logging, signal
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

from flask import Flask, request, Response

# ================= DB Configuration =================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'bookstore-db'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('POSTGRES_DB', 'bookstore'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import pool
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️  psycopg2 not found. Using in-memory fallback mode.", flush=True)

# ================= Flask App =================
app = Flask(__name__)

# ================= Sample Data =================
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

# ================= Logging =================
APP_ENV = os.getenv('APP_ENV', 'development')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').upper()

_log_handler = logging.StreamHandler(sys.stdout)
if APP_ENV == 'production':
    try:
        from pythonjsonlogger import jsonlogger
        _log_handler.setFormatter(jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d',
            rename_fields={'levelname': 'level', 'asctime': 'timestamp'}
        ))
    except ImportError:
        _log_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s %(message)s'
        ))
else:
    _log_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    ))

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    handlers=[_log_handler]
)
logger = logging.getLogger('bookstore')

# ================= Metrics =================
METRICS = {
    'http_requests_total': defaultdict(int),
    'http_request_duration_seconds': defaultdict(float),
    'db_connections_failed_total': 0,
    'db_connections_success_total': 0,
    'orders_created_total': 0,
    'cart_items_added_total': 0,
}

def _record_request(method, path, status, duration):
    label = f'method="{method}",path="{path}",status="{status}"'
    METRICS['http_requests_total'][label] += 1
    METRICS['http_request_duration_seconds'][label] += duration

# ================= JSON Encoder =================
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        from decimal import Decimal
        from datetime import datetime
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def json_response(data, status=200):
    return Response(
        response=json.dumps(data, cls=DecimalEncoder, indent=2, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

# ================= Connection Pool =================
db_pool = None

def init_pool():
    global db_pool
    if not DB_AVAILABLE:
        return
    try:
        db_pool = pool.ThreadedConnectionPool(1, 20, **DB_CONFIG)
        logger.info("DB connection pool initialized (min=1, max=20)")
    except Exception as e:
        logger.error(f"Failed to initialize DB pool: {e}")
        db_pool = None

def get_db_connection(max_retries=3, delay=2):
    if not DB_AVAILABLE or db_pool is None:
        return None
    for attempt in range(max_retries):
        try:
            conn = db_pool.getconn()
            if conn.closed:
                db_pool.putconn(conn, close=True)
                raise psycopg2.OperationalError("Connection was closed")
            conn.autocommit = True
            METRICS['db_connections_success_total'] += 1
            return conn
        except psycopg2.OperationalError as e:
            METRICS['db_connections_failed_total'] += 1
            if attempt == max_retries - 1:
                logger.error(f"DB connection failed after {max_retries} attempts: {e}")
                return None
            logger.warning(f"DB pool attempt {attempt+1}/{max_retries} failed, retrying in {delay}s")
            time.sleep(delay)

def put_db_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)

def init_database():
    conn = get_db_connection()
    if not conn:
        print("⚠️  Running without DB — fallback mode active", flush=True)
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM books")
        count = cur.fetchone()[0]
        cur.close()
        put_db_connection(conn)
        if count == 0:
            print("⚠️  DB connected but no books found. Run 'alembic upgrade head' to initialize schema.", flush=True)
        else:
            print(f"✅ DB connected ({count} books)", flush=True)
        return True
    except Exception as e:
        print(f"⚠️  DB connectivity check failed: {e}", flush=True)
        put_db_connection(conn)
        return False

# ================= Fallback Helpers =================
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

# ================= Flask Hooks =================
@app.before_request
def before_request():
    request._start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - getattr(request, '_start_time', time.time())
    label = f'method="{request.method}",path="{request.path}",status="{response.status_code}"'
    METRICS['http_requests_total'][label] += 1
    METRICS['http_request_duration_seconds'][label] += duration
    if request.path != '/metrics':
        response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# ================= Routes =================

@app.route('/metrics', methods=['GET'])
def metrics():
    lines = []
    lines.append("# HELP http_requests_total Total HTTP requests")
    lines.append("# TYPE http_requests_total counter")
    for label, count in METRICS['http_requests_total'].items():
        lines.append(f"http_requests_total{{{label}}} {count}")
    lines.append("# HELP http_request_duration_seconds Total request duration")
    lines.append("# TYPE http_request_duration_seconds counter")
    for label, total in METRICS['http_request_duration_seconds'].items():
        lines.append(f"http_request_duration_seconds{{{label}}} {total:.6f}")
    lines.append("# HELP db_connections_success_total Successful DB connections")
    lines.append("# TYPE db_connections_success_total counter")
    lines.append(f"db_connections_success_total {METRICS['db_connections_success_total']}")
    lines.append("# HELP db_connections_failed_total Failed DB connections")
    lines.append("# TYPE db_connections_failed_total counter")
    lines.append(f"db_connections_failed_total {METRICS['db_connections_failed_total']}")
    lines.append("# HELP orders_created_total Orders created")
    lines.append("# TYPE orders_created_total counter")
    lines.append(f"orders_created_total {METRICS['orders_created_total']}")
    lines.append("# HELP cart_items_added_total Cart items added")
    lines.append("# TYPE cart_items_added_total counter")
    lines.append(f"cart_items_added_total {METRICS['cart_items_added_total']}")
    lines.append("")
    return Response("\n".join(lines), mimetype='text/plain; version=0.0.4; charset=utf-8')

@app.route('/healthz', methods=['GET'])
def healthz():
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    put_db_connection(conn)
    return json_response({"status": "healthy", "service": "backend", "db": db_status})

@app.route('/ready', methods=['GET'])
def ready():
    conn = get_db_connection()
    db_ok = conn is not None
    put_db_connection(conn)
    return json_response(
        {"status": "ready" if db_ok else "ready (fallback)", "dependencies": {"database": db_ok}}
    )

@app.route('/api/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, title, author, isbn, price, stock_quantity, created_at, updated_at FROM books ORDER BY id")
        books = [dict(row) for row in cur.fetchall()]
        cur.close(); put_db_connection(conn)
        return json_response({"count": len(books), "books": books})
    else:
        return json_response({"count": len(FALLBACK_BOOKS), "books": FALLBACK_BOOKS, "mode": "fallback"})

@app.route('/api/books/search', methods=['GET'])
def search_books():
    keyword = request.args.get('q', '').lower()
    if not keyword:
        return json_response({"error": "missing 'q' parameter"}, 400)
    conn = get_db_connection()
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT * FROM books WHERE title ILIKE %s OR author ILIKE %s ORDER BY id",
            (f'%{keyword}%', f'%{keyword}%')
        )
        results = [dict(r) for r in cur.fetchall()]
        cur.close(); put_db_connection(conn)
        return json_response({"query": keyword, "count": len(results), "books": results})
    else:
        results = [b for b in FALLBACK_BOOKS if keyword in b['title'].lower() or keyword in b['author'].lower()]
        return json_response({"query": keyword, "count": len(results), "books": results, "mode": "fallback"})

@app.route('/api/books/<book_id>', methods=['GET'])
def get_book(book_id):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cur.fetchone()
        cur.close(); put_db_connection(conn)
        if book:
            return json_response(dict(book))
        else:
            return json_response({"error": "not found"}, 404)
    else:
        book = _book_lookup(book_id)
        if book:
            return json_response(book)
        else:
            return json_response({"error": "not found"}, 404)

@app.route('/api/cart', methods=['GET', 'POST'])
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
        session_id = body.get('session_id', '')
        if not session_id:
            return json_response({"error": "missing session_id"}, 400)
        book_id = body.get('book_id')
        quantity = int(body.get('quantity', 1))
        if not book_id or quantity < 1:
            return json_response({"error": "missing book_id or invalid quantity"}, 400)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM carts WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
            if row:
                cart_id = row[0]
            else:
                cur.execute("INSERT INTO carts (session_id) VALUES (%s) RETURNING id", (session_id,))
                cart_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO cart_items (cart_id, book_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (cart_id, book_id) DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
            """, (cart_id, book_id, quantity))
            cur.close(); put_db_connection(conn)
            return json_response({"status": "added", "book_id": book_id, "quantity": quantity}, 201)
        else:
            cart = _get_or_create_fallback_cart(session_id)
            existing = next((it for it in cart["items"] if it["book_id"] == book_id), None)
            if existing:
                existing["quantity"] += quantity
            else:
                cart["items"].append({"id": len(cart["items"]) + 1, "book_id": book_id, "quantity": quantity})
            return json_response({"status": "added", "book_id": book_id, "quantity": quantity, "mode": "fallback"}, 201)

@app.route('/api/cart/item/<int:item_id>', methods=['PUT', 'DELETE'])
def cart_item(item_id):
    if request.method == 'PUT':
        body = request.get_json(silent=True) or {}
        session_id = body.get('session_id', '')
        quantity = int(body.get('quantity', 0))
        if not session_id or quantity < 0:
            return json_response({"error": "missing session_id or invalid quantity"}, 400)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            if quantity == 0:
                cur.execute("DELETE FROM cart_items WHERE id = %s", (item_id,))
            else:
                cur.execute("UPDATE cart_items SET quantity = %s WHERE id = %s", (quantity, item_id))
            cur.close(); put_db_connection(conn)
            return json_response({"status": "updated", "item_id": item_id, "quantity": quantity})
        else:
            cart = _get_or_create_fallback_cart(session_id)
            for it in cart["items"]:
                if it.get("id") == item_id:
                    if quantity == 0:
                        cart["items"].remove(it)
                    else:
                        it["quantity"] = quantity
                    return json_response({"status": "updated", "item_id": item_id, "quantity": quantity, "mode": "fallback"})
            return json_response({"error": "item not found"}, 404)

    else:  # DELETE
        session_id = request.args.get('session_id', '')
        if not session_id:
            return json_response({"error": "missing session_id"}, 400)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
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

@app.route('/api/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'GET':
        session_id = request.args.get('session_id', '')
        if not session_id:
            return json_response({"error": "missing session_id"}, 400)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id, total_amount, status, created_at, updated_at, status_history FROM orders WHERE session_id = %s ORDER BY id DESC", (session_id,))
            orders = [dict(r) for r in cur.fetchall()]
            cur.close(); put_db_connection(conn)
            return json_response({"session_id": session_id, "count": len(orders), "orders": orders})
        else:
            orders = FALLBACK_ORDERS.get(session_id, [])
            return json_response({"session_id": session_id, "count": len(orders), "orders": orders, "mode": "fallback"})

    else:  # POST
        body = request.get_json(silent=True) or {}
        session_id = body.get('session_id', '')
        if not session_id:
            return json_response({"error": "missing session_id"}, 400)
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM carts WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
            if not row:
                cur.close(); put_db_connection(conn)
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
                cur.close(); put_db_connection(conn)
                return json_response({"error": "cart is empty"}, 400)

            stock_issues = []
            for book_id, qty, _, _, _, stock in items:
                if stock < qty:
                    stock_issues.append(f"book {book_id}: requested {qty}, available {stock}")
            if stock_issues:
                cur.close(); put_db_connection(conn)
                return json_response({"error": f"insufficient stock: {'; '.join(stock_issues)}"}, 400)

            total = sum(qty * price for _, qty, price, _, _, _ in items)

            cur.execute(
                "INSERT INTO orders (session_id, total_amount, status, status_history) VALUES (%s, %s, %s, %s) RETURNING id",
                (session_id, total, 'pending', json.dumps([{"status": "pending", "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}]))
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

            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            cur.execute(
                "UPDATE orders SET status = %s, status_history = status_history || %s::jsonb WHERE id = %s",
                ('confirmed', json.dumps({"status": "confirmed", "at": now_iso}), order_id)
            )

            cur.execute("DELETE FROM cart_items WHERE cart_id = %s", (cart_id,))
            cur.close(); put_db_connection(conn)
            logger.info(f"Order created: id={order_id}, total={total}, items={len(items)}")
            METRICS['orders_created_total'] += 1
            return json_response({"status": "created", "order_id": order_id, "total": float(total)}, 201)
        else:
            cart = _get_or_create_fallback_cart(session_id)
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
                "id": order_id, "session_id": session_id, "total_amount": round(total, 2),
                "status": "confirmed", "items": order_items,
                "created_at": now_iso, "updated_at": now_iso,
                "status_history": [{"status": "pending", "at": now_iso}, {"status": "confirmed", "at": now_iso}]
            }
            if session_id not in FALLBACK_ORDERS:
                FALLBACK_ORDERS[session_id] = []
            FALLBACK_ORDERS[session_id].insert(0, order)
            cart["items"] = []
            METRICS['orders_created_total'] += 1
            return json_response({"status": "created", "order_id": order_id, "total": round(total, 2), "mode": "fallback"}, 201)

@app.route('/api/orders/<int:order_id>', methods=['GET'])
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
        for sess, orders in FALLBACK_ORDERS.items():
            for o in orders:
                if o["id"] == order_id:
                    found = o
                    break
            if found:
                break
        if found:
            return json_response(found)
        else:
            return json_response({"error": "not found"}, 404)

# ================= Initialization =================
init_pool()
db_connected = init_database()

if __name__ == "__main__":
    PORT = int(os.getenv('PORT', 8000))
    print(f"📡 Flask Bookstore Backend listening on 0.0.0.0:{PORT}", flush=True)
    # threaded=True is default in Flask 2.3+ when not in debug mode
    app.run(host='0.0.0.0', port=PORT, threaded=True)
