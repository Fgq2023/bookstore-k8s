"""JSON response helpers and custom encoder."""
import json
from decimal import Decimal
from datetime import datetime
from flask import Response


class DecimalEncoder(json.JSONEncoder):
    """Handles Decimal and datetime serialization."""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def json_response(data, status=200):
    """Return a JSON Response with custom encoder."""
    return Response(
        response=json.dumps(data, cls=DecimalEncoder, indent=2, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )
