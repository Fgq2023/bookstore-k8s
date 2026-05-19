"""Database connection pool and helpers."""
import os
import sys
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger('bookstore')

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

from .metrics import METRICS

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


@contextmanager
def db_transaction():
    """Explicit transaction context manager.

    Usage:
        with db_transaction() as conn:
            if not conn:
                return fallback_response
            cur = conn.cursor()
            cur.execute(...)
            # commit on clean exit, rollback on exception
    """
    conn = get_db_connection()
    if not conn:
        yield None
        return
    old_autocommit = conn.autocommit
    conn.autocommit = False
    try:
        yield conn
        conn.commit()
        logger.debug("Transaction committed")
    except Exception:
        conn.rollback()
        logger.warning("Transaction rolled back")
        raise
    finally:
        conn.autocommit = old_autocommit
        put_db_connection(conn)


@contextmanager
def db_cursor(cursor_factory=None):
    """Auto-managed cursor context manager.

    Usage:
        with db_cursor() as cur:
            if not cur:
                return fallback_response
            cur.execute(...)
            # cursor closed and connection returned automatically
    """
    conn = get_db_connection()
    if not conn:
        yield None
        return
    cur = None
    try:
        if cursor_factory:
            cur = conn.cursor(cursor_factory=cursor_factory)
        else:
            cur = conn.cursor()
        yield cur
    finally:
        if cur:
            cur.close()
        put_db_connection(conn)


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
