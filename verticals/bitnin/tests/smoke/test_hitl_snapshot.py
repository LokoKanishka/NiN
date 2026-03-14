from verticals.bitnin.services.bitnin_hitl.snapshot import compute_snapshot_checksum


def test_hitl_snapshot_checksum_is_deterministic():
    payload = {"request": {"approval_id": "abc"}}
    assert compute_snapshot_checksum(payload) == compute_snapshot_checksum(payload)

