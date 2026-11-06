import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / "pefy/integrations/public_api_gateway.py"
spec = importlib.util.spec_from_file_location("public_api_gateway", p)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

class GatewayTests(unittest.TestCase):
    def test_reject_local_address(self):
        with self.assertRaises(ValueError):
            api.fetch_public_json("https://127.0.0.1/private")
    def test_reject_http(self):
        with self.assertRaises(ValueError):
            api.fetch_public_json("http://api.worldbank.org")
    def test_reject_unapproved_host(self):
        with self.assertRaises(ValueError):
            api.fetch_public_json("https://example.com/")
    def test_reject_nonstandard_port(self):
        with self.assertRaises(ValueError):
            api.fetch_public_json("https://api.worldbank.org:8443/")
    def test_reject_fragment(self):
        with self.assertRaises(ValueError):
            api.fetch_public_json("https://api.worldbank.org/#fragment")
    def test_reject_embedded_credentials(self):
        with self.assertRaises(ValueError):
            api.fetch_public_json("https://user:password@api.worldbank.org/")
if __name__ == "__main__":
    unittest.main()
