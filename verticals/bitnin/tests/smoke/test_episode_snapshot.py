import json

from verticals.bitnin.services.bitnin_episode_builder.snapshot import compute_snapshot_checksum, write_snapshot


def test_episode_snapshot_is_deterministic(tmp_path):
    episodes = [
        {
            "episode_id": "ep_1",
            "window_start": "2026-03-01T00:00:00.000Z",
            "window_end": "2026-03-10T23:59:59.999Z",
            "market_signature": {
                "interval": "1d",
                "return_1d": 0.1,
                "return_3d": 0.12,
                "return_7d": "insufficient_history",
                "volatility_regime": "high",
                "drawdown_pre": -0.02,
                "breakout": True,
                "volume_anomaly": True,
                "volume_anomaly_score": 2.0
            },
            "narrative_signature": {
                "topics": ["etf_institucional"],
                "entities": ["Bitcoin"],
                "dominant_cause": "etf_institucional",
                "narrative_confidence": 0.7,
                "event_count": 1
            },
            "summary_local": "sample",
            "outcome": {
                "forward_return_1d": 0.02,
                "forward_return_7d": 0.06,
                "forward_return_30d": "insufficient_horizon",
                "forward_max_up": 0.08,
                "forward_max_down": -0.03,
                "continuation_or_reversion": "continuation"
            },
            "sources": ["market#a"],
            "dataset_version": "fixture-episodes"
        }
    ]
    checksum = compute_snapshot_checksum(episodes)
    path = write_snapshot(
        snapshot_dir=tmp_path,
        dataset_version="fixture-episodes",
        source_slug="BTCUSDT__1d",
        episodes=episodes,
        validation_report={"valid": True, "record_count": 1, "schema_errors": 0, "duplicate_episode_ids": 0},
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["content_checksum"] == checksum
