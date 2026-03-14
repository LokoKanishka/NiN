import json
from pathlib import Path

from verticals.bitnin.services.bitnin_analyst.context import CurrentContextBuilder
from verticals.bitnin.services.bitnin_backtester.replay import build_replay_points
from verticals.bitnin.tests.conftest import load_fixture


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_context_builder_filters_future_data_for_point_in_time(tmp_path):
    market_path = tmp_path / "market.jsonl"
    narrative_path = tmp_path / "narrative.jsonl"
    episodes_path = tmp_path / "episodes.jsonl"
    _write_jsonl(market_path, load_fixture("analyst_market_sample.json"))
    _write_jsonl(narrative_path, load_fixture("analyst_narrative_sample.json"))
    _write_jsonl(episodes_path, load_fixture("analyst_episodes_sample.json"))

    builder = CurrentContextBuilder(
        market_path=market_path,
        narrative_path=narrative_path,
        episodes_path=episodes_path,
    )
    context = builder.build(
        symbol="BTCUSDT",
        interval="1d",
        as_of="2026-03-12T23:59:59.999Z",
    )

    assert context["market_state"]["as_of"] == "2026-03-12T23:59:59.999Z"
    assert context["recent_narrative"]["event_count"] == 1
    assert context["recent_narrative"]["event_ids"] == ["evt_a"]
    assert context["recent_episode_refs"] == ["ep_a", "ep_b"]


def test_replay_points_respect_warmup_and_max_steps(tmp_path):
    market_path = tmp_path / "market.jsonl"
    _write_jsonl(market_path, load_fixture("analyst_market_sample.json"))
    points = build_replay_points(
        market_path=market_path,
        symbol="BTCUSDT",
        interval="1d",
        warmup_bars=8,
        max_steps=1,
    )
    assert len(points) == 1
    assert points[0]["timestamp"] == "2026-03-13T23:59:59.999Z"

