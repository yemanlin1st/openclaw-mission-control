import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "pefy/integrations/omega_service_contract.py"
spec = importlib.util.spec_from_file_location("omega_service_contract", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ContractTests(unittest.TestCase):
    def test_missing_configuration_fails_closed(self):
        report = module.readiness({})
        self.assertTrue(all(not entry["configured"] for entry in report.values()))
    def test_configuration_is_not_live_verification(self):
        env = {key: "configured" for keys in module.REQUIRED.values() for key in keys}
        env["CLERK_JWKS_URL"] = "https://clerk.example.com/jwks"
        env["CLERK_ISSUER"] = "https://clerk.example.com"
        env["RUFLO_MCP_URL"] = "https://ruflo.example.com/mcp"
        report = module.readiness(env)
        self.assertTrue(all(entry["configured"] for entry in report.values()))
        self.assertTrue(all(not entry["verified_live"] for entry in report.values()))

    def test_r2_is_single_s3_compatible_service(self):
        self.assertIn("r2_s3", module.REQUIRED)
        self.assertNotIn("r2", module.REQUIRED)
    def test_invalid_jwks_url_is_rejected(self):
        env = {key: "configured" for keys in module.REQUIRED.values() for key in keys}
        env["CLERK_JWKS_URL"] = "http://localhost/jwks"
        self.assertIn("CLERK_JWKS_URL", module.readiness(env)["clerk"]["invalid"])
if __name__ == "__main__":
    unittest.main()
