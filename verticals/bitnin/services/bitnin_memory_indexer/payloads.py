from __future__ import annotations

import hashlib
import re
from typing import Any


def stable_point_id(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16)


def _infer_symbol(episode: dict[str, Any]) -> str:
    market_source_ref = episode.get("market_source_ref", "")
    match = re.search(r"__([A-Z0-9]+)__", market_source_ref)
    if match:
        return match.group(1)

    sources = episode.get("sources", [])
    for source_ref in sources:
        match = re.search(r"__([A-Z0-9]+)__", source_ref)
        if match:
            return match.group(1)

    return "unknown"


def episode_embedding_text(episode: dict[str, Any]) -> str:
    market = episode["market_signature"]
    narrative = episode["narrative_signature"]
    parts = [
        episode["summary_local"],
        f"trigger_type={episode.get('trigger_type', '')}",
        f"interval={market['interval']}",
        f"volatility_regime={market['volatility_regime']}",
        f"breakout={market['breakout']}",
        f"volume_anomaly={market['volume_anomaly']}",
        f"dominant_cause={narrative['dominant_cause']}",
        f"topics={'|'.join(narrative['topics'])}",
        f"entities={'|'.join(narrative['entities'])}",
    ]
    return " ".join(part for part in parts if part)


def event_embedding_text(event: dict[str, Any]) -> str:
    parts = [
        event["title"],
        event["summary_local"],
        f"topics={'|'.join(event.get('topics', []))}",
        f"entities={'|'.join(event.get('entities', []))}",
    ]
    return " ".join(part for part in parts if part)


def episode_payload(episode: dict[str, Any]) -> dict[str, Any]:
    market = episode["market_signature"]
    narrative = episode["narrative_signature"]
    return {
        "doc_type": "episode",
        "episode_id": episode["episode_id"],
        "symbol": _infer_symbol(episode),
        "interval": market["interval"],
        "window_start": episode["window_start"],
        "window_end": episode["window_end"],
        "topics": narrative["topics"],
        "entities": narrative["entities"],
        "dominant_cause": narrative["dominant_cause"],
        "volatility_regime": market["volatility_regime"],
        "breakout": market["breakout"],
        "volume_anomaly": market["volume_anomaly"],
        "dataset_version": episode["dataset_version"],
        "source_refs": episode["sources"],
        "summary_local": episode["summary_local"],
    }


def event_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "doc_type": "event",
        "event_id": event["event_id"],
        "timestamp_start": event["timestamp_start"],
        "timestamp_end": event["timestamp_end"],
        "topics": event.get("topics", []),
        "entities": event.get("entities", []),
        "relevance_btc": event.get("relevance_btc", 0.0),
        "source_name": event["source_name"],
        "dataset_version": event["dataset_version"],
        "url": event["url"],
        "summary_local": event["summary_local"],
        "title": event["title"],
    }
