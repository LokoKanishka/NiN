from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests


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
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("BITNIN_OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
        self.model = model
        self.timeout = timeout
        self.session = session or requests.Session()

    def analyze(self, *, messages: list[dict[str, str]]) -> LLMResult:
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0,
                },
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("message", {}).get("content", "")
        if not content:
            raise RuntimeError(f"Ollama returned empty content: {payload}")
        parsed = _extract_json(content)
        return LLMResult(
            model_name=self.model,
            raw_response=payload,
            parsed_output=parsed,
        )

