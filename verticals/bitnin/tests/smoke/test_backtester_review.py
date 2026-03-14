from verticals.bitnin.services.bitnin_backtester.review import review_decision


def test_review_marks_reasonable_no_trade_when_coverage_is_low():
    decision = {
        "analysis_ref": "/tmp/a.json",
        "timestamp": "2026-03-13T23:00:00.000Z",
        "decision": {
            "recommended_action": "no_trade",
            "final_status": "insufficient_evidence",
            "confidence": 0.2,
        },
        "outcome": {"gross_future_return_1d": 0.01},
        "market_state": {"summary": "BTCUSDT calm breakout"},
        "retrieved_episode_count": 1,
        "top_retrieval_score": 0.4,
        "narrative_coverage_score": 0.1,
        "result_status": "abstain",
    }
    review = review_decision(decision)
    assert review["no_trade_reasonable"] is True
    assert review["did_not_see"]["future_prices_used_in_analysis"] is False

