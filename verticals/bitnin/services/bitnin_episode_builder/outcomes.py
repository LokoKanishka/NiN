from __future__ import annotations

from typing import Any


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current / previous) - 1.0


def _future_return(closes: list[float], trigger_index: int, horizon: int) -> float | str:
    future_index = trigger_index + horizon
    if future_index >= len(closes):
        return "insufficient_horizon"
    return round(_pct_change(closes[future_index], closes[trigger_index]), 6)


def build_outcome(bars: list[dict[str, Any]], trigger_index: int) -> dict[str, Any]:
    closes = [float(bar["close"]) for bar in bars]
    highs = [float(bar["high"]) for bar in bars]
    lows = [float(bar["low"]) for bar in bars]
    trigger_close = closes[trigger_index]

    forward_return_1d = _future_return(closes, trigger_index, 1)
    forward_return_7d = _future_return(closes, trigger_index, 7)
    forward_return_30d = _future_return(closes, trigger_index, 30)

    future_slice_high = highs[trigger_index + 1 : min(len(highs), trigger_index + 31)]
    future_slice_low = lows[trigger_index + 1 : min(len(lows), trigger_index + 31)]
    if future_slice_high and future_slice_low:
        forward_max_up: float | str = round((max(future_slice_high) / trigger_close) - 1.0, 6)
        forward_max_down: float | str = round((min(future_slice_low) / trigger_close) - 1.0, 6)
    else:
        forward_max_up = "insufficient_horizon"
        forward_max_down = "insufficient_horizon"

    if isinstance(forward_return_7d, float):
        continuation_or_reversion = "continuation" if forward_return_7d >= 0 else "reversion"
    elif isinstance(forward_return_1d, float):
        continuation_or_reversion = "continuation" if forward_return_1d >= 0 else "reversion"
    else:
        continuation_or_reversion = "insufficient_horizon"

    return {
        "forward_return_1d": forward_return_1d,
        "forward_return_7d": forward_return_7d,
        "forward_return_30d": forward_return_30d,
        "forward_max_up": forward_max_up,
        "forward_max_down": forward_max_down,
        "continuation_or_reversion": continuation_or_reversion,
    }
