import structlog
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = structlog.get_logger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler with a simple health check endpoint."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Not Found"}')


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
