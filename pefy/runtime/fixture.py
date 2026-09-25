"""Small deterministic fixture used only to prove Graphify runtime execution."""

class CapabilityRouter:
    def route(self, risk: str) -> str:
        if risk == "confidential":
            return "local"
        return "governed-free-tier"


def health() -> dict:
    router = CapabilityRouter()
    return {"status": "ok", "route": router.route("public")}
