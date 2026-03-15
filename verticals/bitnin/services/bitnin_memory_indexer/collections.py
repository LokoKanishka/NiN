from __future__ import annotations

import json
import os
import urllib.request
import urllib.parse
from typing import Any


QDRANT_CANDIDATE_URLS = [
    "http://127.0.0.1:6333",
    "http://127.0.0.1:6335",
]


class QdrantCollectionManager:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.timeout = timeout
        self.base_url = (base_url or os.getenv("BITNIN_QDRANT_URL") or self._detect_base_url()).rstrip("/")

    def _detect_base_url(self) -> str:
        for candidate in QDRANT_CANDIDATE_URLS:
            try:
                with urllib.request.urlopen(f"{candidate}/collections", timeout=self.timeout) as response:
                    if response.getcode() == 200:
                        return candidate
            except Exception:
                continue
        raise RuntimeError("No reachable Qdrant endpoint found for BitNin")

    def _request(self, method: str, path: str, payload: Any = None) -> Any:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404 and method == "GET":
                return None
            raise RuntimeError(f"Qdrant error {e.code}: {e.read().decode('utf-8')}") from e
        except Exception as e:
            raise RuntimeError(f"Qdrant connection error: {e}") from e

    def list_collections(self) -> list[str]:
        payload = self._request("GET", "/collections")
        return [item["name"] for item in payload["result"]["collections"]]

    def get_collection(self, name: str) -> dict[str, Any] | None:
        res = self._request("GET", f"/collections/{name}")
        return res["result"] if res else None

    def ensure_collection(self, *, name: str, vector_size: int, distance: str = "Cosine") -> dict[str, Any]:
        existing = self.get_collection(name)
        if existing is not None:
            actual_size = existing["config"]["params"]["vectors"]["size"]
            if actual_size != vector_size:
                raise RuntimeError(f"Collection {name} already exists with size {actual_size}, expected {vector_size}")
            return existing
        payload = {"vectors": {"size": vector_size, "distance": distance}}
        self._request("PUT", f"/collections/{name}", payload)
        return self.get_collection(name) or {}

    def upsert_points(self, *, collection: str, points: list[dict[str, Any]]) -> dict[str, Any]:
        return self._request("PUT", f"/collections/{collection}/points", {"points": points})

    def search(self, *, collection: str, vector: list[float], limit: int = 5, query_filter: dict[str, Any] | None = None, with_vector: bool = False) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"vector": vector, "limit": limit, "with_payload": True, "with_vector": with_vector}
        if query_filter:
            payload["filter"] = query_filter
        res = self._request("POST", f"/collections/{collection}/points/search", payload)
        return res["result"]

    def scroll(self, *, collection: str, query_filter: dict[str, Any] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"limit": limit, "with_payload": True}
        if query_filter:
            payload["filter"] = query_filter
        res = self._request("POST", f"/collections/{collection}/points/scroll", payload)
        return res["result"]["points"]
