from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_EMBED_MODEL = "nomic-embed-text:latest"


@dataclass(frozen=True)
class EmbeddingProbe:
    model: str
    dimension: int
    endpoint: str
    sample_text: str
    response_format: str


class OllamaEmbeddingClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str = DEFAULT_EMBED_MODEL,
        timeout: int = 60,
    ) -> None:
        self.base_url = (base_url or os.getenv("BITNIN_OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
        self.model = model
        self.timeout = timeout

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        url = f"{self.base_url}/api/embed"
        payload = {"model": self.model, "input": texts}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return self._embed_texts_legacy(texts)
            raise RuntimeError(f"Ollama embed error {e.code}: {e.read().decode('utf-8')}") from e
        except Exception as e:
            raise RuntimeError(f"Ollama connection error: {e}") from e
        embeddings = payload.get("embeddings", [])
        if not embeddings:
            raise RuntimeError(f"Ollama `/api/embed` returned no embeddings: {payload}")
        return embeddings

    def _embed_texts_legacy(self, texts: list[str]) -> list[list[float]]:
        url = f"{self.base_url}/api/embeddings"
        outputs: list[list[float]] = []
        for text in texts:
            data = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except Exception as e:
                raise RuntimeError(f"Ollama legacy embed error: {e}") from e
            vector = payload.get("embedding")
            if not vector:
                raise RuntimeError(f"Ollama `/api/embeddings` returned no vector: {payload}")
            outputs.append(vector)
        return outputs

    def probe_dimension(self, sample_text: str = "bitnin embedding probe") -> EmbeddingProbe:
        embeddings = self.embed_texts([sample_text])
        vector = embeddings[0]
        return EmbeddingProbe(
            model=self.model,
            dimension=len(vector),
            endpoint=self.base_url,
            sample_text=sample_text,
            response_format="/api/embed",
        )
