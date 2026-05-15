"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-15 08:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === books ===
    op.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id VARCHAR(10) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            isbn VARCHAR(20),
            price NUMERIC(10,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)")

    # === carts ===
    op.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # === cart_items ===
    op.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id SERIAL PRIMARY KEY,
            cart_id INTEGER REFERENCES carts(id) ON DELETE CASCADE,
            book_id VARCHAR(10) NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(cart_id, book_id)
        )
    """)

    # === orders ===
    op.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            total_amount NUMERIC(10,2) DEFAULT 0,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # === order_items ===
    op.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            book_id VARCHAR(10) NOT NULL,
            quantity INTEGER NOT NULL,
            price NUMERIC(10,2) NOT NULL,
            title VARCHAR(255),
            author VARCHAR(255)
        )
    """)

    # Seed sample data if books table is empty
    op.execute("""
        INSERT INTO books (id, title, author, isbn, price)
        VALUES
            ('1', 'Cloud Native Patterns', 'Cornelia Davis', '978-1492041153', 45.99),
            ('2', 'Kubernetes in Action', 'Marko Luksa', '978-1617293726', 49.99),
            ('3', 'Designing Data-Intensive Applications', 'Martin Kleppmann', '978-1449373320', 55.00),
            ('4', 'The Phoenix Project', 'Gene Kim', '978-1942788294', 24.99),
            ('5', 'Site Reliability Engineering', 'Betsy Beyer', '978-1491929124', 39.99)
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS order_items")
    op.execute("DROP TABLE IF EXISTS orders")
    op.execute("DROP TABLE IF EXISTS cart_items")
    op.execute("DROP TABLE IF EXISTS carts")
    op.execute("DROP TABLE IF EXISTS books")
