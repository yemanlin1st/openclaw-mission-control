"""Fail-closed admin endpoint regression tests; no external provider calls."""
import importlib.util
import json
import os
from pathlib import Path
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "pefy" / "runtime" / "graphify_health_server.py"
spec = importlib.util.spec_from_file_location("graphify_health_under_test", MODULE_PATH)
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)

class GraphifyAdminSecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), target.H)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method, path, auth=None):
        headers = {} if auth is None else {"Authorization": auth}
        conn = HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        body = response.read()
        status = response.status
        conn.close()
        return status, body

    def test_public_health_only(self):
        status, data = self.request("GET", "/health")
        self.assertIn(status, (200, 503))
        self.assertIn("status", json.loads(data))

    def test_status_fails_closed_when_admin_token_missing(self):
        with patch.dict(os.environ, {"PEFY_GRAPHIFY_ADMIN_TOKEN": ""}):
            self.assertEqual(self.request("GET", "/status")[0], 503)

    def test_status_requires_valid_bearer(self):
        with patch.dict(os.environ, {"PEFY_GRAPHIFY_ADMIN_TOKEN": "testsecret"}):
            self.assertEqual(self.request("GET", "/status")[0], 401)
            self.assertEqual(self.request("GET", "/status", "Bearer wrong")[0], 401)
            self.assertEqual(self.request("GET", "/status", "Bearer testsecret")[0], 200)

    def test_refresh_cannot_be_triggered_by_get(self):
        with patch.dict(os.environ, {"PEFY_GRAPHIFY_ADMIN_TOKEN": "testsecret"}):
            self.assertEqual(self.request("GET", "/refresh", "Bearer testsecret")[0], 405)

    def test_refresh_requires_admin_and_is_single_flight(self):
        with patch.dict(os.environ, {"PEFY_GRAPHIFY_ADMIN_TOKEN": "testsecret"}):
            self.assertEqual(self.request("POST", "/refresh")[0], 401)
            self.assertEqual(self.request("POST", "/refresh", "Bearer wrong")[0], 401)
            self.assertTrue(target._REFRESH_LOCK.acquire(timeout=1))
            try:
                self.assertEqual(self.request("POST", "/refresh", "Bearer testsecret")[0], 409)
            finally:
                target._REFRESH_LOCK.release()
            done = threading.Event()
            with patch.object(target, "run_checks", side_effect=lambda: done.set()):
                self.assertEqual(self.request("POST", "/refresh", "Bearer testsecret")[0], 202)
                self.assertTrue(done.wait(2))

    def test_unknown_path_returns_404(self):
        self.assertEqual(self.request("GET", "/not-here")[0], 404)

if __name__ == "__main__":
    unittest.main()
