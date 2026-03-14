from __future__ import annotations

from typing import Any


def review_decision(decision: dict[str, Any]) -> dict[str, Any]:
    analysis = decision["decision"]
    gross_1d = decision["outcome"].get("gross_future_return_1d")
    no_trade_reasonable = False
    if analysis["recommended_action"] == "no_trade":
        no_trade_reasonable = (
            analysis["final_status"] == "insufficient_evidence"
            or decision["narrative_coverage_score"] < 0.3
            or decision["retrieved_episode_count"] < 2
            or gross_1d in (None, "insufficient_horizon")
            or abs(float(gross_1d)) < 0.02
        )

    overconfidence = (
        decision["result_status"] == "simulated"
        and float(analysis["confidence"]) >= 0.7
        and not bool(decision["outcome"].get("win"))
    )

    notes = []
    if decision["narrative_coverage_score"] < 0.3:
        notes.append("Cobertura narrativa baja.")
    if decision["retrieved_episode_count"] < 2:
        notes.append("Retrieval de episodios escaso.")
    if analysis["recommended_action"] == "no_trade":
        notes.append("Analista se abstuvo.")
    if overconfidence:
        notes.append("Hubo sobreconfianza frente al resultado simulado.")

    return {
        "analysis_ref": decision["analysis_ref"],
        "timestamp": decision["timestamp"],
        "saw": {
            "market_state": decision["market_state"]["summary"],
            "retrieved_episode_count": decision["retrieved_episode_count"],
            "top_retrieval_score": decision["top_retrieval_score"],
        },
        "did_not_see": {
            "future_prices_used_in_analysis": False,
            "future_narrative_used_in_analysis": False,
        },
        "no_trade_reasonable": no_trade_reasonable,
        "overconfidence": overconfidence,
        "notes": notes,
    }

