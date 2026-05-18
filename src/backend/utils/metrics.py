"""Prometheus-style metrics storage."""
from collections import defaultdict

METRICS = {
    'http_requests_total': defaultdict(int),
    'http_request_duration_seconds': defaultdict(float),
    'db_connections_failed_total': 0,
    'db_connections_success_total': 0,
    'orders_created_total': 0,
    'cart_items_added_total': 0,
}


def record_request(method, path, status, duration):
    label = f'method="{method}",path="{path}",status="{status}"'
    METRICS['http_requests_total'][label] += 1
    METRICS['http_request_duration_seconds'][label] += duration
