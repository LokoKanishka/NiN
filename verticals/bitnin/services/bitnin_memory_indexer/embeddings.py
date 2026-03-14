from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


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
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("BITNIN_OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
        self.model = model
        self.timeout = timeout
        self.session = session or requests.Session()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        endpoint = f"{self.base_url}/api/embed"
        response = self.session.post(
            endpoint,
            json={"model": self.model, "input": texts},
            timeout=self.timeout,
        )
        if response.status_code == 404:
            return self._embed_texts_legacy(texts)
        response.raise_for_status()
        payload = response.json()
        embeddings = payload.get("embeddings", [])
        if not embeddings:
            raise RuntimeError(f"Ollama `/api/embed` returned no embeddings: {payload}")
        return embeddings

    def _embed_texts_legacy(self, texts: list[str]) -> list[list[float]]:
        endpoint = f"{self.base_url}/api/embeddings"
        outputs: list[list[float]] = []
        for text in texts:
            response = self.session.post(
                endpoint,
                json={"model": self.model, "prompt": text},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
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
