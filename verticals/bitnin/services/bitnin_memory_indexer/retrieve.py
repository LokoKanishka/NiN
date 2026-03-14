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
    from verticals.bitnin.services.bitnin_memory_indexer.indexer import QUERIES_ROOT  # type: ignore
else:
    from .collections import QdrantCollectionManager
    from .embeddings import OllamaEmbeddingClient
    from .indexer import QUERIES_ROOT


def build_filter(args: argparse.Namespace) -> dict[str, Any] | None:
    must = []
    if args.symbol:
        must.append({"key": "symbol", "match": {"value": args.symbol}})
    if args.interval:
        must.append({"key": "interval", "match": {"value": args.interval}})
    if args.dataset_version:
        must.append({"key": "dataset_version", "match": {"value": args.dataset_version}})
    if args.topic:
        must.append({"key": "topics", "match": {"any": [args.topic]}})
    if args.breakout is not None:
        must.append({"key": "breakout", "match": {"value": args.breakout}})
    if not must:
        return None
    return {"must": must}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BitNin Qdrant retrieval")
    parser.add_argument("--collection", required=True, choices=["bitnin_episodes", "bitnin_events"])
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--symbol")
    parser.add_argument("--interval")
    parser.add_argument("--dataset-version")
    parser.add_argument("--topic")
    parser.add_argument("--breakout", action=argparse.BooleanOptionalAction, default=None)
    args = parser.parse_args(argv)

    embedder = OllamaEmbeddingClient()
    qdrant = QdrantCollectionManager()
    vector = embedder.embed_texts([args.query])[0]
    query_filter = build_filter(args)
    results = qdrant.search(
        collection=args.collection,
        vector=vector,
        limit=args.limit,
        query_filter=query_filter,
    )

    output = {
        "collection": args.collection,
        "query": args.query,
        "qdrant_base_url": qdrant.base_url,
        "filter": query_filter,
        "results": results,
    }
    QUERIES_ROOT.mkdir(parents=True, exist_ok=True)
    safe_name = args.collection + "__" + "".join(ch if ch.isalnum() else "_" for ch in args.query.lower())[:40]
    (QUERIES_ROOT / f"query__{safe_name}.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
