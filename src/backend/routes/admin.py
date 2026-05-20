"""Admin blueprint."""
import json
import time
import uuid
from flask import Blueprint, request
from pydantic import ValidationError
from utils.response import json_response
from utils.db import get_db_connection, put_db_connection, RealDictCursor
from utils.auth import jwt_required
from utils.cache import cache_delete, cache_clear_prefix
from schemas import AdminStatusUpdateRequest, BookCreateRequest, BookUpdateRequest, format_validation_errors

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required
def update_order_status(order_id):
    """Admin only: update order status manually."""
    if not request.current_user.get('is_admin'):
        return json_response({"success": False, "error": {"code": "FORBIDDEN", "message": "Admin access required"}}, 403)
    body = request.get_json(silent=True) or {}
    try:
        req = AdminStatusUpdateRequest(**body)
    except ValidationError as e:
        return json_response({"success": False, "error": {"code": "VALIDATION_ERROR", **format_validation_errors(e)}}, 400)

    conn = get_db_connection()
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); put_db_connection(conn)
            return json_response({"success": False, "error": {"code": "NOT_FOUND", "message": "Order not found"}}, 404)
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        cur.execute(
            "UPDATE orders SET status = %s, status_history = status_history || %s::jsonb WHERE id = %s",
            (req.status, json.dumps({"status": req.status, "at": now_iso}), order_id)
        )
        cur.close(); put_db_connection(conn)
        cache_delete(f"order:{order_id}")
        return json_response({"success": True, "data": {"order_id": order_id, "status": req.status}})
    return json_response({"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "DB unavailable"}}, 503)


# ============================================================================
# Admin Book Management
# ============================================================================

def _check_admin():
    """Return error response if current user is not admin."""
    if not request.current_user.get('is_admin'):
        return json_response({"success": False, "error": {"code": "FORBIDDEN", "message": "Admin access required"}}, 403)
    return None


@admin_bp.route('/api/admin/books', methods=['GET'])
@jwt_required
def list_books_admin():
    """Admin only: list all books with full details."""
    err = _check_admin()
    if err:
        return err
    conn = get_db_connection()
    if not conn:
        return json_response({"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "DB unavailable"}}, 503)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, title, author, isbn, price, stock_quantity, created_at, updated_at
        FROM books ORDER BY id
    """)
    books = [dict(row) for row in cur.fetchall()]
    cur.close()
    put_db_connection(conn)
    return json_response({"success": True, "data": {"count": len(books), "books": books}})


@admin_bp.route('/api/admin/books', methods=['POST'])
@jwt_required
def create_book_admin():
    """Admin only: add a new book."""
    err = _check_admin()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    try:
        req = BookCreateRequest(**body)
    except ValidationError as e:
        return json_response({"success": False, "error": {"code": "VALIDATION_ERROR", **format_validation_errors(e)}}, 400)

    conn = get_db_connection()
    if not conn:
        return json_response({"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "DB unavailable"}}, 503)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Generate unique string ID since books.id is VARCHAR not SERIAL
        book_id = str(uuid.uuid4())[:8]
        cur.execute("""
            INSERT INTO books (id, title, author, isbn, price, stock_quantity)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, title, author, isbn, price, stock_quantity, created_at, updated_at
        """, (book_id, req.title, req.author, req.isbn, req.price, req.stock_quantity))
        book = dict(cur.fetchone())
        conn.commit()
        cache_clear_prefix("books_list:")
        return json_response({"success": True, "data": book}, 201)
    except Exception as e:
        conn.rollback()
        return json_response({"success": False, "error": {"code": "CONFLICT", "message": str(e)}}, 409)
    finally:
        cur.close()
        put_db_connection(conn)


@admin_bp.route('/api/admin/books/<book_id>', methods=['PUT'])
@jwt_required
def update_book_admin(book_id):
    """Admin only: update a book."""
    err = _check_admin()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    try:
        req = BookUpdateRequest(**body)
    except ValidationError as e:
        return json_response({"success": False, "error": {"code": "VALIDATION_ERROR", **format_validation_errors(e)}}, 400)

    conn = get_db_connection()
    if not conn:
        return json_response({"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "DB unavailable"}}, 503)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Build dynamic update query
        updates = []
        params = []
        if req.title is not None:
            updates.append("title = %s")
            params.append(req.title)
        if req.author is not None:
            updates.append("author = %s")
            params.append(req.author)
        if req.isbn is not None:
            updates.append("isbn = %s")
            params.append(req.isbn)
        if req.price is not None:
            updates.append("price = %s")
            params.append(req.price)
        if req.stock_quantity is not None:
            updates.append("stock_quantity = %s")
            params.append(req.stock_quantity)

        if not updates:
            return json_response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": "No fields to update"}}, 400)

        params.append(book_id)
        cur.execute(f"""
            UPDATE books SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, title, author, isbn, price, stock_quantity, created_at, updated_at
        """, tuple(params))
        book = cur.fetchone()
        if not book:
            cur.close(); put_db_connection(conn)
            return json_response({"success": False, "error": {"code": "NOT_FOUND", "message": "Book not found"}}, 404)
        conn.commit()
        cache_clear_prefix("books_list:")
        cache_delete(f"book:{book_id}")
        return json_response({"success": True, "data": dict(book)})
    except Exception as e:
        conn.rollback()
        return json_response({"success": False, "error": {"code": "CONFLICT", "message": str(e)}}, 409)
    finally:
        cur.close()
        put_db_connection(conn)


@admin_bp.route('/api/admin/books/<book_id>', methods=['DELETE'])
@jwt_required
def delete_book_admin(book_id):
    """Admin only: delete a book."""
    err = _check_admin()
    if err:
        return err
    conn = get_db_connection()
    if not conn:
        return json_response({"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "DB unavailable"}}, 503)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("DELETE FROM books WHERE id = %s RETURNING id", (book_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); put_db_connection(conn)
            return json_response({"success": False, "error": {"code": "NOT_FOUND", "message": "Book not found"}}, 404)
        conn.commit()
        cache_clear_prefix("books_list:")
        cache_delete(f"book:{book_id}")
        return json_response({"success": True, "data": {"message": "Book deleted", "id": book_id}})
    except Exception as e:
        conn.rollback()
        return json_response({"success": False, "error": {"code": "CONFLICT", "message": str(e)}}, 409)
    finally:
        cur.close()
        put_db_connection(conn)
