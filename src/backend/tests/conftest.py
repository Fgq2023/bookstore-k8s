"""pytest fixtures."""
import os
import socket
import threading
import time
import pytest
from unittest.mock import MagicMock, patch
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_db():
    """Returns a mock DB connection and a patch context for utils.db.get_db_connection."""
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    # Make context manager work for with-statements if any
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)

    patcher = patch('utils.db.get_db_connection', return_value=conn)
    patcher.start()
    yield conn, cur
    patcher.stop()


@pytest.fixture
def mock_db_pool():
    """Patches the db_pool to simulate DB_AVAILABLE=True and returns mock connection."""
    import utils.db as db_module
    original_pool = db_module.db_pool
    original_available = db_module.DB_AVAILABLE

    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    conn.closed = 0
    conn.autocommit = True

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = conn

    db_module.db_pool = mock_pool
    db_module.DB_AVAILABLE = True

    yield conn, cur

    db_module.db_pool = original_pool
    db_module.DB_AVAILABLE = original_available


# =============================================================================
# Integration / E2E fixtures (real PostgreSQL via testcontainers)
# =============================================================================

@pytest.fixture(scope="session")
def postgres_container():
    """Spin up a real PostgreSQL container for integration tests.

    Skips if testcontainers or Docker is unavailable.
    """
    pytest.importorskip("testcontainers")
    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers[postgres] not installed")

    try:
        with PostgresContainer("postgres:15-alpine") as postgres:
            yield postgres
    except Exception as exc:
        pytest.skip(f"Could not start PostgreSQL container: {exc}")


@pytest.fixture(scope="module")
def real_db_app(postgres_container):
    """Flask app configured to use the testcontainers PostgreSQL."""
    import utils.db as db_module

    old_environ = dict(os.environ)
    old_db_config = dict(db_module.DB_CONFIG)
    old_db_pool = db_module.db_pool
    old_db_available = db_module.DB_AVAILABLE

    db_host = postgres_container.get_container_host_ip()
    db_port = str(postgres_container.get_exposed_port(5432))
    db_name = postgres_container.dbname
    db_user = postgres_container.username
    db_pass = postgres_container.password

    # 1. Update environment variables
    os.environ.update({
        'DB_HOST': db_host,
        'DB_PORT': db_port,
        'POSTGRES_DB': db_name,
        'POSTGRES_USER': db_user,
        'POSTGRES_PASSWORD': db_pass,
        'APP_ENV': 'testing',
        'LOG_LEVEL': 'warning',
    })

    # 2. Update utils.db module-level config (already imported by conftest)
    db_module.DB_CONFIG.update({
        'host': db_host,
        'port': db_port,
        'dbname': db_name,
        'user': db_user,
        'password': db_pass,
    })
    db_module.db_pool = None
    db_module.DB_AVAILABLE = True

    # 3. Run alembic migrations
    from alembic.config import Config
    from alembic import command
    cfg = Config("alembic.ini")
    db_url = (
        f"postgresql+psycopg2://{db_user}:"
        f"{db_pass}@{db_host}:"
        f"{db_port}/{db_name}"
    )
    cfg.set_main_option("sqlalchemy.url", db_url.replace('%', '%%'))
    command.upgrade(cfg, "head")

    # 4. Create app with fresh DB config
    from app import create_app
    app = create_app()

    yield app

    # Cleanup
    if db_module.db_pool:
        db_module.db_pool.closeall()
    db_module.DB_CONFIG = old_db_config
    db_module.db_pool = old_db_pool
    db_module.DB_AVAILABLE = old_db_available

    os.environ.clear()
    os.environ.update(old_environ)


@pytest.fixture
def real_db_client(real_db_app):
    """Flask test client connected to real PostgreSQL."""
    real_db_app.config['TESTING'] = True
    with real_db_app.test_client() as client:
        yield client


@pytest.fixture
def live_server(real_db_app):
    """Run Flask app on a background thread for E2E HTTP tests."""
    from werkzeug.serving import make_server

    # Find free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    server = make_server("127.0.0.1", port, real_db_app, threaded=True)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    time.sleep(0.3)  # Let server start

    yield f"http://127.0.0.1:{port}"

    server.shutdown()


# =============================================================================
# Pytest hooks
# =============================================================================

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test with real DB")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
