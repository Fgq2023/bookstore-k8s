"""Tests for DecimalEncoder utility."""
import json
from decimal import Decimal
from datetime import datetime, timezone

from main import DecimalEncoder


class TestDecimalEncoder:
    """Test DecimalEncoder handles special types."""

    def test_decimal_encoding(self):
        data = {"price": Decimal("45.99")}
        result = json.dumps(data, cls=DecimalEncoder)
        assert result == '{"price": 45.99}'

    def test_datetime_encoding(self):
        dt = datetime(2026, 5, 15, 10, 30, 0, tzinfo=timezone.utc)
        data = {"created_at": dt}
        result = json.dumps(data, cls=DecimalEncoder)
        assert "2026-05-15T10:30:00" in result

    def test_fallback_encoding(self):
        data = {"name": "test", "value": 42}
        result = json.dumps(data, cls=DecimalEncoder)
        assert result == '{"name": "test", "value": 42}'
