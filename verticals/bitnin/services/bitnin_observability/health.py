from __future__ import annotations

import json
import socket
import urllib.request
from typing import Any


class HealthChecker:
    """Checks health of BitNin dependencies (n8n, Ollama, Qdrant)."""

    def __init__(self, n8n_url: str, ollama_url: str, qdrant_url: str, searxng_url: str):
        self.n8n_url = n8n_url
        self.ollama_url = ollama_url
        self.qdrant_url = qdrant_url
        self.searxng_url = searxng_url

    def check_service(self, name: str, url: str, endpoint: str = "") -> dict[str, Any]:
        target_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            req = urllib.request.Request(target_url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                status = response.getcode()
                return {"service": name, "status": "UP", "code": status, "url": target_url}
        except Exception as e:
            return {"service": name, "status": "DOWN", "error": str(e), "url": target_url}

    def run_all(self, required: list[str] | None = None) -> dict[str, Any]:
        if required is None:
            required = ["ollama", "qdrant", "searxng"] # Default required for BitNin
            
        results = [
            self.check_service("n8n", self.n8n_url, endpoint=""),
            self.check_service("ollama", self.ollama_url, endpoint="/api/tags"),
            self.check_service("qdrant", self.qdrant_url, endpoint="/readyz"),
            self.check_service("searxng", self.searxng_url, endpoint=""),
        ]
        
        # Determine overall state based on requirements
        blocking_failed = False
        degraded = False
        
        for r in results:
            if r["service"] in required and r["status"] == "DOWN":
                blocking_failed = True
            elif r["status"] == "DOWN":
                r["status"] = "UNREACHABLE_BUT_NON_BLOCKING"
                degraded = True
            elif r["status"] == "UP" and r.get("code") != 200:
                # Potentially degraded but responding
                degraded = True
                
        if blocking_failed:
            overall = "DOWN"
        elif degraded:
            overall = "DEGRADED"
        else:
            overall = "UP"
            
        return {"overall": overall, "checks": results, "required": required}


if __name__ == "__main__":
    # Internal defaults based on SSOT (NiN specific: Qdrant 6335, SearXNG 8080)
    checker = HealthChecker(
        n8n_url="http://localhost:5688",
        ollama_url="http://localhost:11434",
        qdrant_url="http://localhost:6335",
        searxng_url="http://localhost:8080",
    )
    print(json.dumps(checker.run_all(required=["ollama", "qdrant", "searxng"]), indent=2))
