from __future__ import annotations

from typing import Any


def _mean(values: list[float]) -> float | str:
    if not values:
        return "not_applicable"
    return round(sum(values) / len(values), 6)


def _confidence_buckets(confidences: list[float]) -> dict[str, int]:
    buckets = {"0.0-0.3": 0, "0.3-0.6": 0, "0.6-1.0": 0}
    for value in confidences:
        if value < 0.3:
            buckets["0.0-0.3"] += 1
        elif value < 0.6:
            buckets["0.3-0.6"] += 1
        else:
            buckets["0.6-1.0"] += 1
    return buckets


def compute_metrics(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    analysis_count = len(decisions)
    no_trade_count = sum(1 for item in decisions if item["decision"]["recommended_action"] == "no_trade")
    watch_count = sum(1 for item in decisions if item["decision"]["recommended_action"] == "observe")
    abstain_count = sum(1 for item in decisions if item["result_status"] == "abstain")
    insufficient_count = sum(1 for item in decisions if item["decision"]["final_status"] == "insufficient_evidence")
    reasonable_context_count = sum(
        1
        for item in decisions
        if item["data_coverage_score"] >= 0.75 and item["retrieved_episode_count"] >= 2
    )
    directional = [
        item
        for item in decisions
        if item["result_status"] == "simulated"
    ]
    directional_returns = [float(item["outcome"]["net_return"]) for item in directional]
    wins = [1.0 if item["outcome"]["win"] else 0.0 for item in directional]
    overconfidence_terms = []
    for item in directional:
        realized = 1.0 if item["outcome"]["win"] else 0.0
        overconfidence_terms.append(max(float(item["decision"]["confidence"]) - realized, 0.0))

    cumulative = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for trade_return in directional_returns:
        cumulative *= 1 + trade_return
        peak = max(peak, cumulative)
        drawdown = (cumulative / peak) - 1
        max_drawdown = min(max_drawdown, drawdown)

    top_scores = [float(item["top_retrieval_score"]) for item in decisions if item["top_retrieval_score"]]
    narrative_scores = [float(item["narrative_coverage_score"]) for item in decisions]
    confidences = [float(item["decision"]["confidence"]) for item in decisions]
    return {
        "analysis_count": analysis_count,
        "no_trade_count": no_trade_count,
        "watch_count": watch_count,
        "abstention_rate": round((abstain_count / analysis_count), 6) if analysis_count else 0.0,
        "insufficient_evidence_rate": round((insufficient_count / analysis_count), 6) if analysis_count else 0.0,
        "reasonable_context_count": reasonable_context_count,
        "directional_action_count": len(directional),
        "hypothetical_return": round(sum(directional_returns), 6) if directional_returns else "not_applicable",
        "max_drawdown_hypothetical": round(max_drawdown, 6) if directional_returns else "not_applicable",
        "win_rate_hypothetical": _mean(wins),
        "expectancy_hypothetical": _mean(directional_returns),
        "overconfidence_error": _mean(overconfidence_terms),
        "confidence_distribution": _confidence_buckets(confidences),
        "avg_narrative_coverage": _mean(narrative_scores),
        "avg_retrieval_quality": _mean(top_scores),
    }

