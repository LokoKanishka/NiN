import json

from verticals.bitnin.services.bitnin_narrative_builder.snapshot import compute_snapshot_checksum, write_snapshot


def test_narrative_snapshot_is_deterministic(tmp_path):
    events = [
        {
            "event_id": "evt_1",
            "timestamp_start": "2026-03-12T09:30:00.000Z",
            "timestamp_end": "2026-03-12T09:31:00.000Z",
            "source_name": "example.com",
            "url": "https://example.com/a",
            "title": "Bitcoin ETF inflows rise",
            "summary_local": "Bitcoin ETF inflows rise. Resumen local basado en metadata permitida.",
            "topics": ["etf_institucional"],
            "entities": ["Bitcoin", "ETF"],
            "dataset_version": "fixture-v1"
        }
    ]
    report = {
        "valid": True,
        "schema_errors": [],
        "timestamp_errors": [],
        "duplicate_event_ids": {},
    }
    checksum = compute_snapshot_checksum(events)
    path = write_snapshot(
        snapshot_dir=tmp_path,
        dataset_version="fixture-v1",
        source="gdelt_doc_artlist",
        query_slug="bitcoin",
        events=events,
        validation_report=report,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["content_checksum"] == checksum
    assert payload["record_count"] == 1
