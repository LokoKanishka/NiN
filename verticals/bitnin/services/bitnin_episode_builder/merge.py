from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from typing import Any

from .outcomes import build_outcome
from .signatures import build_market_signature, build_narrative_signature
from .windows import EpisodeWindow


def find_nearby_narratives(
    narrative_events: list[dict[str, Any]],
    *,
    window_start: str,
    window_end: str,
    minimum_relevance: float = 0.5,
) -> list[dict[str, Any]]:
    start = datetime.fromisoformat(window_start.replace("Z", "+00:00"))
    end = datetime.fromisoformat(window_end.replace("Z", "+00:00"))
    matches: list[dict[str, Any]] = []
    for event in narrative_events:
        ts = datetime.fromisoformat(event["timestamp_start"].replace("Z", "+00:00"))
        if start <= ts <= end and float(event.get("relevance_btc", 0.0)) >= minimum_relevance:
            matches.append(event)
    return sorted(matches, key=lambda item: (item["timestamp_start"], item["event_id"]))


def compute_episode_status(
    *,
    trigger_types: list[str],
    trigger_strength: float,
    narrative_event_count: int,
) -> str:
    if trigger_strength >= 1.5 or "return" in trigger_types or "volume_anomaly" in trigger_types:
        return "confirmed"
    if narrative_event_count > 0 or "volatility_regime" in trigger_types:
        return "ambiguous"
    return "discarded"


def build_episode_id(payload: dict[str, Any]) -> str:
    stable = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:24]


def merge_episode(
    *,
    market_bars: list[dict[str, Any]],
    narrative_events: list[dict[str, Any]],
    trigger_index: int,
    trigger_types: list[str],
    trigger_strength: float,
    window: EpisodeWindow,
    dataset_version: str,
    market_source_ref: str,
    narrative_source_ref: str,
) -> dict[str, Any]:
    pre_bars = market_bars[window.pre_start_index : window.event_start_index]
    window_bars = market_bars[window.event_start_index : window.post_end_index + 1]
    trigger_bar = market_bars[trigger_index]
    window_start = market_bars[window.pre_start_index]["open_time"]
    window_end = market_bars[window.post_end_index]["close_time"]

    nearby_events = find_nearby_narratives(
        narrative_events,
        window_start=window_start,
        window_end=window_end,
    )
    market_signature = build_market_signature(
        bars=market_bars,
        trigger_index=trigger_index,
        pre_bars=pre_bars,
    )
    narrative_signature = build_narrative_signature(nearby_events)
    outcome = build_outcome(market_bars, trigger_index)
    status = compute_episode_status(
        trigger_types=trigger_types,
        trigger_strength=trigger_strength,
        narrative_event_count=narrative_signature["event_count"],
    )

    summary_bits = [
        f"Episodio disparado por {', '.join(trigger_types)} en {trigger_bar['open_time']}",
        f"close={trigger_bar['close']}",
        f"return_1d={market_signature['return_1d']}",
        f"narrative_events={narrative_signature['event_count']}",
    ]
    if narrative_signature["dominant_cause"] != "market_only":
        summary_bits.append(f"dominant_cause={narrative_signature['dominant_cause']}")

    narrative_refs = [
        f"{narrative_source_ref}#{event['event_id']}"
        for event in nearby_events
    ]
    sources = [f"{market_source_ref}#{trigger_bar['open_time']}"] + narrative_refs

    id_payload = {
        "market_source_ref": market_source_ref,
        "trigger_bar_time": trigger_bar["open_time"],
        "trigger_types": sorted(trigger_types),
        "window_start": window_start,
        "window_end": window_end,
        "narrative_ids": [event["event_id"] for event in nearby_events],
    }
    episode_id = build_episode_id(id_payload)

    return {
        "episode_id": episode_id,
        "window_start": window_start,
        "window_end": window_end,
        "market_signature": market_signature,
        "narrative_signature": narrative_signature,
        "summary_local": ". ".join(summary_bits) + ".",
        "outcome": outcome,
        "sources": sources,
        "dataset_version": dataset_version,
        "trigger_type": "|".join(sorted(trigger_types)),
        "trigger_strength": round(trigger_strength, 6),
        "market_source_ref": market_source_ref,
        "narrative_source_refs": narrative_refs,
        "status": status,
        "created_at": trigger_bar["close_time"],
    }
