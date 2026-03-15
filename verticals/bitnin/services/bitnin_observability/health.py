from __future__ import annotations

import json
import socket
import urllib.request
from typing import Any


class HealthChecker:
    """Checks health of BitNin dependencies (n8n, Ollama, Qdrant)."""

    def __init__(self, n8n_url: str, ollama_url: str, qdrant_url: str):
        self.n8n_url = n8n_url
        self.ollama_url = ollama_url
        self.qdrant_url = qdrant_url

    def check_service(self, name: str, url: str) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                status = response.getcode()
                return {"service": name, "status": "UP", "code": status}
        except Exception as e:
            return {"service": name, "status": "DOWN", "error": str(e)}

    def run_all(self) -> dict[str, Any]:
        results = [
            self.check_service("n8n", self.n8n_url),
            self.check_service("ollama", self.ollama_url),
            self.check_service("qdrant", self.qdrant_url),
        ]
        overall = "UP" if all(r["status"] == "UP" for r in results) else "DEGRADED"
        return {"overall": overall, "checks": results}


if __name__ == "__main__":
    # Internal defaults based on SSOT (Unified to 6333)
    checker = HealthChecker(
        n8n_url="http://localhost:5688",
        ollama_url="http://host.docker.internal:11434",
        qdrant_url="http://localhost:6333",
    )
    print(json.dumps(checker.run_all(), indent=2))
