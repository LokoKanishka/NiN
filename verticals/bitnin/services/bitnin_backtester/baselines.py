from __future__ import annotations

from typing import Any


def buy_and_hold_baseline(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    if not decisions:
        return {"strategy": "buy_and_hold", "return": 0.0}
    first_close = float(decisions[0]["entry_reference"]["close"])
    last_close = float(decisions[-1]["outcome"].get("evaluation_end_close", decisions[-1]["entry_reference"]["close"]))
    return {
        "strategy": "buy_and_hold",
        "return": round((last_close / first_close) - 1, 6) if first_close else 0.0,
    }


def abstention_baseline(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "strategy": "never_trade",
        "decision_count": len(decisions),
        "return": 0.0,
    }


def return_signal_baseline(decisions: list[dict[str, Any]], *, threshold: float = 0.02) -> dict[str, Any]:
    hypothetical_returns: list[float] = []
    signal_count = 0
    for decision in decisions:
        recent_return = decision["market_state"]["return_3d"]
        if not isinstance(recent_return, (int, float)):
            continue
        gross_1d = decision["outcome"].get("gross_future_return_1d")
        if gross_1d in (None, "insufficient_horizon"):
            continue
        if recent_return >= threshold:
            hypothetical_returns.append(round(float(gross_1d), 6))
            signal_count += 1
        elif recent_return <= -threshold:
            hypothetical_returns.append(round(-float(gross_1d), 6))
            signal_count += 1
    return {
        "strategy": "return_signal",
        "threshold": threshold,
        "signal_count": signal_count,
        "return": round(sum(hypothetical_returns), 6),
    }
