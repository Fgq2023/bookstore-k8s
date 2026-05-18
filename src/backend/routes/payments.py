"""Payment mock blueprint."""
import json
import time
from flask import Blueprint, request
from psycopg2.extras import RealDictCursor
from utils.response import json_response
from utils.db import get_db_connection, put_db_connection
from schemas import PaymentRequest

payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/api/payments', methods=['POST'])
def create_payment():
    """Mock payment gateway: processes payment for an order."""
    body = request.get_json(silent=True) or {}
    try:
        req = PaymentRequest(**body)
    except Exception as e:
        return json_response({"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}, 400)

    conn = get_db_connection()
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT status FROM orders WHERE id = %s", (req.order_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); put_db_connection(conn)
            return json_response({"success": False, "error": {"code": "NOT_FOUND", "message": "Order not found"}}, 404)
        if row['status'] != 'confirmed':
            cur.close(); put_db_connection(conn)
            return json_response({"success": False, "error": {"code": "INVALID_STATE", "message": f"Order is {row['status']}, cannot pay"}}, 400)
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        cur.execute(
            "UPDATE orders SET status = %s, status_history = status_history || %s::jsonb WHERE id = %s",
            ('shipped', json.dumps({"status": "shipped", "at": now_iso}), req.order_id)
        )
        cur.close(); put_db_connection(conn)
        return json_response({"success": True, "data": {"order_id": req.order_id, "payment_status": "paid", "order_status": "shipped"}})
    return json_response({"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "DB unavailable"}}, 503)
