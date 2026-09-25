#!/usr/bin/env python3
import json, os, shutil, subprocess, tempfile, threading, time, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STARTED_AT=time.time()
RESULT={"status":"initializing","graphify":{},"providers":{}}

PROVIDERS={
 "openai":{"env":"OPENAI_API_KEY","url":"https://api.openai.com/v1/models","auth":"bearer"},
 "nvidia":{"env":"NVIDIA_API_KEY","url":"https://integrate.api.nvidia.com/v1/models","auth":"bearer"},
 "openrouter":{"env":"OPENROUTER_API_KEY","url":"https://openrouter.ai/api/v1/models","auth":"bearer"},
 "groq":{"env":"GROQ_API_KEY","url":"https://api.groq.com/openai/v1/models","auth":"bearer"},
 "huggingface":{"env":"HF_TOKEN","url":"https://huggingface.co/api/whoami-v2","auth":"bearer"},
 "gemini":{"env":"GEMINI_API_KEY","url":"https://generativelanguage.googleapis.com/v1beta/models","auth":"query-key"},
}

def probe(url, token=None, auth=None):
    actual=url
    headers={"User-Agent":"PEFY-Graphify-Health/1.0"}
    if token and auth=="bearer":
        headers["Authorization"]=f"Bearer {token}"
    elif token and auth=="query-key":
        actual += ("&" if "?" in actual else "?") + "key=" + token
    try:
        with urllib.request.urlopen(urllib.request.Request(actual,headers=headers),timeout=12) as r:
            return {"reachable":True,"http_status":r.status,"credential_valid":bool(token) if token else None}
    except urllib.error.HTTPError as e:
        return {"reachable":e.code < 500,"http_status":e.code,"credential_valid":False if token else None}
    except Exception as e:
        return {"reachable":False,"http_status":None,"credential_valid":False if token else None,"error_type":type(e).__name__}

def verify_graphify():
    binary=shutil.which("graphify")
    result={"installed":bool(binary),"version_pin":os.getenv("GRAPHIFY_VERSION","unknown"),"execution_verified":False,"graph_json_created":False}
    if not binary:
        return result
    try:
        with tempfile.TemporaryDirectory(prefix="pefy-graphify-") as td:
            root=Path(td)
            shutil.copy("/opt/pefy/fixture.py",root/"fixture.py")
            proc=subprocess.run([binary,str(root)],cwd=td,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120,env=os.environ.copy())
            candidates=[root/"graphify-out"/"graph.json",Path(td)/"graphify-out"/"graph.json"]
            created=any(p.exists() for p in candidates)
            result.update({"exit_code":proc.returncode,"graph_json_created":created,"execution_verified":proc.returncode==0 and created,"diagnostic_tail":proc.stdout[-1600:]})
    except subprocess.TimeoutExpired:
        result["diagnostic_tail"]="Graphify self-test timed out."
    except Exception as e:
        result["diagnostic_tail"]=f"{type(e).__name__}: {e}"
    return result

def verify_providers():
    out={}
    for name,spec in PROVIDERS.items():
        token=os.getenv(spec["env"])
        out[name]={"credential_present":bool(token),**probe(spec["url"],token,spec["auth"])}
    for name,env_name in (("ollama","OLLAMA_BASE_URL"),("vllm","VLLM_BASE_URL")):
        url=os.getenv(env_name)
        out[name]={"configured":bool(url),"reachable":None} if not url else {"configured":True,**probe(url.rstrip("/")+"/v1/models")}
    return out

def run_checks():
    RESULT["graphify"]=verify_graphify()
    RESULT["providers"]=verify_providers()
    RESULT["status"]="ok" if RESULT["graphify"].get("execution_verified") else "degraded"
    RESULT["checked_at_unix"]=int(time.time())
    Path("/opt/pefy/runtime-status.json").write_text(json.dumps(RESULT,indent=2,sort_keys=True))
    print("PEFY graphify/provider checks: "+json.dumps({
      "status":RESULT["status"],
      "graphify_execution_verified":RESULT["graphify"].get("execution_verified"),
      "graph_json_created":RESULT["graphify"].get("graph_json_created"),
      "provider_credentials":{k:v.get("credential_present",v.get("configured")) for k,v in RESULT["providers"].items()}
    },sort_keys=True),flush=True)

class H(BaseHTTPRequestHandler):
    def sendj(self,code,obj):
        raw=json.dumps(obj,indent=2,sort_keys=True).encode()
        self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path=="/health":
            self.sendj(200 if RESULT["status"]=="ok" else 503,{"status":RESULT["status"],"uptime_seconds":int(time.time()-STARTED_AT)}); return
        if self.path=="/status":
            self.sendj(200,{**RESULT,"uptime_seconds":int(time.time()-STARTED_AT)}); return
        if self.path=="/refresh":
            threading.Thread(target=run_checks,daemon=True).start(); self.sendj(202,{"status":"refreshing"}); return
        self.sendj(404,{"error":"not_found"})
    def log_message(self,fmt,*args): print("health_http",fmt%args,flush=True)

if __name__=="__main__":
    threading.Thread(target=run_checks,daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0",int(os.getenv("PORT","8080"))),H).serve_forever()
