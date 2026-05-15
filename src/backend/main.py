#!/usr/bin/env python3
"""
Cloud-Native Bookstore Backend API
- PostgreSQL integration with retry logic
- Health/Ready probes with DB connectivity check
- Fallback to memory list if DB is temporarily unavailable
- Full REST API: books, cart, orders
- Prometheus-style /metrics endpoint
"""
import os, json, sys, time, re, logging, signal, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

# ================= DB Configuration =================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'bookstore-db'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('POSTGRES_DB', 'bookstore'),
    'user': os.getenv('POSTGRES_USER', 'bookstore_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'SecureP@ssw0rd!2026')
}

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import pool
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️  psycopg2 not found. Using in-memory fallback mode.", flush=True)

# ================= Sample Data =================
FALLBACK_BOOKS = [
    {"id": "1", "title": "Cloud Native Patterns", "author": "Cornelia Davis", "isbn": "978-1492041153", "price": 45.99},
    {"id": "2", "title": "Kubernetes in Action", "author": "Marko Luksa", "isbn": "978-1617293726", "price": 49.99},
    {"id": "3", "title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "isbn": "978-1449373320", "price": 55.00},
    {"id": "4", "title": "The Phoenix Project", "author": "Gene Kim", "isbn": "978-1942788294", "price": 24.99},
    {"id": "5", "title": "Site Reliability Engineering", "author": "Betsy Beyer", "isbn": "978-1491929124", "price": 39.99},
]

# Fallback memory stores
FALLBACK_CARTS = {}   # session_id -> {items: [{cart_item_id, book_id, quantity, title, author, price}]}
FALLBACK_ORDERS = {}  # session_id -> [order dicts]
FALLBACK_ORDER_SEQ = 0

# ================= Logging & Metrics =================
APP_ENV = os.getenv('APP_ENV', 'development')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('bookstore')

# Simple Prometheus-style counters
METRICS = {
    'http_requests_total': defaultdict(int),
    'http_request_duration_seconds': defaultdict(float),
    'db_connections_failed_total': 0,
    'db_connections_success_total': 0,
    'orders_created_total': 0,
    'cart_items_added_total': 0,
}

def _record_request(method, path, status, duration):
    label = f"method=\"{method}\",path=\"{path}\",status=\"{status}\""
    METRICS['http_requests_total'][label] += 1
    METRICS['http_request_duration_seconds'][label] += duration

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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id VARCHAR(10) PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(255) NOT NULL,
                isbn VARCHAR(20),
                price NUMERIC(10,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id SERIAL PRIMARY KEY,
                cart_id INTEGER REFERENCES carts(id) ON DELETE CASCADE,
                book_id VARCHAR(10) NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cart_id, book_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                total_amount NUMERIC(10,2) DEFAULT 0,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                book_id VARCHAR(10) NOT NULL,
                quantity INTEGER NOT NULL,
                price NUMERIC(10,2) NOT NULL,
                title VARCHAR(255),
                author VARCHAR(255)
            )
        """)
        cur.execute("SELECT COUNT(*) FROM books")
        if cur.fetchone()[0] == 0:
            sample = [(b["id"], b["title"], b["author"], b["isbn"], b.get("price", 0)) for b in FALLBACK_BOOKS]
            cur.executemany(
                "INSERT INTO books (id, title, author, isbn, price) VALUES (%s, %s, %s, %s, %s)", sample
            )
            print("✅ Database initialized with sample books", flush=True)
        else:
            # Ensure price column exists on existing data
            cur.execute("UPDATE books SET price = 0 WHERE price IS NULL OR price = 0")
            print("✅ Database already contains data", flush=True)
        cur.close()
        put_db_connection(conn)
        return True
    except Exception as e:
        print(f"⚠️  DB init error: {e}", flush=True)
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

# ================= HTTP Handler =================
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        from decimal import Decimal
        from datetime import datetime
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

class BookstoreAPI(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, cls=DecimalEncoder).encode())

    def _send_text(self, text, status=200, content_type='text/plain'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(text.encode())

    def _send_error(self, message, status=400):
        self._send_json({"error": message}, status)

    def _read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        body = self.rfile.read(length).decode('utf-8')
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def _get_session(self):
        params = parse_qs(urlparse(self.path).query)
        return params.get('session_id', [''])[0]

    def do_OPTIONS(self):
        start = time.time()
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        _record_request('OPTIONS', urlparse(self.path).path, 204, time.time() - start)

    def _do_request(self, method, handler):
        start = time.time()
        status = 200
        try:
            status = handler()
            if status is None:
                status = 200
        except Exception as e:
            logger.exception("Request failed")
            self._send_error(str(e), 500)
            status = 500
        finally:
            _record_request(method, urlparse(self.path).path, status, time.time() - start)
        return status

    def do_GET(self):
        path = urlparse(self.path).path
        params = parse_qs(urlparse(self.path).query)
        session_id = params.get('session_id', [''])[0]

        def handle():
            # 🗺️ Route: /metrics
            if path == '/metrics':
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
                self._send_text("\n".join(lines), content_type='text/plain; version=0.0.4; charset=utf-8')
                return 200

            # 🗺️ Route: /healthz
            if path == '/healthz':
                conn = get_db_connection()
                db_status = "connected" if conn else "disconnected"
                put_db_connection(conn)
                self._send_json({"status": "healthy", "service": "backend", "db": db_status})
                return 200

            # 🗺️ Route: /ready
            if path == '/ready':
                conn = get_db_connection()
                db_ok = conn is not None
                put_db_connection(conn)
                self._send_json(
                    {"status": "ready" if db_ok else "ready (fallback)", "dependencies": {"database": db_ok}}
                )
                return 200

            # 🗺️ Route: /api/books
            if path == '/api/books':
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute("SELECT id, title, author, isbn, price, created_at FROM books ORDER BY id")
                    books = [dict(row) for row in cur.fetchall()]
                    cur.close(); put_db_connection(conn)
                    self._send_json({"count": len(books), "books": books})
                else:
                    self._send_json({"count": len(FALLBACK_BOOKS), "books": FALLBACK_BOOKS, "mode": "fallback"})
                return 200

            # 🗺️ Route: /api/books/search
            if path == '/api/books/search':
                keyword = params.get('q', [''])[0].lower()
                if not keyword:
                    self._send_error("missing 'q' parameter")
                    return 400
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute(
                        "SELECT * FROM books WHERE title ILIKE %s OR author ILIKE %s ORDER BY id",
                        (f'%{keyword}%', f'%{keyword}%')
                    )
                    results = [dict(r) for r in cur.fetchall()]
                    cur.close(); put_db_connection(conn)
                    self._send_json({"query": keyword, "count": len(results), "books": results})
                else:
                    results = [b for b in FALLBACK_BOOKS if keyword in b['title'].lower() or keyword in b['author'].lower()]
                    self._send_json({"query": keyword, "count": len(results), "books": results, "mode": "fallback"})
                return 200

            # 🗺️ Route: /api/books/{id}
            if re.match(r'^/api/books/[^/]+$', path):
                book_id = path.split('/')[-1]
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
                    book = cur.fetchone()
                    cur.close(); put_db_connection(conn)
                    if book:
                        self._send_json(dict(book))
                    else:
                        self._send_error("not found", 404)
                        return 404
                else:
                    book = _book_lookup(book_id)
                    if book:
                        self._send_json(book)
                    else:
                        self._send_error("not found", 404)
                        return 404
                return 200

            # 🗺️ Route: /api/cart
            if path == '/api/cart':
                if not session_id:
                    self._send_error("missing session_id", 400)
                    return 400
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute("SELECT id FROM carts WHERE session_id = %s", (session_id,))
                    row = cur.fetchone()
                    if not row:
                        self._send_json({"session_id": session_id, "items": [], "total": 0})
                    else:
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
                        self._send_json({"session_id": session_id, "items": items, "total": round(total, 2)})
                    cur.close(); put_db_connection(conn)
                else:
                    cart = _get_or_create_fallback_cart(session_id)
                    items = []
                    for it in cart["items"]:
                        b = _book_lookup(it["book_id"])
                        if b:
                            items.append({"id": it.get("id"), "book_id": it["book_id"], "quantity": it["quantity"],
                                          "title": b["title"], "author": b["author"], "price": b.get("price", 0)})
                    total = sum(i["price"] * i["quantity"] for i in items)
                    self._send_json({"session_id": session_id, "items": items, "total": round(total, 2), "mode": "fallback"})
                return 200

            # 🗺️ Route: /api/orders
            if path == '/api/orders':
                if not session_id:
                    self._send_error("missing session_id", 400)
                    return 400
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute("SELECT id, total_amount, status, created_at FROM orders WHERE session_id = %s ORDER BY id DESC", (session_id,))
                    orders = [dict(r) for r in cur.fetchall()]
                    cur.close(); put_db_connection(conn)
                    self._send_json({"session_id": session_id, "count": len(orders), "orders": orders})
                else:
                    orders = FALLBACK_ORDERS.get(session_id, [])
                    self._send_json({"session_id": session_id, "count": len(orders), "orders": orders, "mode": "fallback"})
                return 200

            # 🗺️ Route: /api/orders/{id}
            if re.match(r'^/api/orders/\d+$', path):
                order_id = int(path.split('/')[-1])
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
                    order = cur.fetchone()
                    if not order:
                        cur.close(); put_db_connection(conn)
                        self._send_error("not found", 404)
                        return 404
                    cur.execute("""
                        SELECT book_id, quantity, price, title, author
                        FROM order_items WHERE order_id = %s
                    """, (order_id,))
                    items = [dict(r) for r in cur.fetchall()]
                    cur.close(); put_db_connection(conn)
                    data = dict(order)
                    data["items"] = items
                    self._send_json(data)
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
                        self._send_json(found)
                    else:
                        self._send_error("not found", 404)
                        return 404
                return 200

            self._send_error("not found", 404)
            return 404

        self._do_request('GET', handle)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_json()
        session_id = body.get('session_id', '')

        def handle():
            # 🗺️ Route: /api/cart
            if path == '/api/cart':
                if not session_id:
                    self._send_error("missing session_id", 400)
                    return 400
                book_id = body.get('book_id')
                quantity = int(body.get('quantity', 1))
                if not book_id or quantity < 1:
                    self._send_error("missing book_id or invalid quantity", 400)
                    return 400
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
                    self._send_json({"status": "added", "book_id": book_id, "quantity": quantity}, 201)
                else:
                    cart = _get_or_create_fallback_cart(session_id)
                    existing = next((it for it in cart["items"] if it["book_id"] == book_id), None)
                    if existing:
                        existing["quantity"] += quantity
                    else:
                        cart["items"].append({"id": len(cart["items"]) + 1, "book_id": book_id, "quantity": quantity})
                    self._send_json({"status": "added", "book_id": book_id, "quantity": quantity, "mode": "fallback"}, 201)
                METRICS['cart_items_added_total'] += quantity
                return 201

            # 🗺️ Route: /api/orders
            if path == '/api/orders':
                if not session_id:
                    self._send_error("missing session_id", 400)
                    return 400
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM carts WHERE session_id = %s", (session_id,))
                    row = cur.fetchone()
                    if not row:
                        cur.close(); put_db_connection(conn)
                        self._send_error("cart is empty", 400)
                        return 400
                    cart_id = row[0]
                    cur.execute("""
                        SELECT ci.book_id, ci.quantity, b.price, b.title, b.author
                        FROM cart_items ci
                        JOIN books b ON ci.book_id = b.id
                        WHERE ci.cart_id = %s
                    """, (cart_id,))
                    items = cur.fetchall()
                    if not items:
                        cur.close(); put_db_connection(conn)
                        self._send_error("cart is empty", 400)
                        return 400
                    total = sum(qty * price for _, qty, price, _, _ in items)
                    cur.execute(
                        "INSERT INTO orders (session_id, total_amount, status) VALUES (%s, %s, %s) RETURNING id",
                        (session_id, total, 'confirmed')
                    )
                    order_id = cur.fetchone()[0]
                    for book_id, qty, price, title, author in items:
                        cur.execute(
                            "INSERT INTO order_items (order_id, book_id, quantity, price, title, author) VALUES (%s, %s, %s, %s, %s, %s)",
                            (order_id, book_id, qty, price, title, author)
                        )
                    cur.execute("DELETE FROM cart_items WHERE cart_id = %s", (cart_id,))
                    cur.close(); put_db_connection(conn)
                    self._send_json({"status": "created", "order_id": order_id, "total": float(total)}, 201)
                else:
                    cart = _get_or_create_fallback_cart(session_id)
                    if not cart["items"]:
                        self._send_error("cart is empty", 400)
                        return 400
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
                    order = {
                        "id": order_id, "session_id": session_id, "total_amount": round(total, 2),
                        "status": "confirmed", "items": order_items, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                    if session_id not in FALLBACK_ORDERS:
                        FALLBACK_ORDERS[session_id] = []
                    FALLBACK_ORDERS[session_id].insert(0, order)
                    cart["items"] = []
                    self._send_json({"status": "created", "order_id": order_id, "total": round(total, 2), "mode": "fallback"}, 201)
                METRICS['orders_created_total'] += 1
                return 201

            self._send_error("not found", 404)
            return 404

        self._do_request('POST', handle)

    def do_PUT(self):
        path = urlparse(self.path).path
        body = self._read_json()

        def handle():
            match = re.match(r'^/api/cart/item/(\d+)$', path)
            if match:
                item_id = int(match.group(1))
                session_id = body.get('session_id', '')
                quantity = int(body.get('quantity', 0))
                if not session_id or quantity < 0:
                    self._send_error("missing session_id or invalid quantity", 400)
                    return 400
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    if quantity == 0:
                        cur.execute("DELETE FROM cart_items WHERE id = %s", (item_id,))
                    else:
                        cur.execute("UPDATE cart_items SET quantity = %s WHERE id = %s", (quantity, item_id))
                    cur.close(); put_db_connection(conn)
                    self._send_json({"status": "updated", "item_id": item_id, "quantity": quantity})
                else:
                    cart = _get_or_create_fallback_cart(session_id)
                    for it in cart["items"]:
                        if it.get("id") == item_id:
                            if quantity == 0:
                                cart["items"].remove(it)
                            else:
                                it["quantity"] = quantity
                            self._send_json({"status": "updated", "item_id": item_id, "quantity": quantity, "mode": "fallback"})
                            return 200
                    self._send_error("item not found", 404)
                    return 404
                return 200
            self._send_error("not found", 404)
            return 404

        self._do_request('PUT', handle)

    def do_DELETE(self):
        path = urlparse(self.path).path
        params = parse_qs(urlparse(self.path).query)
        session_id = params.get('session_id', [''])[0]

        def handle():
            match = re.match(r'^/api/cart/item/(\d+)$', path)
            if match:
                item_id = int(match.group(1))
                if not session_id:
                    self._send_error("missing session_id", 400)
                    return 400
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM cart_items WHERE id = %s", (item_id,))
                    cur.close(); put_db_connection(conn)
                    self._send_json({"status": "deleted", "item_id": item_id})
                else:
                    cart = _get_or_create_fallback_cart(session_id)
                    for it in cart["items"]:
                        if it.get("id") == item_id:
                            cart["items"].remove(it)
                            self._send_json({"status": "deleted", "item_id": item_id, "mode": "fallback"})
                            return 200
                    self._send_error("item not found", 404)
                    return 404
                return 200
            self._send_error("not found", 404)
            return 404

        self._do_request('DELETE', handle)

    def log_message(self, format, *args):
        if APP_ENV == 'development':
            logger.info(format % args)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True

# ================= Graceful Shutdown =================
def shutdown_server(server):
    def do_shutdown():
        logger.info("SIGTERM received, initiating graceful shutdown...")
        # Allow a short window for in-flight requests to complete
        time.sleep(1)
        server.shutdown()
    threading.Thread(target=do_shutdown, daemon=True).start()

# ================= Entry Point =================
if __name__ == "__main__":
    print("🚀 Bookstore Backend starting...", flush=True)
    init_pool()
    init_database()
    PORT = int(os.getenv('PORT', 8000))
    print(f"📡 Listening on 0.0.0.0:{PORT}", flush=True)
    server = ThreadedHTTPServer(('0.0.0.0', PORT), BookstoreAPI)
    signal.signal(signal.SIGTERM, lambda signum, frame: shutdown_server(server))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logger.info("Server stopped gracefully")
        sys.exit(0)
