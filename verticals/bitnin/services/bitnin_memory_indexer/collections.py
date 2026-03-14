from __future__ import annotations

import os
from typing import Any

import requests


QDRANT_CANDIDATE_URLS = [
    "http://127.0.0.1:6335",
    "http://127.0.0.1:6333",
]


class QdrantCollectionManager:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.base_url = base_url or os.getenv("BITNIN_QDRANT_URL") or self._detect_base_url()

    def _detect_base_url(self) -> str:
        for candidate in QDRANT_CANDIDATE_URLS:
            try:
                response = self.session.get(f"{candidate}/collections", timeout=self.timeout)
                if response.ok:
                    return candidate
            except requests.RequestException:
                continue
        raise RuntimeError("No reachable Qdrant endpoint found for BitNin")

    def list_collections(self) -> list[str]:
        response = self.session.get(f"{self.base_url}/collections", timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        return [item["name"] for item in payload["result"]["collections"]]

    def get_collection(self, name: str) -> dict[str, Any] | None:
        response = self.session.get(f"{self.base_url}/collections/{name}", timeout=self.timeout)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()["result"]

    def ensure_collection(self, *, name: str, vector_size: int, distance: str = "Cosine") -> dict[str, Any]:
        existing = self.get_collection(name)
        if existing is not None:
            actual_size = existing["config"]["params"]["vectors"]["size"]
            if actual_size != vector_size:
                raise RuntimeError(
                    f"Collection {name} already exists with size {actual_size}, expected {vector_size}"
                )
            return existing

        payload = {
            "vectors": {
                "size": vector_size,
                "distance": distance,
            }
        }
        response = self.session.put(
            f"{self.base_url}/collections/{name}",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return self.get_collection(name) or {}

    def upsert_points(self, *, collection: str, points: list[dict[str, Any]]) -> dict[str, Any]:
        response = self.session.put(
            f"{self.base_url}/collections/{collection}/points",
            json={"points": points},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def search(
        self,
        *,
        collection: str,
        vector: list[float],
        limit: int = 5,
        query_filter: dict[str, Any] | None = None,
        with_vector: bool = False,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
            "with_vector": with_vector,
        }
        if query_filter:
            payload["filter"] = query_filter

        response = self.session.post(
            f"{self.base_url}/collections/{collection}/points/search",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["result"]

    def scroll(
        self,
        *,
        collection: str,
        query_filter: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"limit": limit, "with_payload": True}
        if query_filter:
            payload["filter"] = query_filter
        response = self.session.post(
            f"{self.base_url}/collections/{collection}/points/scroll",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["result"]["points"]
