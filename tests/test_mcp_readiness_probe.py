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

    def test_external_upstream_rejected(self):
        old = probe.UPSTREAM
        try:
            probe.UPSTREAM = "https://example.org/health"
            self.assertFalse(probe.upstream_ready())
        finally:
            probe.UPSTREAM = old

if __name__ == "__main__":
    unittest.main()
