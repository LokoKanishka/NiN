from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[4]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from verticals.bitnin.services.bitnin_memory_indexer.collections import QdrantCollectionManager  # type: ignore
    from verticals.bitnin.services.bitnin_memory_indexer.embeddings import OllamaEmbeddingClient  # type: ignore
    from verticals.bitnin.services.bitnin_memory_indexer.indexer import EVENTS_COLLECTION, EPISODES_COLLECTION  # type: ignore
else:
    from .collections import QdrantCollectionManager
    from .embeddings import OllamaEmbeddingClient
    from .indexer import EVENTS_COLLECTION, EPISODES_COLLECTION


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BitNin memory verification")
    parser.add_argument("--query", default="bitcoin etf volatility episode")
    args = parser.parse_args(argv)

    embedder = OllamaEmbeddingClient()
    qdrant = QdrantCollectionManager()
    probe = embedder.probe_dimension()

    episode_collection = qdrant.get_collection(EPISODES_COLLECTION)
    event_collection = qdrant.get_collection(EVENTS_COLLECTION)

    episode_results = qdrant.search(
        collection=EPISODES_COLLECTION,
        vector=embedder.embed_texts([args.query])[0],
        limit=3,
    )
    event_results = qdrant.search(
        collection=EVENTS_COLLECTION,
        vector=embedder.embed_texts([args.query])[0],
        limit=3,
    )

    output = {
        "embedding_probe": {
            "model": probe.model,
            "dimension": probe.dimension,
            "endpoint": probe.endpoint,
        },
        "qdrant_base_url": qdrant.base_url,
        "collections": {
            EPISODES_COLLECTION: episode_collection,
            EVENTS_COLLECTION: event_collection,
        },
        "round_trip": {
            "episode_results": episode_results,
            "event_results": event_results,
        },
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
