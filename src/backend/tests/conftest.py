"""Pytest fixtures and configuration for bookstore backend tests."""
import pytest
import threading
import time
import sys
import os

# Ensure main.py can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import ThreadedHTTPServer, BookstoreAPI


@pytest.fixture(scope="session")
def test_server():
    """Start a test server in fallback mode (no DB required)."""
    server = ThreadedHTTPServer(("127.0.0.1", 0), BookstoreAPI)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    time.sleep(0.3)  # wait for server to start
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    thread.join(timeout=2)
