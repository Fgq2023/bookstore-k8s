"""Flask application factory."""
import os
import sys
import time
import uuid
import signal
import logging
from flask import Flask, request
from routes import probes_bp, books_bp, cart_bp, orders_bp, auth_bp, payments_bp, admin_bp
from utils.response import json_response
from utils.metrics import record_request
from utils.db import init_pool, init_database

APP_ENV = os.getenv('APP_ENV', 'development')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').upper()

_log_handler = logging.StreamHandler(sys.stdout)
if APP_ENV == 'production':
    try:
        from pythonjsonlogger import jsonlogger
        _log_handler.setFormatter(jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d',
            rename_fields={'levelname': 'level', 'asctime': 'timestamp'}
        ))
    except ImportError:
        _log_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s %(message)s'
        ))
else:
    _log_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    ))

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    handlers=[_log_handler]
)
logger = logging.getLogger('bookstore')


def create_app():
    app = Flask(__name__)

    # Rate limiting
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        # Prefer Redis backend; fallback to memory for single-worker or local dev
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            storage_uri = redis_url
            storage_options = {"socket_connect_timeout": 2, "socket_timeout": 2}
            logger.info("Rate limiter using Redis backend")
        else:
            storage_uri = "memory://"
            storage_options = {}
            logger.info("Rate limiter using memory backend")

        limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=["200 per minute", "50 per 10 seconds"],
            storage_uri=storage_uri,
            storage_options=storage_options,
            strategy="fixed-window"
        )
        logger.info("Rate limiter initialized")
    except ImportError:
        limiter = None
        logger.warning("Flask-Limiter not installed, rate limiting disabled")

    def rate_limit(limit_str):
        if limiter:
            return limiter.limit(limit_str)
        return lambda f: f

    # Attach rate_limit to app so routes can import it
    app.rate_limit = rate_limit

    # Register blueprints
    app.register_blueprint(probes_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(admin_bp)

    # Apply rate limits to auth endpoints after blueprint registration
    if limiter:
        for endpoint, view_func in app.view_functions.items():
            if endpoint.endswith('.register') and hasattr(view_func, '__name__') and view_func.__name__ == 'register':
                limiter.limit("5 per minute")(view_func)
            if endpoint.endswith('.login') and hasattr(view_func, '__name__') and view_func.__name__ == 'login':
                limiter.limit("10 per minute")(view_func)

    # Before/After request hooks
    @app.before_request
    def before_request():
        request._start_time = time.time()
        request.id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        logger.info(f"[{request.id}] {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        duration = time.time() - getattr(request, '_start_time', time.time())
        record_request(request.method, request.path, response.status_code, duration)
        # Request tracing
        response.headers.add('X-Request-ID', getattr(request, 'id', 'unknown'))
        # Security headers
        response.headers.add('X-Content-Type-Options', 'nosniff')
        response.headers.add('X-Frame-Options', 'DENY')
        response.headers.add('X-XSS-Protection', '1; mode=block')
        response.headers.add('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        response.headers.add('Referrer-Policy', 'strict-origin-when-cross-origin')
        # CORS
        if request.path != '/metrics':
            origin = request.headers.get('Origin', '')
            allowed = ['http://localhost:5173', 'http://localhost:3000', 'http://bookstore.local']
            if any(origin.startswith(a) for a in allowed) or not origin:
                response.headers.add('Access-Control-Allow-Origin', origin or '*')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return json_response({"success": False, "error": {"code": "NOT_FOUND", "message": "Resource not found"}}, 404)

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Unhandled 500 error")
        return json_response({"success": False, "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}, 500)

    @app.errorhandler(Exception)
    def handle_exception(e):
        try:
            from flask_limiter.errors import RateLimitExceeded
            if isinstance(e, RateLimitExceeded):
                return json_response({"success": False, "error": {"code": "RATE_LIMITED", "message": str(e)}}, 429)
        except ImportError:
            pass
        logger.exception("Unhandled exception")
        return json_response({"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}, 500)

    # Graceful shutdown
    shutdown_requested = False

    def handle_signal(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True
        logger.info(f"Received signal {signum}, starting graceful shutdown...")
        import routes.probes as probes_module
        probes_module.shutdown_requested = True
        from utils.db import db_pool
        if db_pool:
            try:
                db_pool.closeall()
                logger.info("DB connection pool closed")
            except Exception as e:
                logger.warning(f"Error closing pool: {e}")
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Init DB
    init_pool()
    db_connected = init_database()
    logger.info(f"App initialized. DB connected: {db_connected}")

    return app


app = create_app()
