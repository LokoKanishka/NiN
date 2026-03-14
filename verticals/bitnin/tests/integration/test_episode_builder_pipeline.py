import json

from verticals.bitnin.services.bitnin_episode_builder.builder import EpisodeDatasetBuilder
from verticals.bitnin.tests.conftest import FIXTURES_DIR


def test_episode_builder_pipeline_is_idempotent(monkeypatch, tmp_path):
    builder = EpisodeDatasetBuilder()

    raw_dir = tmp_path / "raw"
    normalized_dir = tmp_path / "normalized"
    snapshots_dir = tmp_path / "snapshots"
    logs_dir = tmp_path / "logs"
    for path in (raw_dir, normalized_dir, snapshots_dir, logs_dir):
        path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("verticals.bitnin.services.bitnin_episode_builder.builder.RAW_ROOT", raw_dir)
    monkeypatch.setattr("verticals.bitnin.services.bitnin_episode_builder.builder.NORMALIZED_ROOT", normalized_dir)
    monkeypatch.setattr("verticals.bitnin.services.bitnin_episode_builder.builder.SNAPSHOT_ROOT", snapshots_dir)
    monkeypatch.setattr("verticals.bitnin.services.bitnin_episode_builder.builder.LOG_ROOT", logs_dir)

    market_path = str(FIXTURES_DIR / "episode_market_sample.json")
    narrative_path = str(FIXTURES_DIR / "episode_narrative_sample.json")

    first = builder.build(
        dataset_version="fixture-episodes",
        market_path=market_path,
        narrative_path=narrative_path,
        symbol="BTCUSDT",
        interval="1d",
        pre_bars=3,
        post_bars=7,
    )
    second = builder.build(
        dataset_version="fixture-episodes",
        market_path=market_path,
        narrative_path=narrative_path,
        symbol="BTCUSDT",
        interval="1d",
        pre_bars=3,
        post_bars=7,
    )

    first_lines = (normalized_dir / "episodes__BTCUSDT__1d__fixture-episodes.jsonl").read_text(encoding="utf-8").splitlines()
    episodes = [json.loads(line) for line in first_lines]

    assert first["episode_count"] == second["episode_count"]
    assert episodes
    assert len({episode["episode_id"] for episode in episodes}) == len(episodes)
