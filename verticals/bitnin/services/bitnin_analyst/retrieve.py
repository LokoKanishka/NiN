from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verticals.bitnin.services.bitnin_memory_indexer.collections import QdrantCollectionManager
from verticals.bitnin.services.bitnin_memory_indexer.embeddings import OllamaEmbeddingClient


def _safe_slug(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value.lower())[:48]


def _within_cutoff(timestamp_value: str | None, cutoff: str | None) -> bool:
    if not cutoff or not timestamp_value:
        return True
    return timestamp_value <= cutoff


class AnalystRetriever:
    def __init__(
        self,
        *,
        embedder: OllamaEmbeddingClient | None = None,
        qdrant: QdrantCollectionManager | None = None,
        raw_root: Path,
    ) -> None:
        self.embedder = embedder or OllamaEmbeddingClient()
        self.qdrant = qdrant or QdrantCollectionManager()
        self.raw_root = raw_root

    def retrieve(
        self,
        *,
        analysis_id: str,
        context: dict[str, Any],
        top_k_episodes: int = 5,
        top_k_events: int = 5,
    ) -> dict[str, Any]:
        self.raw_root.mkdir(parents=True, exist_ok=True)
        market_state = context["market_state"]
        narrative = context["recent_narrative"]
        episode_query = (
            f"{market_state['symbol']} {market_state['interval']} "
            f"return_1d={market_state['return_1d']} return_3d={market_state['return_3d']} "
            f"return_7d={market_state['return_7d']} volatility={market_state['volatility_regime']} "
            f"breakout={market_state['breakout']} volume_anomaly={market_state['volume_anomaly']} "
            f"topics={'|'.join(narrative['top_topics'])}"
        )
        event_query = (
            f"{market_state['symbol']} narrative "
            f"topics={'|'.join(narrative['top_topics'])} entities={'|'.join(narrative['top_entities'])} "
            f"max_relevance_btc={narrative['max_relevance_btc']}"
        )

        episode_vector = self.embedder.embed_texts([episode_query])[0]
        event_vector = self.embedder.embed_texts([event_query])[0]
        episode_filter = {
            "must": [
                {"key": "symbol", "match": {"value": market_state["symbol"]}},
                {"key": "interval", "match": {"value": market_state["interval"]}},
                {"key": "dataset_version", "match": {"value": context["dataset_versions"]["episodes"]}},
            ]
        }
        event_filter = {
            "must": [
                {"key": "dataset_version", "match": {"value": context["dataset_versions"]["narrative"]}},
            ]
        }

        raw_episode_results = self.qdrant.search(
            collection="bitnin_episodes",
            vector=episode_vector,
            limit=max(top_k_episodes * 10, 50),
            query_filter=episode_filter,
        )
        raw_event_results = self.qdrant.search(
            collection="bitnin_events",
            vector=event_vector,
            limit=max(top_k_events * 10, 50),
            query_filter=event_filter,
        )
        cutoff = context.get("retrieval_cutoff")
        episode_results = [
            item
            for item in raw_episode_results
            if _within_cutoff(item.get("payload", {}).get("window_end"), cutoff)
        ][:top_k_episodes]
        event_results = [
            item
            for item in raw_event_results
            if _within_cutoff(item.get("payload", {}).get("timestamp_start"), cutoff)
        ][:top_k_events]

        episode_query_path = self.raw_root / f"analysis_query__{analysis_id}__episodes__{_safe_slug(episode_query)}.json"
        event_query_path = self.raw_root / f"analysis_query__{analysis_id}__events__{_safe_slug(event_query)}.json"
        episode_query_path.write_text(
            json.dumps(
                {
                    "analysis_id": analysis_id,
                    "collection": "bitnin_episodes",
                    "query": episode_query,
                    "filter": episode_filter,
                    "results": episode_results,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        event_query_path.write_text(
            json.dumps(
                {
                    "analysis_id": analysis_id,
                    "collection": "bitnin_events",
                    "query": event_query,
                    "filter": event_filter,
                    "results": event_results,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        return {
            "queries": {
                "episodes": episode_query,
                "events": event_query,
            },
            "episode_results": episode_results,
            "event_results": event_results,
            "query_refs": [str(episode_query_path), str(event_query_path)],
        }
