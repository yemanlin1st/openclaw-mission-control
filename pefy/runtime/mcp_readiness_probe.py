"""Isolated readiness probe for the PEFY MCP gateway.

This probe reports readiness only when an independently managed MCP
upstream has passed its own health check. It does not execute agent code.
"""
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
UPSTREAM = os.environ.get("MCP_UPSTREAM_HEALTH_URL", "")
TIMEOUT = float(os.environ.get("MCP_HEALTH_TIMEOUT", "2"))

def upstream_ready():
    if not UPSTREAM or not UPSTREAM.startswith(("http://127.0.0.1:", "http://localhost:")):
        return False
    try:
        with urllib.request.urlopen(UPSTREAM, timeout=TIMEOUT) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/healthz", "/readyz"):
            self.send_error(404)
            return
        ready = self.path == "/healthz" or upstream_ready()
        body = json.dumps({"status": "ok" if ready else "not_ready"}).encode()
        self.send_response(200 if ready else 503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
