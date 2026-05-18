"""JWT helpers and decorators."""
import os
import time
from functools import wraps
from flask import request
from utils.response import json_response

JWT_SECRET = os.getenv('JWT_SECRET', 'bookstore-dev-secret-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', '24'))


def generate_token(user_id, username, is_admin=False):
    import jwt as pyjwt
    payload = {
        'user_id': user_id,
        'username': username,
        'is_admin': is_admin,
        'exp': time.time() + JWT_EXPIRY_HOURS * 3600,
        'iat': time.time()
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token):
    import jwt as pyjwt
    try:
        return pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return json_response(
                {"success": False, "error": {"code": "UNAUTHORIZED", "message": "Missing or invalid Authorization header"}},
                401
            )
        token = auth_header.split(' ', 1)[1]
        payload = verify_token(token)
        if not payload:
            return json_response(
                {"success": False, "error": {"code": "UNAUTHORIZED", "message": "Invalid or expired token"}},
                401
            )
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated
