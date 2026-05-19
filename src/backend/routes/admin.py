"""Admin blueprint."""
import json
import time
from flask import Blueprint, request
from pydantic import ValidationError
from utils.response import json_response
from utils.db import get_db_connection, put_db_connection, RealDictCursor
from utils.auth import jwt_required
from utils.cache import cache_delete
from schemas import AdminStatusUpdateRequest, format_validation_errors

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
