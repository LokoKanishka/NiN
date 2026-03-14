from verticals.bitnin.services.bitnin_analyst.snapshot import compute_snapshot_checksum


def test_analyst_snapshot_checksum_is_deterministic():
    analysis = {
        "analysis_id": "abc",
        "timestamp": "2026-03-13T23:00:00.000Z",
        "market_state": {"summary": "x"},
        "dominant_hypothesis": "y",
        "supporting_factors": ["a"],
        "counterarguments": ["b"],
        "retrieved_episodes": [],
        "confidence": 0.2,
        "recommended_action": "no_trade",
        "risk_level": "unknown",
        "why_now": ["n"],
        "why_not": ["m"],
        "data_coverage_score": 0.5,
        "narrative_coverage_score": 0.0,
        "final_status": "insufficient_evidence",
    }
    assert compute_snapshot_checksum(analysis) == compute_snapshot_checksum(analysis)

