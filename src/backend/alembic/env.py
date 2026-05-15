"""Alembic environment configuration.

Uses environment variables for DB connection (same as main.py).
Migrations use raw SQL via op.execute() — no SQLAlchemy ORM required.
"""
import os
import sys
from logging.config import fileConfig
from urllib.parse import quote_plus

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add parent dir to path so we can import main if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build DB URL from environment (same vars as main.py)
DB_HOST = os.getenv('DB_HOST', 'bookstore-db')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'bookstore')
DB_USER = os.getenv('POSTGRES_USER', 'bookstore_user')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'SecureP@ssw0rd!2026')

DB_URL = f"postgresql+psycopg2://{quote_plus(DB_USER)}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# Escape '%' for ConfigParser interpolation; it will unescape when read back
config.set_main_option('sqlalchemy.url', DB_URL.replace('%', '%%'))

# We use raw SQL migrations; no SQLAlchemy ORM metadata needed
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
