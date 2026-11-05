"""Conservative public API client: explicit allowlist, no credentials, bounded responses."""
import ipaddress
import json
import socket
import ssl
import http.client
import urllib.parse

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
    addresses = {result[4][0] for result in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError("Non-public destination blocked")
    address = sorted(addresses)[0]
    class PinnedHTTPSConnection(http.client.HTTPSConnection):
        def connect(self):
            raw = socket.create_connection((address, 443), timeout=5)
            self.sock = self._context.wrap_socket(raw, server_hostname=host)
    conn = PinnedHTTPSConnection(host, port=443, timeout=5, context=ssl.create_default_context())
    try:
        target = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
        conn.request("GET", target, headers={"Accept": "application/json", "User-Agent": "PEFY-PublicAPI-Gateway/0.2", "Host": host})
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError("Unexpected upstream status or redirect")
        if "json" not in response.getheader("Content-Type", "").lower():
            raise ValueError("Unexpected content type")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Response too large")
        return json.loads(data)
    finally:
        conn.close()
