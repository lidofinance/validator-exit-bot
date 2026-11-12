"""Unit tests for the container health probe."""

import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

import pytest

from src import healthcheck


def _serve(status: int) -> HTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(status)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture
def healthy_server():
    server = _serve(200)
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def stale_server():
    server = _serve(503)
    yield server
    server.shutdown()
    server.server_close()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TestProbe:
    """Test the probe exit code for each state of the health server."""

    def test_probe_returns_zero_on_200(self, healthy_server):
        """Test that a fresh pulse (200) is a passed probe."""
        url = f"http://127.0.0.1:{healthy_server.server_port}/health"
        assert healthcheck.probe(url) == 0

    def test_probe_returns_one_on_503(self, stale_server):
        """Test that a stale pulse (503) is a failed probe."""
        url = f"http://127.0.0.1:{stale_server.server_port}/health"
        assert healthcheck.probe(url) == 1

    def test_probe_returns_one_when_nothing_listens(self):
        """Test that a closed port is a failed probe, not an exception."""
        assert healthcheck.probe(f"http://127.0.0.1:{_free_port()}/health") == 1


class TestMain:
    """Test that the probe targets the health server of this container."""

    def test_main_reads_server_port(self, healthy_server, monkeypatch):
        """Test that SERVER_PORT selects the port."""
        monkeypatch.setenv("SERVER_PORT", str(healthy_server.server_port))
        assert healthcheck.main() == 0

    def test_main_uses_the_default_port(self, monkeypatch):
        """Test that the probe asks port 9010 when SERVER_PORT is not set."""
        monkeypatch.delenv("SERVER_PORT", raising=False)

        with patch("src.healthcheck.probe", return_value=0) as mock_probe:
            assert healthcheck.main() == 0

        mock_probe.assert_called_once_with("http://127.0.0.1:9010/health")

    def test_main_fails_on_another_port(self, healthy_server, monkeypatch):
        """Test that the probe does not pass when SERVER_PORT points elsewhere."""
        monkeypatch.setenv("SERVER_PORT", str(_free_port()))
        assert healthcheck.main() == 1
