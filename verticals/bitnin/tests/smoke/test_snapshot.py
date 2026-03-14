import json

from verticals.bitnin.services.bitnin_dataset_builder.snapshot import compute_content_checksum, write_snapshot


def test_snapshot_is_deterministic(tmp_path):
    records = [
        {
            "symbol": "BTCUSDT",
            "source": "binance_klines",
            "interval": "1d",
            "open_time": "2026-01-01T00:00:00.000Z",
            "close_time": "2026-01-01T23:59:59.999Z",
            "open": 1.0,
            "high": 2.0,
            "low": 0.5,
            "close": 1.5,
            "volume": 10.0,
            "dataset_version": "fixture-v1"
        }
    ]
    report = {
        "valid": True,
        "schema_errors": [],
        "duplicates": [],
        "gaps": [],
        "price_errors": [],
        "timestamp_errors": [],
    }

    checksum = compute_content_checksum(records)
    path = write_snapshot(
        snapshot_dir=tmp_path,
        dataset_version="fixture-v1",
        source="binance_klines",
        symbol="BTCUSDT",
        interval="1d",
        records=records,
        validation_report=report,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["content_checksum"] == checksum
    assert payload["record_count"] == 1
