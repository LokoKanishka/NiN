from verticals.bitnin.services.bitnin_dataset_builder.normalize import normalize_binance_klines
from verticals.bitnin.services.bitnin_dataset_builder.sources import RawFetchResult
from verticals.bitnin.services.bitnin_dataset_builder.validate import validate_market_bars
from verticals.bitnin.tests.conftest import load_fixture


def test_validate_market_bars_reports_valid_fixture():
    raw = RawFetchResult(
        source="binance_klines",
        symbol="BTCUSDT",
        interval="4h",
        requested_at="2026-03-13T00:00:00.000Z",
        endpoint="https://data-api.binance.vision/api/v3/klines",
        params={"symbol": "BTCUSDT", "interval": "4h", "limit": 1000},
        payload=load_fixture("binance_klines_sample.json"),
    )
    records = normalize_binance_klines(raw, dataset_version="fixture-v1")

    report = validate_market_bars(records)
    assert report["valid"] is True
    assert report["schema_errors"] == []
    assert report["duplicates"] == []


def test_validate_market_bars_detects_duplicate_and_price_errors():
    invalid = [
        {
            "symbol": "BTCUSDT",
            "source": "binance_klines",
            "interval": "1d",
            "open_time": "2026-01-01T00:00:00.000Z",
            "close_time": "2026-01-01T23:59:59.999Z",
            "open": 101.0,
            "high": 100.0,
            "low": 90.0,
            "close": 89.0,
            "volume": 1.0,
            "dataset_version": "fixture-v1"
        },
        {
            "symbol": "BTCUSDT",
            "source": "binance_klines",
            "interval": "1d",
            "open_time": "2026-01-01T00:00:00.000Z",
            "close_time": "2026-01-01T23:59:59.999Z",
            "open": 99.0,
            "high": 100.0,
            "low": 95.0,
            "close": 98.0,
            "volume": 1.0,
            "dataset_version": "fixture-v1"
        }
    ]

    report = validate_market_bars(invalid)
    assert report["valid"] is False
    assert report["duplicates"]
    assert report["price_errors"]
