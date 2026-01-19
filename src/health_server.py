import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
import structlog

import src.variables as variables

logger = structlog.get_logger(__name__)

_last_pulse = datetime.now()


def pulse():
    try:
        requests.get(f"http://localhost:{variables.SERVER_PORT}/pulse/", timeout=10)
    except requests.exceptions.ConnectionError as error:
        logger.warning(
            {"msg": "Healthcheck server is not responding.", "error": str(error)}
        )


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler with a simple health check endpoint."""

    def do_GET(self):
        global _last_pulse

        if self.path == "/pulse/":
            _last_pulse = datetime.now()
        if datetime.now() - _last_pulse > timedelta(minutes=10):
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b'{"metrics": "fail", "reason": "timeout exceeded"}\n')
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"metrics": "ok", "reason": "ok"}\n')


def _run_server(port: int):
    """Start the HTTP server (blocking)."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    logger.info(f"Health check available at http://localhost:{port}/health")
    httpd.serve_forever()


def start_health_server(port: int):
    """Start the HTTP server in a background thread."""
    logger.info(f"Starting HTTP server on port {port}")
    server_thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    server_thread.start()
    return server_thread
