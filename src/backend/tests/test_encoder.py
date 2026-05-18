"""Tests for JSON encoder and response helpers."""
import json
from decimal import Decimal
from datetime import datetime
from utils.response import DecimalEncoder, json_response


def test_decimal_encoder():
    data = {
        'price': Decimal('45.99'),
        'created_at': datetime(2024, 1, 1, 12, 0, 0)
    }
    encoded = json.dumps(data, cls=DecimalEncoder)
    decoded = json.loads(encoded)
    assert decoded['price'] == 45.99
    assert decoded['created_at'] == '2024-01-01T12:00:00'


def test_json_response():
    resp = json_response({'key': 'value'}, 201)
    assert resp.status_code == 201
    assert resp.content_type == 'application/json'
    data = json.loads(resp.data)
    assert data['key'] == 'value'
