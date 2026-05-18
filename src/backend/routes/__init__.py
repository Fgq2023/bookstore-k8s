"""Register all blueprints."""
from .probes import probes_bp
from .books import books_bp
from .cart import cart_bp
from .orders import orders_bp
from .auth import auth_bp
from .payments import payments_bp
from .admin import admin_bp

__all__ = ['probes_bp', 'books_bp', 'cart_bp', 'orders_bp', 'auth_bp', 'payments_bp', 'admin_bp']
