import json

from verticals.bitnin.services.bitnin_dataset_builder.builder import MarketDatasetBuilder
from verticals.bitnin.services.bitnin_dataset_builder.sources import RawFetchResult
from verticals.bitnin.tests.conftest import load_fixture


def test_builder_persists_normalized_and_snapshot(monkeypatch, tmp_path):
    builder = MarketDatasetBuilder()

    raw_dir = tmp_path / "raw"
    normalized_dir = tmp_path / "normalized"
    snapshots_dir = tmp_path / "snapshots"
    logs_dir = tmp_path / "logs"
    for path in (raw_dir, normalized_dir, snapshots_dir, logs_dir):
        path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("verticals.bitnin.services.bitnin_dataset_builder.builder.RAW_ROOT", raw_dir)
    monkeypatch.setattr("verticals.bitnin.services.bitnin_dataset_builder.builder.NORMALIZED_ROOT", normalized_dir)
    monkeypatch.setattr("verticals.bitnin.services.bitnin_dataset_builder.builder.SNAPSHOT_ROOT", snapshots_dir)
    monkeypatch.setattr("verticals.bitnin.services.bitnin_dataset_builder.builder.LOG_ROOT", logs_dir)

    fixture = RawFetchResult(
        source="blockchain_charts_market_price",
        symbol="BTCUSD",
        interval="1d",
        requested_at="2026-03-13T00:00:00.000Z",
        endpoint="https://api.blockchain.info/charts/market-price",
        params={"timespan": "all", "format": "json", "sampled": "false"},
        payload=load_fixture("blockchain_market_price_sample.json"),
    )

    class FakeSource:
        def fetch_market_price(self, **kwargs):
            return fixture

    monkeypatch.setattr(
        "verticals.bitnin.services.bitnin_dataset_builder.builder.BlockchainChartsSource",
        lambda: FakeSource(),
    )

    result = builder.build_blockchain_market_price(dataset_version="fixture-v1", mode="full")

    raw_payload = json.loads((raw_dir / next(iter(raw_dir.iterdir())).name).read_text(encoding="utf-8"))
    normalized_lines = (
        normalized_dir / "blockchain_charts_market_price__BTCUSD__1d__fixture-v1.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    snapshot_files = list(snapshots_dir.iterdir())

    assert result.record_count == 3
    assert raw_payload["source"] == "blockchain_charts_market_price"
    assert len(normalized_lines) == 3
    assert len(snapshot_files) == 1
