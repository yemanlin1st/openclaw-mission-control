"""Conservative public API client: explicit allowlist, no credentials, bounded responses."""
import ipaddress
import json
import socket
import urllib.parse
import urllib.request

ALLOWED_HOSTS = frozenset({"api.worldbank.org", "restcountries.com"})
MAX_BYTES = 1_000_000

def fetch_public_json(url: str):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("HTTPS URL without embedded credentials or custom port required")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise ValueError("API host not approved")
    if parsed.fragment:
        raise ValueError("Fragments not permitted")
    for result in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
        address = ipaddress.ip_address(result[4][0])
        if not address.is_global:
            raise ValueError("Non-public destination blocked")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ValueError("Redirects are disabled")
    opener = urllib.request.build_opener(NoRedirect())
    request = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"PEFY-PublicAPI-Gateway/0.1"})
    with opener.open(request, timeout=5) as response:
        if response.status != 200:
            raise ValueError("Unexpected upstream status")
        if "json" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("Unexpected content type")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Response too large")
        return json.loads(data)
