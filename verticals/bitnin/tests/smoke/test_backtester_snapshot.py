from verticals.bitnin.services.bitnin_backtester.snapshot import compute_snapshot_checksum


def test_backtester_snapshot_checksum_is_deterministic():
    payload = {"run": {"run_id": "abc"}, "report": {"metrics": {"analysis_count": 1}}}
    assert compute_snapshot_checksum(payload) == compute_snapshot_checksum(payload)

