"""Add users table for JWT authentication

Revision ID: 003
Revises: 002
Create Date: 2026-05-18 20:00:00.000000

"""
from alembic import op

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Trigger for updated_at
    op.execute("""
        DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
        CREATE TRIGGER trg_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
    """)

    # Add user_id to carts and orders (nullable for backward compat with session-based carts)
    op.execute("""
        ALTER TABLE carts
        ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
    """)
    op.execute("""
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
    """)

    # Indexes for auth lookups and user-scoped queries
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_carts_user_id ON carts(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_orders_user_id")
    op.execute("DROP INDEX IF EXISTS idx_carts_user_id")
    op.execute("DROP INDEX IF EXISTS idx_users_email")
    op.execute("DROP INDEX IF EXISTS idx_users_username")

    op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS user_id")
    op.execute("ALTER TABLE carts DROP COLUMN IF EXISTS user_id")

    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users")
    op.execute("DROP TABLE IF EXISTS users")
