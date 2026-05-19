"""Books blueprint."""
import json
from flask import Blueprint, request
from pydantic import ValidationError
from psycopg2.extras import RealDictCursor
from utils.response import json_response
from utils.db import get_db_connection, put_db_connection
from utils.cache import cache_get, cache_set
from utils.fallback import FALLBACK_BOOKS
from schemas import BookListQuery, format_validation_errors

books_bp = Blueprint('books', __name__)


@books_bp.route('/api/books', methods=['GET'])
def get_books():
    try:
        q = BookListQuery(page=request.args.get('page', 1, type=int),
                          per_page=request.args.get('per_page', 20, type=int))
    except ValidationError as e:
        return json_response({"error": format_validation_errors(e)}, 400)

    page = q.page
    per_page = q.per_page
    cache_key = f"books_list:{page}:{per_page}"
    cached = cache_get(cache_key)
    if cached:
        return json_response(cached)

    conn = get_db_connection()
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT COUNT(*) AS cnt FROM books")
        total = cur.fetchone()['cnt']
        offset = (page - 1) * per_page
        cur.execute("""
            SELECT id, title, author, isbn, price, stock_quantity, created_at, updated_at
            FROM books ORDER BY id LIMIT %s OFFSET %s
        """, (per_page, offset))
        books = [dict(row) for row in cur.fetchall()]
        cur.close(); put_db_connection(conn)
        result = {
            "count": len(books), "total": total, "page": page,
            "per_page": per_page, "books": books
        }
        cache_set(cache_key, result, ttl_seconds=60)
        return json_response(result)
    else:
        return json_response({
            "count": len(FALLBACK_BOOKS), "total": len(FALLBACK_BOOKS),
            "page": 1, "per_page": per_page, "books": FALLBACK_BOOKS, "mode": "fallback"
        })


@books_bp.route('/api/books/search', methods=['GET'])
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


@books_bp.route('/api/books/<book_id>', methods=['GET'])
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
        from utils.fallback import _book_lookup
        book = _book_lookup(book_id)
        if book:
            return json_response(book)
        else:
            return json_response({"error": "not found"}, 404)
