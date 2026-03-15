from __future__ import annotations

import json
import os
import urllib.request
import urllib.parse
from dataclasses import dataclass
from typing import Any


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_ANALYST_MODEL = "qwen2.5:14b"


@dataclass(frozen=True)
class LLMResult:
    model_name: str
    raw_response: dict[str, Any]
    parsed_output: dict[str, Any]


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        stripped = "\n".join(line for line in lines if not line.startswith("```")).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(stripped[start : end + 1])


class OllamaAnalystClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str = DEFAULT_ANALYST_MODEL,
        timeout: int = 120,
    ) -> None:
        self.base_url = (base_url or os.getenv("BITNIN_OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
        self.model = model
        self.timeout = timeout

    def analyze(self, *, messages: list[dict[str, str]]) -> LLMResult:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Ollama HTTP error {e.code}: {e.read().decode('utf-8')}") from e
        except Exception as e:
            raise RuntimeError(f"Ollama connection error: {e}") from e
        content = payload.get("message", {}).get("content", "")
        if not content:
            raise RuntimeError(f"Ollama returned empty content: {payload}")
        parsed = _extract_json(content)
        return LLMResult(
            model_name=self.model,
            raw_response=payload,
            parsed_output=parsed,
        )

