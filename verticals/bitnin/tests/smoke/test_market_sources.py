from verticals.bitnin.services.bitnin_dataset_builder.normalize import (
    normalize_binance_klines,
    normalize_blockchain_market_price,
)
from verticals.bitnin.services.bitnin_dataset_builder.sources import RawFetchResult
from verticals.bitnin.tests.conftest import load_fixture


def test_normalize_blockchain_market_price_fixture():
    raw = RawFetchResult(
        source="blockchain_charts_market_price",
        symbol="BTCUSD",
        interval="1d",
        requested_at="2026-03-13T00:00:00.000Z",
        endpoint="https://api.blockchain.info/charts/market-price",
        params={"timespan": "all", "format": "json", "sampled": "false"},
        payload=load_fixture("blockchain_market_price_sample.json"),
    )

    records = normalize_blockchain_market_price(raw, dataset_version="fixture-v1")
    assert len(records) == 3
    assert records[0]["source"] == "blockchain_charts_market_price"
    assert records[0]["interval"] == "1d"
    assert records[0]["open"] == records[0]["close"] == records[0]["high"] == records[0]["low"]


def test_normalize_binance_klines_fixture():
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
    assert len(records) == 2
    assert records[0]["symbol"] == "BTCUSDT"
    assert records[0]["trade_count"] == 98765
    assert records[0]["quote_volume"] == 115000000.0
