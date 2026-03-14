from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

from verticals.bitnin.services.bitnin_analyst.context import parse_utc


INTERVAL_TTLS = {
    "1d": timedelta(days=1),
    "4h": timedelta(hours=4),
    "1h": timedelta(hours=1),
}


def _iso_plus(timestamp: str, delta: timedelta) -> str:
    return (parse_utc(timestamp) + delta).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def map_analysis_action(recommended_action: str) -> str:
    if recommended_action == "long":
        return "buy"
    if recommended_action == "short":
        return "sell"
    if recommended_action in {"reduce", "hedge"}:
        return "reduce"
    if recommended_action in {"flat", "observe"}:
        return "hold"
    return "no_trade"


def build_shadow_intent(*, analysis: dict[str, Any], reasoning_ref: str, mode: str = "shadow") -> dict[str, Any]:
    market_state = analysis["market_state"]
    seed = json.dumps(
        {
            "analysis_id": analysis["analysis_id"],
            "mode": mode,
            "action": analysis["recommended_action"],
            "timestamp": market_state["as_of"],
        },
        sort_keys=True,
    )
    interval = market_state["interval"]
    ttl = INTERVAL_TTLS.get(interval, timedelta(days=1))
    return {
        "intent_id": hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24],
        "mode": mode,
        "action": map_analysis_action(analysis["recommended_action"]),
        "entry_reference": {
            "symbol": market_state["symbol"],
            "interval": interval,
            "timestamp": market_state["as_of"],
            "price": market_state["close"],
        },
        "stop_reference": None,
        "take_profit_reference": None,
        "valid_until": _iso_plus(market_state["as_of"], ttl),
        "reasoning_ref": reasoning_ref,
        "approved": False,
        "created_at": analysis["timestamp"],
        "status": "open",
        "final_status": analysis["final_status"],
        "confidence": analysis["confidence"],
        "notes": list(analysis.get("why_not", [])) or list(analysis.get("notes", [])),
    }


def expire_intent(intent: dict[str, Any], *, as_of: str) -> dict[str, Any]:
    updated = dict(intent)
    if updated["status"] == "open" and parse_utc(as_of) > parse_utc(updated["valid_until"]):
        updated["status"] = "expired"
    return updated

