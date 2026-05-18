"""Probes and metrics blueprints."""
from flask import Blueprint, Response
from utils.response import json_response
from utils.db import get_db_connection, put_db_connection, DB_AVAILABLE
from utils.metrics import METRICS

probes_bp = Blueprint('probes', __name__)

# Mutable shutdown flag (modified by app factory via signal handler)
shutdown_requested = False


@probes_bp.route('/metrics', methods=['GET'])
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


@probes_bp.route('/startup', methods=['GET'])
def startup():
    if not DB_AVAILABLE:
        return json_response({"status": "ok", "db": "unavailable"}, 200)
    conn = get_db_connection()
    if conn:
        put_db_connection(conn)
        return json_response({"status": "ok", "db": "connected"}, 200)
    return json_response({"status": "ok", "db": "fallback"}, 200)


@probes_bp.route('/healthz', methods=['GET'])
def healthz():
    if shutdown_requested:
        return json_response({"status": "unhealthy", "reason": "shutting down"}, 503)
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    put_db_connection(conn)
    return json_response({"status": "healthy", "service": "backend", "db": db_status})


@probes_bp.route('/ready', methods=['GET'])
def ready():
    conn = get_db_connection()
    db_ok = conn is not None
    put_db_connection(conn)
    return json_response(
        {"status": "ready" if db_ok else "ready (fallback)", "dependencies": {"database": db_ok}}
    )
