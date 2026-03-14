from __future__ import annotations

from typing import Any


def _direction_for_action(action: str) -> int:
    if action == "long":
        return 1
    if action == "short":
        return -1
    return 0


def is_directional_action(action: str) -> bool:
    return _direction_for_action(action) != 0


def simulate_decision(
    *,
    run_id: str,
    analysis: dict[str, Any],
    analysis_ref: str,
    current_bar: dict[str, Any],
    future_bars: list[dict[str, Any]],
    evaluation_bars: int,
    cost_bps: float,
    slippage_bps: float,
) -> dict[str, Any]:
    entry_close = float(current_bar["close"])
    action = analysis["recommended_action"]
    direction = _direction_for_action(action)
    gross_future_return_1d = None
    if future_bars:
        gross_future_return_1d = round((float(future_bars[0]["close"]) / entry_close) - 1, 6)

    outcome: dict[str, Any] = {
        "gross_future_return_1d": gross_future_return_1d,
        "counterfactual_long_return_1d": gross_future_return_1d,
        "evaluation_end_close": float(future_bars[-1]["close"]) if future_bars else entry_close,
    }
    evaluation_window = {
        "bars": evaluation_bars,
        "start": current_bar["close_time"],
        "end": future_bars[-1]["close_time"] if future_bars else current_bar["close_time"],
    }
    result_status = "abstain"

    if not future_bars:
        result_status = "insufficient_horizon"
        outcome["net_return"] = "insufficient_horizon"
        outcome["max_drawdown"] = "insufficient_horizon"
        outcome["win"] = "insufficient_horizon"
    elif direction == 0:
        result_status = "abstain"
        outcome["net_return"] = 0.0
        outcome["max_drawdown"] = 0.0
        outcome["win"] = False
    else:
        cost_decimal = (cost_bps + slippage_bps) / 10000.0
        last_close = float(future_bars[-1]["close"])
        raw_move = round(((last_close / entry_close) - 1) * direction, 6)
        net_return = round(raw_move - cost_decimal, 6)
        path_returns = [
            round(((float(bar["close"]) / entry_close) - 1) * direction, 6)
            for bar in future_bars
        ]
        max_drawdown = round(min(path_returns), 6) if path_returns else 0.0
        result_status = "simulated"
        outcome.update(
            {
                "net_return": net_return,
                "max_drawdown": max_drawdown,
                "win": net_return > 0,
            }
        )

    return {
        "run_id": run_id,
        "analysis_ref": analysis_ref,
        "timestamp": analysis["timestamp"],
        "decision": {
            "analysis_id": analysis["analysis_id"],
            "recommended_action": analysis["recommended_action"],
            "final_status": analysis["final_status"],
            "confidence": analysis["confidence"],
        },
        "entry_reference": {
            "symbol": current_bar["symbol"],
            "interval": current_bar["interval"],
            "close_time": current_bar["close_time"],
            "close": entry_close,
        },
        "outcome": outcome,
        "evaluation_window": evaluation_window,
        "result_status": result_status,
        "dataset_versions": analysis["dataset_versions"],
        "market_state": analysis["market_state"],
        "retrieved_episode_count": len(analysis["retrieved_episodes"]),
        "top_retrieval_score": analysis["retrieved_episodes"][0]["score"] if analysis["retrieved_episodes"] else 0.0,
        "data_coverage_score": analysis["data_coverage_score"],
        "narrative_coverage_score": analysis["narrative_coverage_score"],
    }
