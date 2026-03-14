from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verticals.bitnin.services.bitnin_analyst.context import parse_utc


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_shadow_review(
    *,
    intent: dict[str, Any],
    analysis: dict[str, Any],
    market_path: Path,
) -> dict[str, Any]:
    entry = intent["entry_reference"]
    bars = [
        row
        for row in _read_jsonl(market_path)
        if row.get("symbol") == entry["symbol"] and row.get("interval") == entry["interval"]
    ]
    future_bars = [
        row
        for row in sorted(bars, key=lambda item: item["open_time"])
        if parse_utc(row["close_time"]) > parse_utc(intent["valid_until"])
    ]
    if future_bars:
        observed_bar = future_bars[0]
        realized_return = round((float(observed_bar["close"]) / float(entry["price"])) - 1, 6)
        review_status = "reviewed"
        context_changed = abs(realized_return) >= 0.03
    else:
        observed_bar = None
        realized_return = "insufficient_horizon"
        review_status = "pending_horizon"
        context_changed = False

    abstention_reasonable = False
    if intent["action"] in {"no_trade", "hold"}:
        abstention_reasonable = (
            analysis["final_status"] == "insufficient_evidence"
            or analysis["narrative_coverage_score"] < 0.3
            or realized_return == "insufficient_horizon"
            or abs(float(realized_return)) < 0.02
        )

    return {
        "intent_id": intent["intent_id"],
        "reviewed_at": observed_bar["close_time"] if observed_bar else intent["valid_until"],
        "suggested_action": intent["action"],
        "intent_status_before_review": intent["status"],
        "review_status": review_status,
        "observed_after_validity": {
            "close_time": observed_bar["close_time"] if observed_bar else intent["valid_until"],
            "close": float(observed_bar["close"]) if observed_bar else None,
            "realized_return": realized_return,
        },
        "abstention_reasonable": abstention_reasonable,
        "context_changed": context_changed,
        "missing_coverage": {
            "market": analysis["data_coverage_score"] < 0.75,
            "narrative": analysis["narrative_coverage_score"] < 0.3,
        },
    }

