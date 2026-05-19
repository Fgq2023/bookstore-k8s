"""Authentication blueprint."""
import logging
from flask import Blueprint, request
from pydantic import ValidationError
from utils.response import json_response
from utils.db import get_db_connection, put_db_connection, RealDictCursor
from utils.auth import generate_token, jwt_required
from schemas import RegisterRequest, LoginRequest, format_validation_errors

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger('bookstore')

try:
    import psycopg2
    IntegrityError = psycopg2.IntegrityError
except ImportError:
    psycopg2 = None
    IntegrityError = Exception


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    body = request.get_json(silent=True) or {}
    try:
        req = RegisterRequest(**body)
    except ValidationError as e:
        return json_response({"success": False, "error": {"code": "VALIDATION_ERROR", **format_validation_errors(e)}}, 400)

    from werkzeug.security import generate_password_hash
    password_hash = generate_password_hash(req.password)
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (req.username, req.email, password_hash)
            )
            user_id = cur.fetchone()[0]
            cur.close(); put_db_connection(conn)
            token = generate_token(user_id, req.username)
            return json_response({"success": True, "data": {"user_id": user_id, "username": req.username, "token": token}}, 201)
        except IntegrityError:
            cur.close(); put_db_connection(conn)
            return json_response({"success": False, "error": {"code": "CONFLICT", "message": "Username or email already exists"}}, 409)
    else:
        return json_response({"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "DB unavailable, cannot register"}}, 503)


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    body = request.get_json(silent=True) or {}
    try:
        req = LoginRequest(**body)
    except ValidationError as e:
        return json_response({"success": False, "error": {"code": "VALIDATION_ERROR", **format_validation_errors(e)}}, 400)

    from werkzeug.security import check_password_hash
    conn = get_db_connection()
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username = %s", (req.username,))
        user = cur.fetchone()
        cur.close(); put_db_connection(conn)
        if not user or not check_password_hash(user['password_hash'], req.password):
            return json_response({"success": False, "error": {"code": "UNAUTHORIZED", "message": "Invalid credentials"}}, 401)
        token = generate_token(user['id'], user['username'], user['is_admin'])
        return json_response({"success": True, "data": {"user_id": user['id'], "username": user['username'], "is_admin": user['is_admin'], "token": token}})
    else:
        return json_response({"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "DB unavailable"}}, 503)


@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required
def get_me():
    user = request.current_user
    return json_response({"success": True, "data": {"user_id": user['user_id'], "username": user['username'], "is_admin": user.get('is_admin', False)}})
