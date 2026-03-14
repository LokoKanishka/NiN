from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[4]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from verticals.bitnin.services.bitnin_memory_indexer.collections import QdrantCollectionManager  # type: ignore
    from verticals.bitnin.services.bitnin_memory_indexer.embeddings import OllamaEmbeddingClient  # type: ignore
    from verticals.bitnin.services.bitnin_memory_indexer.payloads import (  # type: ignore
        episode_embedding_text,
        episode_payload,
        event_embedding_text,
        event_payload,
        stable_point_id,
    )
else:
    from .collections import QdrantCollectionManager
    from .embeddings import OllamaEmbeddingClient
    from .payloads import (
        episode_embedding_text,
        episode_payload,
        event_embedding_text,
        event_payload,
        stable_point_id,
    )


BITNIN_ROOT = Path(__file__).resolve().parents[2]
MEMORY_ROOT = BITNIN_ROOT / "runtime" / "memory" / "qdrant"
EXPORTS_ROOT = MEMORY_ROOT / "exports"
QUERIES_ROOT = MEMORY_ROOT / "queries"
LOGS_ROOT = MEMORY_ROOT / "logs"

EPISODES_COLLECTION = "bitnin_episodes"
EVENTS_COLLECTION = "bitnin_events"


class BitNinMemoryIndexer:
    def __init__(self) -> None:
        for path in (EXPORTS_ROOT, QUERIES_ROOT, LOGS_ROOT):
            path.mkdir(parents=True, exist_ok=True)
        self.embedder = OllamaEmbeddingClient()
        self.qdrant = QdrantCollectionManager()

    def index(
        self,
        *,
        episodes_path: str,
        events_path: str,
        dataset_version: str,
    ) -> dict[str, Any]:
        probe = self.embedder.probe_dimension()
        self._write_json(
            EXPORTS_ROOT / f"embedding_probe__{probe.model.replace(':', '_')}__{probe.dimension}.json",
            {
                "model": probe.model,
                "dimension": probe.dimension,
                "endpoint": probe.endpoint,
                "sample_text": probe.sample_text,
                "response_format": probe.response_format,
            },
        )

        self.qdrant.ensure_collection(name=EPISODES_COLLECTION, vector_size=probe.dimension)
        self.qdrant.ensure_collection(name=EVENTS_COLLECTION, vector_size=probe.dimension)
        self._write_json(
            EXPORTS_ROOT / f"collections__{dataset_version}.json",
            {
                "qdrant_base_url": self.qdrant.base_url,
                "collections": {
                    EPISODES_COLLECTION: self.qdrant.get_collection(EPISODES_COLLECTION),
                    EVENTS_COLLECTION: self.qdrant.get_collection(EVENTS_COLLECTION),
                },
            },
        )

        episodes = self._read_jsonl(Path(episodes_path))
        events = self._read_jsonl(Path(events_path))
        episode_result = self._index_documents(
            collection=EPISODES_COLLECTION,
            docs=episodes,
            payload_builder=episode_payload,
            text_builder=episode_embedding_text,
            id_field="episode_id",
        )
        event_result = self._index_documents(
            collection=EVENTS_COLLECTION,
            docs=events,
            payload_builder=event_payload,
            text_builder=event_embedding_text,
            id_field="event_id",
        )

        result = {
            "dataset_version": dataset_version,
            "embedding_model": probe.model,
            "embedding_dimension": probe.dimension,
            "qdrant_base_url": self.qdrant.base_url,
            "collections": [EPISODES_COLLECTION, EVENTS_COLLECTION],
            "episodes": episode_result,
            "events": event_result,
        }
        self._write_json(LOGS_ROOT / f"indexer__{dataset_version}.json", result)
        return result

    def _index_documents(
        self,
        *,
        collection: str,
        docs: list[dict[str, Any]],
        payload_builder,
        text_builder,
        id_field: str,
    ) -> dict[str, Any]:
        texts = [text_builder(doc) for doc in docs]
        vectors = self.embedder.embed_texts(texts)
        points = []
        sample_payload = None
        for doc, vector in zip(docs, vectors):
            payload = payload_builder(doc)
            sample_payload = sample_payload or payload
            points.append(
                {
                    "id": stable_point_id(str(doc[id_field])),
                    "vector": vector,
                    "payload": payload,
                }
            )
        upsert_response = self.qdrant.upsert_points(collection=collection, points=points)
        return {
            "collection": collection,
            "document_count": len(docs),
            "sample_payload": sample_payload,
            "upsert_result": upsert_response,
        }

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BitNin Qdrant memory indexer")
    parser.add_argument("--episodes-path", required=True)
    parser.add_argument("--events-path", required=True)
    parser.add_argument("--dataset-version", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_cli_parser()
    args = parser.parse_args(argv)
    result = BitNinMemoryIndexer().index(
        episodes_path=args.episodes_path,
        events_path=args.events_path,
        dataset_version=args.dataset_version,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
