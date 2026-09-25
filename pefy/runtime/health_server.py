#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STARTED_AT = time.time()
RESULT = {"status": "initializing", "graphify": {}, "agentswarms": {}, "providers": {}, "supabase": {}}

PROVIDERS = {
    "openai": {"env": "OPENAI_API_KEY", "url": "https://api.openai.com/v1/models", "auth": "bearer"},
    "nvidia": {"env": "NVIDIA_API_KEY", "url": "https://integrate.api.nvidia.com/v1/models", "auth": "bearer"},
    "openrouter": {"env": "OPENROUTER_API_KEY", "url": "https://openrouter.ai/api/v1/models", "auth": "bearer"},
    "groq": {"env": "GROQ_API_KEY", "url": "https://api.groq.com/openai/v1/models", "auth": "bearer"},
    "huggingface": {"env": "HF_TOKEN", "url": "https://huggingface.co/api/whoami-v2", "auth": "bearer"},
    "gemini": {"env": "GEMINI_API_KEY", "url": "https://generativelanguage.googleapis.com/v1beta/models", "auth": "query-key"},
}

def http_probe(url, token=None, auth=None):
    actual = url
    headers = {"User-Agent": "PEFY-Capability-Health/1.0"}
    if token and auth == "bearer":
        headers["Authorization"] = f"Bearer {token}"
    elif token and auth == "query-key":
        sep = "&" if "?" in actual else "?"
        actual = f"{actual}{sep}key={token}"
    req = urllib.request.Request(actual, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            return {"reachable": True, "http_status": response.status, "credential_valid": bool(token)}
    except urllib.error.HTTPError as exc:
        return {"reachable": exc.code < 500, "http_status": exc.code, "credential_valid": False if token else None}
    except Exception as exc:
        return {"reachable": False, "http_status": None, "credential_valid": False if token else None, "error_type": type(exc).__name__}

def verify_graphify():
    binary = shutil.which("graphify")
    base = {"installed": bool(binary), "version_pin": os.getenv("GRAPHIFY_VERSION", "unknown"), "binary": bool(binary), "execution_verified": False}
    if not binary:
        return base
    try:
        with tempfile.TemporaryDirectory(prefix="pefy-graphify-") as td:
            root = Path(td)
            shutil.copy("/opt/pefy/fixture.py", root / "fixture.py")
            proc = subprocess.run([binary, str(root)], cwd=td, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=90, env=os.environ.copy())
            candidates = [root / "graphify-out" / "graph.json", Path(td) / "graphify-out" / "graph.json"]
            graph_exists = any(p.exists() for p in candidates)
            base.update({"exit_code": proc.returncode, "graph_json_created": graph_exists, "execution_verified": proc.returncode == 0 and graph_exists, "diagnostic_tail": proc.stdout[-1200:]})
    except subprocess.TimeoutExpired:
        base["diagnostic_tail"] = "Graphify self-test timed out after 90 seconds."
    except Exception as exc:
        base["diagnostic_tail"] = f"{type(exc).__name__}: {exc}"
    return base

def verify_agentswarms():
    home = Path(os.getenv("AGENTSWARMS_HOME", "/opt/agentswarms"))
    expected = os.getenv("AGENTSWARMS_COMMIT", "")
    package = home / "package.json"
    node_modules = home / "node_modules"
    actual = None
    try:
        actual = subprocess.check_output(["git", "-C", str(home), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    except Exception:
        pass

    audit_counts = {"info": 0, "low": 0, "moderate": 0, "high": 0, "critical": 0, "total": 0}
    audit_path = Path("/opt/pefy/agentswarms-npm-audit-prod.json")
    if audit_path.exists():
        try:
            audit = json.loads(audit_path.read_text())
            meta = audit.get("metadata", {}).get("vulnerabilities", {})
            for key in audit_counts:
                audit_counts[key] = int(meta.get(key, 0) or 0)
        except Exception:
            audit_counts["parse_error"] = True

    supply_chain_gate = audit_counts.get("critical", 0) == 0 and audit_counts.get("high", 0) == 0
    runtime_requested = os.getenv("AGENTSWARMS_ENABLED", "false").lower() == "true"

    return {
        "installed": package.exists() and node_modules.exists(),
        "source_present": package.exists(),
        "dependencies_installed": node_modules.exists(),
        "expected_commit": expected,
        "actual_commit": actual,
        "revision_verified": bool(actual and expected and actual == expected),
        "license": "Elastic-2.0",
        "mode": "internal-governed-workbench",
        "production_dependency_audit": audit_counts,
        "supply_chain_gate_passed": supply_chain_gate,
        "application_runtime_requested": runtime_requested,
        "application_runtime_enabled": runtime_requested and supply_chain_gate,
    }

def verify_supabase():
    names = ["SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_SERVICE_ROLE_KEY", "PROVIDER_CREDS_SECRET"]
    presence = {name: bool(os.getenv(name)) for name in names}
    return {"dedicated_backend_configured": all(presence.values()), "variables_present": presence, "secret_values_exposed": False}

def verify_providers():
    result = {}
    for name, spec in PROVIDERS.items():
        token = os.getenv(spec["env"])
        probe = http_probe(spec["url"], token=token, auth=spec["auth"])
        result[name] = {"credential_present": bool(token), **probe}
    for name, env_name in (("ollama", "OLLAMA_BASE_URL"), ("vllm", "VLLM_BASE_URL")):
        url = os.getenv(env_name)
        if url:
            probe = http_probe(url.rstrip("/") + "/v1/models")
            result[name] = {"configured": True, **probe}
        else:
            result[name] = {"configured": False, "reachable": None}
    return result

def run_checks():
    RESULT["graphify"] = verify_graphify()
    RESULT["agentswarms"] = verify_agentswarms()
    RESULT["supabase"] = verify_supabase()
    RESULT["providers"] = verify_providers()
    core_ok = RESULT["graphify"].get("installed") and RESULT["agentswarms"].get("installed") and RESULT["agentswarms"].get("revision_verified")
    RESULT["status"] = "ok" if core_ok else "degraded"
    RESULT["checked_at_unix"] = int(time.time())

class Handler(BaseHTTPRequestHandler):
    def _write(self, code, body):
        raw = json.dumps(body, indent=2, sort_keys=True).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/health":
            self._write(200 if RESULT["status"] in {"ok", "initializing"} else 503, {"status": RESULT["status"], "uptime_seconds": int(time.time() - STARTED_AT)})
            return
        if self.path == "/status":
            safe = dict(RESULT)
            safe["uptime_seconds"] = int(time.time() - STARTED_AT)
            self._write(200, safe)
            return
        if self.path == "/refresh":
            threading.Thread(target=run_checks, daemon=True).start()
            self._write(202, {"status": "refreshing"})
            return
        self._write(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        print("health_http", fmt % args, flush=True)

if __name__ == "__main__":
    threading.Thread(target=run_checks, daemon=True).start()
    port = int(os.getenv("PORT", "8080"))
    print(f"PEFY capability health server listening on {port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
