"""Fail-closed configuration contract for isolated PEFY integration services.

No secrets are printed, and missing provider configuration never implies readiness.
"""
import os
from urllib.parse import urlsplit

REQUIRED = {
    "neon": ("DATABASE_URL",),
    "clerk": ("CLERK_JWKS_URL", "CLERK_ISSUER", "CLERK_AUDIENCE"),
    "resend": ("RESEND_API_KEY", "RESEND_FROM_EMAIL"),
    "cloudflare": ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
    "r2_s3": ("R2_ACCOUNT_ID", "R2_BUCKET", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"),
    "firebase": ("FIREBASE_PROJECT_ID", "FIREBASE_SERVICE_ACCOUNT_JSON"),
    "ruflo": ("RUFLO_MCP_URL",),
}
URL_FIELDS = ("CLERK_JWKS_URL", "CLERK_ISSUER", "RUFLO_MCP_URL")

def readiness(env=None):
    env = os.environ if env is None else env
    report = {}
    for service, keys in REQUIRED.items():
        missing = [key for key in keys if not env.get(key)]
        invalid = []
        for key in keys:
            if key in URL_FIELDS and env.get(key):
                parsed = urlsplit(env[key])
                if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                    invalid.append(key)
        report[service] = {"ready": not missing and not invalid, "missing": missing, "invalid": invalid}
    return report

if __name__ == "__main__":
    import json
    print(json.dumps(readiness(), sort_keys=True))
