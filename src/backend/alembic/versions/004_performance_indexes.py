"""Add performance indexes for books, orders, and cart_items

Revision ID: 004
Revises: 003
Create Date: 2026-05-18 21:00:00.000000

"""
from alembic import op

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite index for book search (title + author)
    op.execute("CREATE INDEX IF NOT EXISTS idx_books_title_author ON books(title, author)")
    # ISBN lookup index
    op.execute("CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn)")
    # Orders by session + time (for order history)
    op.execute("CREATE INDEX IF NOT EXISTS idx_orders_session_created ON orders(session_id, created_at DESC)")
    # Cart items lookup
    op.execute("CREATE INDEX IF NOT EXISTS idx_cart_items_cart_book ON cart_items(cart_id, book_id)")
    # Order items lookup
    op.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_order_items_order")
    op.execute("DROP INDEX IF EXISTS idx_cart_items_cart_book")
    op.execute("DROP INDEX IF EXISTS idx_orders_session_created")
    op.execute("DROP INDEX IF EXISTS idx_books_isbn")
    op.execute("DROP INDEX IF EXISTS idx_books_title_author")
