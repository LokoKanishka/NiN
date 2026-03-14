from verticals.bitnin.services.bitnin_shadow.snapshot import compute_snapshot_checksum


def test_shadow_snapshot_checksum_is_deterministic():
    payload = {"intent": {"intent_id": "abc"}, "report_ref": "/tmp/report.md"}
    assert compute_snapshot_checksum(payload) == compute_snapshot_checksum(payload)

