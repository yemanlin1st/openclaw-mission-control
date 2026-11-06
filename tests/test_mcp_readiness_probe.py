import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "pefy/runtime/mcp_readiness_probe.py"
spec = importlib.util.spec_from_file_location("mcp_readiness_probe", path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class ReadinessTests(unittest.TestCase):
    def test_unconfigured_upstream_fails_closed(self):
        old = probe.UPSTREAM
        try:
            probe.UPSTREAM = ""
            self.assertFalse(probe.upstream_ready())
        finally:
            probe.UPSTREAM = old

    def test_loopback_userinfo_rejected(self):
        old = probe.UPSTREAM
        try:
            probe.UPSTREAM = "http://evil@localhost:8080/readyz"
            self.assertFalse(probe.upstream_ready())
        finally:
            probe.UPSTREAM = old

    def test_loopback_redirect_not_followed(self):
        from unittest.mock import patch
        old = probe.UPSTREAM
        try:
            probe.UPSTREAM = "http://127.0.0.1:8080/readyz"
            with patch.object(probe.urllib.request, "build_opener") as mocked:
                mocked.return_value.open.side_effect = probe.urllib.error.HTTPError(probe.UPSTREAM, 302, "redirect", {}, None)
                self.assertFalse(probe.upstream_ready())
        finally:
            probe.UPSTREAM = old

    def test_external_upstream_rejected(self):
        old = probe.UPSTREAM
        try:
            probe.UPSTREAM = "https://example.org/health"
            self.assertFalse(probe.upstream_ready())
        finally:
            probe.UPSTREAM = old

if __name__ == "__main__":
    unittest.main()
