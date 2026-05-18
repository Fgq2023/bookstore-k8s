"""pytest fixtures."""
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
