"""Add updated_at, stock_quantity, and order status constraints

Revision ID: 002
Revises: 001
Create Date: 2026-05-15 14:00:00.000000

"""
from alembic import op

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add updated_at to all tables
    for table in ['books', 'carts', 'cart_items', 'orders', 'order_items']:
        op.execute(f"""
            ALTER TABLE {table}
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)

    # Add stock_quantity to books
    op.execute("""
        ALTER TABLE books
        ADD COLUMN IF NOT EXISTS stock_quantity INTEGER DEFAULT 100
    """)

    # Add status_history to orders (JSON field for audit trail)
    op.execute("""
        ALTER TABLE orders
        ADD COLUMN IF NOT EXISTS status_history JSONB DEFAULT '[]'::jsonb
    """)

    # Create trigger function for auto-updating updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)

    # Attach triggers to all tables
    for table in ['books', 'carts', 'cart_items', 'orders', 'order_items']:
        op.execute(f"""
            DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table};
            CREATE TRIGGER trg_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
        """)

    # Add constraint for order status values
    op.execute("""
        ALTER TABLE orders
        DROP CONSTRAINT IF EXISTS chk_order_status;
        ALTER TABLE orders
        ADD CONSTRAINT chk_order_status
        CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled'))
    """)

    # Update existing books with stock
    op.execute("""
        UPDATE books SET stock_quantity = 100 WHERE stock_quantity IS NULL
    """)

    # Add index on orders.status for faster queries
    op.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")


def downgrade() -> None:
    # Remove triggers
    for table in ['books', 'carts', 'cart_items', 'orders', 'order_items']:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Remove columns
    for table in ['books', 'carts', 'cart_items', 'orders', 'order_items']:
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS updated_at")

    op.execute("ALTER TABLE books DROP COLUMN IF EXISTS stock_quantity")
    op.execute("ALTER TABLE orders DROP COLUMN IF EXISTS status_history")
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS chk_order_status")
    op.execute("DROP INDEX IF EXISTS idx_orders_status")
