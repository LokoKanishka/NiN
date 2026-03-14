from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, pstdev
from typing import Any


RETURN_ABS_THRESHOLD = 0.03
ROLLING_VOL_THRESHOLD = 0.025
VOLUME_ANOMALY_MULTIPLIER = 1.8
NARRATIVE_RELEVANCE_THRESHOLD = 0.6
NARRATIVE_MARKET_CONFIRMATION_THRESHOLD = 0.01
ROLLING_WINDOW = 7


@dataclass(frozen=True)
class TriggerCandidate:
    index: int
    trigger_types: tuple[str, ...]
    trigger_strength: float
    nearby_narrative_ids: tuple[str, ...]


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current / previous) - 1.0


def _mean_quote_volume(bar: dict[str, Any]) -> float:
    value = bar.get("quote_volume")
    if isinstance(value, (int, float)):
        return float(value)
    return float(bar.get("volume", 0.0))


def _nearby_narratives(
    narrative_events: list[dict[str, Any]],
    bar_open: datetime,
    bar_close: datetime,
    hours_padding: int = 24,
) -> list[dict[str, Any]]:
    lower = bar_open - timedelta(hours=hours_padding)
    upper = bar_close + timedelta(hours=hours_padding)
    matches: list[dict[str, Any]] = []
    for event in narrative_events:
        ts = datetime.fromisoformat(event["timestamp_start"].replace("Z", "+00:00"))
        if lower <= ts <= upper:
            matches.append(event)
    return matches


def detect_trigger_candidates(
    market_bars: list[dict[str, Any]],
    narrative_events: list[dict[str, Any]],
) -> list[TriggerCandidate]:
    candidates: list[TriggerCandidate] = []
    last_selected_index = -10

    closes = [float(bar["close"]) for bar in market_bars]
    for index, bar in enumerate(market_bars):
        trigger_types: list[str] = []
        strengths: list[float] = []

        if index > 0:
            return_1d = abs(_pct_change(closes[index], closes[index - 1]))
            if return_1d >= RETURN_ABS_THRESHOLD:
                trigger_types.append("return")
                strengths.append(return_1d / RETURN_ABS_THRESHOLD)
        else:
            return_1d = 0.0

        if index >= 2:
            start = max(1, index - ROLLING_WINDOW + 1)
            recent_returns = [
                abs(_pct_change(closes[i], closes[i - 1]))
                for i in range(start, index + 1)
            ]
            realized_vol = pstdev(recent_returns) if len(recent_returns) > 1 else 0.0
            if realized_vol >= ROLLING_VOL_THRESHOLD:
                trigger_types.append("volatility_regime")
                strengths.append(realized_vol / ROLLING_VOL_THRESHOLD)
        else:
            realized_vol = 0.0

        if index >= 3:
            prior_volumes = [_mean_quote_volume(item) for item in market_bars[max(0, index - ROLLING_WINDOW):index]]
            if prior_volumes:
                ratio = _mean_quote_volume(bar) / max(mean(prior_volumes), 1e-9)
                if ratio >= VOLUME_ANOMALY_MULTIPLIER:
                    trigger_types.append("volume_anomaly")
                    strengths.append(ratio / VOLUME_ANOMALY_MULTIPLIER)

        bar_open = datetime.fromisoformat(bar["open_time"].replace("Z", "+00:00"))
        bar_close = datetime.fromisoformat(bar["close_time"].replace("Z", "+00:00"))
        nearby = _nearby_narratives(narrative_events, bar_open, bar_close)
        relevant_narratives = [
            event
            for event in nearby
            if float(event.get("relevance_btc", 0.0)) >= NARRATIVE_RELEVANCE_THRESHOLD
        ]
        if relevant_narratives and (
            abs(return_1d) >= NARRATIVE_MARKET_CONFIRMATION_THRESHOLD
            or "volume_anomaly" in trigger_types
            or "volatility_regime" in trigger_types
        ):
            trigger_types.append("narrative_reinforced")
            strengths.append(
                max(float(event.get("relevance_btc", 0.0)) for event in relevant_narratives)
            )

        if not trigger_types:
            continue

        if index - last_selected_index <= 1:
            continue

        trigger_types = sorted(set(trigger_types))
        trigger_strength = round(max(strengths) if strengths else 1.0, 4)
        candidates.append(
            TriggerCandidate(
                index=index,
                trigger_types=tuple(trigger_types),
                trigger_strength=trigger_strength,
                nearby_narrative_ids=tuple(sorted(event["event_id"] for event in relevant_narratives)),
            )
        )
        last_selected_index = index

    return candidates
