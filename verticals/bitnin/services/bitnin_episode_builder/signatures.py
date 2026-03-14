from __future__ import annotations

from collections import Counter
from statistics import mean, pstdev
from typing import Any


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current / previous) - 1.0


def _horizon_return(closes: list[float], index: int, horizon: int) -> float | str:
    if index - horizon < 0:
        return "insufficient_history"
    return round(_pct_change(closes[index], closes[index - horizon]), 6)


def build_market_signature(
    *,
    bars: list[dict[str, Any]],
    trigger_index: int,
    pre_bars: list[dict[str, Any]],
) -> dict[str, Any]:
    closes = [float(bar["close"]) for bar in bars]
    current = bars[trigger_index]
    interval = current["interval"]

    return_1d = _horizon_return(closes, trigger_index, 1)
    return_3d = _horizon_return(closes, trigger_index, 3)
    return_7d = _horizon_return(closes, trigger_index, 7)

    if trigger_index >= 2:
        start = max(1, trigger_index - 6)
        realized = [abs(_pct_change(closes[i], closes[i - 1])) for i in range(start, trigger_index + 1)]
        vol = pstdev(realized) if len(realized) > 1 else 0.0
    else:
        vol = 0.0

    if vol >= 0.03:
        volatility_regime = "high"
    elif vol >= 0.015:
        volatility_regime = "medium"
    else:
        volatility_regime = "low"

    if pre_bars:
        max_pre_close = max(float(bar["close"]) for bar in pre_bars)
        min_pre_low = min(float(bar["low"]) for bar in pre_bars)
        drawdown_pre = round((min_pre_low / max_pre_close) - 1.0, 6) if max_pre_close else 0.0
        breakout = float(current["close"]) > max(float(bar["high"]) for bar in pre_bars)
        prior_quote = [float(bar.get("quote_volume", bar["volume"])) for bar in pre_bars]
        baseline = mean(prior_quote) if prior_quote else 0.0
        current_quote = float(current.get("quote_volume", current["volume"]))
        volume_score = (current_quote / baseline) if baseline else 0.0
    else:
        drawdown_pre = "insufficient_history"
        breakout = False
        volume_score = 0.0

    return {
        "interval": interval,
        "return_1d": return_1d,
        "return_3d": return_3d,
        "return_7d": return_7d,
        "volatility_regime": volatility_regime,
        "drawdown_pre": drawdown_pre,
        "breakout": breakout,
        "volume_anomaly": volume_score >= 1.8,
        "volume_anomaly_score": round(volume_score, 6),
    }


def build_narrative_signature(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {
            "topics": [],
            "entities": [],
            "dominant_cause": "market_only",
            "narrative_confidence": 0.0,
            "event_count": 0,
        }

    topic_counter: Counter[str] = Counter()
    entity_counter: Counter[str] = Counter()
    scores: list[float] = []
    for event in events:
        topic_counter.update(event.get("topics", []))
        entity_counter.update(event.get("entities", []))
        score = float(event.get("confidence_source", 0.0)) * float(event.get("relevance_btc", 0.0))
        scores.append(score)

    dominant_cause = topic_counter.most_common(1)[0][0] if topic_counter else "uncategorized"
    topics = [item for item, _ in topic_counter.most_common(5)]
    entities = [item for item, _ in entity_counter.most_common(8)]
    confidence = round(mean(scores), 6) if scores else 0.0

    return {
        "topics": topics,
        "entities": entities,
        "dominant_cause": dominant_cause,
        "narrative_confidence": confidence,
        "event_count": len(events),
    }
