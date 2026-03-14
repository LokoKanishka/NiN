from verticals.bitnin.services.bitnin_backtester.metrics import compute_metrics


def test_metrics_capture_abstention():
    decisions = [
        {
            "decision": {"recommended_action": "no_trade", "final_status": "insufficient_evidence", "confidence": 0.2},
            "result_status": "abstain",
            "data_coverage_score": 1.0,
            "retrieved_episode_count": 1,
            "top_retrieval_score": 0.4,
            "narrative_coverage_score": 0.1,
            "market_state": {"return_3d": 0.01},
            "outcome": {"gross_future_return_1d": 0.01},
        },
        {
            "decision": {"recommended_action": "observe", "final_status": "ok", "confidence": 0.55},
            "result_status": "abstain",
            "data_coverage_score": 1.0,
            "retrieved_episode_count": 3,
            "top_retrieval_score": 0.7,
            "narrative_coverage_score": 0.5,
            "market_state": {"return_3d": 0.03},
            "outcome": {"gross_future_return_1d": 0.02},
        },
    ]
    metrics = compute_metrics(decisions)
    assert metrics["analysis_count"] == 2
    assert metrics["abstention_rate"] == 1.0
    assert metrics["insufficient_evidence_rate"] == 0.5

