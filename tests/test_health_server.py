"""Tests of what the health server writes for a request."""

import threading
from http.server import HTTPServer
from unittest.mock import patch

import pytest
import requests

from src.health_server import HealthCheckHandler


@pytest.fixture
def health_url():
    server = HTTPServer(("127.0.0.1", 0), HealthCheckHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/health"
    server.shutdown()
    server.server_close()


def test_request_writes_nothing_to_stderr(health_url, capsys):
    """Test that a probe request adds no plain-text access line to the output."""
    requests.get(health_url, timeout=5)

    assert capsys.readouterr().err == ""


def test_request_is_a_debug_line_of_the_logger(health_url):
    """Test that the request is still visible at the debug level."""
    with patch("src.health_server.logger") as logger:
        requests.get(health_url, timeout=5)

    (line,) = [call.args[0] for call in logger.debug.call_args_list]
    assert line["msg"] == "Health server request"
    assert "GET /health" in line["value"]
